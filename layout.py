"""
layout.py
Estrutura visual da plataforma Preservar IA e Crédito.
Sem lógica de negócio — apenas montagem dos componentes Dash.
"""

from dash import dcc, html
import dash_bootstrap_components as dbc

from helpers import mapa_vazio_html


def criar_layout() -> html.Div:
    return html.Div([

        # ── HEADER ──────────────────────────────────────────────────────
        html.Div(className="header-wrap", children=[
            html.Div(className="header-inner", children=[
                html.Div(
                    style={"display": "flex", "alignItems": "center", "gap": "14px"},
                    children=[
                        html.Div("🌿", className="header-logo-mark"),
                        html.Div([
                            html.H1("Preservar IA e Crédito Familiar Sustentável", className="header-title"),
                            html.P(
                                "Global Solution · ASG e o Crédito da Agricultura Familiar",
                                className="header-subtitle",
                            ),
                        ]),
                    ],
                ),
                html.Span("Plataforma Ativa", className="header-badge"),
            ]),
        ]),

        # ── CONTEÚDO PRINCIPAL ───────────────────────────────────────────
        html.Div(
            style={"padding": "28px 32px", "maxWidth": "1400px", "margin": "0 auto"},
            children=[
                dbc.Row([

                    # ── COLUNA ESQUERDA: FORMULÁRIO + RESULTADO ──────────
                    dbc.Col([
                        _card_busca(),
                        dbc.Spinner(
                            html.Div(id="resultado-analise", children=[_estado_vazio()]),
                            color="success",
                            spinner_style={"width": "2rem", "height": "2rem"},
                        ),
                    ], md=5),

                    # ── COLUNA DIREITA: MAPA ─────────────────────────────
                    dbc.Col([
                        _card_mapa(),
                    ], md=7),

                ], className="g-4"),
                
                html.Br(),
                
                # ── [MANUAL ESG DE INSTRUÇÕES NO RODAPÉ] ──────────────────
                html.Div(
                    className="container mb-5",
                    style={"maxWidth": "1140px", "padding": "0", "marginTop": "30px"},
                    children=[
                        html.H5(
                            "📘 Manual de Instruções & Critérios de Elegibilidade (Preservar IA)", 
                            style={"color": "#4B5563", "fontWeight": "bold", "marginBottom": "15px"}
                        ),
                        html.P(
                            "Esta plataforma utiliza inteligência geoespacial automatizada (Google Earth Engine e satélites ESA/Dynamic World) "
                            "combinada com um classificador de Machine Learning XGBoost de 16 variáveis para determinar as alçadas de crédito do FIDC ESG. "
                            "A precificação avalia a transição tridimensional real do solo entre as safras de 2016 e 2023:",
                            style={"color": "#6B7280", "fontSize": "14px", "textAlign": "justify"}
                        ),
                        
                        dbc.Row([
                            # Coluna 1: Regra Ouro
                            dbc.Col(md=4, children=[
                                html.Div(
                                    style={
                                        "padding": "15px", "backgroundColor": "#f0fdf4", 
                                        "border": "1px solid #bbf7d0", "borderRadius": "8px", "height": "100%"
                                    },
                                    children=[
                                        html.H6("🏆 CLASSE OURO (Bônus Verde)", style={"color": "#16a34a", "fontWeight": "bold"}),
                                        html.Small([
                                            html.Strong("Critério: "), "Queda de pastagens ativas com floresta intacta, ou expansão de lavouras sobre áreas abertas no Cerrado/Caatinga/Pampa/Pantanal.",
                                            html.Br(), html.Br(),
                                            "Premia produtores que promovem a transição ecológica e a agricultura de baixo carbono. Concede desconto de -0.5% a.a. nos juros climáticos."
                                        ], style={"color": "#14532d", "fontSize": "13px"})
                                    ]
                                )
                            ]),
                            
                            # Coluna 2: Regra Regular
                            dbc.Col(md=4, children=[
                                html.Div(
                                    style={
                                        "padding": "15px", "backgroundColor": "#f0f9ff", 
                                        "border": "1px solid #bae6fd", "borderRadius": "8px", "height": "100%"
                                    },
                                    children=[
                                        html.H6("✅ CLASSE REGULAR (Taxa Padrão)", style={"color": "#0369a1", "fontWeight": "bold"}),
                                        html.Small([
                                            html.Strong("Critério: "), "Estabilidade absoluta das classes desde 2016, regeneração compensada ou Integração Lavoura-Pecuária (ILP) proporcional.",
                                            html.Br(), html.Br(),
                                            "Destinado ao produtor em conformidade básica que mantém seu uso tradicional estável ou adota manejo equilibrado. Acesso às taxas convencionais do Plano Safra."
                                        ], style={"color": "#0c4a6e", "fontSize": "13px"})
                                    ]
                                )
                            ]),
                            
                            # Coluna 3: Regra Crítica
                            dbc.Col(md=4, children=[
                                html.Div(
                                    style={
                                        "padding": "15px", "backgroundColor": "#fef2f2", 
                                        "border": "1px solid #fecaca", "borderRadius": "8px", "height": "100%"
                                    },
                                    children=[
                                        html.H6("🚨 CLASSE CRÍTICA (Bloqueio ESG)", style={"color": "#dc2626", "fontWeight": "bold"}),
                                        html.Small([
                                            html.Strong("Critério: "), "Desmatamento severo (>15%) ou avanço pecuário agressivo (>20%) com supressão de vegetação nativa (tolerância de 5% para ruídos).",
                                            html.Br(), html.Br(),
                                            "Bloqueio automático imediato do pleito de crédito rural na esteira de compliance devido ao alto risco de passivo socioambiental e descumprimento legal."
                                        ], style={"color": "#7f1d1d", "fontSize": "13px"})
                                    ]
                                )
                            ]),
                        ], className="g-3 mt-2"),

                        html.Div(
                            style={
                                "marginTop": "20px", "padding": "12px", 
                                "backgroundColor": "#f9fafb", "borderRadius": "6px", "border": "1px solid #e5e7eb"
                            },
                            children=[
                                html.Small([
                                    html.Strong("📌 Matriz Legal de Biomas (Código Florestal): "),
                                    "Bioma Amazônia: Limite estrito de 20% de área convertida (80% Reserva Legal) | ",
                                    "Cerrado (Amazônia Legal): Limite de 65% de conversão | ",
                                    "Cerrado e demais biomas: Limite de até 80% de conversão permitida. ",
                                    html.Br(),
                                    html.Strong("⚠️ Hard-Block de Porte Familiar: "),
                                    "Imóveis rurais cuja área total ultrapassar o limite municipal de 4 Módulos Fiscais (INCRA) são desclassificados automaticamente na esteira fundiária de Governança (G)."
                                ], style={"color": "#4B5563", "fontSize": "12px"})
                            ]
                        )
                    ]
                )
            ]
        )
    ])


# ── Blocos internos ──────────────────────────────────────────────────────────

def _card_busca() -> html.Div:
    # Os 8 códigos reais selecionados para a lista suspensa
    exemplos_car = [
        "MT-5108600-81A4B8AC56604EFEAD1C9CA0DA6A4A51",
        "MT-5108600-81762AC703A349F18A632CF48BD7D6EE",
        "MG-3100104-002B8EAD21C84FFD9E6408101C4B54F6",
        "MG-3100104-017E5F338BF844B49339FE3FD28F92E3",
        "AC-1200435-0318105B6E0B4C70B656748ADF57D846",
        "AC-1200500-22BD7D269B374A0E92AB908852EE178E",
        "PB-2500502-051C1FB841654C26B12399091CFD2BD2",
        "PB-2500502-06175FD034A24E149F423DACD8F978D2"
    ]

    return html.Div(className="card-pronaf", style={"marginBottom": "18px"}, children=[
        html.Div(className="card-header-pronaf", children=[
            html.Div("🔍", className="card-header-icon"),
            html.P("Consulta de Imóvel Rural", className="card-header-title"),
        ]),
        html.Div(className="card-body-pronaf", children=[
            html.Label("Selecione um CAR na lista ou digite um código manualmente", className="input-label"),
            
            # Campo para inserção de dados
            dcc.Input(
                id="input-car",
                type="text",
                className="input-car",
                placeholder="Clique duas vezes para abrir a lista ou cole um CAR...",
                list="lista-sugestoes-car",
                style={"width": "100%", "marginBottom": "15px"}
            ),
            
            # Lista dinâmica nativa de sugestões
            html.Datalist(
                id="lista-sugestoes-car",
                children=[html.Option(value=car) for car in exemplos_car]
            ),
            
            html.Button(
                "⚡ Analisar via Satélite & IA",
                id="btn-analisar",
                className="btn-analisar",
                n_clicks=0,
            ),
        ]),
    ])


def _card_mapa() -> html.Div:
    return html.Div(className="card-pronaf", style={"height": "100%"}, children=[
        html.Div(className="card-header-pronaf", children=[
            html.Div("🗺️", className="card-header-icon"),
            html.P("Análise Espacial e Delimitação Vetorial", className="card-header-title"),
        ]),
        html.Div(style={"padding": "0"}, children=[
            html.Iframe(
                id="mapa-folium",
                srcDoc=mapa_vazio_html(),
                style={
                    "width": "100%",
                    "height": "560px",
                    "border": "none",
                    "borderRadius": "0 0 20px 20px",
                },
            ),
        ]),
    ])


def _estado_vazio() -> html.Div:
    return html.Div(className="card-pronaf", children=[
        html.Div(className="card-body-pronaf", children=[
            html.Div(className="estado-vazio", children=[
                html.Div("🛰️", className="estado-vazio-icon"),
                html.P("Insira o código do CAR e clique em Analisar para ativar os satélites."),
            ]),
        ]),
    ])