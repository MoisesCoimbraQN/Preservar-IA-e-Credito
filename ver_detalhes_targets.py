import pandas as pd
import os

caminho_base = 'dados_car/base_treino_nacional_xgboost.csv'

if not os.path.exists(caminho_base):
    print(f"❌ Erro: O arquivo '{caminho_base}' não foi encontrado. Aguarde o término do pipeline de satélites.")
    exit()

# 1. Carregar a base analítica gerada
df = pd.read_csv(caminho_base)

# Dicionário de tradução para ficar legível na tela
traducao_target = {
    0: "🚨 0: TAXA DE MERCADO (Inconformidade/Risco)",
    1: "🌿 1: TAXA PADRÃO VERDE (Baixa Intensidade)",
    2: "🏆 2: TAXA MASTER OURO (Preserva + Produz)"
}

print("="*80)
print(f"🔍 [AUDITORIA DE TARGETS] Analisando {len(df)} propriedades rurais...")
print("="*80)

# 2. Mostrar exemplos reais de cada Target para validação das regras
for t in [0, 1, 2]:
    sub_df = df[df['target_risco_esg'] == t]
    
    print(f"\n👉 Exemplos de Imóveis Classificados com o Target {t}:")
    print(f"   (Total nesta categoria: {len(sub_df)} imóveis)")
    print("-" * 80)
    
    if len(sub_df) == 0:
        print("   ❌ Nenhum imóvel encontrado nesta alçada ainda.")
    else:
        # Seleciona as colunas principais para exibir de forma limpa no terminal
        colunas_exibicao = [
            'id_car', 'estado', 'area_total_ha', 
            'var_floresta_pct', 'pasto_pct', 'lavoura_pct'
        ]
        # Pega as primeiras 5 linhas desse target para te mostrar
        amostra = sub_df[colunas_exibicao].head(5)
        print(amostra.to_string(index=False))
    print("-" * 80)

# 3. EXTRA: Salvar uma amostra no Excel para você abrir e ver todos se quiser
try:
    caminho_amostra_excel = 'dados_car/amostra_auditoria_targets.xlsx'
    # Salva as primeiras 100 linhas da base para inspecionar no Excel
    df.head(100).to_excel(caminho_amostra_excel, index=False)
    print(f"\n💡 [DICA] Salvei as primeiras 100 linhas completas em '{caminho_amostra_excel}'")
    print("   Você pode abrir esse arquivo no Excel para ver o target de cada um linha por linha!")
except Exception:
    pass

print("="*80)