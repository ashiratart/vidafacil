import pytesseract
from pdf2image import convert_from_path
import re

# Caminho do PDF
caminho_pdf = "automatizar/04-10.pdf"
nota_chave = "Nº do Documento"

# Configuração do Tesseract
tesseract_config = '--psm 6'  # Modo semi-estruturado
tesseract_lang = 'por'        # Idioma português

def realizar_ocr_em_pdf(pdf_path):
    print(f"🔍 Convertendo o PDF '{pdf_path}' em imagens para OCR...")
    imagens = convert_from_path(pdf_path)

    nota_encontrada = False

    for i, imagem in enumerate(imagens):
        print(f"\n--- Página {i + 1} ---")
        texto = pytesseract.image_to_string(imagem, config=tesseract_config, lang=tesseract_lang)
        
        # Texto contínuo
        texto_continuo = " ".join(texto.split())

        if nota_chave.lower() in texto_continuo.lower():
            print(f"\n✅ Campo '{nota_chave}' encontrado na página {i + 1}")

            # Regex tolerante a palavras no meio antes do número
            padrao = re.search(
                rf"{re.escape(nota_chave)}(?:\s+\S+){{0,5}}?\s+(\d+)",
                texto_continuo,
                re.IGNORECASE
            )

            if padrao:
                numero_nota = padrao.group(1)
                print(f"🧾 Número da nota fiscal: {numero_nota}")
                nota_encontrada = True
                break
            else:
                print("⚠️ Campo encontrado, mas número não identificado.")
        else:
            print(f"❌ Campo '{nota_chave}' não encontrado nesta página.")

    if not nota_encontrada:
        print("\n❌ Nenhuma nota fiscal encontrada no documento.")

# Executa o OCR
realizar_ocr_em_pdf(caminho_pdf)

