import os
import re
import pandas as pd
import pytesseract
from pdf2image import convert_from_path
from tqdm import tqdm
from PIL import Image, ImageEnhance, ImageFilter
import torch
import numpy as np
from datasets import load_dataset
from transformers import (
    AutoTokenizer,
    AutoModelForSequenceClassification,
    TrainingArguments,
    Trainer,
    EarlyStoppingCallback
)
import evaluate

# ===============================
# CONFIGURAÇÃO
# ===============================
PASTA_ANO_FISCAL = "automatizar/pdfs/BOLETOS" 
CSV_DATASET = "resultados/dataset_classificacao.csv"
TIPOS_VALIDOS = {"NF", "Boleto"}  # tipos aceitos para treino
MODELO_BASE = "neuralmind/bert-base-portuguese-cased"
MAX_TOKENS = 256

# ===============================
# FUNÇÕES DE OCR E PRÉ-PROCESSAMENTO
# ===============================
tesseract_config = '--psm 6'
tesseract_lang = 'por'

def preprocessar_imagem(img):
    """Melhora contraste e nitidez para OCR."""
    img = img.convert("L")
    img = img.filter(ImageFilter.MedianFilter())
    enhancer = ImageEnhance.Contrast(img)
    img = enhancer.enhance(2)
    return img

def normalizar_texto(texto):
    """Remove espaços extras e padroniza datas/valores."""
    texto = " ".join(texto.split())
    texto = re.sub(r"\d{2}/\d{2}/\d{4}", "<DATA>", texto)
    texto = re.sub(r"\d{1,3}(?:\.\d{3})*,\d{2}", "<VALOR>", texto)
    return texto

def extrair_texto_pdf(pdf_path):
    """Extrai texto de todas as páginas do PDF."""
    imagens = convert_from_path(pdf_path, dpi=300)
    texto_final = []
    for img in imagens:
        img = preprocessar_imagem(img)
        texto = pytesseract.image_to_string(img, config=tesseract_config, lang=tesseract_lang)
        texto_final.append(normalizar_texto(texto))
    return " ".join(texto_final)

# ===============================
# MONTAGEM DO DATASET
# ===============================
if os.path.exists(CSV_DATASET):
    df_existente = pd.read_csv(CSV_DATASET)
    registros_existentes = set(zip(df_existente["texto"], df_existente["label"]))
else:
    registros_existentes = set()
dados = []

for pasta_mes, _, arquivos in os.walk(PASTA_ANO_FISCAL):
    for arq in arquivos:
        if arq.lower().endswith(".pdf"):
            partes = arq.rsplit(" - ", 1)
            if len(partes) < 2:
                continue
            tipo = partes[-1].replace(".pdf", "").strip()
            if tipo not in TIPOS_VALIDOS:
                continue

            caminho_pdf = os.path.join(pasta_mes, arq)
            texto = extrair_texto_pdf(caminho_pdf)
            if (texto, tipo) not in registros_existentes:
                dados.append({"texto": texto, "label": tipo})

if dados:
    df_novo = pd.DataFrame(dados)
    if os.path.exists(CSV_DATASET):
        df_final = pd.concat([df_existente, df_novo], ignore_index=True)
    else:
        df_final = df_novo
    df_final.to_csv(CSV_DATASET, index=False)
    print(f"✅ Dataset atualizado com {len(df_final)} registros.")
else:
    print("⚠️ Nenhum novo documento para adicionar ao dataset.")

# ===============================
# TREINAMENTO DO MODELO
# ===============================
dataset = load_dataset('csv', data_files=CSV_DATASET)
tokenizer = AutoTokenizer.from_pretrained(MODELO_BASE)
labels_map = {"NF": 0, "Boleto": 1}

def preprocess_function(examples):
    return tokenizer(examples["texto"], truncation=True, padding="max_length", max_length=MAX_TOKENS)

dataset = dataset.map(preprocess_function, batched=True)
dataset = dataset.map(lambda e: {"label": labels_map[e["label"]]})
splits = dataset["train"].train_test_split(test_size=0.2, stratify_by_column="label", seed=42)

model = AutoModelForSequenceClassification.from_pretrained(MODELO_BASE, num_labels=2)

# Métricas
acc = evaluate.load("accuracy")
f1_metric = evaluate.load("f1")
def compute_metrics(eval_pred):
    logits, labels = eval_pred
    preds = np.argmax(logits, axis=-1)
    return {
        "accuracy": acc.compute(predictions=preds, references=labels)["accuracy"],
        "f1": f1_metric.compute(predictions=preds, references=labels, average="weighted")["f1"]
    }

# Balanceamento de classes
df_labels = pd.read_csv(CSV_DATASET)
class_counts = df_labels["label"].value_counts().to_dict()
total_samples = len(df_labels)
class_weights = {labels_map[k]: total_samples / v for k, v in class_counts.items()}
class_weights_tensor = torch.tensor([class_weights[0], class_weights[1]], dtype=torch.float)
model.config.class_weights = class_weights_tensor.tolist()

# Argumentos de treino
args = TrainingArguments(
    output_dir="./resultados_classificador",
    evaluation_strategy="epoch",
    save_strategy="epoch",
    learning_rate=3e-5,
    per_device_train_batch_size=8,
    per_device_eval_batch_size=8,
    num_train_epochs=10,
    weight_decay=0.01,
    logging_dir="./logs",
    logging_steps=10,
    load_best_model_at_end=True,
    metric_for_best_model="f1",
    greater_is_better=True
)

# Treinador
trainer = Trainer(
    model=model,
    args=args,
    train_dataset=splits["train"],
    eval_dataset=splits["test"],
    tokenizer=tokenizer,
    compute_metrics=compute_metrics,
    callbacks=[EarlyStoppingCallback(early_stopping_patience=3)]
)

print("🚀 Iniciando treinamento...")
trainer.train()

# Salvar modelo
model.save_pretrained("resultados")
tokenizer.save_pretrained("resultados")
print("✅ Modelo treinado e salvo em ./resultados")

# Lembrete de instalar as dependências necessárias:
# pip install pytesseract pdf2image pillow transformers datasets evaluate tqdm
#pip install scikit-learn --break-system-packages


