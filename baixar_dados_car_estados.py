import os
import json
import requests
import urllib3
from requests.adapters import HTTPAdapter
from urllib3.util.ssl_ import create_urllib3_context

# Desativa alertas de SSL no terminal
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# 🛡️ Adaptador SSL tolerante para o GeoServer do Governo
class UmidificadorSSLAdapter(HTTPAdapter):
    def init_poolmanager(self, *args, **kwargs):
        context = create_urllib3_context()
        context.options |= 0x4  # OP_LEGACY_SERVER_CONNECT
        context.check_hostname = False
        kwargs['ssl_context'] = context
        return super(UmidificadorSSLAdapter, self).init_poolmanager(*args, **kwargs)

# Configuração dos 5 Estados Estratégicos para o seu MVP
# Mapeamos estados de diferentes regiões e biomas do Brasil
ESTADOS_ALVO = ["ac", "mg", "pb", "sp", "pa"]
LIMITE_POR_ESTADO = 10  # Baixa 10 imóveis reais de cada estado para testar

print("🚀 Iniciando a esteira de captura de dados em lote do SICAR...")

# Garante que a pasta de destino existe
if not os.path.exists("dados_car"):
    os.makedirs("dados_car")
    print("📁 Pasta 'dados_car' criada com sucesso.")

sessao = requests.Session()
sessao.mount("https://", UmidificadorSSLAdapter())

for uf in ESTADOS_ALVO:
    print(f"\n📡 Conectando à camada do estado: {uf.upper()}...")
    
    # URL WFS para download em lote limitado pelo maxFeatures
    url_lote = (
        f"https://geoserver.car.gov.br/geoserver/sicar/ows?"
        f"service=WFS&version=1.0.0&request=GetFeature&"
        f"typeName=sicar%3Asicar_imoveis_{uf}&"
        f"outputFormat=application%2Fjson&"
        f"maxFeatures={LIMITE_POR_ESTADO}"
    )
    
    try:
        resposta = sessao.get(url_lote, verify=False, timeout=20)
        if resposta.status_code != 200:
            print(f"❌ Erro ao acessar a API de {uf.upper()} (Status {resposta.status_code})")
            continue
            
        dados_estado = resposta.json()
        features = dados_estado.get("features", [])
        
        print(f"📥 {len(features)} imóveis localizados. Separando e salvando arquivos...")
        
        sucessos = 0
        for f in features:
            propriedades = f.get("properties", {})
            # Extrai o código oficial do CAR (Ex: MG-3164308-...)
            id_car = propriedades.get("cod_imovel", propriedades.get("codigo_imovel"))
            
            if not id_car:
                continue
                
            # Limpa o ID removendo possíveis pontos para bater com o nosso padrão sanitizado
            id_car_limpo = id_car.strip().upper().replace(".", "")
            
            # Encapsula a feature individual de volta no formato de FeatureCollection que o GEE espera
            geojson_individual = {
                "type": "FeatureCollection",
                "features": [f]
            }
            
            caminho_salvar = f"dados_car/{id_car_limpo}.geojson"
            
            with open(caminho_salvar, "w", encoding="utf-8") as arquivo_out:
                json.dump(geojson_individual, arquivo_out, ensure_print=False, indent=2)
            sucessos += 1
            
        print(f"✅ Concluído para {uf.upper()}: {sucessos} arquivos offline gerados.")
        
    except Exception as e:
        print(f"💥 Falha crítica ao processar o estado {uf.upper()}: {e}")

print("\n🎯 Processo finalizado! Sua pasta 'dados_car' agora está abastecida com dados de produção.")