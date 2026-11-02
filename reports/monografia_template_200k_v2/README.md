# Relatório TCC — versão no template fornecido

Autor: Felipe Macedo Cordeiro. Orientador: Leandro Tavares Correia (grafia confirmada
pelo pesquisador após consulta aos registros da UnB). Título: **Contribuição
preditiva de representações de letras para a popularidade no Spotify**.

## Upload no Overleaf

1. Crie um projeto com **Upload Project** e selecione o ZIP desta versão.
2. Em **Menu/Settings**, mantenha **Main document = main.tex**.
3. Selecione **XeLaTeX** e recompile. As referências usam **BibTeX**, processado
   automaticamente pelo Overleaf/latexmk. Não é necessário executar Biber.

O projeto é completo para compilação: inclui textos, bibliografia, emblema do
template, cinco figuras e dez tabelas. Não precisa das bases de pesquisa, de
letras, de modelos ou do SSD. O PDF foi compilado de fato a partir destes fontes,
com Tectonic 0.17.0/XeTeX/BibTeX, e não reconstruído com outro gerador.

## Organização acadêmica

- `introducao.tex`: problema, justificativa e objetivos.
- `refteorico.tex`: fundamentos e fórmulas com fontes originais.
- `metodologia.tex`: Spotify bruto → LRCLIB → amostragem → integração → domínio
  observado → representações e validação.
- `resultados.tex`: desempenho, incerteza condicional, cauda, clipping e subgrupos.
- `conclusao.tex`: conclusões e continuidade delimitada.
- Dois apêndices científicos: definições das 21 medidas e cálculo dos limites
  auxiliares. Registros de execução e pendências administrativas ficam fora do PDF.

## Relação com os modelos fornecidos

O projeto segue classe `article` 12pt/A4, margens 3/3/2/2 cm, espaço de 1,5,
cabeçalhos alternados, emblema/capa/rosto e cinco seções principais do template.
Equações são numeradas por subseção, como no exemplo de Ana. As referências
autor-data usam `abntex2cite`/`abntex2-alf`, o mesmo backend do exemplo, em lugar
do BibLaTeX/Biber do ZIP de template. Foram eliminadas importações duplicadas,
placeholders e a numeração inicial fixa em oito; a paginação é automática.
Não se presume que o arquivo fornecido substitua toda exigência de depósito.

A consulta a três TCCs da coleção de Estatística da BDM complementou a avaliação
de estrutura, fórmulas e bibliografias. Os TCCs não são referências científicas
da monografia: citam-se diretamente as fontes originais pertinentes, conferidas
por autor/editora/periódico. O exemplo de Ana e os TCCs da BDM não são distribuídos
neste pacote. As correspondências e verificações estão no relatório de revisão
do repositório e em `referencias_conferidas.csv`.

## Limites e preservação

Esta é uma versão acadêmica para revisão, preservando integralmente os resultados
e arquivos anteriores. A avaliação principal continua congelada. Data do escore,
versão exata do CSV e sentido de `year` não foram inventados. Matching, seleção
textual, variante E5, exposição histórica e alcance dos intervalos são explicados
no texto, sem inferência automática de catálogo ou causalidade.

O script 29 do repositório produz somente duas ilustrações novas e uma tabela de
agregados pequenos e reutiliza figuras/tabelas já auditadas. Não é necessário
executá-lo para compilar este projeto. `proveniencia_figuras.json` registra entradas
e hashes; `source_data/perfil_catalogo.json` contém apenas agregados públicos.
