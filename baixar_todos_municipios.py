import pandas as pd

print("⏳ Gerando base de dados de Módulos Fiscais para a Global Solution...")

try:
    # Banco de dados nativo compilado (Módulos do INCRA por código IBGE)
    # Inclui o mapeamento de referência nacional e os polos do PRONAF
    base_municipios = {
        'codigo_ibge': [
            2511400, 2507507, 2504009, 3550308, 3516200, 3543402,
            5107909, 5107602, 5103403, 1501402, 1506807, 1500602,
            4106902, 4113700, 4314902, 4305108, 3106200, 3154606,
            2111300, 2105302, 2927408, 2910800, 2304400, 2312908,
            3164308  # 🧀 São Roque de Minas - MG (Adicionado para o novo caso de teste)
        ],
        'municipio': [
            'Picuí', 'João Pessoa', 'Campina Grande', 'São Paulo', 'Franca', 'Ribeirão Preto',
            'Sinop', 'Rondonópolis', 'Cuiabá', 'Belém', 'Santarém', 'Altamira',
            'Curitiba', 'Londrina', 'Porto Alegre', 'Caxias do Sul', 'Belo Horizonte', 'Ribeirão das Neves',
            'São Luís', 'Imperatriz', 'Salvador', 'Feira de Santana', 'Fortaleza', 'Sobral',
            'São Roque de Minas'  # Nome do município correspondente
        ],
        'uf': [
            'PB', 'PB', 'PB', 'SP', 'SP', 'SP',
            'MT', 'MT', 'MT', 'PA', 'PA', 'PA',
            'PR', 'PR', 'RS', 'RS', 'MG', 'MG',
            'MA', 'MA', 'BA', 'BA', 'CE', 'CE',
            'MG'  # Estado correspondente
        ],
        'modulo_fiscal_ha': [
            55.0, 15.0, 20.0, 5.0, 20.0, 15.0,
            80.0, 60.0, 50.0, 5.0, 75.0, 75.0,
            5.0, 18.0, 5.0, 12.0, 5.0, 18.0,
            25.0, 45.0, 7.0, 20.0, 12.0, 30.0,
            35.0  # Módulo fiscal real de São Roque de Minas (35 ha por módulo)
        ]
    }
    
    df = pd.DataFrame(base_municipios)
    
    # Salva o arquivo final atualizado por cima do anterior
    df.to_csv('modulos_fiscais_incra.csv', index=False)
    
    print("\n✅ Sucesso, Moisés!")
    print("📦 Arquivo 'modulos_fiscais_incra.csv' atualizado com São Roque de Minas (MG).")
    print("🚀 Base local reconstruída com total integridade por script!")

except Exception as e:
    print(f"❌ Erro ao estruturar os dados: {e}")