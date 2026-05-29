import ee

# Inicializa apontando para o seu projeto configurado
ee.Initialize(project='sustentabilidade-e-cred-rural')

print("✅ Google Earth Engine inicializado com sucesso!")

# 1. DADOS DO IMÓVEL (Sítio Olho d'água das Onças - PB)
latitude = -6.431292
longitude = -36.290417

ponto_central = ee.Geometry.Point([longitude, latitude])
geometria_fazenda = ponto_central.buffer(100) 

print("✅ Polígono de teste gerado com sucesso!")

# =========================================================================
# ANÁLISE 1: FLORESTA NATIVA (Dataset Hansen NASA/USGS)
# =========================================================================
dados_hansen = ee.Image("UMD/hansen/global_forest_change_2025_v1_13").clip(geometria_fazenda)

floresta_2000_img = dados_hansen.select('treecover2000').gte(30)
perda_img = dados_hansen.select('loss')
ganho_img = dados_hansen.select('gain')

area_pixel = ee.Image.pixelArea()

stats_original = floresta_2000_img.multiply(area_pixel).reduceRegion(
    reducer=ee.Reducer.sum(), geometry=geometria_fazenda, scale=30, maxPixels=1e9
)
stats_perda = perda_img.multiply(area_pixel).reduceRegion(
    reducer=ee.Reducer.sum(), geometry=geometria_fazenda, scale=30, maxPixels=1e9
)
stats_ganho = ganho_img.multiply(area_pixel).reduceRegion(
    reducer=ee.Reducer.sum(), geometry=geometria_fazenda, scale=30, maxPixels=1e9
)

ha_original = stats_original.getNumber('treecover2000').divide(10000).getInfo()
ha_perda = stats_perda.getNumber('loss').divide(10000).getInfo()
ha_ganho = stats_ganho.getNumber('gain').divide(10000).getInfo()
ha_atual = ha_original - ha_perda + ha_ganho


# =========================================================================
# ANÁLISE 2: USO DO SOLO / PASTAGENS (Dataset Google/WRI Dynamic World)
# =========================================================================
# Dynamic World usa dados de IA baseados no Sentinel-2 (10m de resolução)
colecao_dw = ee.ImageCollection("GOOGLE/DYNAMICWORLD/V1")

# Filtramos uma janela de tempo segura no início do projeto (2019) e uma recente (2023)
dw_2019 = colecao_dw.filterDate('2019-01-01', '2019-12-31').filterBounds(geometria_fazenda).mean()
dw_recente = colecao_dw.filterDate('2023-01-01', '2023-12-31').filterBounds(geometria_fazenda).mean()

# Selecionamos a banda de probabilidade de ser Pastagem ('grass')
pasto_2019_img = dw_2019.select('grass').gte(0.2) # Pixels com mais de 20% de certeza de pasto
pasto_recente_img = dw_recente.select('grass').gte(0.2)

# Redução regional para computar os hectares de pasto (escala de 10 metros!)
stats_pasto_2019 = pasto_2019_img.multiply(area_pixel).reduceRegion(
    reducer=ee.Reducer.sum(), geometry=geometria_fazenda, scale=10, maxPixels=1e9
)
stats_pasto_recente = pasto_recente_img.multiply(area_pixel).reduceRegion(
    reducer=ee.Reducer.sum(), geometry=geometria_fazenda, scale=10, maxPixels=1e9
)

ha_pasto_2019 = stats_pasto_2019.getNumber('grass').divide(10000).getInfo()
ha_pasto_recente = stats_pasto_recente.getNumber('grass').divide(10000).getInfo()


# =========================================================================
# 4. SAÍDAS ISOLADAS PARA O ALGORITMO DE CLASSIFICAÇÃO
# =========================================================================
print("\n" + "="*50)
print("📥 VARIÁVEIS EXTRAÍDAS (PRONTAS PARA O MODELO FINAL)")
print("="*50)
print(f"-> Floresta Original (2000)   : {ha_original:.2f} ha")
print(f"-> Floresta Atual             : {ha_atual:.2f} ha (Perda: {ha_perda:.2f} ha | Ganho: {ha_ganho:.2f} ha)")
print(f"-> Área de Pastagem (2019)    : {ha_pasto_2019:.2f} ha")
print(f"-> Área de Pastagem (Recente) : {ha_pasto_recente:.2f} ha")
print("="*50)

var_floresta = ha_atual - ha_original
var_pasto = ha_pasto_recente - ha_pasto_2019

print("\n📝 DIAGNÓSTICO PRELIMINAR:")
print(f"• Variação da Floresta: {var_floresta:+.2f} ha")
print(f"• Variação da Pastagem: {var_pasto:+.2f} ha (Período 2019-2023)")