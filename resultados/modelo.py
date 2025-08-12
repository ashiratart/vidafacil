import os
import pandas as pd
import pytesseract
from pdf2image import convert_from_path
from tqdm import tqdm


tesseract_config = '--psm 6'
tesseract_lang = 'por'  # português


def extrair_texto_pdf(pdf_path):
    imagens = convert_from_path(pdf_path)
    texto_final = []
    for img in imagens:
        texto = pytesseract.image_to_string(img, config=tesseract_config, lang=tesseract_lang)
        texto_final.append(" ".join(texto.split()))
    return " ".join(texto_final)


pasta_base = "automatizar/pdfs"  # caminho
dados = []

for label in ["NF", "BOLETO"]:
    pasta = os.path.join(pasta_base, label)
    for arq in tqdm(os.listdir(pasta), desc=f"Lendo {label}"):
        if arq.lower().endswith(".pdf"):
            caminho_pdf = os.path.join(pasta, arq)
            texto = extrair_texto_pdf(caminho_pdf)
            dados.append({"texto": texto, "label": label})

df = pd.DataFrame(dados)
df.to_csv("dataset_classificacao.csv", index=False)
print(f"✅ Dataset salvo com {len(df)} registros.")

# ===============================
#  Treinamento do modelo
# ===============================
from datasets import load_dataset
from transformers import AutoTokenizer, AutoModelForSequenceClassification, TrainingArguments, Trainer
import numpy as np
import evaluate

dataset = load_dataset('csv', data_files="dataset_classificacao.csv")

tokenizer = AutoTokenizer.from_pretrained("distilbert-base-multilingual-cased")

# Tokenizar textos
dataset = dataset.map(lambda e: tokenizer(e["texto"], truncation=True, padding="max_length", max_length=512), batched=True)

# Mapear rótulos para números
labels_map = {"NF": 0, "BOLETO": 1}
dataset = dataset.map(lambda e: {"label": labels_map[e["label"]]})

# Dividir treino e teste
splits = dataset["train"].train_test_split(test_size=0.2)

# Carregar modelo
model = AutoModelForSequenceClassification.from_pretrained("distilbert-base-multilingual-cased", num_labels=2)

# Métrica
acc = evaluate.load("accuracy")
def compute_metrics(eval_pred):
    logits, labels = eval_pred
    preds = np.argmax(logits, axis=-1)
    return acc.compute(predictions=preds, references=labels)

# Configurações de treino
args = TrainingArguments(
    output_dir="./resultados_classificador",
    evaluation_strategy="epoch",
    learning_rate=2e-5,
    per_device_train_batch_size=8,
    per_device_eval_batch_size=8,
    num_train_epochs=3,
    weight_decay=0.01,
    logging_dir="./logs",
    logging_steps=10,
    save_strategy="epoch"
)

# Criar treinador
trainer = Trainer(
    model=model,
    args=args,
    train_dataset=splits["train"],
    eval_dataset=splits["test"],
    tokenizer=tokenizer,
    compute_metrics=compute_metrics
)

# Treinar
trainer.train()

# Salvar modelo treinado
model.save_pretrained("./modelo_classificador")
tokenizer.save_pretrained("./modelo_classificador")

print("✅ Modelo treinado e salvo em ./modelo_classificador")
