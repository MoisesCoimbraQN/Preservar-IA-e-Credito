import ee

try:
    # 1. Tenta inicializar a biblioteca
    ee.Initialize()
    print("✅ Google Earth Engine inicializado com sucesso!")
except Exception as e:
    # 2. Se for a primeira vez na máquina, ele vai pedir para você autenticar
    print("🔄 Autenticação necessária. Siga as instruções na tela...")
    ee.Authenticate()
    ee.Initialize()
    print("✅ Google Earth Engine autenticado e inicializado!")

# 3. TESTE DE CONEXÃO: Vamos tentar ler os metadados do MapBiomas (Uso do Solo do Brasil)
try:
    mapbiomas_dados = ee.ImageCollection("projects/mapbiomas-workspace/public/collection8/mapbiomas_collection80_integration_v1")
    # Pegamos apenas uma imagem recente para testar a velocidade da query
    imagem_teste = mapbiomas_dados.filter(ee.Filter.eq('year', 2022)).first()
    info = imagem_teste.getInfo()
    print("✅ Conexão com a base do MapBiomas confirmada!")
    print(f"ID da Imagem capturada: {info['id']}")
except Exception as err:
    print(f"❌ Erro ao puxar dados do MapBiomas: {err}")