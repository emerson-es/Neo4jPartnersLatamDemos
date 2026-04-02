# 🔗 Neo4j para Tecnologia — Data Lineage, Dependências, Governança e MDM

> Material de pré-venda Neo4j para o domínio de TI, demonstrando capacidades e diferenciais para IT Governance, Data Lineage, MDM e Análise de Impacto.

---

## 📋 Sobre o Projeto

Este repositório contém scripts Cypher, consultas de demonstração e documentação de pré-venda para o domínio de **Tecnologia e Governança de Dados**.

O material cobre os casos de uso de **Data Lineage, Dependências de Sistemas, Governança e MDM** — com foco em rastreabilidade ponta a ponta, análise de impacto em cascata e conformidade regulatória.

---

## 📊 Visão Geral do Modelo

| Entidade | Detalhe                                              |
|----------|------------------------------------------------------|
| System   | Sistemas de negócio ou tecnologia (id, name)         |
| Process  | Processos ETL, batch jobs, integrações (id, name)    |
| Report   | Relatórios gerados pelos processos (id, name)        |
| User     | Usuários que acionam processos (id, name)            |
| Dataset  | Conjuntos de dados consumidos ou produzidos (id, name)|
| Database | Bases de dados onde datasets são armazenados (id, name)|
| Log      | Registro de auditoria de execução (id, name)         |

**Relacionamentos:**

| Relacionamento   | Semântica                                              |
|------------------|--------------------------------------------------------|
| READS            | System lê um Dataset (dependência de consumo)          |
| WRITES           | System escreve em um Dataset (produção de dados)       |
| S_INPUT_TO_P     | System fornece input para um Process                   |
| S_OUTPUT_TO_P    | System produz output para um Process                   |
| P_INPUT_TO_S     | Process alimenta um System                             |
| P_OUTPUT_TO_S    | Process alimenta um System (resultado)                 |
| U_INPUT_TO_P     | User aciona um Process (rastreabilidade)               |
| P_OUTPUT_TO_R    | Process gera um Report                                 |
| LOGS_TO          | Process registra execução em Log (auditoria)           |
| STORED_IN        | Dataset está armazenado em Database                    |

---

## 🗂️ Modelo de Dados

```
(User)-[:U_INPUT_TO_P]─────────────→ (Process)
(System)-[:S_INPUT_TO_P]───────────→ (Process)
(System)-[:S_OUTPUT_TO_P]──────────→ (Process)
(Process)-[:P_INPUT_TO_S]──────────→ (System)
(Process)-[:P_OUTPUT_TO_S]─────────→ (System)
(Process)-[:P_OUTPUT_TO_R]─────────→ (Report)
(Process)-[:LOGS_TO]───────────────→ (Log)
(System)-[:READS]──────────────────→ (Dataset)
(System)-[:WRITES]─────────────────→ (Dataset)
(Dataset)-[:STORED_IN]─────────────→ (Database)
```

---

## 🚀 Casos de Uso

| # | Caso de Uso                              | Valor de Negócio                                                                          |
|---|------------------------------------------|-------------------------------------------------------------------------------------------|
| 1 | **Análise de Impacto em Cascata**        | Identifica todos os sistemas e relatórios afetados por uma falha — em segundos             |
| 2 | **Data Lineage Ponta a Ponta**           | Rastreia o caminho completo de um dado desde o usuário até o relatório final               |
| 3 | **Governança e Auditoria de Processos**  | Detecta processos operando sem log — gaps de conformidade invisíveis em ferramentas tradicionais |
| 4 | **MDM e Detecção de Inconsistências**    | Identifica sistemas que leem e escrevem no mesmo dataset — causa raiz de conflitos de MDM   |
| 5 | **Mapa para Modernização e Migração**    | Calcula a sequência ótima de migração com base na topologia de dependências                 |

---

## 🔍 Consultas de Demonstração

### Datasets Mais Críticos da Organização
```cypher
MATCH (s:System)-[:READS]->(d:Dataset)
RETURN d.name AS dataset, count(DISTINCT s) AS sistemas_dependentes
ORDER BY sistemas_dependentes DESC LIMIT 10
```

### Análise de Impacto em Cascata
```cypher
WITH 'Dataset 1166' AS nomeDataset
MATCH (d:Dataset {name: nomeDataset})<-[:READS]-(s:System)
WITH d, collect(DISTINCT s.name) AS sistemas_afetados
UNWIND sistemas_afetados AS sys_nome
MATCH (s2:System {name: sys_nome})-[:S_OUTPUT_TO_P]->(p:Process)-[:P_OUTPUT_TO_R]->(r:Report)
RETURN d.name AS dataset_critico,
       size(sistemas_afetados) AS sistemas_impactados,
       collect(DISTINCT r.name) AS relatorios_em_risco
```

### Processos sem Log de Auditoria
```cypher
MATCH (p:Process)
WHERE NOT (p)-[:LOGS_TO]->(:Log)
OPTIONAL MATCH (p)-[:P_OUTPUT_TO_R]->(r:Report)
RETURN p.name AS processo, count(r) AS relatorios_sem_rastreio
ORDER BY relatorios_sem_rastreio DESC LIMIT 10
```

### Detecção de Conflitos MDM
```cypher
MATCH (s:System)-[:READS]->(d:Dataset)<-[:WRITES]-(s)
OPTIONAL MATCH (d)-[:STORED_IN]->(db:Database)
RETURN s.name AS sistema, d.name AS dataset_conflito,
       db.name AS banco,
       'ALERTA: Sistema é simultaneamente leitor e escritor' AS risco_mdm
ORDER BY dataset_conflito
```

### Usuários com Maior Raio de Impacto
```cypher
MATCH (u:User)-[:U_INPUT_TO_P]->(p:Process)-[:P_OUTPUT_TO_R]->(r:Report)
RETURN u.name AS usuario,
       count(DISTINCT p) AS processos_ativados,
       count(DISTINCT r) AS relatorios_acessados
ORDER BY relatorios_acessados DESC LIMIT 10
```

### Linhagem Visual de um Processo (Grafo)
```cypher
MATCH (u:User)-[r1:U_INPUT_TO_P]->(p:Process {name: 'Process 1117'})
OPTIONAL MATCH (s:System)-[r2:S_INPUT_TO_P]->(p)
OPTIONAL MATCH (p)-[r3:P_OUTPUT_TO_R]->(r:Report)
OPTIONAL MATCH (p)-[r4:LOGS_TO]->(l:Log)
RETURN u, r1, p, r2, s, r3, r, r4, l
```

---

## 📁 Documentação

| Arquivo | Descrição |
|---------|-----------|
| [`Neo4j_PreVenda_DataLineage.pdf`](./Neo4j_PreVenda_DataLineage.pdf) | Documento completo de pré-venda com modelo de dados, casos de uso, scripts comentados, queries de demo e comparativo Neo4j vs ferramentas tradicionais |

O documento inclui:
- ✅ Inventário completo do modelo de dados (nós, relacionamentos, propriedades)
- ✅ Texto explicativo para audiência não-técnica (CIOs, CDOs, gestores de TI)
- ✅ 4 scripts Cypher reutilizáveis e parametrizados
- ✅ 6 consultas prontas para demonstração ao vivo
- ✅ Tabela comparativa Neo4j vs SQL/ferramentas tradicionais para argumentação em pré-venda

---

## ⚖️ Neo4j vs. Ferramentas Tradicionais — Resumo

| Capacidade                    | SQL / Ferramentas Tradicionais             | Neo4j                                               |
|-------------------------------|--------------------------------------------|-----------------------------------------------------|
| Análise de impacto em cascata | JOINs múltiplos, horas de análise manual   | 1 query — resultado em segundos                     |
| Data Lineage ponta a ponta    | Documentação manual em wikis e planilhas   | Caminho navegável e sempre atualizado               |
| Gaps de auditoria             | Relatórios batch, visão defasada           | Query em tempo real sobre todos os processos        |
| MDM — conflitos de dados      | Detectado apenas após incidente            | Identificação preventiva por padrão de grafo        |
| Planejamento de migração      | Meses de workshops e entrevistas           | Topologia calculada automaticamente                 |
| Rastreabilidade por usuário   | Logs dispersos em sistemas isolados        | Caminho completo User → Process → Report em 1 query |

---

## 🛠️ Tecnologias

- **Neo4j** — banco de dados de grafo
- **Cypher** — linguagem de consulta
- **Neo4j GDS** (Graph Data Science) — algoritmos de centralidade e detecção de dependências
- **Neo4j Browser / Bloom** — visualização interativa do grafo de dependências

---
