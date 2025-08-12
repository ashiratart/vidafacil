import os
import pytesseract
from pdf2image import convert_from_path
import re

# 🔹 Deep Learning (opcional) – carrega só se existir
try:
    from transformers import pipeline
    DL_MODE = True
    # Troque o caminho do modelo abaixo pelo que você treinar
    classificador = pipeline("text-classification", model="./modelo_classificador")
except ImportError:
    DL_MODE = False
    classificador = None

# Configurações globais
tesseract_config = '--psm 6'
tesseract_lang = 'por'

# Definições de documentos (fallback)
DEFINIR_NF = {"Prefeitura", "Nota Fiscal", "Nota de Serviço", "Recibo"}
DEFINIR_BOLETO = {"Linha Digitável", "Código de Barras", "Agência/Código do Beneficiário", "Linha Digitavel", "Agência", "Código do Beneficiário"}

CAMPOS_BOLETO = {
    "Nº do Documento": r"\d+",
    "Vencimento": r"\d{2}/\d{2}/\d{4}",
    "Valor do Documento": r"\d{1,3}(?:\.\d{3})*,\d{2}"
}

CAMPOS_NF = {
    "Número da Nota": r"\d+",
    "Data de Emissão": r"\d{2}/\d{2}/\d{4}(?:\s+\d{2}:\d{2}(?::\d{2})?)?",
    "Data e Hora de Emissão": r"\d{2}/\d{2}/\d{4}(?:\s+\d{2}:\d{2}(?::\d{2})?)?",
    "Valor Total da Nota": r"R?\$?\s*\d{1,3}(?:\.\d{3})*,\d{2}"
}

# -------------------------
# CLASSIFICAÇÃO DE DOCUMENTO
# -------------------------
def detectar_tipo_documento(texto_continuo):
    """Classifica documento usando DL se disponível, senão usa fallback"""
    if DL_MODE and classificador:
        resultado = classificador(texto_continuo[:512], truncation=True)  # corta para evitar texto enorme
        tipo_predito = resultado[0]['label'].upper()
        print(f"🤖 Classificação IA: {tipo_predito}")
        return tipo_predito

    # Fallback por palavras-chave
    texto_lower = texto_continuo.lower()
    if any(p.lower() in texto_lower for p in DEFINIR_BOLETO):
        return "BOLETO"
    if any(p.lower() in texto_lower for p in DEFINIR_NF):
        return "NF"
    return "DESCONHECIDO"

# -------------------------
# RENOMEAR PDF
# -------------------------
def renomear_pdf(caminho, tipo):
    pasta, nome_arquivo = os.path.split(caminho)
    nome, ext = os.path.splitext(nome_arquivo)
    novo_nome = f"{nome}_{tipo}{ext}"
    novo_caminho = os.path.join(pasta, novo_nome)
    os.rename(caminho, novo_caminho)
    print(f"📂 Arquivo renomeado para: {novo_nome}")
    return novo_caminho

# -------------------------
# EXTRAÇÃO POR REGEX (FALLBACK)
# -------------------------
def extrair_campos(texto_continuo, campos):
    encontrados = {}
    for chave, padrao_base in campos.items():
        if chave.lower() in texto_continuo.lower():
            padrao = re.search(
                rf"{re.escape(chave)}(?:\s+\S+){{0,5}}?\s+({padrao_base})",
                texto_continuo,
                re.IGNORECASE
            )
            encontrados[chave] = padrao.group(1) if padrao else None
    return encontrados

# -------------------------
# PROCESSAR PDF
# -------------------------
def processar_pdf(pdf_path, extrair_dados=False):
    print(f"\n🔍 Processando o PDF '{pdf_path}'...")
    imagens = convert_from_path(pdf_path)
    
    tipo_documento = None
    campos_encontrados = {}
    campos_referencia = {}
    
    for i, imagem in enumerate(imagens):
        texto = pytesseract.image_to_string(imagem, config=tesseract_config, lang=tesseract_lang)
        texto_continuo = " ".join(texto.split())
        
        # Detecta tipo na primeira página
        if tipo_documento is None:
            tipo_documento = detectar_tipo_documento(texto_continuo)
            print(f"📄 Documento detectado como: {tipo_documento}")
            campos_referencia = CAMPOS_NF if tipo_documento == "NF" else CAMPOS_BOLETO
            campos_encontrados = {campo: None for campo in campos_referencia}
        
        # Extração de dados (regex por enquanto)
        if extrair_dados:
            novos_campos = extrair_campos(texto_continuo, campos_referencia)
            for campo, valor in novos_campos.items():
                if valor and not campos_encontrados[campo]:
                    campos_encontrados[campo] = valor
                    print(f"✅ {campo}: {valor} (página {i+1})")
            
            if all(campos_encontrados.values()):
                break
    
    novo_caminho = renomear_pdf(pdf_path, tipo_documento)
    
    if extrair_dados:
        print("\n📋 Resultados finais:")
        for campo, valor in campos_encontrados.items():
            print(f"{campo}: {valor if valor else '❌ não encontrado'}")
    
    return novo_caminho, tipo_documento, campos_encontrados if extrair_dados else None

# -------------------------
# EXECUÇÃO
# -------------------------
if __name__ == "__main__":
    caminho_completo = "automatizar/04-10.pdf"
    processar_pdf(caminho_completo, extrair_dados=True)
