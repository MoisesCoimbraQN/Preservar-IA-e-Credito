import pandas as pd
import os

caminho_base = 'dados_car/base_treino_nacional_xgboost.csv'

if not os.path.exists(caminho_base):
    print(f"❌ Erro: O arquivo '{caminho_base}' não foi encontrado.")
    print("Certifique-se de que a sua base de 5941 registros está nessa pasta.")
    exit()

# 1. Carregar a base de dados de 5941 registros que já está salva
df = pd.read_csv(caminho_base)

print(f"🔄 [RECALIBRAÇÃO] Lendo {len(df)} propriedades rurais...")
print("🎯 Nova Filosofia: Target 2 focado em DESMATAMENTO ZERO (Guardião Ambiental).")

# 2. Função com a tua nova regra baseada no satélite de desmatamento (Hansen)
def aplicar_nova_regra_desmatamento(linha):
    var_floresta = linha['var_floresta_pct']
    pasto = linha['pasto_pct']
    lavoura = linha['lavoura_pct']
    uso_total = pasto + lavoura
    
    # Identifica o teto legal do bioma pelas colunas do One-Hot
    teto_uso = 80.0
    if linha.get('bioma_Amazonia', 0) == 1:
        teto_uso = 20.0
    elif linha.get('bioma_Cerrado', 0) == 1 and str(linha.get('id_car', '')).startswith('PA'):
        teto_uso = 65.0

    # 🚨 Alçada 0 (Taxa de Mercado): Estourou o teto da lei OU desmatamento agressivo (> 20%)
    if var_floresta > 20.0 or uso_total > teto_uso:
        return 0
    
    # 🏆 Alçada 2 (Taxa Master Ouro): Cumpre a lei de uso E tem DESMATAMENTO RIGOROSAMENTE ZERO!
    elif var_floresta == 0.0 and uso_total <= teto_uso:
        return 2
    
    # 🌿 Alçada 1 (Taxa Padrão Verde): Cumpre a lei de uso, mas teve alguma supressão permitida (até 20%)
    else:
        return 1

# 3. Aplicar a nova lógica na coluna de alçadas
df['target_risco_esg'] = df.apply(aplicar_nova_regra_desmatamento, axis=1)

# 4. Salvar as alterações de volta no mesmo arquivo CSV
df.to_csv(caminho_base, index=False)

print("\n✅ Recalibração Concluída com Sucesso!")
print("📋 Nova Distribuição das Alçadas de Crédito para o XGBoost:")
distr = df['target_risco_esg'].value_counts().sort_index()
nomes_classes = {0: "Taxa de Mercado", 1: "Taxa Padrão Verde", 2: "Taxa Master Ouro"}
for classe, qtd in distr.items():
    print(f"   🔹 Classe {classe} [{nomes_classes[classe]}]: {qtd} imóveis ({(qtd/len(df))*100:.1f}%)")