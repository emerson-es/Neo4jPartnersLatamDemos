# 💰 Neo4j para o Mercado Financeiro — Compliance, Fraude, Risco e Crédito

> Material de pré-venda Neo4j para o setor financeiro, demonstrando capacidades e diferenciais para Compliance, Detecção de Fraude, Gestão de Risco e Análise de Crédito em fundos de investimento.

---

## 📋 Sobre o Projeto

Este repositório contém scripts Cypher, consultas de demonstração e documentação de pré-venda para o domínio de **Bancos, Financeiras e Gestoras de Investimento**.

O material cobre os casos de uso de **Compliance, Fraude, Risco e Crédito** aplicados ao ecossistema de fundos de investimento — com foco em detecção de conflito de interesse, análise de risco sistêmico, mapeamento de fund of funds e monitoramento regulatório.

---

## 📊 Visão Geral do Modelo

| Entidade               | Detalhe                                                                 |
|------------------------|-------------------------------------------------------------------------|
| Fundo                  | cnpj, razao_social, classe, tipo, situacao, patrimonio_liquido, taxas   |
| Instituicao_Financeira | cnpj, nome, tipo — administradoras, gestoras, custodiantes, controladoras |
| Auditor                | cnpj, nome, tipo — Big Four e auditorias independentes                  |
| Titulo_Publico         | codigo_selic, isin, tipo_titulo, emissao, vencimento                    |
| Ativo_Codificado       | codigo_ativo, isin, descricao_ativo, tipo_ativo, tipo_aplicacao         |

**Relacionamentos:**

| Relacionamento | Semântica                                                          |
|----------------|--------------------------------------------------------------------|
| COMPRA         | Fundo compra Ativo, Título Público ou outro Fundo (com peso e período) |
| ADMINISTRA     | Instituição Financeira administra Fundo                            |
| GERE           | Instituição Financeira gere a carteira do Fundo                    |
| CUSTODIA       | Instituição Financeira custodia os ativos do Fundo                 |
| CONTROLA       | Instituição Financeira controla o Fundo (cotista controlador)      |
| AUDITA         | Auditor audita o Fundo                                             |

---

## 🗂️ Modelo de Dados

```
(Auditor)-[:AUDITA]──────────────────────────────→ (Fundo)
(Instituicao_Financeira)-[:ADMINISTRA]───────────→ (Fundo)
(Instituicao_Financeira)-[:GERE]─────────────────→ (Fundo)
(Instituicao_Financeira)-[:CUSTODIA]─────────────→ (Fundo)
(Instituicao_Financeira)-[:CONTROLA]─────────────→ (Fundo)
(Fundo)-[:COMPRA {weight, anomes}]───────────────→ (Titulo_Publico)
(Fundo)-[:COMPRA {weight, anomes}]───────────────→ (Ativo_Codificado)
(Fundo)-[:COMPRA {weight, anomes}]───────────────→ (Fundo)  ← fund of funds
```

> O atributo `weight` no relacionamento `COMPRA` representa o percentual da carteira alocado naquele ativo — chave para análise de concentração e risco.

---

## 🚀 Casos de Uso

| # | Caso de Uso                                  | Valor de Negócio                                                                              |
|---|----------------------------------------------|-----------------------------------------------------------------------------------------------|
| 1 | **Detecção de Conflito de Interesse**        | Identifica instituições que acumulam administração, gestão e custódia no mesmo fundo           |
| 2 | **Análise de Risco Sistêmico e Contágio**    | Mapeia o raio de impacto de um ativo ou fundo em toda a rede em segundos                      |
| 3 | **Mapeamento de Fund of Funds (N Níveis)**   | Revela a exposição real de cotistas em cadeias de fundos com até 5 níveis de aninhamento       |
| 4 | **Detecção de Concentração de Carteira**     | Alerta fundos com mais de X% do patrimônio em um único ativo — monitoramento em tempo real     |
| 5 | **Rede de Auditoria e Governança**           | Identifica fundos sem cobertura de auditoria e sobrecargas operacionais nos auditores          |

---

## 🔍 Consultas de Demonstração

### Conflito de Interesse — Instituições com Múltiplos Papéis
```cypher
MATCH (i:Instituicao_Financeira)-[:ADMINISTRA]->(f:Fundo)
MATCH (i)-[:GERE]->(f)
MATCH (i)-[:CUSTODIA]->(f)
RETURN i.nome AS instituicao, count(f) AS fundos_multiplos_papeis
ORDER BY fundos_multiplos_papeis DESC LIMIT 10
```

### Risco Sistêmico — Fundos Expostos a um Título Público
```cypher
WITH 'LETRAS FINANCEIRAS DO TESOURO' AS tituloAlvo
MATCH (t:Titulo_Publico {tipo_titulo: tituloAlvo})<-[c:COMPRA]-(f:Fundo)
RETURN t.tipo_titulo AS titulo,
       count(DISTINCT f) AS fundos_expostos,
       round(avg(c.weight)*100)/100 AS peso_medio_carteira
```

### Fund of Funds — Cadeia de Aninhamento
```cypher
MATCH path = (f1:Fundo)-[:COMPRA*2..5]->(fn:Fundo)
RETURN f1.razao_social AS fundo_raiz,
       fn.razao_social AS fundo_folha,
       length(path) AS profundidade,
       [n IN nodes(path) | n.razao_social] AS cadeia
ORDER BY profundidade DESC LIMIT 10
```

### Concentração de Carteira Acima do Limite
```cypher
WITH 0.50 AS limiteConcentracao
MATCH (f:Fundo)-[c:COMPRA]->(a)
WHERE c.weight > limiteConcentracao
  AND f.situacao = 'EM FUNCIONAMENTO NORMAL'
RETURN f.razao_social AS fundo, f.classe AS classe,
       coalesce(a.descricao_ativo, a.tipo_titulo, a.razao_social) AS ativo,
       round(c.weight * 100) AS pct_carteira, c.anomes AS periodo
ORDER BY c.weight DESC
```

### Top Controladores do Mercado
```cypher
MATCH (i:Instituicao_Financeira)-[:CONTROLA]->(f:Fundo)
RETURN i.nome AS controlador, count(f) AS fundos_controlados
ORDER BY fundos_controlados DESC LIMIT 10
```

### Cobertura de Auditoria por Auditor
```cypher
MATCH (a:Auditor)-[:AUDITA]->(f:Fundo)
RETURN a.nome AS auditor, count(f) AS fundos_auditados
ORDER BY fundos_auditados DESC
```

---

## 📁 Documentação

| Arquivo | Descrição |
|---------|-----------|
| [`Neo4j_PreVenda_Financeiro.pdf`](./Neo4j_PreVenda_Financeiro.pdf) | Documento completo de pré-venda com modelo de dados, casos de uso, scripts comentados, queries de demo e comparativo Neo4j vs SQL para o mercado financeiro |

O documento inclui:
- ✅ Inventário completo do modelo de dados (nós, relacionamentos, propriedades)
- ✅ Texto explicativo para audiência não-técnica (CROs, CCOs, gestores de risco)
- ✅ 4 scripts Cypher reutilizáveis e parametrizados
- ✅ 6 consultas prontas para demonstração ao vivo
- ✅ Tabela comparativa Neo4j vs SQL/sistemas tradicionais para argumentação em pré-venda

---

## 📌 Distribuição dos Fundos no Modelo

| Classe                 | Qtd.   | % do Total |
|------------------------|--------|------------|
| Fundo Multimercado     | 25.140 | 65,2%      |
| Fundo de Renda Fixa    | 6.454  | 16,7%      |
| Fundo de Ações         | 5.917  | 15,4%      |
| Fundo Referenciado     | 637    | 1,7%       |
| Outros                 | 385    | 1,0%       |

---

## ⚖️ Neo4j vs. SQL para o Mercado Financeiro — Resumo

| Capacidade                    | SQL / Sistemas Tradicionais                    | Neo4j                                               |
|-------------------------------|------------------------------------------------|-----------------------------------------------------|
| Conflito de interesse         | JOINs múltiplos entre tabelas de papéis        | 1 query — todos os papéis em uma única travessia    |
