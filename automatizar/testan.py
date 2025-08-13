import os
import re
import pandas as pd
import pytesseract
from pdf2image import convert_from_path
from tqdm import tqdm
from PIL import Image, ImageEnhance, ImageFilter

# ===============================
# Configuração do OCR
# ===============================
tesseract_config = '--psm 6'
tesseract_lang = 'por'

# Palavras-chave para detecção de tipo
DEFINIR_NF = {"Prefeitura", "Nota Fiscal", "Nota de Serviço", "Recibo"}
DEFINIR_BOLETO = {"Linha Digitável", "Código de Barras", "Agência/Código do Beneficiário", "Agência", "Código do Beneficiário"}

# ===============================
# Funções auxiliares
# ===============================
def preprocessar_imagem(img):
    """Melhora contraste e nitidez para OCR."""
    img = img.convert("L")  # escala de cinza
    img = img.filter(ImageFilter.MedianFilter())  # remove ruído
    enhancer = ImageEnhance.Contrast(img)
    img = enhancer.enhance(2)  # aumenta contraste
    return img

def normalizar_texto(texto):
    """Remove espaços extras e padroniza datas/valores."""
    texto = " ".join(texto.split())  # remove múltiplos espaços
    texto = re.sub(r"\d{2}/\d{2}/\d{4}", "<DATA>", texto)
    texto = re.sub(r"\d{1,3}(?:\.\d{3})*,\d{2}", "<VALOR>", texto)
    return texto

def detectar_tipo_documento(texto):
    """Define rótulo do documento baseado no texto extraído."""
    texto_lower = texto.lower()
    if any(p.lower() in texto_lower for p in DEFINIR_BOLETO):
        return "BOLETO"
    if any(p.lower() in texto_lower for p in DEFINIR_NF):
        return "NF"
    return "BOLETO"  # fallback

def extrair_texto_pdf(pdf_path):
    """Extrai texto processando cada página do PDF."""
    imagens = convert_from_path(pdf_path, dpi=300)
    texto_final = []
    for img in imagens:
        img = preprocessar_imagem(img)
        texto = pytesseract.image_to_string(img, config=tesseract_config, lang=tesseract_lang)
        texto_final.append(normalizar_texto(texto))
    return " ".join(texto_final)

# ===============================
# Montagem do dataset
# ===============================
pasta_base = "automatizar/pdfs"
csv_dataset = "dataset_classificacao.csv"
dados = []

# Carregar dataset existente para evitar duplicatas
if os.path.exists(csv_dataset):
    df_existente = pd.read_csv(csv_dataset)
    registros_existentes = set(zip(df_existente["texto"], df_existente["label"]))
else:
    registros_existentes = set()

# Ler PDFs e extrair dados
for pasta_raiz, _, arquivos in os.walk(pasta_base):
    for arq in tqdm(arquivos, desc=f"Lendo PDFs"):
        if arq.lower().endswith(".pdf"):
            caminho_pdf = os.path.join(pasta_raiz, arq)
            texto = extrair_texto_pdf(caminho_pdf)
            label = detectar_tipo_documento(texto)

            if (texto, label) not in registros_existentes:
                dados.append({"texto": texto, "label": label})

# Salvar dataset atualizado
if dados:
    df_novo = pd.DataFrame(dados)
    if os.path.exists(csv_dataset):
        df_final = pd.concat([df_existente, df_novo], ignore_index=True)
    else:
        df_final = df_novo
    df_final.to_csv(csv_dataset, index=False)
    print(f"✅ Dataset salvo/atualizado com {len(df_final)} registros.")
else:
    print("⚠️ Nenhum novo documento para adicionar ao dataset.")
