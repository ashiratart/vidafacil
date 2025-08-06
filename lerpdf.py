import pdfplumber
import re

caminho_pdf = "Fatura Claro-2.pdf"
nota_chave = "Nº do Documento"

with pdfplumber.open(caminho_pdf) as pdf:
    print(f"Lendo o PDF: {caminho_pdf}")
    
    if not pdf.pages:
        print("⚠️ O PDF não contém páginas.")
        exit(1)

    nota_encontrada = False

    for i, pagina in enumerate(pdf.pages):
        texto = pagina.extract_text()

        print(f"\n--- Página {i + 1} ---\n")
        print(texto)

        if nota_chave in texto:
            print(f"\n✅ Campo '{nota_chave}' encontrado na página {i + 1}")

            # Usando regex para extrair o número após "Nº do Documento"
            padrao = re.search(rf"{re.escape(nota_chave)}\s*[:\-]?\s*(\d+)", texto)

            if padrao:
                numero_nota = padrao.group(1)
                print(f"🧾 Número da nota fiscal: {numero_nota}")
                nota_encontrada = True
                break 
            else:
                print("⚠️ Número da nota não identificado, embora o campo tenha sido encontrado.")
        else:
            print(f"❌ Campo '{nota_chave}' não encontrado na página {i + 1}")

    if not nota_encontrada:
        print("\n❌ Nenhuma nota fiscal encontrada no documento.")
