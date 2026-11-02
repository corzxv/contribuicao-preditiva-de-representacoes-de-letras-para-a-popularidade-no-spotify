# Escrita e figuras da linha recente — concluído

Depois das etapas 22/23, o script 24 consolidou somente agregados públicos pequenos
(696 linhas de subgrupos e tabelas globais), em operação leve. Nenhum dado individual,
modelo ou vetor foi lido para essa geração. Nenhum treino/retuning foi executado.

## Material entregue

- `reports/overleaf_dominio_observado_200k_v1/`: novo projeto parcial, main.tex,
  seis tabelas, quatro figuras PNG 300 dpi/SVG, referências, fonte manuscrito.json,
  agregados de origem e proveniência/hashes.
- `reports/overleaf_dominio_observado_200k_v1.zip`: 28 arquivos, CRC e caminhos
  relativos verificados, sem letras/bases/modelos/previsões individuais.
- `output/pdf/resultados_dominio_observado_200k_v1.pdf`: leitura de sete páginas,
  gerada com ReportLab e renderizada/inspecionada. Não é exportação do TeX.
- `reports/verificacao_publicacao_200k_v1.json`: integridade e escopo da verificação.

main.tex compilou com sucesso no editor LaTeX integrado do Codex; não foi necessário
instalar TeX no terminal. No Overleaf, enviar o ZIP, escolher main.tex, compilador
pdfLaTeX/UTF-8 e compilar duas vezes. Não é necessário acesso aos dados ou Python.
O PDF de leitura e o TeX compartilham manuscrito.json, mas podem ter paginações
diferentes. Não afirmar que o PDF é saída do compilador TeX.

## Conteúdo e limites

Métodos, resultado global, estabilidade entre folds/remoção condicional de
componentes, cauda de popularidade, idiomas, exposição histórica e discussão.
O ganho médio favorável não é uniforme: erro alto nos casos 80-100 e piora nos
idiomas incertos foram incluídos. Sem IC/p-valores ou exclusão de casos para
melhorar desempenho. Resultados de subgrupos são exploratórios; pacote parcial,
sem capa/template oficial, introdução ou revisão bibliográfica completa.

Preservar o pacote antigo reports/overleaf_resultados_coorte_aceita_v1/. Para
integrar no texto completo, copiar/adaptar hierarquia e pacotes, consolidar
bibliografia e preservar os resultados dos universos distintos. O caminho do
arquivo principal completo foi solicitado ao pesquisador, pois não foi localizado
na busca do repositório. Não mover ou sobrescrever projeto desconhecido.

## Reprodução opcional, leve — não é próxima tarefa pesada

```powershell
& "C:\Users\Concursos Felipe\Documents\UnB\TCC\.venv\Scripts\python.exe" "C:\Users\Concursos Felipe\Documents\UnB\TCC\scripts\24_consolidar_resultados_monografia.py"
```

Produz TeX/ZIP/figuras a partir de agregados já concluídos. Recusa regenerar
arquivos que tenham sido editados manualmente; usar --project com nova pasta
para preservar revisões. Depois de revisar texto no editor, não sobrescrevê-lo.

PDF de leitura opcional, usando ReportLab do runtime disponibilizado neste ambiente:

```powershell
& "C:\Users\Concursos Felipe\Documents\UnB\TCC\.venv\Scripts\python.exe" "C:\Users\Concursos Felipe\Documents\UnB\TCC\scripts\24_consolidar_resultados_monografia.py" --pdf-python "C:\Users\Concursos Felipe\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"
```

O caminho do runtime é específico deste ambiente; não é requisito para compilar
no Overleaf. Nenhuma dependência foi instalada no venv durante esta entrega.
Próximo trabalho: integração/escrita e revisão das limitações, sem repetir 17–23.
