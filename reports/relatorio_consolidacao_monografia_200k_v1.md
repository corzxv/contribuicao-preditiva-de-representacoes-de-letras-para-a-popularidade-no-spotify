# Consolidação da monografia — 02/11/2026

## Entrega e situação

Versão única, completa quanto aos capítulos solicitados e compilável, para revisão
acadêmica. Não é uma declaração de aprovação de banca ou conformidade institucional.
Autor Felipe Macedo Cordeiro; orientador Leandro Tavares Correa, informado pelo
pesquisador. Título definido para a consolidação com autorização do pesquisador.

- Fonte: reports/monografia_consolidada_200k_v1/main.tex.
- ZIP: reports/monografia_consolidada_200k_v1.zip.
- PDF compilado: output/pdf/monografia_consolidada_200k_v1.pdf.
- 57 páginas; 11 capítulos; quatro apêndices; 14 tabelas; oito figuras;
  bibliografia .bib com 19 entradas verificadas.

## Seções concluídas

| Parte | Conteúdo integrado e evidência |
| --- | --- |
| Pré-textuais | Capa, folha de rosto para revisão, nota de versão, resumo/abstract, siglas, sumário e listas. Sem dados de defesa inventados |
| 1 — Introdução | Problema, objetivos, justificativa, contribuição e delimitação do alvo observado |
| 2 — Fundamentação | Predição/perdas, Ridge, representações textuais, dependência/CV e desenho amostral; revisão metodológica temática, sem alegar revisão sistemática exaustiva |
| 3 — Fontes | Spotify acessível, derivação LFM2b histórica e LRCLIB textual; respostas/unidades/datas distintas |
| 4 — Amostra e integração | Sorteio de 200 mil, inclusão integral ≥80, 981 estratos, probabilidades/pesos, recuperação v2, critérios e destinos reconciliados |
| 5 — Descritiva e seleção | Médias/quantis/distribuições reais, cobertura, estratos sem letras, diagnóstico de equivalência e corpus multilingue |
| 6 — Representações | Entrada comum, 21 definições, E5 congelado, janelas/pooling/L2, desvio real do token de espaço e escopo das auditorias |
| 7 — Modelagem | Quatro configurações de variáveis Ridge, componentes/folds comuns 5×3, pré-processamento restrito ao treino, grade/critério, métricas e pesos |
| 8 — Resultados | Métricas de quatro blocos/duas referências, cinco contrastes, sensibilidade de avaliação, folds e alphas selecionados |
| 9 — Diagnósticos | Limites auxiliares condicionais, influência por componente, idioma/gênero, cauda, negativos e clipping separado |
| 10 — Discussão | Magnitude/alcance, matching, seleção, representação, exposição histórica, incerteza e utilidade não uniforme |
| 11 — Conclusões | Resposta à pergunta empírica e trabalhos futuros delimitados, sem nova rodada automática de modelos |
| Referências | 19 entradas com fontes e metadados; DOI/edições distinguidos, correção de artigo identificada, s.d. onde não há data confirmada |
| Apêndices A–D | Dicionário de descritores, rastreabilidade/reprodução, trajetória/compatibilidade e pendências/lista para o orientador |

## Investigação e reaproveitamento do acervo

Foram inventariados 195 arquivos acadêmicos de docs/reports; 135 arquivos textuais
foram lidos integralmente e os demais arquivos gráficos/documentais classificados
por arquivo e contexto. Não se afirma uma nova auditoria visual de cada figura
histórica. Inventário e cabeçalhos em INVENTARIO_REAPROVEITAMENTO.json no pacote.
Não foram localizados .cls/.sty/.bst institucionais nesses materiais.

Reaproveitamento por compatibilidade:

| Família | Conteúdo aproveitado | Conteúdo preservado sem misturar |
| --- | --- | --- |
| Integração Spotify–LFM2b v0.1/v0.1.1 | Papéis das fontes, separação de respostas, preservação e limites de identidade | Universo de 111.758 pares e suas tabelas/figuras não representam a coorte atual |
| Pilotos/desenvolvimento/teste v0.2–v0.6 | Motivação, princípios de validação e registro da exposição do teste | Métricas de 7.648/2.592 e vetores MiniLM não foram transportados |
| Diagnósticos/ampliação v0.7–v0.9 | História da exploração e necessidade de evitar confirmação retrospectiva | Outros algoritmos, curvas e amostras não viraram resultados Ridge recentes |
| Coorte ampliada antiga / Overleaf histórico | Organização e princípios metodológicos reutilizáveis | Resultados de 58.633 observações e seus modelos não foram agregados aos atuais |
| Catálogo/amostra/recuperação v2 | Caracterização, desenho, cobertura e seleção da linha principal | Diagnóstico v3 não aplicado não adiciona 31 casos à coorte |
| Etapas 17–24 atuais | Representações, dados/folds, métricas e oito figuras compatíveis, parte reaproveitadas e parte geradas de agregados | PDF e pacote parciais preservados, sem substituição |
| Parecer 25–27 | Incerteza condicional, resíduos, clipping e desvio do prefixo | Nenhum intervalo foi promovido a IC integral; nenhum vetor do corpus foi refeito |

## Pendências reais e fontes de confirmação

1. Data de medição de popularity: não confirmada. Verificar documentação do
   publicador correspondente ao CSV/hash; não inferir pela atualização ou download.
2. Versão exata do Kaggle e aquisição original: manifesto comprova reuso/verificação,
   não data original de download. Conferir registro histórico do publicador/autor.
3. Significado de year: confirmar sem presumir ano original de lançamento.
4. Modelo institucional e requisitos formais: obter da coordenação/orientador do
   Bacharelado em Estatística. Nenhuma classe homologada localizada; a classe report
   e natbib/plainnat não foram anunciadas como conformidade institucional.
5. Banca, defesa, ficha catalográfica e procedimentos de depósito: preencher somente
   depois de informação institucional/autor confirmada.
6. Precisão semântica do matching: não estimada por revisão humana probabilística.
   Auditoria de integridade e inspeções dirigidas não autorizam inventar taxa global.
7. Condições específicas das fontes para distribuição: pacote não contém letras
   ou dados individuais; manter distinção entre licença de software/dados e letras.

O nome do orientador e a autorização para definir um título foram resolvidos
nesta conversa; não permanecem como lacunas. Não há dependência de localizar
um TeX principal antigo: o novo main.tex é a entrada consolidada.

## Pontos para revisar com o orientador

1. Formulação de população/estimando e separação entre descrição, predição e
   inferência populacional; restrição às aceitas.
2. Interpretação de 2,84% frente ao Baseline e incremento pequeno/inconclusivo
   frente ao Profundo, sem significância integral ou equivalência presumida.
3. Transparência da variante E5 com token extra; impacto preditivo não medido;
   preservação do resultado sem afirmar conformidade canônica.
4. Alcance das conclusões diante da revisão humana de matching ainda limitada.
5. Cauda/subgrupos: desempenho médio não implica estimação adequada de hits.
6. Adequação institucional, estilo bibliográfico e lacunas documentais que possam
   permanecer explicitamente não confirmadas na versão de defesa.

## Verificação executada

Compilação completa por Tectonic 0.17.0/XeTeX com BibTeX, em ambiente temporário
isolado. O compilador foi obtido da distribuição oficial, com SHA-256 do ZIP
conferido. Somente recursos tipográficos foram baixados. Nenhum dado da pesquisa
foi enviado a serviço de compilação remoto por esse procedimento.

Na versão final: zero referência/citação indefinida, zero overfull/underfull de
texto no log; aviso inputenc ignorado é esperado no engine Unicode. O diagnóstico
Fontconfig de configuração padrão não impediu uso das fontes TeX incorporadas.
As 57 páginas foram renderizadas e inspecionadas: 44 permaneceram pixel a pixel
iguais à revisão anterior e 13 páginas alteradas ou repaginadas foram reinspecionadas.
Foi removida uma página órfã de URL na bibliografia.

Dez testes de normalização e diagnósticos de fechamento passaram; Ruff check/format
e git diff --check verificados. Houve geração editorial leve de tabelas/figuras a
partir de agregados existentes, sem ler matrizes individuais, executar LRCLIB,
gerar embeddings do corpus, carregar modelos de regressão ou treinar.

154 relatórios, fontes/figuras e PDFs/ZIPs anteriores têm hashes registrados e
conferidos; entradas dos agregados e contratos de modelagem também foram mantidas.
Nenhum resultado científico anterior foi sobrescrito ou alterado. A documentação
canônica de continuidade foi atualizada por autorização do pesquisador. Comprovação
em reports/verificacao_monografia_consolidada_200k_v1.json e nos manifestos do pacote.
