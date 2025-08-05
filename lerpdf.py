import pdfplumber

# Caminho para a nota fiscal em PDF
caminho_pdf = "nota_fiscal.pdf"

with pdfplumber.open(caminho_pdf) as pdf:
    for i, pagina in enumerate(pdf.pages):
        texto = pagina.extract_text()
        print(f"\n--- Página {i+1} ---\n")
        print(texto)
