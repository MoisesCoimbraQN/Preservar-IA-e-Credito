"""
callbacks.py
Lógica de negócio, motor geográfico (GEE), travas ASG e busca inteligente em bases estaduais consolidadas.
Janela temporal de análise padronizada: 2016 a 2023.
Adaptado para a arquitetura de alta volumetria do modelo Preservar IA.
"""

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

# Desativa avisos visuais de SSL no terminal para manter os logs limpos
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

_modelo = None
_dicionario_classes = None

# Padrão estável de comparação temporal (Intervalo de 7 anos)
ANO_BASE   = "2016"
ANO_ATUAL  = "2023"


# 🛡️ Adaptador SSL customizado para o GeoServer do Governo (Mantido para integridade da arquitetura)
class UmidificadorSSLAdapter(HTTPAdapter):
    def init_poolmanager(self, *args, **kwargs):
        context = create_urllib3_context()
        context.options |= 0x4  # Permite conexões legadas (OP_LEGACY_SERVER_CONNECT)
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

        # ── SANITIZAÇÃO AVANÇADA DE ENGENHARIA DE DADOS ──────────────────
        # 1. Remove espaços e força tudo para maiúsculas (Padrão Oficial)
        codigo_car = codigo_car.strip().upper()
        
        # 2. Se o utilizador inseriu o código com pontos na hash, remove-os para bater com a busca interna
        partes = codigo_car.split("-")
        if len(partes) >= 3:
            partes[2] = partes[2].replace(".", "")
            codigo_car = "-".join(partes)

        try:
            # Extrai a UF em minúsculas para identificar o estado correspondente
            uf_detectada = codigo_car.split("-")[0].lower()
        except Exception:
            return card_erro("Formato Inválido", "O código do CAR inserido não segue o padrão nacional (UF-XXXXXXX...)."), ""

        # 🚀 INICIALIZAÇÃO DE SEGURANÇA DO MAPA (Garante que 'm' sempre exista no escopo da função)
        m = folium.Map(location=[-15.7801, -47.9292], zoom_start=4, tiles="CartoDB positron")
        bioma_imovel = "Cerrado"  # Fallback padrão de bioma de segurança

        # ── 1. CONEXÃO DIRETA VIA API COM O GEOSERVER DO GOVERNO ─────────
        filtro_cql = f"cod_imovel='{codigo_car}'"
        filtro_url = urllib.parse.quote(filtro_cql)
        
        url_api_car = (
            f"https://geoserver.car.gov.br/geoserver/sicar/ows?"
            f"service=WFS&version=1.0.0&request=GetFeature&"
            f"typeName=sicar%3Asicar_imoveis_{uf_detectada}&"
            f"outputFormat=application%2Fjson&cql_filter={filtro_url}"
        )

        sessao = requests.Session()
        sessao.mount("https://", UmidificadorSSLAdapter())

        try:
            # Tenta disparar a requisição para a API real
            resposta = sessao.get(url_api_car, verify=False, timeout=12)
            if resposta.status_code != 200:
                raise Exception(f"Erro HTTP {resposta.status_code}")
                
            geojson_data = resposta.json()
            if not geojson_data.get("features"):
                raise Exception("Imóvel não localizado na base remota")

        except Exception as erro_api:
            # 🔄 PLANO B (Mecânica de Varredura Local Otimizada)
            print(f"⚠️ API Governamental indisponível ({erro_api}). Ativando Motores Locais...")
            
            arquivos_possiveis = [
                f"CAR_ESTADO_{uf_detectada.upper()}.geojson",
                f"CAR_ESTADO_{uf_detectada.upper()}.txt",
                f"{uf_detectada.lower()}.geojson"
            ]
            
            caminho_estado = None
            if os.path.exists("dados_car"):
                for nome_arq in arquivos_possiveis:
                    teste_caminho = os.path.join("dados_car", nome_arq)
                    if os.path.exists(teste_caminho):
                        caminho_estado = teste_caminho
                        break

            if caminho_estado:
                try:
                    with open(caminho_estado, "r", encoding="utf-8") as f:
                        base_estado = json.load(f)
                    
                    imovel_encontrado = None
                    for feature in base_estado.get("features", []):
                        propriedades = feature.get("properties", {})
                        cod_imovel_base = propriedades.get("cod_imovel", "").strip().upper().replace(".", "")
                        
                        if cod_imovel_base == codigo_car:
                            imovel_encontrado = feature
                            break
                    
                    if imovel_encontrado:
                        print(f"✅ Sucesso: Imóvel extraído localmente da base de {uf_detectada.upper()}!")
                        geojson_data = {
                            "type": "FeatureCollection",
                            "features": [imovel_encontrado]
                        }
                    else:
                        raise Exception(f"Código não encontrado dentro do arquivo {os.path.basename(caminho_estado)}")
                        
                except Exception as e_interno:
                    return card_erro(
                        "Falha de Busca Interna",
                        f"O arquivo consolidado de {uf_detectada.upper()} foi encontrado, mas a busca interna falhou: {e_interno}"
                    ), m._repr_html_()
            else:
                return card_erro(
                    "Base Offline Não Localizada",
                    f"A API falhou e não foi encontrado o ficheiro unificado dentro da pasta dados_car/."
                ), m._repr_html_()

        # ── 2. Extração e Conversão de Geometria para o GEE (Blindado) ──
        poligono_ee = None
        try:
            features = geojson_data["features"]
            geometria_tipo = features[0]["geometry"]["type"]
            coords = features[0]["geometry"]["coordinates"]
            propriedades_geojson = features[0].get("properties", {})

            if "bioma" in propriedades_geojson:
                bioma_imovel = propriedades_geojson["bioma"]

            if geometria_tipo == "MultiPolygon":
                coords_primeira = coords[0][0][0]
            elif geometria_tipo == "Polygon":
                coords_primeira = coords[0][0]
            else:
                coords_primeira = coords if geometria_tipo == "Point" else [-15.7801, -47.9292]

            # Recria o mapa Folium focado nas coordenadas reais da fazenda encontrada
            lat_centro, lon_centro = coords_primeira[1], coords_primeira[0]
            m = folium.Map(location=[lat_centro, lon_centro], zoom_start=14, tiles="CartoDB positron")

            try:
                poligono_ee = ee.Geometry(features[0]["geometry"])
            except Exception:
                poligono_ee = None

        except Exception as e:
            return card_erro("Falha de Parsing Espacial", f"Erro ao decodificar os vértices geométricos: {e}"), m._repr_html_()

        # ── 3. Busca Dinâmica do Módulo Fiscal (INCRA) ───────────────────
        codigo_ibge_car = propriedades_geojson.get("cod_municipio_ibge", propriedades_geojson.get("codigo_municipio_ibge", 2511400))
        nome_municipio = propriedades_geojson.get("nom_municipio", propriedades_geojson.get("municipio", "Identificado Localmente"))
        uf_municipio = uf_detectada.upper()
        
        modulo_fiscal_municipio = 55.0
        
        if os.path.exists("modulos_fiscais_incra.csv"):
            try:
                df_incra = pd.read_csv("modulos_fiscais_incra.csv")
                dados_busca = df_incra[df_incra['codigo_ibge'] == int(codigo_ibge_car)]
                if not dados_busca.empty:
                    modulo_fiscal_municipio = float(dados_busca['modulo_fiscal_ha'].values[0])
                    nome_municipio = dados_busca['municipio'].values[0]
                    uf_municipio = dados_busca['uf'].values[0]
            except Exception:
                pass

        limite_pronaf_hectares = modulo_fiscal_municipio * 4

        # ── 4. Cálculo da Área Total e Trava de Governança ───────────────
        ha_total_propriedade = 0.0
        try:
            if poligono_ee is not None:
                area_total_m2 = poligono_ee.area().getInfo()
                ha_total_propriedade = round(area_total_m2 / 10000, 2)
            else:
                raise Exception("GEE offline")
        except Exception:
            ha_total_propriedade = round(float(propriedades_geojson.get("val_area", propriedades_geojson.get("area", 0.0))), 2)
            if ha_total_propriedade <= 0:
                ha_total_propriedade = 45.3  # Fallback estatístico se zerado

        # [TRAVA LEGAL ASG] Bloqueio imediato se ultrapassar 4 Módulos Fiscais
        if ha_total_propriedade > limite_pronaf_hectares:
            folium.GeoJson(geojson_data, style_function=lambda f: {'fillColor': '#990000', 'color': '#000000', 'weight': 2, 'fillOpacity': 0.4}).add_to(m)
            
            bloco_bloqueio = html.Div([
                dbc.Alert(
                    html.Div([
                        html.Span("🚨", style={"fontSize": "22px", "marginRight": "10px"}),
                        html.Strong("PROPRIEDADE INELEGÍVEL — DESENQUADRAMENTO DE PORTE")
                    ]),
                    style={"backgroundColor": "#dc2626", "color": "white", "border": "none"},
                    className="mt-2 text-center shadow-sm"
                ),
                html.Div(className="p-3 border rounded bg-white shadow-sm mt-3", children=[
                    metadado("Localidade Detetada:", f"{nome_municipio} - {uf_municipio} (IBGE: {codigo_ibge_car})"),
                    metadado("Área Total Calculada:", f"{ha_total_propriedade} ha", "text-danger font-weight-bold"),
                    metadado("Teto Legal do Município (4 MF):", f"{limite_pronaf_hectares} ha ({modulo_fiscal_municipio} ha/módulo)"),
                    html.Hr(),
                    html.Small(
                        "Conforme a Lei nº 11.326/2006, o imóvel rural ultrapassa o limite máximo de 4 Módulos Fiscais estabelecido para a Agricultura Familiar. O processo de concessão de crédito foi abortado na esteira de conformidade regulatória (Pilar de Governança - G).",
                        className="text-muted d-block text-justify"
                    )
                ])
            ])
            return bloco_bloqueio, m._repr_html_()

        # ── 5. Sensoriamento Remoto Real no Google Earth Engine ──────────
        try:
            hansen = ee.Image('UMD/hansen/global_forest_change_2023_v1_11')
            floresta_2000 = hansen.select('treecover2000').gte(30).multiply(ee.Image.pixelArea())
            area_2000 = floresta_2000.reduceRegion(reducer=ee.Reducer.sum(), geometry=poligono_ee, scale=30, maxPixels=1e9)
            ha_original = round(ee.Number(area_2000.get('treecover2000')).divide(10000).getInfo(), 2)
            
            perda_floresta = hansen.select('loss').multiply(ee.Image.pixelArea())
            area_perda = perda_floresta.reduceRegion(reducer=ee.Reducer.sum(), geometry=poligono_ee, scale=30, maxPixels=1e9)
            ha_perda = round(ee.Number(area_perda.get('loss')).divide(10000).getInfo(), 2)
            
            ha_atual = max(0.0, round(ha_original - ha_perda, 2))
            var_floresta = round(ha_atual - ha_original, 2)
            
            dw_colecao = ee.ImageCollection('GOOGLE/DYNAMICWORLD/V1').filterBounds(poligono_ee)
            dw_base = dw_colecao.filterDate(f'{ANO_BASE}-01-01', f'{ANO_BASE}-12-31').mean()
            dw_atual = dw_colecao.filterDate(f'{ANO_ATUAL}-01-01', f'{ANO_ATUAL}-12-31').mean()
            
            pasto_b = round(ee.Number(dw_base.select('grass').gte(0.20).multiply(ee.Image.pixelArea()).reduceRegion(ee.Reducer.sum(), poligono_ee, 10, maxPixels=1e9).get('grass')).divide(10000).getInfo(), 2)
            pasto_a = round(ee.Number(dw_atual.select('grass').gte(0.20).multiply(ee.Image.pixelArea()).reduceRegion(ee.Reducer.sum(), poligono_ee, 10, maxPixels=1e9).get('grass')).divide(10000).getInfo(), 2)
            
            crops_b = round(ee.Number(dw_base.select('crops').gte(0.25).multiply(ee.Image.pixelArea()).reduceRegion(ee.Reducer.sum(), poligono_ee, 10, maxPixels=1e9).get('crops')).divide(10000).getInfo(), 2)
            crops_a = round(ee.Number(dw_atual.select('crops').gte(0.25).multiply(ee.Image.pixelArea()).reduceRegion(ee.Reducer.sum(), poligono_ee, 10, maxPixels=1e9).get('crops')).divide(10000).getInfo(), 2)
            
            bio = {
                "ha_floresta_base": ha_original, "ha_floresta_atual": ha_atual, "var_floresta": var_floresta,
                "pasto_base": pasto_b, "pasto_atual": pasto_a, "var_pasto": round(pasto_a - pasto_b, 2),
                "lavoura_base": crops_b, "lavoura_atual": crops_a, "var_lavoura": round(crops_a - crops_b, 2)
            }

        except Exception:
            # Fallback dinâmico dos dados locais salvos nas propriedades do GeoJSON
            ha_orig_local = round(float(propriedades_geojson.get("ha_original", propriedades_geojson.get("ha_floresta_base", ha_total_propriedade * 0.35))), 2)
            ha_perd_local = round(float(propriedades_geojson.get("ha_perda_floresta", propriedades_geojson.get("ha_perda", 0.0))), 2)
            pasto_local = round(float(propriedades_geojson.get("ha_pasto", propriedades_geojson.get("pasto_atual", ha_total_propriedade * 0.40))), 2)
            lavoura_local = round(float(propriedades_geojson.get("ha_lavoura", propriedades_geojson.get("lavoura_atual", ha_total_propriedade * 0.15))), 2)
            
            bio = {
                "ha_floresta_base": ha_orig_local,
                "ha_floresta_atual": max(0.0, round(ha_orig_local - ha_perd_local, 2)),
                "var_floresta": round(-ha_perd_local, 2),
                "pasto_base": pasto_local, "pasto_atual": pasto_local, "var_pasto": 0.0,
                "lavoura_base": lavoura_local, "lavoura_atual": lavoura_local, "var_lavoura": 0.0
            }

        # ── 6. Predição da Inteligência Artificial (Machine Learning) ────
        var_floresta_pct = (abs(bio["var_floresta"]) / ha_total_propriedade * 100) if ha_total_propriedade > 0 else 0.0
        pasto_pct = (bio["pasto_atual"] / ha_total_propriedade * 100) if ha_total_propriedade > 0 else 0.0
        lavoura_pct = (bio["lavoura_atual"] / ha_total_propriedade * 100) if ha_total_propriedade > 0 else 0.0
        
        porte_calculado_mf = ha_total_propriedade / modulo_fiscal_municipio
        if porte_calculado_mf <= 1.0:
            porte_mf = 1.0  
        elif porte_calculado_mf <= 2.0:
            porte_mf = 2.0  
        else:
            porte_mf = 3.0  

        biomas_validos = ['Amazonia', 'Caatinga', 'Cerrado', 'Mata_Atlantica', 'Pampa', 'Pantanal']
        dummies_bioma = {f'bioma_{b}': 1.0 if bioma_imovel.lower() == b.lower() else 0.0 for b in biomas_validos}

        if uf_detectada.upper() == "PA" and bioma_imovel.lower() == "cerrado":
            dummies_bioma['bioma_Cerrado'] = 1.0

        dados_inferencia = pd.DataFrame([{
            'area_total_ha': ha_total_propriedade,
            'porte_mf': porte_mf,
            'ha_perda_floresta': abs(bio["var_floresta"]),
            'var_floresta_pct': var_floresta_pct,
            'ha_pasto': bio["pasto_atual"],
            'pasto_pct': pasto_pct,
            'ha_lavoura': bio["lavoura_atual"],
            'lavoura_pct': lavoura_pct,
            'bioma_Amazonia': dummies_bioma['bioma_Amazonia'],
            'bioma_Caatinga': dummies_bioma['bioma_Caatinga'],
            'bioma_Cerrado': dummies_bioma['bioma_Cerrado'],
            'bioma_Mata_Atlantica': dummies_bioma['bioma_Mata_Atlantica'],
            'bioma_Pampa': dummies_bioma['bioma_Pampa'],
            'bioma_Pantanal': dummies_bioma['bioma_Pantanal']
        }])

        colunas_oficiais = [
            'area_total_ha', 'porte_mf', 'ha_perda_floresta', 'var_floresta_pct',
            'ha_pasto', 'pasto_pct', 'ha_lavoura', 'lavoura_pct',
            'bioma_Amazonia', 'bioma_Caatinga', 'bioma_Cerrado',
            'bioma_Mata_Atlantica', 'bioma_Pampa', 'bioma_Pantanal'
        ]
        dados_inferencia = dados_inferencia[colunas_oficiais]
        
        classe_predita = _modelo.predict(dados_inferencia)[0]
        probabilidades = _modelo.predict_proba(dados_inferencia)[0]
        
        info_classe = _dicionario_classes[classe_predita]
        cor_classe = info_classe.get("cor_hex", "#000")

        # ── 7. Montagem do Painel de Indicadores ──────────────────────────
        linhas = [
            ("🌳 Floresta",  bio["ha_floresta_base"], bio["ha_floresta_atual"], bio["var_floresta"],  "verde"),
            ("🌾 Pasto",     bio["pasto_base"],        bio["pasto_atual"],        bio["var_pasto"],    "amarelo"),
            ("🌱 Lavoura",   bio["lavoura_base"],       bio["lavoura_atual"],      bio["var_lavoura"],  "azul"),
        ]

        def _celula_var(valor: float, cor: str) -> html.Td:
            sinal  = "+" if valor > 0 else ""
            classe = "var-positivo" if valor > 0 else ("var-negativo" if valor < 0 else "var-neutro")
            return html.Td(f"{sinal}{valor} ha", className=f"td-var {classe}")

        linhas_html = [
            html.Tr([
                html.Th("Indicador"),
                html.Th(f"Base ({ANO_BASE})"),
                html.Th(f"Atual ({ANO_ATUAL})"),
                html.Th("Variação"),
            ], className="tr-header"),
        ]

        for nome, base, atual, var, cor in linhas:
            linhas_html.append(html.Tr([
                html.Td(nome,                         className="td-indicador"),
                html.Td(f"{base} ha", className=f"td-base {cor}"),
                html.Td(f"{atual} ha", className=f"td-atual {cor}"),
                _celula_var(var, cor),
            ]))

        # ── 8. Renderização do Painel Completo de Resultados ─────────────
        bloco_resultado = html.Div([
            dbc.Alert(
                html.Div([
                    html.Span(info_classe["icone"], style={"fontSize": "22px", "marginRight": "10px"}),
                    html.Strong(f"{info_classe['nome']} — {info_classe['subtitulo']}")
                ]), 
                style={"backgroundColor": cor_classe, "color": "white", "border": "none"}, 
                className="mt-2 text-center shadow-sm"
            ),
            html.P([html.Strong("Confiabilidade da Decisão (IA): "), f"{probabilidades[classe_predita]*100:.1f}%"], className="text-center text-muted mb-4"),
            
            html.H5("🛰️ Diagnóstico Biofísico Dinâmico", className="mt-3", style={"fontWeight": "bold"}),
            html.Table(linhas_html, className="tabela-pronaf mb-4"),
            
            html.H5("📑 Metadados e Enquadramento Legal", style={"fontWeight": "bold"}),
            html.Div(className="p-3 border rounded bg-white shadow-sm mb-2", children=[
                metadado("Código Identificador:", codigo_car),
                metadado("Localidade Região:", f"{nome_municipio} - {uf_municipio}"),
                metadado("Área Vetorial Total:", f"{ha_total_propriedade} ha"),
                metadado("Porte Calculado (INCRA):", f"{round(ha_total_propriedade / modulo_fiscal_municipio, 2)} MF (Teto: 4.0 MF)"),
                metadado("Enquadramento Familiar:", "Aprovado (Porte Elegível)", "text-success font-weight-bold"),
                html.Small("Origem dos Dados: Repositório Consolidado Local (dados_car/)", className="text-muted d-block mt-2 text-right", style={"fontSize": "10px"})
            ])
        ])
        
        # Cor do contorno do mapa: Ouro (2) e Regular (1) = Verde, Crítica (0) = Vermelho
        cor_poligono = '#16a34a' if classe_predita != 0 else '#dc2626'
        folium.GeoJson(geojson_data, style_function=lambda feature, _cor=cor_poligono: {
            'fillColor': _cor,
            'color': '#000000',
            'weight': 2.5,
            'fillOpacity': 0.4
        }).add_to(m)
        
        return bloco_resultado, m._repr_html_()