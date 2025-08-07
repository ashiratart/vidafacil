import pytesseract
from pdf2image import convert_from_path
import re

# Caminho do PDF
caminho_pdf = "04-10.pdf"
nota_chave = "Nº do Documento"

# Configuração do Tesseract
tesseract_config = '--psm 6'  # Modo semi-estruturado
tesseract_lang = 'por'        # Idioma português (instale com: sudo apt install tesseract-ocr-por)

# Se estiver no Windows e tesseract não estiver no PATH, descomente e edite:
# pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

def realizar_ocr_em_pdf(pdf_path):
    print(f"🔍 Convertendo o PDF '{pdf_path}' em imagens para OCR...")
    imagens = convert_from_path(pdf_path)

    nota_encontrada = False

    for i, imagem in enumerate(imagens):
        print(f"\n--- Página {i + 1} ---")
        texto = pytesseract.image_to_string(imagem, config=tesseract_config, lang=tesseract_lang)
        print(texto)

        if nota_chave in texto:
            print(f"\n✅ Campo '{nota_chave}' encontrado na página {i + 1}")

            # Expressão regular para encontrar o número após "Nº do Documento"
            padrao = re.search(rf"{re.escape(nota_chave)}\s*[:\-]?\s*(\d+)", texto)

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
