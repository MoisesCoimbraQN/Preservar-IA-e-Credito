import pandas as pd
import numpy as np
from xgboost import XGBClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, confusion_matrix
import joblib
import os

print("📊 [FIDC ESG] Lendo a Base Analítica Nacional Consolidada (ABT)...")
caminho_base = 'dados_car/base_treino_nacional_xgboost.csv'

if not os.path.exists(caminho_base):
    print(f"❌ Erro: O arquivo '{caminho_base}' não foi encontrado. Rode o pipeline 'treinar_base_nacional.py' primeiro.")
    exit()

# Carregar o dataset gerado pelo pipeline de satélite
df = pd.read_csv(caminho_base)

# 1. Mapeamento das Colunas de Decisão (Features)
# Captura as colunas de bioma geradas pelo One-Hot Encoding (bioma_Amazonia, bioma_Cerrado, etc.)
colunas_biomas = [col for col in df.columns if 'bioma_' in col]

# Lista exata das 11 colunas preditivas estruturadas
features = [
    'area_total_ha', 
    'porte_mf', 
    'ha_perda_floresta', 
    'var_floresta_pct', 
    'ha_pasto', 
    'pasto_pct', 
    'ha_lavoura', 
    'lavoura_pct'
] + colunas_biomas

X = df[features]
y = df['target_risco_esg']

print(f"📈 Matriz de Features carregada: {X.shape[0]} propriedades com {X.shape[1]} variáveis de decisão.")

# Exibir a distribuição real das 3 alçadas na base de dados para validação
print("\n📋 Distribuição das Alçadas de Crédito geradas pelo pipeline:")
distribuicao = y.value_counts().sort_index()
nomes_classes = {0: "🚨 Taxa de Mercado (Risco/Inconformidade)", 1: "🌿 Taxa Padrão Verde (Baixa Intensidade)", 2: "🏆 Taxa Master Ouro (Alta Eficiência + Lei)"}
for classe, qtd in distribuicao.items():
    print(f"   🔹 Classificação {classe} [{nomes_classes[classe]}]: {qtd} imóveis ({(qtd/len(y))*100:.1f}%)")

# 2. Divisão Estatística: Treino (80%) e Teste/Validação (20%)
# O 'stratify=y' é obrigatório aqui para garantir que a proporção das 3 taxas seja idêntica no treino e no teste
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, stratify=y, random_state=42)

print(f"\n🧱 Divisão de Amostragem Concluída:")
print(f"   🔹 Registros para Treinamento do Algoritmo: {X_train.shape[0]}")
print(f"   🔹 Registros para Validação Cega (Teste): {X_test.shape[0]}")

print("\n🤖 Configurando e Treinando o Classificador Multiclasse XGBoost...")

# 3. Inicialização do Modelo XGBoost para 3 Classes
# Parâmetros calibrados para evitar Overfitting e lidar com dados multiclasse do agronegócio
modelo_xgb = XGBClassifier(
    n_estimators=150,
    max_depth=5,
    learning_rate=0.05,
    objective='multi:softprob',  # Define o objetivo para classificação multiclasse probabilística
    num_class=3,                 # Informa que o modelo prevê exatamente as classes 0, 1 e 2
    random_state=42,
    eval_metric='mlogloss'
)

# O modelo estuda os padrões de cruzamento (Bioma vs Uso vs Desmatamento) aqui
modelo_xgb.fit(X_train, y_train)

# 4. Avaliação de Performance com Dados Inéditos (X_test)
y_pred = modelo_xgb.predict(X_test)

print("\n" + "="*60)
print("📋 RELATÓRIO DE PERFORMANCE DA INTELIGÊNCIA ARTIFICIAL (NUCLEA FIAP)")
print("="*60)

# Gerar relatório completo de métricas (Precision, Recall, F1-Score) para cada alçada
target_names_plataforma = [
    '0: Taxa de Mercado', 
    '1: Taxa Padrão Verde', 
    '2: Taxa Master Ouro'
]
print(classification_report(y_test, y_pred, target_names=target_names_plataforma, zero_division=0))

print("🔍 Matriz de Confusão Cruzada (Acertos vs Erros de Alocação):")
matriz = confusion_matrix(y_test, y_pred)

# Exibir a matriz de forma visual no terminal
df_matriz = pd.DataFrame(matriz, index=target_names_plataforma, columns=[f"Previu {c}" for c in target_names_plataforma])
print(df_matriz)

# 5. Exportação do "Cérebro" Treinado para o Deploy
caminho_modelo = 'modelo_credito.pkl'
joblib.dump(modelo_xgb, caminho_modelo)

print("\n" + "="*60)
print(f"🚀 PIPELINE DE MACHINE LEARNING CONCLUÍDO COM SUCESSO!")
print(f"📦 Arquivo binário exportado na raiz: '{caminho_modelo}'")
# Salva as colunas na ordem exata para blindar o app.py contra erros de input de dados
joblib.dump(features, 'features_modelo.pkl')
print("💡 O cérebro preditivo de 3 alçadas está pronto para consumo no Dashboard Dash.")
print("="*60)