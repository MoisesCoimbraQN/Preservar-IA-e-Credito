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
                            html.H1("Preservar IA e Crédito", className="header-title"),
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
                
                # ── [MANUAL ESG DE INSTRUÇÕES NO RODAPÉ] ──────────────────
                html.Hr(style={"marginTop": "50px", "marginBottom": "30px", "color": "#ccc"}),

                html.Div(
                    className="container mb-5",
                    style={"maxWidth": "1140px", "padding": "0"},
                    children=[
                        html.H5(
                            "📘 Manual de Instruções & Critérios de Elegibilidade (Preservar IA)", 
                            style={"color": "#4B5563", "fontWeight": "bold", "marginBottom": "15px"}
                        ),
                        html.P(
                            "Esta plataforma utiliza inteligência geoespacial automatizada (Google Earth Engine e satélite NASA Hansen) "
                            "combinada com um classificador de Machine Learning XGBoost para determinar as alçadas de crédito do FIDC ESG. "
                            "A precificação e a elegibilidade dos imóveis rurais seguem critérios rígidos de governança ambiental e social:",
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
                                        html.H6("🏆 CLASSE OURO (Bônus Máximo)", style={"color": "#16a34a", "fontWeight": "bold"}),
                                        html.Small([
                                            html.Strong("Critério: "), "Desmatamento Zero (var_floresta_pct == 0.0) E uso da terra em total conformidade legal.",
                                            html.Br(), html.Br(),
                                            "Destinado aos produtores familiares que atuam como verdadeiros guardiões da floresta, mantendo o ecossistema intacto. Garante acesso às menores taxas de juros do fundo climático."
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
                                            html.Strong("Critério: "), "Uso da terra dentro do limite do bioma, mas com supressão florestal histórica ou permitida (≤ 20%).",
                                            html.Br(), html.Br(),
                                            "Aplica-se ao produtor regular que cumpre o Código Florestal e respeita a Reserva Legal, mas registrou alguma alteração na cobertura vegetal dentro das janelas permitidas."
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
                                        html.H6("🚨 CLASSE CRÍTICA (Bloqueio/Risco)", style={"color": "#dc2626", "fontWeight": "bold"}),
                                        html.Small([
                                            html.Strong("Critério: "), "Desmatamento agressivo (> 20.0% da área) OU estouro do teto de uso permitido no Bioma.",
                                            html.Br(), html.Br(),
                                            "Imóveis rurais com inconformidades graves enfrentam o bloqueio da operação ou a aplicação da taxa de mercado cheia devido ao alto risco de compliance e passivo socioambient."
                                        ], style={"color": "#7f1d1d", "fontSize": "13px"})
                                    ]
                                )
                            ]),
                        ], className="g-3 mt-2"),

                        # Rodapé de limites dinâmicos por bioma
                        html.Div(
                            style={
                                "marginTop": "20px", "padding": "12px", 
                                "backgroundColor": "#f9fafb", "borderRadius": "6px", "border": "1px solid #e5e7eb"
                            },
                            children=[
                                html.Small([
                                    html.Strong("📌 Tetos de Uso Permitido (Código Florestal): "),
                                    "Bioma Amazônia: Máximo 20% de uso (80% Reserva Legal) | ",
                                    "Cerrado (Amazônia Legal): Máximo 65% de uso | ",
                                    "Cerrado e demais biomas nacionais: Máximo 80% de uso. ",
                                    html.Br(),
                                    html.Strong("⚠️ Trava de Porte Familiar: "),
                                    "Imóveis que ultrapassarem o limite regional de 4 Módulos Fiscais (INCRA) são desqualificados automaticamente na esteira de Governança (G)."
                                ], style={"color": "#4B5563", "fontSize": "12px"})
                            ]
                        )
                    ]
                ),
            ],
        ),
    ])


# ── Blocos internos ──────────────────────────────────────────────────────────

def _card_busca() -> html.Div:
    # Os 8 códigos reais que você separou para a banca testar na lista suspensa
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
            
            # 🚀 CAMPO DUPLO PERFEITO: Aceita digitação livre completa...
            dcc.Input(
                id="input-car",
                type="text",
                className="input-car",
                placeholder="Clique duas vezes para abrir a lista ou cole um CAR...",
                list="lista-sugestoes-car",  # Vinculado ao DataList abaixo
                style={"width": "100%", "marginBottom": "15px"}
            ),
            
            # 🛰️ ...e fornece os seus 8 exemplos como uma lista suspensa nativa do navegador!
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