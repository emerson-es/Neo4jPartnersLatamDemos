# 🌎 Neo4j Partners LATAM Demos

> Coleção de **10 demonstrações por indústria** construídas sobre **Neo4j** — com modelos de dados, consultas Cypher, dashboards e documentação de pré-venda prontas para uso por parceiros na América Latina.

---

## 📋 Sobre

Materiais de apoio para **demonstrações, workshops e apresentações de pré-venda** que mostram como grafos resolvem problemas reais em diferentes setores. Cada demo inclui modelo de dados, queries prontas para demonstração ao vivo e comparativos Neo4j vs. abordagens tradicionais.


---

## 🗂️ Demos Disponíveis

### ✈️ [Aviação — Rotas e Redes de Conexão](./demo_aerolatam_neo4j)
Malha aérea LATAM modelada como grafo com algoritmos GDS pré-computados (Betweenness, Eigenvector, Louvain). Identifica hubs críticos, comunidades operacionais, gaps de mercado e caminho mínimo entre aeroportos.

### 🔗 [Tecnologia — Data Lineage e Governança](./demo_datalineage_neo4j)
Rastreabilidade ponta a ponta entre Systems, Processes, Datasets e Reports. Análise de impacto em cascata, detecção de gaps de auditoria, conflitos de MDM e mapa de dependências para migração.

### ⚡ [Energia — Rede Elétrica Inteligente](./demo_energia_neo4j)
Rede elétrica georreferenciada (geradores, barramentos, links, estações) com sensores IoT, manutenção e Customer 360. Dashboard NeoDash com análise de impacto por geocodificação e roteamento entre equipamentos.

### 🏦 [Financial Services — Visão 360°](./demo_fsi360_neo4j)
Customer 360 bancário com recomendação híbrida (5 estratégias), detecção de redes de conluio via WCC e identificação de pagamentos circulares PIX via Quantified Path Patterns. Dashboard Aura com 5 cockpits.

### 💰 [Mercado Financeiro — Fundos de Fundos](./demo_fundosdefundos_neo4j)
Ecossistema de ~38 mil fundos de investimento com instituições, auditores, títulos e ativos. Detecta conflito de interesse, risco sistêmico, cadeias de fund of funds até 5 níveis e concentração de carteira.

### 🏥 [Saúde — Jornada do Paciente](./demo_jornadapaciente_neo4j)
Patient Journey completo com 14 tipos de nó conectados por jornada temporal (FIRST → NEXT → LAST). Fraude em sinistros, segmentação de risco CRM, alertas de alergia e cobertura por plano de saúde.

### ⚖️ [Jurídico — Knowledge Graph com Gen AI](./demo_normas_neo4j)
~48 mil textos jurídicos com embeddings vetoriais (1536 dims) pré-computados. Grafo de dependências normativas, cadeia de responsabilidade e busca semântica GraphRAG para assistente jurídico.

### 🏢 [Receita Federal — CNPJ, Sócios e Eleições](./demo_receitafederal_neo4j)
Grafo completo do CNPJ (~52,9 mi de empresas) enriquecido com dados eleitorais e geoespaciais. Grupos econômicos, sócios em comum, PPE e doações eleitorais cruzadas com cadastro empresarial.

### 👥 [Recursos Humanos — Skills e Talentos](./demo_rh_neo4j)
Grafo de Pessoas, Competências, Cargos e Empresas com rede social interna. Matching de candidatos por skills, gap analysis para PDI e detecção de influenciadores organizacionais.

### 📡 [Telecom — Churn, Rede e Manutenção](./demo_telecom_Neo4J)
App Streamlit (TelcoGraph) com Customer 360 e topologia de infraestrutura core-to-edge. Usa Louvain, FastRP e KNN para predição de churn, análise de impacto de falhas e custos de manutenção.

---

## 📊 Capacidades por Demo

| Demo | Indústria | GDS | Dashboards | GenAI | Geo |
|---|---|:---:|:---:|:---:|:---:|
| ✈️ Aviação | Logística | ✅ | — | — | ✅ |
| 🔗 Data Lineage | Tecnologia | ✅ | — | — | — |
| ⚡ Energia | Utilities | ✅ | NeoDash | — | ✅ |
| 🏦 FSI 360 | Financeiro | ✅ | Aura | — | — |
| 💰 Fundos | Capitais | — | — | — | — |
| 🏥 Saúde | Healthcare | ✅ | — | — | ✅ |
| ⚖️ Normas | Jurídico | ✅ | — | ✅ | — |
| 🏢 CNPJ | Governo | ✅ | — | — | ✅ |
| 👥 RH | RH | ✅ | — | — | — |
| 📡 Telecom | Telecom | ✅ | Streamlit | — | ✅ |

---

## 🚀 Como Utilizar

### Ambiente de Parceiros

| Campo | Valor |
|---|---|
| **URL** | `Sera compartilhado` |
| **Username / Password** | *(fornecido pelo administrador)* |

Cada demo possui seu próprio database no servidor. Consulte o README de cada pasta para instruções específicas de conexão e dashboards.

### Rodar localmente

```bash
git clone https://github.com/emerson-es/Neo4j-Partners-Latam-Demos.git
cd Neo4j-Partners-Latam-Demos
```

---

## 📄 Licença

Projeto disponibilizado para fins de **demonstração e aprendizado**.

> ⚠️ Conteúdo fornecido "como está" (as is), sem garantias de qualquer natureza.
