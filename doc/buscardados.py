import pyodbc
import csv
import os

# Configuração da conexão com o SQL Server
conexao = pyodbc.connect(
    'DRIVER={ODBC Driver 17 for SQL Server};'
    'SERVER=localhost;'
    'DATABASE=SeuBanco;'
    'UID=seu_usuario;'
    'PWD=sua_senha;'
)

cursor = conexao.cursor()

# Caminho para salvar os resultados
output_dir = "resultados_csv"
os.makedirs(output_dir, exist_ok=True)

# Lê o arquivo CSV com os nomes das tabelas
with open('tabelas.csv', newline='', encoding='utf-8') as csvfile:
    leitor = csv.reader(csvfile)
    for linha in leitor:
        if not linha:
            continue
        tabela = linha[0].strip()
        if not tabela:
            continue

        try:
            query = f"SELECT TOP 2 * FROM {tabela}"
            cursor.execute(query)

            colunas = [desc[0] for desc in cursor.description]
            resultados = cursor.fetchall()

            print(f"\n📌 Tabela: {tabela} — {len(resultados)} linhas encontradas")

            if not resultados:
                print("⚠️ Nenhum dado encontrado. Pulando...")
                continue

            # Cria o arquivo CSV de saída
            nome_arquivo = os.path.join(output_dir, f"tabela_{tabela}.csv")
            with open(nome_arquivo, mode='w', newline='', encoding='utf-8') as saida_csv:
                escritor = csv.writer(saida_csv)
                escritor.writerow(colunas)  # cabeçalhos
                for linha in resultados:
                    escritor.writerow([str(campo) if campo is not None else "NULL" for campo in linha])

            print(f"✅ Resultado salvo em: {nome_arquivo}")

        except Exception as e:
            print(f"❌ Erro ao processar a tabela '{tabela}': {e}")

# Encerra a conexão
cursor.close()
conexao.close()
