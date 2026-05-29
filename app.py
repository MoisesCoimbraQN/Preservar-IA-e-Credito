"""
app.py
Ponto de entrada da plataforma Preservar IA.
Responsabilidades:
  - Criar a instância Dash e expor o servidor para deploy (Render)
  - Inicializar dependências externas de forma segura (GEE, modelo ML)
  - Conectar layout e callbacks
  - Subir o servidor
"""

import joblib
import ee
import dash
import dash_bootstrap_components as dbc

import callbacks
from layout import criar_layout

# ── Google Earth Engine (Ajustado para Nuvem/Render) ─────────────────────────
try:
    ee.Initialize(project='sustentabilidade-e-cred-rural')
    print("🛰️ Google Earth Engine inicializado com sucesso!")
except Exception as e:
    print(f"⚠️ Aviso GEE: Não foi possível autenticar os satélites em tempo real ({str(e)}).")
    print("🚀 O sistema utilizará os Motores Locais Offline (dados_car/) com sucesso!")

# ── Modelo de Machine Learning (XGBoost Homologado) ─────────────────────────
modelo = joblib.load("modelo_credito.pkl")

# Dicionário de classes mapeado de acordo com a sua nova Matriz de Decisão ESG
dicionario_classes = {
    0: {"nome": "CLASSE CRÍTICA", "subtitulo": "Bloqueado por Risco Ambiental / Inconformidade", "cor_hex": "#dc2626", "icone": "🚨"},
    1: {"nome": "CLASSE REGULAR", "subtitulo": "Aprovado com Taxa Padrão — Estável",                  "cor_hex": "#0369a1", "icone": "✅"},
    2: {"nome": "CLASSE OURO",    "subtitulo": "Aprovado com Bônus Máximo — Desmatamento Zero",        "cor_hex": "#16a34a", "icone": "🥇"},
}

# ── App Dash ─────────────────────────────────────────────────────────────────
app = dash.Dash(
    __name__,
    external_stylesheets=[dbc.themes.BOOTSTRAP],
    suppress_callback_exceptions=True,
)

app.title = "Preservar IA — Crédito Sustentável Familiar"

# Linha obrigatória para o Render localizar o servidor
server = app.server 

# ── Layout e callbacks ───────────────────────────────────────────────────────
app.layout = criar_layout()
callbacks.registrar(app, modelo, dicionario_classes)

# ── Servidor ─────────────────────────────────────────────────────────────────
if __name__ == '__main__':
    app.run(debug=True, dev_tools_hot_reload=False)