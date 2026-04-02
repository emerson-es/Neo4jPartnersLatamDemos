"""
Arquivo de configuração centralizado do TelcoGraph.

Defina as variáveis de ambiente abaixo antes de rodar a aplicação.
Veja o arquivo .env.example para a lista completa.
"""

import os

# ══════════════════════════════════════════════════════════════════════════════
# NEO4J — Conexão com o banco de grafos
# Preencha aqui OU defina variáveis de ambiente (têm prioridade)
# ══════════════════════════════════════════════════════════════════════════════
NEO4J_URI = os.getenv("NEO4J_URI", "neo4j://SEU_HOST_AQUI")
NEO4J_USER = os.getenv("NEO4J_USER", "SEU_USUARIO")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "SUA_SENHA_AQUI")
NEO4J_DATABASE = os.getenv("NEO4J_DATABASE", "telcographchurn")

# ══════════════════════════════════════════════════════════════════════════════
# AURA API — Text2Cypher (agente de linguagem natural) - OPCIONAL
# ══════════════════════════════════════════════════════════════════════════════
AURA_API_CLIENT_ID = os.getenv("AURA_API_CLIENT_ID", "")
AURA_API_CLIENT_SECRET = os.getenv("AURA_API_CLIENT_SECRET", "")
AURA_API_TEXT2CYPHER_ENDPOINT = os.getenv("AURA_API_TEXT2CYPHER_ENDPOINT", "")
AURA_TOKEN_URL = os.getenv("AURA_TOKEN_URL", "https://api.neo4j.io/oauth/token")

# ══════════════════════════════════════════════════════════════════════════════
# IMAGENS — Logos e imagens da sidebar / capa
# ══════════════════════════════════════════════════════════════════════════════
LOGO_NEO4J_URL = os.getenv(
    "LOGO_NEO4J_URL",
    "https://cdn.prod.website-files.com/653986a9412d138f23c5b8cb/65c3ee6c93dc929503742ff6_1_E5u7PfGGOQ32_H5dUVGerQ%402x.png",
)
LOGO_EMPRESA_URL = os.getenv(
    "LOGO_EMPRESA_URL",
    "https://cdn-icons-png.flaticon.com/512/1285/1285744.png",
)

# ══════════════════════════════════════════════════════════════════════════════
# URLS — Links externos usados na aplicação
# ══════════════════════════════════════════════════════════════════════════════
KAGGLE_DATASET_URL = os.getenv(
    "KAGGLE_DATASET_URL",
    "https://www.kaggle.com/datasets/yeanzc/telco-customer-churn-ibm-dataset",
)
GOOGLE_FONTS_URL = "https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap"
