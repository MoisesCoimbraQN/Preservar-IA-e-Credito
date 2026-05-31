"""
treinar_modelo_xgboost.py
Motor de treinamento supervisionado do Preservar IA.
Ajustado para mapear 16 features explicativas de transição temporal tridimensional.
"""

import os
import pandas as pd
import numpy as np
from xgboost import XGBClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, confusion_matrix
import joblib

print("\n" + "="*80)
print(" 📊 [FIDC ESG] INICIALIZANDO O TREINAMENTO DO CÉREBRO PREDITIVO - PRESERVAR IA")
print("="*80)

caminho_base = 'dados_car/base_treino_nacional_xgboost.csv'

if not os.path.exists(caminho_base):
    print(f"❌ Erro Crítico: O arquivo '{caminho_base}' não foi encontrado.")
    print("👉 Por favor, execute o pipeline geoespacial 'treinar_base_nacional.py' primeiro.")
    exit()

# Carregar a Tabela Analítica Base (ABT) gerada na nuvem
df = pd.read_csv(caminho_base)
print(f"✔️ [DATASET]: ABT carregada com sucesso contendo {len(df)} registros rurais.")

# 1. Isolamento Dinâmico das Dummies de Biomas
colunas_biomas = [col for col in df.columns if 'bioma_' in col]

# 2. Estruturação Oficial das 16 Features Explicativas Tridimensionais
features = [
    'area_total_ha', 'porte_mf', 'ha_perda_floresta', 'var_floresta_pct', 
    'var_pasto_pct', 'var_lavoura_pct', # Variáveis de transição temporal real
    'ha_pasto', 'pasto_pct', 'ha_lavoura', 'lavoura_pct'
] + colunas_biomas

X = df[features]
y = df['target_risco_esg']

print(f"✔️ [MATRIZ]: Modelo configurado estritamente com {len(features)} variáveis explicativas.")

# 3. Segregação Estratificada dos Dados (80% Treino / 20% Teste)
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, stratify=y, random_state=42)

# 4. Ajuste e Calibração do Algoritmo Gradient Boosting (XGBoost)
modelo_xgb = XGBClassifier(
    n_estimators=150, 
    max_depth=5, 
    learning_rate=0.05,
    objective='multi:softprob', 
    num_class=3, 
    random_state=42, 
    eval_metric='mlogloss'
)

print("[TREINO]: Ajustando árvores de decisão aos critérios do Código Florestal...")
modelo_xgb.fit(X_train, y_train)

# 5. Avaliação Macroscópica de Performance com Amostras Inéditas
y_pred = modelo_xgb.predict(X_test)

print("\n" + "="*80)
print(" 📋 RELATÓRIO DE PERFORMANCE DA INTELIGÊNCIA ARTIFICIAL (DESAFIO FIAP)")
print("="*80)

# Mapeamento atualizado dos nomes das alçadas de decisão do banco
target_names_plataforma = [
    'Alçada 0: Risco Crítico (Bloqueado)', 
    'Alçada 1: Risco Regular (Plano Safra)', 
    'Alçada 2: Risco Ouro (Bônus Verde)'
]
print(classification_report(y_test, y_pred, target_names=target_names_plataforma, zero_division=0))

print("🔍 Matriz de Confusão Cruzada (Mapeamento de Acertos vs Erros de Alocação):")
matriz = confusion_matrix(y_test, y_pred)
df_matriz = pd.DataFrame(matriz, index=target_names_plataforma, columns=[f"Previu {c[:9]}" for c in target_names_plataforma])
print(df_matriz)
print("="*80)

# 6. Serialização e Persistência dos Artefatos Estáticos
joblib.dump(modelo_xgb, 'modelo_credito.pkl')
joblib.dump(features, 'features_modelo.pkl')

print("\n🚀 [SUCESSO]: O cérebro estatístico de 16 features explicativas foi salvo em 'modelo_credito.pkl'!")
print("👉 Os artefatos estão prontos para subir via Git para homologação no Render.\n")