# ⚖️ Neo4j para o Setor Jurídico — Knowledge Graph de Normas com Gen AI

> Material de pré-venda Neo4j para o domínio jurídico e de compliance, demonstrando capacidades e diferenciais para Análise de Documentos, Dependências Normativas, Assistente Jurídico com Gen AI e Rastreabilidade de Autoria.

---

## 📋 Sobre o Projeto

Este repositório contém scripts Cypher, consultas de demonstração e documentação de pré-venda baseados em um **Knowledge Graph Jurídico com Gen AI integrada** — um banco de normas, portarias, resoluções e atos oficiais com textos completos, embeddings vetoriais pré-computados, taxonomia jurídica e grafo de dependências normativas.

O material cobre os casos de uso de **Análise de Documentos, Gen AI (GraphRAG), Normas e Leis, Dependências Normativas e Compliance Jurídico** — com foco em escritórios de advocacia, departamentos jurídicos, órgãos públicos e equipes de compliance.

---

## 📊 Visão Geral do Modelo

| Entidade               | Volume  | Papel                                                                        |
|------------------------|---------|------------------------------------------------------------------------------|
| TextoSim               | 48.291  | Texto integral + **embedding vetorial (1536 dims)** — base da Gen AI / RAG  |
| Meta_Publicacao        | 38.777  | Metadados de publicação oficial                                              |
| Meta_Documento_Oficial | 38.541  | Metadados enriquecidos com categoria, tema e gênero                          |
| Meta_Documento         | 38.316  | Nome do arquivo, URL do PDF, link para o documento físico                    |
| Documento_Oficial      | 9.750   | Normas, portarias, resoluções, recomendações (CNMP)                          |
| Pessoa                 | 5.980   | Pessoas mencionadas, assinantes e signatários dos documentos                 |
| Referencia_Externa     | 3.481   | Leis, normas e atos externos citados nos documentos                          |
| Assinante / Signatario | 844/693 | Quem assinou formalmente cada ato ou norma                                   |
| Meta_Tema              | 100     | Taxonomia temática jurídica (Penalidade, Inspeção, Aposentadoria etc.)       |
| Meta_Categoria         | 15      | Tipo de documento (Resolução, Portaria, Nota Técnica etc.)                   |

**Relacionamentos principais:**

| Relacionamento                   | Volume  | Semântica                                                          |
|----------------------------------|---------|--------------------------------------------------------------------|
| REPRESENTA                       | 48.291  | Meta_Documento_Oficial → TextoSim (embedding vetorial)             |
| ASSOCIADA_A_TEMA                 | 38.505  | Documento classificado por tema jurídico                           |
| ASSOCIADA_A_CATEGORIA            | 38.503  | Documento classificado por categoria normativa                     |
| ASSOCIADO_A_TEXTOSIM             | 31.675  | Documento vinculado ao seu texto semântico                         |
| ASSOCIADO_A_PESSOA               | 22.353  | Documento menciona ou é assinado por Pessoa                        |
| POSSUI_ASSINANTE                 | 10.980  | Documento possui Assinante formal                                  |
| RELACIONADO_A_DOCUMENTO_OFICIAL  | 3.553   | **Norma DEPENDE DE / ALTERA outra norma** — grafo de dependências  |
| ASSOCIADO_A_REFERENCIA_EXTERNA   | 3.331   | Documento cita lei ou norma externa                                |

---

## 🗂️ Modelo de Dados

```
(Meta_Categoria) <-[:ASSOCIADA_A_CATEGORIA]- (Meta_Documento_Oficial)
(Meta_Tema)      <-[:ASSOCIADA_A_TEMA]------  (Meta_Documento_Oficial)
(Meta_Genero)    <-[:ASSOCIADA_A_GENERO]----  (Meta_Documento_Oficial)
(Meta_Publicacao)<-[:ASSOCIADA_A_PUBLICACAO]- (Meta_Documento_Oficial)

(Meta_Documento_Oficial)-[:ASSOCIADO_A_DOCUMENTO]------→ (Meta_Documento)
(Meta_Documento_Oficial)-[:ASSOCIADO_A_DOCUMENTO_OFICIAL]→ (Documento_Oficial)
(Meta_Documento_Oficial)-[:ASSOCIADO_A_TEXTOSIM]--------→ (TextoSim)  ← embedding vetorial
(Meta_Documento_Oficial)-[:ASSOCIADO_A_PESSOA]----------→ (Pessoa)
(Meta_Documento_Oficial)-[:POSSUI_ASSINANTE]------------→ (Assinante)
(Meta_Documento_Oficial)-[:ASSOCIADO_A_SIGNATARIO]------→ (Signatario)
(Meta_Documento_Oficial)-[:ASSOCIADO_A_REFERENCIA_EXTERNA]→ (Referencia_Externa)

(Documento_Oficial)-[:RELACIONADO_A_DOCUMENTO_OFICIAL]--→ (Documento_Oficial)
                                         ↑ grafo de dependências normativas
```

> O nó **TextoSim** contém o texto integral do documento e seu **embedding vetorial pré-computado** — pronto para busca semântica e GraphRAG sem reprocessamento.

---

## 🚀 Casos de Uso

| # | Caso de Uso                                    | Valor de Negócio                                                                                      |
|---|------------------------------------------------|-------------------------------------------------------------------------------------------------------|
| 1 | **Assistente Jurídico com GraphRAG**           | Busca semântica vetorial + contexto de grafo = respostas jurídicas precisas e citáveis                |
| 2 | **Análise de Dependências e Impacto Normativo**| Identifica todos os documentos afetados por uma alteração normativa em milissegundos                  |
| 3 | **Rastreabilidade e Cadeia de Responsabilidade**| Reconstrói quem assinou o quê, em que tema, com qual autoridade                                       |
| 4 | **Mapeamento de Referências Externas**         | Detecta normas internas que citam legislação desatualizada — gap de compliance automatizado            |
| 5 | **Classificação Inteligente do Acervo**        | Embeddings sugerem classificação automática por similaridade semântica                                 |

---

## 🔍 Consultas de Demonstração

### Normas Mais Referenciadas (Hub Normativo)
```cypher
MATCH (d:Documento_Oficial)<-[:RELACIONADO_A_DOCUMENTO_OFICIAL]-(other:Documento_Oficial)
RETURN d.doficialTitulo AS norma, d.doficialTipo AS tipo,
       count(other) AS vezes_referenciada
ORDER BY vezes_referenciada DESC LIMIT 10
```

### Grafo de Dependência de uma Norma
```cypher
MATCH (alvo:Documento_Oficial)
WHERE alvo.doficialTitulo CONTAINS 'CNMP-PRESI no 57'
OPTIONAL MATCH (alvo)<-[r1:RELACIONADO_A_DOCUMENTO_OFICIAL]-(dep:Documento_Oficial)
OPTIONAL MATCH (alvo)-[r2:RELACIONADO_A_DOCUMENTO_OFICIAL]->(base:Documento_Oficial)
RETURN alvo, r1, dep, r2, base
```

### Cadeia de Responsabilidade por Pessoa
```cypher
WITH 'Antônio Augusto Brandão de Aras' AS nomePessoa
MATCH (p:Pessoa {pessoaNome: nomePessoa})
<-[:ASSOCIADO_A_PESSOA]-(md:Meta_Documento_Oficial)
OPTIONAL MATCH (md)-[:ASSOCIADA_A_CATEGORIA]->(c:Meta_Categoria)
RETURN p.pessoaNome AS pessoa, c.mcategoriaCategoria AS categoria, count(md) AS documentos
ORDER BY documentos DESC
```

### Documentos por Tema Jurídico
```cypher
MATCH (md:Meta_Documento_Oficial)-[:ASSOCIADA_A_TEMA]->(t:Meta_Tema)
WHERE t.mtemaTema = 'Penalidade administrativa'
OPTIONAL MATCH (md)-[:ASSOCIADO_A_DOCUMENTO]->(doc:Meta_Documento)
RETURN md.mdocumentoUnico AS documento, doc.mdocumentoUrl AS url
LIMIT 20
```

### Busca Semântica com Embeddings (GraphRAG)
```cypher
// Substitua o vetor pelo embedding gerado para sua pergunta
WITH [/* embedding da pergunta */] AS queryEmbedding
MATCH (t:TextoSim)
WHERE t.embedding IS NOT NULL
WITH t, gds.similarity.cosine(queryEmbedding, t.embedding) AS score
WHERE score > 0.80
MATCH (md:Meta_Documento_Oficial)-[:ASSOCIADO_A_TEXTOSIM]->(t)
RETURN t.texto[0..500] AS trecho, score AS similaridade
ORDER BY score DESC LIMIT 10
```

### Referências Externas mais Citadas
```cypher
MATCH (md:Meta_Documento_Oficial)-[:ASSOCIADO_A_REFERENCIA_EXTERNA]->(r:Referencia_Externa)
RETURN r.referenciaexternaDescricao AS referencia_externa,
       count(md) AS documentos_que_citam
ORDER BY documentos_que_citam DESC LIMIT 15
```

---

## 📁 Documentação

| Arquivo | Descrição |
|---------|-----------|
| [`Neo4j_PreVenda_Juridico.pdf`](./Neo4j_PreVenda_Juridico.pdf) | Documento completo de pré-venda com modelo de dados, 5 casos de uso, scripts comentados, queries de demo e comparativo Neo4j vs GED tradicional |

O documento inclui:
- ✅ Inventário completo do modelo de dados com volumes e papel de cada entidade
- ✅ Texto explicativo para audiência não-técnica (advogados, compliance officers, gestores jurídicos)
- ✅ 4 scripts Cypher reutilizáveis e parametrizados (incluindo busca vetorial GraphRAG)
- ✅ 6 consultas prontas para demonstração ao vivo no Neo4j Browser
- ✅ Tabela comparativa Neo4j + Gen AI vs GED tradicional para argumentação em pré-venda

---

## 📌 Taxonomia do Acervo — Categorias de Documentos

| Categoria                  | Volume  | Natureza Jurídica              |
|----------------------------|---------|--------------------------------|
| Termo de Cooperação        | 23.108  | Ato bilateral entre órgãos     |
| Portaria da Corregedoria   | 6.966   | Ato normativo interno          |
| Portaria da Secretaria Geral | 4.010 | Ato administrativo             |
| Portaria da Presidência    | 3.804   | Ato de gestão superior         |
| Resolução                  | 312     | Norma de caráter geral         |
| Recomendação               | 128     | Orientação não vinculante      |
| Nota Técnica / Súmula / Enunciado | 64 | Interpretação e jurisprudência |

---

## ⚖️ Neo4j + Gen AI vs. Soluções Tradicionais — Resumo

| Capacidade                    | GED / Ferramentas Tradicionais         | Neo4j + Gen AI (GraphRAG)                     |
|-------------------------------|----------------------------------------|-----------------------------------------------|
| Busca semântica               | Palavras-chave — alto ruído            | Embeddings vetoriais — busca por significado  |
| Dependências normativas       | Documentos isolados — sem relações     | Grafo de dependências — impacto em cascata    |
| Rastreabilidade de autoria    | Metadados textuais desconexos          | Grafo Pessoa-Documento navegável              |
| Análise de impacto normativo  | Levantamento manual — semanas          | Query Cypher — milissegundos                  |
| Assistente jurídico (LLM)     | LLM sem contexto — respostas genéricas | GraphRAG: LLM + grafo = respostas citáveis    |
| Classificação do acervo       | Taxonomia manual — custosa             | Similaridade vetorial sugere classificação    |
| Visualização das relações     | Não disponível em GEDs                 | Neo4j Bloom — mapa interativo do acervo       |

---

## 🛠️ Tecnologias

- **Neo4j** — banco de dados de grafo
- **Cypher** — linguagem de consulta
- **Neo4j GDS** (Graph Data Science) — `gds.similarity.cosine` para busca vetorial
- **Embeddings Vetoriais** — armazenados nativamente no grafo (1536 dimensões por documento)
- **GraphRAG** — padrão de Retrieval-Augmented Generation com contexto de grafo
- **Neo4j Browser / Bloom** — visualização interativa do acervo normativo

---
