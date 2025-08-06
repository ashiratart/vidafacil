import pdfplumber

# Caminho do seu PDF
caminho_pdf = "04-10.pdf"

with pdfplumber.open(caminho_pdf) as pdf:
    print(f"Lendo o PDF: {caminho_pdf}")
    
    if not pdf.pages:
        print("⚠️ O PDF não contém páginas.")
        exit(1)

    nota_encontrada = False

    for i, pagina in enumerate(pdf.pages):
        tabelas = pagina.extract_tables()

        # DEBUG: se quiser ver todas as tabelas extraídas, descomente abaixo
        for t_idx, tabela in enumerate(tabelas, start=1):
             print(f"\n--- Tabela {t_idx} ---")
             for linha in tabela:
                 print(linha)

        for tabela in tabelas:
            for idx, linha in enumerate(tabela):
                if linha and any(celula and "Nº do Documento" in celula for celula in linha):
                    # Tenta pegar a próxima linha (com o valor)
                    if idx + 1 < len(tabela):
                        linha_valor = tabela[idx + 1]
                        numero_nota = linha_valor[0].strip() if linha_valor[0] else "Não encontrado"
                        print(f"\n✅ Número da nota fiscal encontrado na página {i+1}: {numero_nota}")
                        nota_encontrada = True
                        break
            if nota_encontrada:
                break

    if not nota_encontrada:
        print("\n❌ Nenhuma nota fiscal encontrada no documento.")
