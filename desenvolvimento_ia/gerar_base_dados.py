import pandas as pd
import numpy as np

# Mantendo a semente para consistência
np.random.seed(42)

print("⚙️ Escalando a base de dados para 1000 registros históricos com ruído...")

lista_propriedades = []

# Gerando 1000 registros distribuídos igualmente entre os perfis (~250 cada)
for i in range(1000):
    ha_orig = round(np.random.uniform(5.0, 150.0), 2)
    perfil = np.random.choice(['preservado_alimento', 'preservado_pasto', 'desmatador', 'degradado'])
    
    # Ruídos estocásticos normais de medição
    ruido_medicao_flor = np.random.normal(0, 0.4) 
    ruido_medicao_pasto = np.random.normal(0, 0.6)
    
    if perfil == 'preservado_alimento':
        var_flor = round(np.random.uniform(-0.01, 2.0) + ruido_medicao_flor, 2)
        pasto_rec = round(max(0.0, np.random.uniform(0.0, 1.5) + ruido_medicao_pasto), 2)
        crops_rec = round(max(0.0, np.random.uniform(4.0, 20.0) + np.random.normal(0, 1.5)), 2)
        mapbiomas_c21 = 1
        target = 0 # Ouro
        
    elif perfil == 'preservado_pasto':
        var_flor = round(np.random.uniform(-0.03, 0.03) + ruido_medicao_flor, 2)
        pasto_rec = round(max(0.0, np.random.uniform(15.0, 60.0) + ruido_medicao_pasto), 2)
        crops_rec = round(max(0.0, np.random.uniform(0.0, 1.0)), 2)
        mapbiomas_c21 = 0
        target = 2 # Regular
        
    elif perfil == 'desmatador':
        var_flor = round(np.random.uniform(-45.0, -3.0) + ruido_medicao_flor, 2) # Queda drástica
        pasto_rec = round(max(0.0, np.random.uniform(10.0, 50.0) + ruido_medicao_pasto), 2)
        crops_rec = round(max(0.0, np.random.uniform(0.0, 5.0)), 2)
        mapbiomas_c21 = np.random.choice([0, 1])
        target = 1 # Crítico
        
    else: # Degradado/Seca
        var_flor = round(np.random.uniform(-0.04, 0.04) + ruido_medicao_flor, 2)
        pasto_rec = round(max(0.0, np.random.uniform(0.0, 3.0) + ruido_medicao_pasto), 2)
        crops_rec = 0.00
        mapbiomas_c21 = 0
        target = 2 # Regular

    ha_at = round(max(0.1, ha_orig + var_flor), 2)
    var_floresta_calc = round(ha_at - ha_orig, 2)
    
    # Taxa de erro de rotulagem de 10% (Inversão de alvos)
    if np.random.rand() < 0.10:
        target = np.random.choice([0, 1, 2])
        
    lista_propriedades.append({
        'ha_original': ha_orig,
        'ha_atual': ha_at,
        'var_floresta': var_floresta_calc,
        'pasto_recente': pasto_rec,
        'lavoura_ativa_crops': crops_rec,
        'mosaico_mapbiomas_c21': mapbiomas_c21,
        'classe_risco': target
    })

df_treino = pd.DataFrame(lista_propriedades)
df_treino = df_treino.sample(frac=1, random_state=42).reset_index(drop=True)
df_treino.to_csv('dataset_treino.csv', index=False)

print(f"💾 Base de dados robusta gerada! 'dataset_treino.csv' salvo com {len(df_treino)} linhas.")