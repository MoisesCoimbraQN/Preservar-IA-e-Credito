import joblib
import ee
import dash
import dash_bootstrap_components as dbc

import callbacks
from layout import criar_layout

try:
    ee.Initialize(project='sustentabilidade-e-cred-rural')
    print("🛰️ Google Earth Engine inicializado com sucesso!")
except Exception as e:
    print("🚀 Utilizando os Motores Locais Offline (dados_car/) com sucesso!")

# Carrega o novo cérebro treinado
modelo = joblib.load("modelo_credito.pkl")

dicionario_classes = {
    0: {"nome": "CLASSE CRÍTICA", "subtitulo": "Bloqueado por Risco Ambiental / Inconformidade", "cor_hex": "#dc2626", "icone": "🚨"},
    1: {"nome": "CLASSE REGULAR", "subtitulo": "Aprovado com Taxa Padrão — Estável",                  "cor_hex": "#0369a1", "icone": "✅"},
    2: {"nome": "CLASSE OURO",    "subtitulo": "Aprovado com Bônus Máximo — Desmatamento Zero",        "cor_hex": "#16a34a", "icone": "🥇"},
}

app = dash.Dash(
    __name__,
    external_stylesheets=[dbc.themes.BOOTSTRAP],
    suppress_callback_exceptions=True,
)

app.title = "Preservar IA — Crédito Sustentável Familiar"
server = app.server 

app.layout = criar_layout()
callbacks.registrar(app, modelo, dicionario_classes)

if __name__ == '__main__':
    app.run(debug=True, dev_tools_hot_reload=False)