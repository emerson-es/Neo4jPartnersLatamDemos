# TelcoGraph - Analise de Assinantes e Redes com Neo4j e Graph Data Science

Dashboard interativo em **Streamlit** que transforma dados tabulares de churn de telecom em um grafo **Customer 360** no Neo4j, combinando analise comportamental de assinantes com topologia de infraestrutura e custos de manutencao.

![Python](https://img.shields.io/badge/Python-3.9%2B-blue)
![Streamlit](https://img.shields.io/badge/Streamlit-1.x-FF4B4B)
![Neo4j](https://img.shields.io/badge/Neo4j-5.x-008CC1)

---

## Visao Geral

A aplicacao modela o [dataset de churn do Kaggle (IBM Telco)](https://www.kaggle.com/datasets/yeanzc/telco-customer-churn-ibm-dataset) como um grafo no Neo4j, permitindo percorrer relacoes complexas entre clientes, demograficos, planos, servicos e infraestrutura de rede para revelar insights impossiveis de obter com metodos tabulares tradicionais.

### Modelo de Grafo

**Dominio do Cliente:**
```
Customer -[:LIVES_AT]-> Location
Customer -[:HAS_CONTRACT]-> Contract
Customer -[:PAYS_WITH]-> PaymentMethod
Customer -[:SUBSCRIBES_TO]-> Service
Customer -[:SIMILAR_TO]-> Customer
Customer -[:WATCHED_MOVIE]-> Movie
```

**Infraestrutura de Rede:**
```
CoreNetwork -> RegionalHub -> CentralOffice -> DistributionCabinet -> AccessNode -> CPE -> Customer
Equipment -[:HAS_MAINTENANCE]-> MaintenanceEvent -[:CAUSED]-> MaintenanceEvent
```

---

## Secoes da Aplicacao

### Analise Customer 360
| Secao | Descricao |
|-------|-----------|
| **O que os Dados Representam** | Schema do grafo e entidades principais |
| **A Geografia** | Mapa de bolhas com concentracao de clientes e taxa de churn por cidade |
| **Entendendo o Grafo Customer 360** | Vizinhanca interativa de clientes com todos os relacionamentos |
| **Redes de Similaridade** | Comunidades via Louvain; exploracao de similaridade ate 4 graus |
| **Combinacoes de Servicos com Alto Churn** | Pares de servicos com maior risco de churn |
| **GDS: Comunidades de Churn** | Perfil de clusters, scatter plot de risco e membros de alto risco |
| **Falhas Geo-Espaciais** | Clientes em raio de N km de churners com suporte tecnico |
| **Heatmap de Churn** | Matriz Contrato x Pagamento com filtro por cidade |
| **Recomendacoes de Filmes** | Filtragem colaborativa baseada em clientes similares |
| **Previsao de Risco com KNN** | KNN com embeddings FastRP para predicao de churn e motivo |

### Topologia de Rede
| Secao | Descricao |
|-------|-----------|
| **Visao Hierarquica da Rede** | Topologia core-to-edge com profundidade configuravel (1-4 camadas) |
| **Rastreamento de Caminho do Cliente** | Path completo Cliente -> CPE -> ... -> CoreNetwork com latencia e distancia |
| **Capacidade e Utilizacao** | Utilizacao de AccessNodes com alertas critico/warning/saudavel |
| **Analise de Impacto de Falhas** | Cascata de falhas e impacto downstream em clientes |
| **Manutencao e SLA** | Eventos por prioridade/tipo, conformidade SLA, frequencia de falhas |
| **Custos de Manutencao** | Custos por categoria, tipo, camada de rede; top 10 eventos mais caros |
| **Analise de Causa Raiz** | 5 visoes de causalidade: reincidencia, cadeia completa, raio de impacto |
| **Linha do Tempo de Incidentes** | Timeline com custo acumulado, scatter de outages, zoom mensal |

---

## Algoritmos Graph Data Science (GDS)

- **Louvain** - Deteccao de comunidades de clientes similares
- **FastRP** (Fast Random Projection) - Embeddings de grafo para KNN
- **KNN** (K-Nearest Neighbors) - Predicao de churn baseada em similaridade topologica

---

## Tecnologias

| Categoria | Stack |
|-----------|-------|
| Framework Web | Streamlit |
| Banco de Dados | Neo4j (Cypher) |
| Algoritmos de Grafo | Neo4j GDS (Louvain, FastRP, KNN) |
| Visualizacao de Grafos | neo4j-viz |
| Geoespacial | GeoPandas, Contextily, OpenStreetMap |
| Graficos | Matplotlib, Seaborn |
| API | Neo4j Aura API (Text2Cypher) |

---

## Como Rodar

### Pre-requisitos

- Python 3.9+
- Neo4j 5.x com GDS instalado e o grafo carregado

### 1. Clonar o repositorio

```bash
git clone https://github.com/SEU_USUARIO/AppTelcoGraph.git
cd AppTelcoGraph
```

### 2. Criar ambiente virtual

**Windows (PowerShell):**
```powershell
python -m venv venv
venv\Scripts\activate
```

**Linux/Mac:**
```bash
python -m venv venv
source venv/bin/activate
```

### 3. Instalar dependencias

```bash
pip install -r reqs.txt
```

### 4. Configurar credenciais

Edite o arquivo `app_config.py` com as credenciais do seu Neo4j:

```python
NEO4J_URI = os.getenv("NEO4J_URI", "neo4j://SEU_HOST_AQUI")
NEO4J_USER = os.getenv("NEO4J_USER", "SEU_USUARIO")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "SUA_SENHA_AQUI")
NEO4J_DATABASE = os.getenv("NEO4J_DATABASE", "telcographchurn")
```

Ou use variaveis de ambiente (recomendado para producao):

```powershell
$env:NEO4J_URI="neo4j://seu-host:7687"
$env:NEO4J_USER="neo4j"
$env:NEO4J_PASSWORD="sua_senha"
$env:NEO4J_DATABASE="telcographchurn"
```

### 5. Rodar

```bash
streamlit run app_telcograph_v3_4.py
```

A aplicacao abre automaticamente em `http://localhost:8501`.

---

## Estrutura do Projeto

```
AppTelcoGraph/
  app_telcograph_v3_4.py   # Aplicacao principal Streamlit
  app_config.py             # Configuracoes (credenciais, URLs, imagens)
  neo4j_analysis.py         # Wrapper de queries Cypher
  reqs.txt                  # Dependencias Python
  .env.example              # Template de variaveis de ambiente
  .gitignore                # Arquivos ignorados pelo Git
```

---

## Dataset

Baseado no [IBM Telco Customer Churn](https://www.kaggle.com/datasets/yeanzc/telco-customer-churn-ibm-dataset) do Kaggle, enriquecido com:
- Dados sinteticos de filmes assistidos/avaliados
- Topologia de rede (Core -> Regional -> Central Office -> Access -> CPE)
- Eventos de manutencao com cascatas de causalidade

---
## AVISO DE ISENÇÃO DE RESPONSABILIDADE

Este software é fornecido "como está" (as is), sem garantias de qualquer natureza, sejam expressas ou implícitas, incluindo, mas não se limitando a, garantias de comercialização, adequação a uma finalidade específica ou não violação de direitos.
Em nenhuma circunstância os autores, colaboradores ou detentores dos direitos autorais serão responsabilizados por quaisquer danos, perdas, reclamações ou prejuízos — diretos, indiretos, incidentais, especiais, consequenciais ou de qualquer outra natureza — decorrentes do uso, impossibilidade de uso ou desempenho deste software, ainda que tenham sido previamente informados da possibilidade de tais danos.
O uso deste software é feito por sua própria conta e risco. Ao utilizá-lo, você concorda integralmente com os termos desta isenção de responsabilidade.
