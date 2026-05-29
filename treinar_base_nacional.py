import os
import geopandas as gpd
import pandas as pd
import ee
import time

# 1. Inicializar o motor do Google Earth Engine
print("🔄 Inicializando o motor do Google Earth Engine com Regras Florestais Nacionais...")
ee.Initialize(project='sustentabilidade-e-cred-rural')

PASTA_TREINO = 'dados_treino_biomas/'
AMOSTRAS_INTERNAS = 1000  # 🚀 AMPLIAÇÃO DA AMOSTRAGEM PARA 1000 IMÓVEIS POR BIOMA

BIOMAS_MAPEADOS = {
    'PA': 'Amazonia', 
    'GO': 'Cerrado', 
    'ES': 'Mata_Atlantica',
    'CE': 'Caatinga', 
    'MS': 'Pantanal', 
    'RS': 'Pampa'
}

def extrair_metricas_satelite(geom_ee):
    """ Calcula Floresta (Hansen), Pasto e Lavoura (MapBiomas) para o polígono """
    metricas = {'perda_floresta': 0.0, 'area_pasto': 0.0, 'area_lavoura': 0.0}
    try:
        # A. PERDA DE FLORESTA (Hansen)
        hansen = ee.Image('UMD/hansen/global_forest_change_2023_v1_11')
        loss_area = hansen.select('loss').multiply(ee.Image.pixelArea()).reduceRegion(
            reducer=ee.Reducer.sum(), geometry=geom_ee, scale=30, maxPixels=1e9
        ).getInfo()
        metricas['perda_floresta'] = round((loss_area.get('loss', 0) / 10000), 2)
        
        # B. USO DO SOLO: PASTO E LAVOURA (MapBiomas Coleção 8)
        mapbiomas = ee.ImageCollection('projects/mapbiomas-workspace/public/collection8/mapbiomas_collection80_integration_v1')\
            .filterDate('2022-01-01', '2023-12-31').mosaic()
            
        area_imagem = ee.Image.pixelArea()
        
        # Código 15 = Pastagem no MapBiomas
        pasto_mask = mapbiomas.eq(15)
        pasto_stats = area_imagem.updateMask(pasto_mask).reduceRegion(
            reducer=ee.Reducer.sum(), geometry=geom_ee, scale=30, maxPixels=1e9
        ).getInfo()
        metricas['area_pasto'] = round((pasto_stats.get('area', 0) / 10000), 2)
        
        # Código 18 = Agricultura (Culturas) no MapBiomas
        lavoura_mask = mapbiomas.eq(18)
        lavoura_stats = area_imagem.updateMask(lavoura_mask).reduceRegion(
            reducer=ee.Reducer.sum(), geometry=geom_ee, scale=30, maxPixels=1e9
        ).getInfo()
        metricas['area_lavoura'] = round((lavoura_stats.get('area', 0) / 10000), 2)
        
    except Exception:
        pass
    return metricas

if not os.path.exists(PASTA_TREINO):
    print(f"❌ Erro: A pasta '{PASTA_TREINO}' não existe.")
    exit()

todos_arquivos = [f for f in os.listdir(PASTA_TREINO) if f.endswith('.geojson')]
registros_para_treino = []

print(f"\n🚀 PIPELINE NACIONAL MULTI-REGRA — MATRIZ EM LARGA ESCALA (N={AMOSTRAS_INTERNAS})")

for arquivo in todos_arquivos:
    try:
        partes = arquivo.split('_')
        uf = partes[-1].replace('.geojson', '').upper()
        if uf not in BIOMAS_MAPEADOS: continue
            
        bioma = BIOMAS_MAPEADOS[uf]
        caminho_completo = os.path.join(PASTA_TREINO, arquivo)
        
        print(f"\n📁 Processando base de {uf} ({bioma}). Extrais {AMOSTRAS_INTERNAS} amostras...")
        gdf_completo = gpd.read_file(caminho_completo)
        
        # Sorteia dinamicamente até 1000 amostras do GeoJSON do estado
        gdf_amostra = gdf_completo.sample(n=min(AMOSTRAS_INTERNAS, len(gdf_completo)), random_state=42)
        
        for indice, (idx_original, linha) in enumerate(gdf_amostra.iterrows(), 1):
            try:
                id_car = str(linha['cod_imovel']) if 'cod_imovel' in gdf_amostra.columns else f"{uf}-{idx_original}"
                area_ha = float(linha['area']) if 'area' in gdf_amostra.columns else 0.1
                modulo_fiscal = float(linha['m_fiscal']) if 'm_fiscal' in gdf_amostra.columns else 0.0
                
                if area_ha <= 0.1: continue
                
                # Executa a chamada combinada de satélites no GEE
                geom_json = linha.geometry.__geo_interface__
                geom_ee = ee.Geometry(geom_json)
                sat = extrair_metricas_satelite(geom_ee)
                
                var_floresta_pct = round((sat['perda_floresta'] / area_ha) * 100, 2)
                pasto_pct = round((sat['area_pasto'] / area_ha) * 100, 2)
                lavoura_pct = round((sat['area_lavoura'] / area_ha) * 100, 2)
                
                # 1. Calcular o uso total consolidado da terra
                uso_total_pct = pasto_pct + lavoura_pct
                
                # 2. Definir o teto legal permitido por bioma (Código Florestal)
                if bioma == 'Amazonia':
                    teto_uso_permitido = 20.0
                elif bioma == 'Cerrado' and uf.upper() == 'PA': 
                    teto_uso_permitido = 65.0
                elif bioma == 'Cerrado':
                    teto_uso_permitido = 80.0
                else:
                    teto_uso_permitido = 80.0

                # ⚖️ MATRIZ DE PRECIFICAÇÃO HOMOLOGADA — FILOSOFIA DE CONSERVAÇÃO FLORESTAL
                # Alçada 0 (Taxa de Mercado): Estourou a lei de uso OU desmatamento agressivo (> 20%)
                if var_floresta_pct > 20.0 or uso_total_pct > teto_uso_permitido:
                    target_esg = 0
                
                # Alçada 2 (Taxa Master Ouro): Cumpre a lei E tem DESMATAMENTO RIGOROSAMENTE ZERO
                elif var_floresta_pct == 0.0 and uso_total_pct <= teto_uso_permitido:
                    target_esg = 2
                
                # Alçada 1 (Taxa Padrão Verde): Cumpre a lei, mas teve alguma supressão permitida/histórica
                else:
                    target_esg = 1
                
                registros_para_treino.append({
                    'id_car': id_car, 'bioma': bioma, 'estado': uf.lower(),
                    'area_total_ha': round(area_ha, 2), 'porte_mf': round(modulo_fiscal, 4),
                    'ha_perda_floresta': sat['perda_floresta'], 'var_floresta_pct': var_floresta_pct,
                    'ha_pasto': sat['area_pasto'], 'pasto_pct': pasto_pct,
                    'ha_lavoura': sat['area_lavoura'], 'lavoura_pct': lavoura_pct,
                    'target_risco_esg': target_esg
                })
                
                # Print resumido para não inundar o terminal
                if indice % 50 == 0 or target_esg == 2:
                    print(f"   ➔ Processados {indice}/{AMOSTRAS_INTERNAS} de {uf} | Último Target: {target_esg}")
                
                # Pausa estratégica para respeitar os limites de requisição do Earth Engine
                time.sleep(0.1)
                
            except Exception:
                continue
    except Exception:
        continue

# 3. Consolidar e Salvar a ABT Ampliada
if registros_para_treino:
    df_abt = pd.DataFrame(registros_para_treino)
    
    # One-Hot Encoding dos Biomas
    df_abt = pd.get_dummies(df_abt, columns=['bioma'], prefix='bioma', dtype=int)
    for b in BIOMAS_MAPEADOS.values():
        col = f'bioma_{b}'
        if col not in df_abt.columns: df_abt[col] = 0
            
    # Garantir a criação da pasta caso não exista
    os.makedirs('dados_car', exist_ok=True)
    df_abt.to_csv('dados_car/base_treino_nacional_xgboost.csv', index=False)
    print(f"\n✅ Concluído! Nova base volumétrica gerada com {len(df_abt)} registros na tabela analítica.")