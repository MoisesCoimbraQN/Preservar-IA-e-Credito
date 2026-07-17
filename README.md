# Preservar IA e Crédito 🌾🛰️

> **Plataforma Inteligente de Concessão de Crédito Rural e Análise de Risco Socioambiental (ESG)**

O **Preservar IA** é uma solução de Engenharia e Ciência de Dados desenvolvida para automatizar, validar e precificar a esteira de crédito agrícola para produtores rurais. Unindo Inteligência Artificial (XGBoost) e Sensoriamento Remoto, a plataforma analisa dados históricos de transição do solo, faz o cruzamento com módulos fiscais do INCRA e enquadra o produtor em alçadas de risco/crédito (**Crítica**, **Regular** ou **Ouro**), permitindo a concessão de incentivos e bônus verdes (taxas de juros reduzidas) em conformidade com o Novo Código Florestal Brasileiro.

---

## 🚀 Funcionalidades Principais

*   **Esteira de Crédito Automatizada:** Análise síncrona e instantânea do imóvel rural a partir do código do SICAR / IBGE.
*   **Sensor Fusion Real-Time:** Conexão direta com sensores orbitais de alta resolução para validação das mudanças de solo.
*   **Inteligência Geográfica:** Mapeamento dinâmico e interativo de polígonos de propriedades com sinalização visual de conformidade (verde/vermelho).
*   **Mecanismo de Resiliência (Fallback):** Arquitetura blindada contra falhas de conexão de APIs de terceiros na nuvem.

---

## 🛠️ Ecossistema Tecnológico

### 1. Interface do Usuário & Front-end (Dashboard)
*   **Dash (Plotly) & Dash Bootstrap Components (DBC):** Framework para aplicação web interativa em Python puro, garantindo uma UI responsiva e moderna.
*   **Folium (Leaflet.js):** Renderização de mapas interativos com contornos dinâmicos das propriedades agrícolas.

### 2. Sensoriamento Remoto & Inteligência Geográfica
*   **Google Earth Engine (GEE) API:** Processamento geoespacial em nuvem sob demanda (dados históricos Landsat e uso do solo Sentinel-2 via *Dynamic World*).
*   **GeoJSON / JSON:** Padrão estruturado para o trânsito de coordenadas espaciais e vértices de propriedades.

### 3. Inteligência Artificial & Modelagem Preditiva
*   **XGBoost (XGBClassifier):** Algoritmo de *Gradient Boosting* de alta performance para classificar produtores rurais em alçadas com base em 14 variáveis ambientais e fundiárias.
*   **Scikit-learn:** Construção e gerenciamento de pipelines de modelagem estatística.
*   **Joblib:** Serialização, persistência e carga otimizada do modelo treinado.

### 4. Engenharia de Dados & Consumo de APIs
*   **Pandas:** Manipulação de dados tabulares e cruzamento inteligente de códigos IBGE e Módulos Fiscais do INCRA.
*   **Requests & Urllib3:** Requisições HTTP síncronas contra o GeoServer governamental com adaptador SSL customizado.

### 5. Infraestrutura & DevOps
*   **Python 3.14:** Linguagem base de toda a inteligência da solução.
*   **Gunicorn:** Servidor HTTP WSGI para o ambiente de produção.
*   **Render:** Plataforma Cloud utilizada para hospedagem e deploy automatizado.
*   **Git & GitHub:** Controle de versão e esteiras de integração/deploy contínuo (CI/CD).

---

## 🗺️ Engenharia de Dados & Amostragem Estatística

Para viabilizar o processamento geoespacial em escala de laboratório e garantir a robustez estatística do classificador, o escopo do projeto foi delimitado a uma amostragem estratégica de **10 estados brasileiros**. A seleção cobriu com máxima fidelidade as nuances regulatórias e assinaturas de todos os biomas nacionais (Amazônia, Cerrado, Mata Atlântica, Caatinga, Pampa e Pantanal).

*   **Volume da ABT (Tabela Analítica Base):** 5.941 vetores de imóveis rurais.
*   **Divisão de Dados:** 4.752 registros para treino e 1.189 registros inéditos para validação.
*   **Performance do Modelo:** O classificador XGBoost atingiu **0.99 de acurácia** na validação.

### Janela Temporal Selecionada (2016 - 2023)
*   **2016 (Marco Inicial):** Escolhido como a "linha de base estável" por representar a consolidação prática das regras do Novo Código Florestal e o primeiro ano cheio de dados da constelação Sentinel-2.
*   **2023 (Marco Final):** Definido para garantir o fechamento de anos agrícolas completamente consolidados pelas agências internacionais (NASA e ESA), eliminando o ruído de safras incompletas e blindando o modelo contra falsos positivos de desmatamento.

---

## 📈 Análise de Relevância das Variáveis (Feature Importance)

A tomada de decisão da inteligência artificial foi dominada pela dinâmica tridimensional de transição do solo ($\Delta$ de $2016 \rightarrow 2023$), com o **Bioma Mata Atlântica** assumindo um papel crucial de corte regulatório devido às exigências restritivas de proteção jurídica do ecossistema:

1.  `var_lavoura_pct` ➔ **38.98%** (Variação percentual de agricultura)
2.  `var_pasto_pct` ➔ **19.74%** (Variação percentual de pastagem)
3.  `var_floresta_pct` ➔ **15.90%** (Variação percentual de cobertura arbórea)
4.  `bioma_Mata_Atlantica` ➔ **13.15%** (Fator de assimetria regulatória e compliance)

---

## ⚠️ Critérios de Implantação & Mecanismo de Fallback

1.  **Requisito de Ambiente Local:** A execução plena das consultas dinâmicas de satélite em ambiente de desenvolvimento requer um cadastro ativo e homologado na plataforma **Google Earth Engine (GEE)** através de um projeto Cloud.
2.  **Arquitetura de Fallback em Produção:** Durante o deploy na plataforma **Render**, restrições severas de rede impedem que o servidor mantenha uma conexão estável e direta com a API do Google Earth Engine. 
3.  **Garantia de Disponibilidade:** Para blindar o ecossistema, a solução foi projetada com resiliência: se o handshake com o GEE falhar, o fluxo de processamento é desviado síncronamente para o **Motor Local Offline** (alimentado pelas bases históricas estruturadas de `dados_car/` e `modulos_fiscais_incra.csv`), garantindo que a esteira de crédito nunca sofra interrupções.

Link da plataforma: https://preservar-ia-e-credito.onrender.com/

---
Desenvolvido como projeto prático para o **Global Solution - Fiap 1/2026**.
