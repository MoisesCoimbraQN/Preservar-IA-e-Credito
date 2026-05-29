import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.tree import DecisionTreeClassifier
from sklearn.metrics import accuracy_score, classification_report
import joblib

print("🧠 Iniciando pipeline de ML com Calibração de Risco (Foco em Recall)...")

# 1. Carrega os dados
df = pd.read_csv('dataset_treino.csv')

X = df[['ha_original', 'ha_atual', 'var_floresta', 'pasto_recente', 'lavoura_ativa_crops', 'mosaico_mapbiomas_c21']]
y = df['classe_risco']

X_treino, X_teste, y_treino, y_teste = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)

# =========================================================================
# 🎯 A SACADA TÉCNICA: PESOS DAS CLASSES (Class Weight)
# Damos peso 5 para a Classe 1 (Desmatamento) e peso 1 para as outras.
# Isso força o modelo a priorizar o Recall da classe crítica.
# =========================================================================
pesos_ajustados = {0: 1, 1: 5, 2: 1}

modelo_inteligente = DecisionTreeClassifier(
    max_depth=4, 
    random_state=42, 
    class_weight=pesos_ajustados # Ativando a penalização de risco
)
modelo_inteligente.fit(X_treino, y_treino)

# 5. Avaliação
predicoes = modelo_inteligente.predict(X_teste)
acuracia = accuracy_score(y_teste, predicoes)

print(f"🎯 Treinamento com Matriz de Peso Concluído!")
print(f"📈 Acurácia Global Recalibrada: {acuracia * 100:.1f}%")

print("\n📊 RELATÓRIO DE MÉTRICAS PROTEGIDAS CONTRA RISCO:")
print(classification_report(
    y_teste, 
    predicoes, 
    target_names=['Classe Ouro (Alimento + Verde)', 'Classe Crítica (Desmatamento)', 'Classe Regular (Pasto/Neutro)']
))

# 6. Salvando o novo modelo blindado
joblib.dump(modelo_inteligente, 'modelo_pronaf.joblib')
print("💾 Modelo blindado salvo com sucesso em 'modelo_pronaf.joblib'!")