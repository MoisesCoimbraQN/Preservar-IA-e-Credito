import os
import geopandas as gpd
import pandas as pd
import ee
import time
import numpy as np

print("🔄 Inicializando o motor do Google Earth Engine para auditoria histórica...")
ee.Initialize(project='sustentabilidade-e-cred-rural')

PASTA_TREINO = 'dados_treino_biomas/'
AMOSTRAS_INTERNAS = 1000  # Configuração massiva para os 6.000 registros de produção

BIOMAS_MAPEADOS = {
    'PA': 'Amazonia', 
    'GO': 'Cerrado', 
    'ES': 'Mata_Atlantica',
    'CE': 'Caatinga', 
    'MS': 'Pantanal', 
    'RS': 'Pampa'
}

def extrair_transicao_dinamica_dw(geom_ee):
    """
    Consome o Dynamic World V1 para extrair a cobertura real de 2016 e 2023,
    calculando as variações líquidas reais de Floresta, Pasto e Lavoura.
    """
    resultado = {
        "floresta_pct": 0.0, "pasto_pct": 0.0, "lavoura_pct": 0.0,
        "var_floresta_pct": 0.0, "var_pasto_pct": 0.0, "var_lavoura_pct": 0.0
    }
    try:
        colecao_dw = ee.ImageCollection("GOOGLE/DYNAMICWORLD/V1")
        
        # 1. SAFRA ANTERIOR (ANO BASE 2016)
        mosaico_2016 = colecao_dw.filterBounds(geom_ee).filterDate('2016-01-01', '2016-12-31').select('label').median()
        stats_16 = ee.Image.cat([mosaico_2016.eq(1), mosaico_2016.eq(2), mosaico_2016.eq(4)]).reduceRegion(
            reducer=ee.Reducer.mean(), geometry=geom_ee, scale=30, maxPixels=1e8
        ).getInfo()
        
        f_16 = (stats_16.get('label', 0) or 0) * 100
        p_16 = (stats_16.get('label_1', 0) or 0) * 100
        l_16 = (stats_16.get('label_2', 0) or 0) * 100

        # 2. SAFRA ATUAL (ANO ATUAL 2023)
        mosaico_2023 = colecao_dw.filterBounds(geom_ee).filterDate('2023-01-01', '2023-12-31').select('label').median()
        stats_23 = ee.Image.cat([mosaico_2023.eq(1), mosaico_2023.eq(2), mosaico_2023.eq(4)]).reduceRegion(
            reducer=ee.Reducer.mean(), geometry=geom_ee, scale=30, maxPixels=1e8
        ).getInfo()
        
        f_23 = (stats_23.get('label', 0) or 0) * 100
        p_23 = (stats_23.get('label_1', 0) or 0) * 100
        l_23 = (stats_23.get('label_2', 0) or 0) * 100

        resultado["floresta_pct"] = round(f_23, 2)
        resultado["pasto_pct"] = round(p_23, 2)
        resultado["lavoura_pct"] = round(l_23, 2)
        resultado["var_floresta_pct"] = round(f_23 - f_16, 2)
        resultado["var_pasto_pct"] = round(p_23 - p_16, 2)
        resultado["var_lavoura_pct"] = round(l_23 - l_16, 2)
    except Exception:
        pass
    return resultado

if not os.path.exists(PASTA_TREINO):
    print(f"❌ Erro: A pasta '{PASTA_TREINO}' não existe.")
    exit()

todos_arquivos = [f for f in os.listdir(PASTA_TREINO) if f.endswith('.geojson')]
registros_para_treino = []

print(f"\n🚀 PIPELINE NACIONAL MULTI-REGRA — MATRIZ EM LARGA ESCALA")

for arquivo in todos_arquivos:
    try:
        partes = arquivo.split('_')
        uf = partes[-1].replace('.geojson', '').upper()
        if uf not in BIOMAS_MAPEADOS: continue
            
        bioma = BIOMAS_MAPEADOS[uf]
        caminho_completo = os.path.join(PASTA_TREINO, arquivo)
        
        print(f"\n📁 Processando base de {uf} ({bioma})...")
        gdf_completo = gpd.read_file(caminho_completo)
        gdf_amostra = gdf_completo.sample(n=min(AMOSTRAS_INTERNAS, len(gdf_completo)), random_state=42)
        
        for indice, (idx_original, linha) in enumerate(gdf_amostra.iterrows(), 1):
            try:
                id_car = str(linha['cod_imovel']) if 'cod_imovel' in gdf_amostra.columns else f"{uf}-{idx_original}"
                area_ha = float(linha['area']) if 'area' in gdf_amostra.columns else 0.1
                modulo_fiscal = float(linha['m_fiscal']) if 'm_fiscal' in gdf_amostra.columns else 0.0
                
                if area_ha <= 0.1: continue
                
                geom_json = linha.geometry.__geo_interface__
                geom_ee = ee.Geometry(geom_json)
                sat = extrair_transicao_dinamica_dw(geom_ee)
                
                vf = sat["var_floresta_pct"]
                vp = sat["var_pasto_pct"]
                vl = sat["var_lavoura_pct"]
                
                eh_bioma_nao_florestal = (bioma in ['Cerrado', 'Caatinga', 'Pampa', 'Pantanal'])

                # ⚖️ MATRIZ DE PRECICAÇÃO ESG HOMOLOGADA REFORMULADA
                if (vf < -15.0) or (vp > 20.0 and vf <= 5.0 and vf >= -10.0):
                    target_esg = 0
                elif (vf == 0.0 and vp == 0.0 and vl == 0.0) or \
                     (vp > 0.0 and vf > 0.0) or \
                     (vp > 0.0 and vl > 0.0 and abs(vp - vl) <= 5.0):
                    target_esg = 1
                elif (vf >= -10.0 and vf <= 0.0 and vp < 0.0) or (vl > 0.0 and eh_bioma_nao_florestal):
                    target_esg = 2
                else:
                    target_esg = 1
                
                registros_para_treino.append({
                    'id_car': id_car, 'bioma': bioma, 'estado': uf.lower(),
                    'area_total_ha': round(area_ha, 2), 'porte_mf': round(modulo_fiscal, 4),
                    'ha_perda_floresta': round(area_ha * (sat['floresta_pct'] / 100) * 0.02, 2), 
                    'var_floresta_pct': vf, 'var_pasto_pct': vp, 'var_lavoura_pct': vl,
                    'ha_pasto': round(area_ha * (sat['pasto_pct'] / 100), 2), 'pasto_pct': sat['pasto_pct'],
                    'ha_lavoura': round(area_ha * (sat['lavoura_pct'] / 100), 2), 'lavoura_pct': sat['lavoura_pct'],
                    'target_risco_esg': target_esg
                })
            except Exception:
                continue
    except Exception:
        continue

if registros_para_treino:
    df_abt = pd.DataFrame(registros_para_treino)
    df_abt = pd.get_dummies(df_abt, columns=['bioma'], prefix='bioma', dtype=int)
    for b in BIOMAS_MAPEADOS.values():
        col = f'bioma_{b}'
        if col not in df_abt.columns: df_abt[col] = 0
            
    os.makedirs('dados_car', exist_ok=True)
    df_abt.to_csv('dados_car/base_treino_nacional_xgboost.csv', index=False)
    print(f"\n✅ Concluído! ABT gerada com {df_abt.shape[1]} colunas.")