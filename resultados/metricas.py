# Métricas para lembrar-se
# 📊 As métricas mais importantes nesse caso:

#  -  Accuracy (acurácia) → porcentagem de classificações corretas.

#    -  Precision (precisão) → dos PDFs classificados como "Boleto", quantos realmente eram boletos.

#    -  Recall (revocação) → dos boletos existentes, quantos o modelo achou.

#    -  F1-score → equilíbrio entre precisão e recall.
# monitoramento.py
import pandas as pd
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, classification_report
from datetime import datetime
import os

# ==== CONFIGURAÇÕES ====
ARQUIVO_ROTULOS = "datasets/rotulos_reais.csv"
ARQUIVO_PREDICOES = "datasets/predicoes.csv"
HISTORICO_LOGS = "logs_metricas/historico.csv"

# ==== 1. Ler datasets ====
rotulos_df = pd.read_csv(ARQUIVO_ROTULOS)
predicoes_df = pd.read_csv(ARQUIVO_PREDICOES)

# Garantir que só vamos comparar arquivos que existem nos dois
df = pd.merge(rotulos_df, predicoes_df, on="arquivo", suffixes=("_real", "_prev"))

y_true = df["classe_real"]
y_pred = df["classe_prev"]

# ==== 2. Calcular métricas ====
accuracy = accuracy_score(y_true, y_pred)
precision = precision_score(y_true, y_pred, average="weighted", zero_division=0)
recall = recall_score(y_true, y_pred, average="weighted", zero_division=0)
f1 = f1_score(y_true, y_pred, average="weighted", zero_division=0)

# ==== 3. Criar registro de log ====
registro = {
    "data_execucao": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    "total_arquivos": len(df),
    "accuracy": accuracy,
    "precision": precision,
    "recall": recall,
    "f1_score": f1
}

# Criar pasta de logs se não existir
os.makedirs(os.path.dirname(HISTORICO_LOGS), exist_ok=True)

# Salvar no histórico
if not os.path.exists(HISTORICO_LOGS):
    historico_df = pd.DataFrame([registro])
else:
    historico_df = pd.read_csv(HISTORICO_LOGS)
    historico_df = pd.concat([historico_df, pd.DataFrame([registro])], ignore_index=True)

historico_df.to_csv(HISTORICO_LOGS, index=False)

# ==== 4. Mostrar no terminal ====
print("\n📊 RESULTADOS DO MONITORAMENTO 📊")
print(f"Total de arquivos analisados: {len(df)}")
print(f"Accuracy : {accuracy:.2%}")
print(f"Precision: {precision:.2%}")
print(f"Recall   : {recall:.2%}")
print(f"F1-Score : {f1:.2%}")
print("\n--- Relatório por Classe ---")
print(classification_report(y_true, y_pred, zero_division=0))
