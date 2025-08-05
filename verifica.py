#!/usr/bin/env python3

import csv
import os

Notas = "notasmes.csv"

def inicializar_arquivo():
    if not os.path.exists(Notas):
        print(f"Arquivo '{Notas}' ainda não criado.")
        exit(1)

def ler():
    print("\nLista de registros encontrados no CSV:\n")
    with open(Notas, newline='', encoding="utf-8") as l:
        reader = csv.DictReader(l)
        for i, linha in enumerate(reader, start=1):
            print(f"{i} | {linha['Apelido']} | {linha['Codigo']}")

def verificar_pdfs_existentes(pasta_pdfs="."):
    apelidos_csv = set()

    # Lê todos os apelidos do CSV
    with open(Notas, newline='', encoding="utf-8") as l:
        reader = csv.DictReader(l)
        for linha in reader:
            apelido = linha.get('Apelido', '').strip().lower()
            if apelido:
                apelidos_csv.add(apelido)

    if not apelidos_csv:
        print("⚠️ Nenhum apelido encontrado no CSV.")
        return False

    # Lista arquivos PDF na pasta
    arquivos_pdf = [
        f for f in os.listdir(pasta_pdfs)
        if f.lower().endswith(".pdf")
    ]
    nomes_pdfs = set(
        os.path.splitext(f)[0].strip().lower()
        for f in arquivos_pdf
    )

    faltando = apelidos_csv - nomes_pdfs

    if faltando:
        print("\n❌ Os seguintes apelidos não possuem PDF correspondente:")
        for apelido in sorted(faltando):
            print(f"- {apelido}.pdf")
        print("\n⚠️ Certifique-se de que os PDFs estejam na pasta correta.")
        return False
    else:
        print("✅ Todos os PDFs correspondentes aos apelidos estão presentes.")
        return True

def main():
    print("📁 Verificador de PDFs por Apelido")
    print("===================================")
    print("\nDeseja continuar? (Y/n) > ", end="")
    resposta = input().strip().lower()

    if resposta == 'y' or resposta == '':
        inicializar_arquivo()
        ler()
        verificar_pdfs_existentes()
        print("\n✅ Operação concluída.\n")
    else:
        print("🚫 Operação cancelada. Saindo do programa.")

if __name__ == "__main__":
    main()
