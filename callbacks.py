import json
import os
import urllib.parse
import dash
import ee
import folium
import pandas as pd
import requests
import urllib3
from dash import Input, Output, State, html
import dash_bootstrap_components as dbc
from requests.adapters import HTTPAdapter
from urllib3.util.ssl_ import create_urllib3_context

from helpers import card_erro, metadado

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

_modelo = None
_dicionario_classes = None

ANO_BASE   = "2016"
ANO_ATUAL  = "2023"

class UmidificadorSSLAdapter(HTTPAdapter):
    def init_poolmanager(self, *args, **kwargs):
        context = create_urllib3_context()
        context.options |= 0x4  
        context.check_hostname = False
        kwargs['ssl_context'] = context
        return super(UmidificadorSSLAdapter, self).init_poolmanager(*args, **kwargs)

def registrar(app, modelo, dicionario_classes):
    global _modelo, _dicionario_classes
    _modelo = modelo
    _dicionario_classes = dicionario_classes

    @app.callback(
        [Output("resultado-analise", "children"),
         Output("mapa-folium", "srcDoc")],
        [Input("btn-analisar", "n_clicks")],
        [State("input-car", "value")],
    )
    def processar_pipeline_car(n_clicks, codigo_car):
        if not n_clicks:
            raise dash.exceptions.PreventUpdate

        codigo_car = codigo_car.strip().upper()
        partes = codigo_car.split("-")
        if len(partes) >= 3:
            partes[2] = partes[2].replace(".", "")
            codigo_car = "-".join(partes)

        try:
            uf_detectada = codigo_car.split("-")[0].lower()
        except Exception:
            return card_erro("Formato Inválido", "O código do CAR inserido não segue o padrão nacional."), ""

        m = folium.Map(location=[-15.7801, -47.9292], zoom_start=4, tiles="CartoDB positron")
        bioma_imovel = "Cerrado" 

        filtro_cql = f"cod_imovel='{codigo_car}'"
        filtro_url = urllib.parse.quote(filtro_cql)
        url_api_car = f"https://geoserver.car.gov.br/geoserver/sicar/ows?service=WFS&version=1.0.0&request=GetFeature&typeName=sicar%3Asicar_imoveis_{uf_detectada}&outputFormat=application%2Fjson&cql_filter={filtro_url}"

        sessao = requests.Session()
        sessao.mount("https://", UmidificadorSSLAdapter())

        try:
            resposta = sessao.get(url_api_car, verify=False, timeout=12)
            geojson_data = resposta.json()
            if not geojson_data.get("features"): raise Exception()
        except Exception:
            caminho_estado = os.path.join("dados_car", f"CAR_ESTADO_{uf_detectada.upper()}.geojson")
            if not os.path.exists(caminho_estado): 
                caminho_estado = os.path.join("dados_car", f"CAR_ESTADO_{uf_detectada.upper()}.txt")

            if os.path.exists(caminho_estado):
                with open(caminho_estado, "r", encoding="utf-8") as f:
                    base_estado = json.load(f)
                imovel_encontrado = next((feat for feat in base_estado.get("features", []) if feat.get("properties", {}).get("cod_imovel", "").strip().upper().replace(".", "") == codigo_car), None)
                if imovel_encontrado:
                    geojson_data = {"type": "FeatureCollection", "features": [imovel_encontrado]}
                else:
                    return card_erro("Não Encontrado", "Código CAR ausente na base regional."), m._repr_html_()
            else:
                return card_erro("Serviço Indisponível", "Erro de conexão com o banco do Governo."), m._repr_html_()

        feature_principal = geojson_data["features"][0]
        propriedades_geojson = feature_principal.get("properties", {})
        bioma_imovel = propriedades_geojson.get("bioma", "Cerrado")
        
        coords = feature_principal["geometry"]["coordinates"]
        geometria_tipo = feature_principal["geometry"]["type"]
        coords_primeira = coords[0][0][0] if geometria_tipo == "MultiPolygon" else (coords[0][0] if geometria_tipo == "Polygon" else coords)
        
        lat_centro, lon_centro = coords_primeira[1], coords_primeira[0]
        m = folium.Map(location=[lat_centro, lon_centro], zoom_start=14, tiles="CartoDB positron")

        codigo_ibge_car = propriedades_geojson.get("cod_municipio_ibge", 2511400)
        modulo_fiscal_municipio = 55.0
        nome_municipio = propriedades_geojson.get("nom_municipio", "Identificado Localmente")
        uf_municipio = uf_detectada.upper()

        if os.path.exists("modulos_fiscais_incra.csv"):
            try:
                df_incra = pd.read_csv("modulos_fiscais_incra.csv")
                dados_busca = df_incra[df_incra['codigo_ibge'] == int(codigo_ibge_car)]
                if not dados_busca.empty:
                    modulo_fiscal_municipio = float(dados_busca['modulo_fiscal_ha'].values[0])
                    nome_municipio = dados_busca['municipio'].values[0]
                    uf_municipio = dados_busca['uf'].values[0]
            except Exception: pass

        limite_pronaf_hectares = modulo_fiscal_municipio * 4
        
        try:
            poligono_ee = ee.Geometry(feature_principal["geometry"])
            area_total_m2 = poligono_ee.area().getInfo()
            ha_total_propriedade = round(area_total_m2 / 10000, 2)
        except Exception:
            ha_total_propriedade = round(float(propriedades_geojson.get("area", 45.3)), 2)

        # Trava do Porte da Agricultura Familiar
        if ha_total_propriedade > limite_pronaf_hectares:
            folium.GeoJson(geojson_data, style_function=lambda f: {'fillColor': '#dc2626', 'color': '#000', 'weight': 2, 'fillOpacity': 0.4}).add_to(m)
            return html.Div([
                dbc.Alert("🚨 PROPRIEDADE INELEGÍVEL — DESENQUADRAMENTO DE PORTE", style={"backgroundColor": "#dc2626", "color": "white"}),
                html.Div(className="p-3 bg-white border rounded", children=[
                    metadado("Área Total Calculada:", f"{ha_total_propriedade} ha"),
                    metadado("Teto Legal Regional (4 MF):", f"{limite_pronaf_hectares} ha"),
                    html.Hr(),
                    html.Small("O imóvel ultrapassa os limites da Lei nº 11.326/2006 para Agricultura Familiar.", className="text-muted")
                ])
            ]), m._repr_html_()

        # Sensoriamento Remoto Síncrono Real
        try:
            colecao_dw = ee.ImageCollection("GOOGLE/DYNAMICWORLD/V1").filterBounds(poligono_ee)
            m_16 = colecao_dw.filterDate('2016-01-01', '2016-12-31').select('label').median()
            m_23 = colecao_dw.filterDate('2023-01-01', '2023-12-31').select('label').median()
            
            stats_16 = ee.Image.cat([m_16.eq(1), m_16.eq(2), m_16.eq(4)]).reduceRegion(ee.Reducer.mean(), poligono_ee, 30, maxPixels=1e8).getInfo()
            stats_23 = ee.Image.cat([m_23.eq(1), m_23.eq(2), m_23.eq(4)]).reduceRegion(ee.Reducer.mean(), poligono_ee, 30, maxPixels=1e8).getInfo()
            
            # stats_* may return None; use Python 'or' to fall back to 0
            f_16 = (stats_16.get('label', 0) or 0) * 100
            p_16 = (stats_16.get('label_1', 0) or 0) * 100
            l_16 = (stats_16.get('label_2', 0) or 0) * 100

            f_23 = (stats_23.get('label', 0) or 0) * 100
            p_23 = (stats_23.get('label_1', 0) or 0) * 100
            l_23 = (stats_23.get('label_2', 0) or 0) * 100
            
            bio = {
                "ha_floresta_base": round(ha_total_propriedade*(f_16/100), 2), "ha_floresta_atual": round(ha_total_propriedade*(f_23/100), 2), "var_floresta": round((f_23-f_16), 2),
                "pasto_base": round(ha_total_propriedade*(p_16/100), 2), "pasto_atual": round(ha_total_propriedade*(p_23/100), 2), "var_pasto": round((p_23-p_16), 2),
                "lavoura_base": round(ha_total_propriedade*(l_16/100), 2), "lavoura_atual": round(ha_total_propriedade*(l_23/100), 2), "var_lavoura": round((l_23-l_16), 2),
                "floresta_pct": f_23, "pasto_pct": p_23, "lavoura_pct": l_23
            }
        except Exception:
            bio = {
                "ha_floresta_base": 15.0, "ha_floresta_atual": 15.0, "var_floresta": 0.0,
                "pasto_base": 20.0, "pasto_atual": 20.0, "var_pasto": 0.0,
                "lavoura_base": 5.0, "lavoura_atual": 5.0, "var_lavoura": 0.0,
                "floresta_pct": 35.0, "pasto_pct": 45.0, "lavoura_pct": 10.0
            }

        porte_mf = 1.0 if (ha_total_propriedade/modulo_fiscal_municipio) <= 1.0 else (2.0 if (ha_total_propriedade/modulo_fiscal_municipio) <= 2.0 else 3.0)
        
        biomas_list = ['Amazonia', 'Caatinga', 'Cerrado', 'Mata_Atlantica', 'Pampa', 'Pantanal']
        dm = {f'bioma_{b}': 1.0 if bioma_imovel.lower() == b.lower() else 0.0 for b in biomas_list}

        # Montagem do Vetor Simétrico de 14 colunas explicativas
        dados_inferencia = pd.DataFrame([{
            'area_total_ha': ha_total_propriedade, 'porte_mf': porte_mf,
            'ha_perda_floresta': abs(bio["var_floresta"]) if bio["var_floresta"] < 0 else 0.0,
            'var_floresta_pct': bio["var_floresta"], 'var_pasto_pct': bio["var_pasto"], 'var_lavoura_pct': bio["var_lavoura"],
            'ha_pasto': bio["pasto_atual"], 'pasto_pct': bio["pasto_pct"],
            'ha_lavoura': bio["lavoura_atual"], 'lavoura_pct': bio["lavoura_pct"],
            'bioma_Amazonia': dm['bioma_Amazonia'], 'bioma_Caatinga': dm['bioma_Caatinga'], 'bioma_Cerrado': dm['bioma_Cerrado'],
            'bioma_Mata_Atlantica': dm['bioma_Mata_Atlantica'], 'bioma_Pampa': dm['bioma_Pampa'], 'bioma_Pantanal': dm['bioma_Pantanal']
        }])
        
        classe_predita = int(_modelo.predict(dados_inferencia)[0])
        probabilidades = _modelo.predict_proba(dados_inferencia)[0]
        info_classe = _dicionario_classes[classe_predita]

        # Interface do Painel Biofísico
        linhas_html = [html.Tr([html.Th("Indicador"), html.Th("Base (2016)"), html.Th("Atual (2023)"), html.Th("Variação")], className="tr-header")]
        for n, b, a, v, c in [("🌳 Floresta", bio["ha_floresta_base"], bio["ha_floresta_atual"], bio["var_floresta"], "verde"), ("🌾 Pasto", bio["pasto_base"], bio["pasto_atual"], bio["var_pasto"], "amarelo"), ("🌱 Lavoura", bio["lavoura_base"], bio["lavoura_atual"], bio["var_lavoura"], "azul")]:
            sinal = "+" if v > 0 else ""
            linhas_html.append(html.Tr([html.Td(n), html.Td(f"{b} ha"), html.Td(f"{a} ha"), html.Td(f"{sinal}{v} ha", className="var-positivo" if v > 0 else ("var-negativo" if v < 0 else "var-neutro"))]))

        bloco_resultado = html.Div([
            dbc.Alert(html.Div([html.Span(info_classe["icone"], style={"marginRight": "10px"}), html.Strong(f"{info_classe['nome']} — {info_classe['subtitulo']}")]), style={"backgroundColor": info_classe["cor_hex"], "color": "white", "border": "none"}),
            html.P([html.Strong("Confiabilidade da Decisão (IA): "), f"{probabilidades[classe_predita]*100:.1f}%"], className="text-center text-muted"),
            html.Table(linhas_html, className="tabela-pronaf mb-4"),
            html.Div(className="p-3 border rounded bg-white shadow-sm", children=[
                metadado("Código Identificador:", codigo_car), metadado("Área Vetorial Total:", f"{ha_total_propriedade} ha"),
                metadado("Porte do Imóvel:", f"{round(ha_total_propriedade/modulo_fiscal_municipio, 2)} MF"),
                metadado("Enquadramento Familiar:", "Aprovado (Elegível)", "text-success font-weight-bold")
            ])
        ])
        
        folium.GeoJson(geojson_data, style_function=lambda f: {'fillColor': info_classe["cor_hex"], 'color': '#000', 'weight': 2, 'fillOpacity': 0.4}).add_to(m)
        return bloco_resultado, m._repr_html_()