import pandas as pd
import joblib

print("📥 Carregando inteligência do modelo de risco...")
# 1. Carrega o modelo treinado que salvamos anteriormente
modelo = joblib.load('modelo_pronaf.joblib')

# 2. Dados REAIS coletados via satélite para o Sítio Olho d'água das Onças
dados_car_exemplo = {
    'ha_original': 0.17,
    'ha_atual': 0.17,
    'var_floresta': 0.00,
    'pasto_recente': 0.00,
    'lavoura_ativa_crops': 0.00,      # Dado real do satélite para a coordenada
    'mosaico_mapbiomas_c21': 0        # Não é área de mosaico agrícola fragmentado
}

# 3. Organiza os dados em um DataFrame de uma única linha
# CRÍTICO: As colunas precisam estar na exata mesma ordem do treinamento!
colunas_modelo = ['ha_original', 'ha_atual', 'var_floresta', 'pasto_recente', 'lavoura_ativa_crops', 'mosaico_mapbiomas_c21']
df_inferencia = pd.DataFrame([dados_car_exemplo])[colunas_modelo]

# 4. O modelo faz a predição (inferência)
resultado_id = modelo.predict(df_inferencia)[0]

# Mapeia o ID numérico de volta para o texto de negócio do banco
dicionario_classes = {
    0: "🥇 CLASSE OURO (Aprovado com Bônus Máximo - Sustentabilidade + Alimento)",
    1: "🚨 CLASSE CRÍTICA (Bloqueado por Risco de Desmatamento/Conversão)",
    2: "✅ CLASSE REGULAR (Aprovado com Taxa Padrão - Propriedade Estável)"
}

print("\n" + "="*60)
print("📊 RESULTADO DA ANÁLISE DE MACHINE LEARNING DO SEU CAR:")
print("="*60)
print(f"-> Veredito Final do Modelo: {dicionario_classes[resultado_id]}")
print("="*60)

# Opcional: Mostrar as probabilidades de o CAR pertencer a cada classe
probabilidades = modelo.predict_proba(df_inferencia)[0]
print("\n🎯 Nível de certeza da IA para cada cenário:")
print(f"• Chance de ser Ouro (Alimento): {probabilidades[0]*100:.1f}%")
print(f"• Chance de ser Crítico (Risco): {probabilidades[1]*100:.1f}%")
print(f"• Chance de ser Regular (Estável): {probabilidades[2]*100:.1f}%")