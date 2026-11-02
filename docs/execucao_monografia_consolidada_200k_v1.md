# Monografia consolidada — 02/11/2026

Modelagem principal encerrada por decisão explícita do pesquisador (D-022).
Próximo trabalho é revisão acadêmica de uma monografia completa, não procurar
melhores modelos, recuperar mais letras ou regenerar o corpus.

Entrada: reports/monografia_consolidada_200k_v1/main.tex.
Entrega: ZIP de mesmo nome e output/pdf/monografia_consolidada_200k_v1.pdf.
Relatório de seções/pendências: reports/relatorio_consolidacao_monografia_200k_v1.md.
Autor/orientador: Felipe Macedo Cordeiro / Leandro Tavares Correa.

57 páginas compiladas do TeX, 11 capítulos, quatro apêndices, 14 tabelas,
oito figuras e 19 referências. Não é o PDF ReportLab do trecho parcial antigo.
Revisão visual concluída; bibliografia, referências cruzadas e preservação auditadas.
Modelo institucional não confirmado; não afirmar conformidade ABNT/UnB.

Para importar: enviar ZIP ao Overleaf, selecionar main.tex, pdfLaTeX e compilar.
O fluxo inclui BibTeX/natbib/plainnat. Todos os recursos estão no pacote; não
requer acesso a bases, letras, modelos ou execução Python. A paginação pode variar
entre engines, sem alterar os resultados. A versão entregue foi compilada por
Tectonic 0.17.0, usando apenas fontes/pacotes tipográficos em cache temporário.

## Reprodução editorial opcional, já executada

```powershell
& "C:\Users\Concursos Felipe\Documents\UnB\TCC\.venv\Scripts\python.exe" "C:\Users\Concursos Felipe\Documents\UnB\TCC\scripts\28_preparar_artefatos_monografia.py"
```

Somente agregados existentes, com orçamentos explícitos de tamanho/linhas; não
lê bases individuais nem toca a pipeline. O gerador protege tabelas/figuras
editadas manualmente. Capítulos são fontes autorais e não são sobrescritos.
Nenhum comando pesado está pendente ou é necessário para revisar o texto.

## Regras para a revisão

- Preservar resultados: Baseline 8,3525, Tradicional 8,2957, Profundo 8,1285,
  Combinado 8,1151; ganho relativo conjunto 2,84%.
- Limites auxiliares são condicionais/exploratórios e não cobrem toda a incerteza
  de seleção e treinamento. Não anunciar superioridade confirmada frente ao Profundo.
- Manter variante E5 explicitada: token adicional de espaço, sem medir seu impacto
  no MAE ou substituir vetores/previsões depois dos testes.
- Não misturar métricas históricas com a linha atual, mudar população/pesos/folds
  ou inferir datas de coleta ausentes. Pendências detalhadas no Apêndice D.
- Scripts 17–27 são etapas concluídas; não repetir para atualizar redação.

Verificação final: verificacao_monografia_consolidada_200k_v1.json; inventário de
195 materiais/135 textos e 154 artefatos prévios protegidos no projeto. Nenhum
commit/push ou movimento de dados/modelos foi realizado.
