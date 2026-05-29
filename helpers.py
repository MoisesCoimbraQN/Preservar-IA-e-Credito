"""
helpers.py
Funções auxiliares de UI reutilizadas por layout.py e callbacks.py.
"""

import folium
from dash import html


def mapa_vazio_html() -> str:
    """Mapa centralizado no Brasil para o estado inicial da página."""
    m = folium.Map(location=[-15.7801, -47.9292], zoom_start=4, tiles="CartoDB positron")
    return m._repr_html_()


def metadado(chave: str, valor: str, classe: str = "") -> html.Div:
    """Linha chave/valor para a lista de metadados legais."""
    return html.Div(className="metadado-row", children=[
        html.Span(chave, className="metadado-chave"),
        html.Span(valor, className=f"metadado-valor {classe}"),
    ])


def card_erro(titulo: str, mensagem: str) -> html.Div:
    """Card de erro genérico (arquivo não encontrado, geometria inválida, etc.)."""
    return html.Div(className="card-pronaf", children=[
        html.Div(className="card-body-pronaf", children=[
            html.Div(style={
                "background": "#fef2f2", "border": "1.5px solid #fecaca",
                "borderRadius": "10px", "padding": "18px",
            }, children=[
                html.P(titulo, style={
                    "fontFamily": "Syne, sans-serif", "fontWeight": "700",
                    "color": "#dc2626", "margin": "0 0 6px",
                }),
                html.P(mensagem, style={"fontSize": "13px", "color": "#7f1d1d", "margin": 0}),
            ]),
        ]),
    ])