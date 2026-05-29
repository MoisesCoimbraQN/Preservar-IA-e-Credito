import pandas as pd
import numpy as np
import joblib
import os
import matplotlib.pyplot as plt

print("🔍 [AUDITORIA] Carregando o Modelo Nacional e os Metadados...")

# Ajuste o nome aqui para o arquivo exato que você salvou (ex: 'modelo_credito.pkl')
caminho_modelo = 'modelo_credito.pkl'
caminho_features = 'features_modelo.pkl'
caminho_base = 'dados_car/base_treino_nacional_xgboost.csv'

if not os.path.exists(caminho_modelo):
    print(f"❌ Erro: O arquivo do modelo '{caminho_modelo}' não foi encontrado na raiz.")
    exit()

# 1. Carregar os arquivos binários
modelo = joblib.load(caminho_modelo)
features = joblib.load(caminho_features)

print("✅ Modelo carregado com sucesso!")
print(f"📋 O modelo foi treinado esperando exatamente as seguintes {len(features)} colunas:")
print(f"   ➔ {features}\n")

# 2. Extrair a Importância das Variáveis (Feature Importance)
# Isso mostra para a banca quais colunas pesaram mais na decisão do FIDC
importancias = modelo.feature_importances_
indices = np.argsort(importancias)[::-1]

print("🏆 RANKING DE IMPORTÂNCIA DAS COLUNAS (O que a IA olha mais):")
print("=" * 60)
for i, idx in enumerate(indices):
    print(f"   {i+1}º. {features[idx]:<25} ➔ {importancias[idx]*100:.2f}% de relevância")
print("=" * 60)

# 3. Verificar a distribuição da base se o CSV existir
if os.path.exists(caminho_base):
    df = pd.read_csv(caminho_base)
    print("\n📊 Análise Estatística da Base de Dados Gerada:")
    print(f"   🔹 Total de propriedades avaliadas: {len(df)}")
    
    nomes_classes = {
        0: "🚨 Taxa de Mercado (Risco/Inconformidade)",
        1: "🌿 Taxa Padrão Verde (Baixa Intensidade)",
        2: "🏆 Taxa Master Ouro (Alta Eficiência + Lei)"
    }
    
    distr = df['target_risco_esg'].value_counts().sort_index()
    print("   🔹 Distribuição final das alçadas no dataset:")
    for classe, qtd in distr.items():
        rotulo = nomes_classes.get(classe, f"Classe {classe}")
        print(f"      ➔ {rotulo}: {qtd} imóveis ({(qtd/len(df))*100:.1f}%)")

# 4. Gerar Gráfico de Importância para colocar nos slides da FIAP
try:
    plt.figure(figsize=(10, 6))
    plt.title("Importância das Features - Modelo de Crédito ESG Nacional")
    plt.bar(range(len(features)), importancias[indices], align="center", color="seagreen")
    plt.xticks(range(len(features)), [features[i] for i in indices], rotation=45, ha='right')
    plt.tight_layout()
    plt.savefig('dados_car/importancia_features_fiap.png')
    print("\n📊 [SUCESSO] Gráfico 'importancia_features_fiap.png' gerado na pasta 'dados_car/'!")
except Exception as e:
    print(f"\n⚠️ Não foi possível gerar o gráfico: {e}")