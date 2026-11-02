# Monografia consolidada — versão para revisão acadêmica

Autor: Felipe Macedo Cordeiro. Orientador: Leandro Tavares Correa, confirmado
pelo pesquisador em 02/11/2026. O título descritivo foi definido com autorização
para esta consolidação. Nenhuma data de defesa, banca ou titulação do orientador
foi presumida.

Arquivo principal: **main.tex**. Há 11 capítulos, quatro apêndices, resumo,
abstract, siglas, sumário, listas, 14 tabelas, oito figuras e 19 referências.
O PDF entregue tem 57 páginas na compilação Tectonic 0.17.0; paginação pode
variar com compilador/versão. É o PDF compilado do TeX, não renderização paralela
de um texto diferente.

## Importar no Overleaf

1. New Project > Upload Project e selecionar o ZIP.
2. Confirmar main.tex como Main document.
3. Usar pdfLaTeX e uma versão recente do TeX Live. XeLaTeX também é compatível;
   a compilação local foi feita por Tectonic/XeTeX.
4. Recompile. A bibliografia BibTeX usa natbib/plainnat; o fluxo do Overleaf
   resolve automaticamente as passagens para bibliografia e referências.

Todos os capítulos, tabelas, PNGs e referências estão no pacote. Não é necessário
Python, acesso a bases, letras ou modelos para compilar. SVGs são opções editáveis;
o TeX usa PNGs. Não há fontes institucionais externas ou classe personalizada.

## Escopo e preservação

Avaliação Ridge congelada no domínio de 77.535 faixas. Quatro configurações de
variáveis, mesmos casos/folds; encoder neural congelado. As limitações incluem
seleção das letras, dependência/exposição histórica, cauda e token extra do prefixo
E5. Limites auxiliares não representam incerteza integral do treinamento.

Nenhum resultado dos dois pacotes parciais anteriores foi substituído. Eles
permanecem históricos. Este projeto é novo; a reprodução editorial não executa
recuperação, treinamento ou embeddings.

PROVENIENCIA_AGREGADOS.json registra entradas/hash dos agregados e arquivos
gerados. source_data/ contém somente agregados públicos pequenos. Inventário e
preservação anteriores estão em INVENTARIO_REAPROVEITAMENTO.json e
PRESERVACAO_ANTERIOR.json. references/VERIFICACAO_REFERENCIAS.csv distingue
metadados confirmados e lacunas das fontes; o JSON de DOI guarda a conferência
bibliográfica estruturada.

## Revisão pendente

Não foi localizado modelo institucional UnB aplicável no repositório. Classe
report, margens e estilo de referências são escolhas editoriais para revisão,
sem declaração de conformidade ABNT/UnB. Pendências específicas e seis pontos
para o orientador estão no Apêndice D. Datas da popularidade, versão do CSV e
significado de year permanecem não confirmados. A revisão humana de matching
não foi substituída por auditoria criptográfica.

No repositório, o script 28 e monograph_assets.py recompõem somente tabelas/figuras
de agregados, protegendo saídas editadas manualmente. Capítulos são fontes autorais
editáveis e não são sobrescritos pelo gerador. A modelagem não deve ser reaberta
automaticamente para revisar a monografia.
