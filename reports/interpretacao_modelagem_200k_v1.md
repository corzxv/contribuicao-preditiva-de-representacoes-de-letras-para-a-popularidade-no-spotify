# Primeira comparação Ridge — domínio observado (02/11/2026)

Fonte: `modelagem_200k_v1/integral/resumo_modelagem.json`, métricas, contrastes e
alphas do script 22. Execução manual concluída: 77.535 faixas, CV agrupada aninhada
5×3, 20 partes Ridge e dez referências; 360 ajustes internos, zero avisos registrados.
Última retomada 651,372 s (19 novas partes/uma reutilizada), não tempo total acumulado.
Os números abaixo são pontos descritivos das previsões externas, sem IC/p-valores.

## Resultados nas mesmas observações

| Bloco/Referência | MAE não ponderado | RMSE | R² | MAE com pesos originais |
| --- | ---: | ---: | ---: | ---: |
| Baseline | 8,3525 | 10,8255 | 0,5087 | 8,2194 |
| Tradicional | 8,2957 | 10,7538 | 0,5152 | 8,1652 |
| Profundo | 8,1285 | 10,5540 | 0,5330 | 8,0032 |
| Combinado | 8,1151 | 10,5381 | 0,5344 | 7,9908 |
| Média do treino externo | 12,5621 | 15,4463 | -0,0003 | 12,4181 |
| Mediana do treino externo | 12,4786 | 15,5708 | -0,0165 | 12,3213 |

Cada variante tem n=77.535; treino com pesos iguais, alpha escolhido só pela
MAE interna não ponderada. Pesos são aplicados apenas à métrica de sensibilidade,
nas mesmas previsões. Não há treino ponderado, clipping, PCA ou nova seleção.

## Incremento observado

| Contraste | Delta MAE | Delta MAE ponderado |
| --- | ---: | ---: |
| Tradicional − Baseline | -0,0568 | -0,0542 |
| Profundo − Baseline | -0,2240 | -0,2163 |
| Combinado − Baseline | -0,2374 | -0,2286 |
| Combinado − Tradicional | -0,1806 | -0,1744 |
| Combinado − Profundo | -0,0134 | -0,0123 |

Delta negativo indica menor erro do primeiro bloco. Frente ao Baseline, reduções
relativas de MAE: Tradicional 0,680%, Profundo 2,681%, Combinado 2,842%. Na
avaliação ponderada, Combinado reduz MAE em 2,781% frente ao Baseline. A ordenação
se mantém com pesos originais; magnitude/direção pontual dos contrastes são similares.

Há contribuição preditiva incremental observada de letras neste procedimento
Ridge; o bloco de embeddings apresenta incremento maior que os 21 descritores
tradicionais isoladamente. O ganho total é modesto na escala de popularidade:
Combinado reduz aproximadamente 0,24 ponto de erro absoluto médio frente ao
Baseline. Acrescentar os descritores ao Profundo reduz só 0,0134 ponto. Isso não
estabelece significância estatística, equivalência prática ou superioridade universal.
Também não atribui causalmente o incremento a características isoladas da letra.

## Integridade e limites

Inspeção do agente: resumo concluído, zero partes pendentes, arquivo global com
77.535 linhas e hash correspondente; 30 modelos/arquivos de previsões com hashes
e footers conferidos, cada parte com 15.507 observações. Código/protocolo 22 e
assinatura preservados. Não houve desserialização, refit ou novo treino real pelo
agente. A reprodução integral linha a linha/diagnósticos será manual no script 23.

Não inferir ausência total de vazamento por inspeção de contagens: regras de
artista/composição/texto e sua auditoria em 21 são operacionais, não identificadores
universais. A exposição do teste histórico v0.6 permanece declarada. Integridade
técnica não certifica precisão semântica de todos os matches Spotify–LRCLIB.

Os quatro blocos são representações comparadas dentro da família Ridge, não
quatro famílias de algoritmos nem teste de toda possível representação textual.
Seis escolhas de alpha entre vinte ficaram no extremo inferior da grade; é limite
de resolução da comparação fixada, não motivo para expandi-la após ver o teste.

Conforme protocolo, previsões sem clipping: Baseline 537, Tradicional 585,
Profundo 610 e Combinado 615 fora de 0..100 (Combinado ~0,79%). Esse diagnóstico
não autoriza substituir as métricas primárias por uma versão pós-processada.

## Alcance estatístico e próxima etapa

Os resultados se referem ao domínio observado das 77.535 faixas com letras
aceitas, sob o desenho agrupado utilizado. Não são inferência causal, previsão
de sucesso futuro ou prova de representatividade do catálogo ou de todas as músicas com letras.
Pesos originais não corrigem automaticamente o mecanismo de disponibilidade textual.

A sensibilidade à ponderação pontual não alterou a ordenação, mas estabilidade
por fold/subgrupo/componente ainda será examinada. Não tratar erros de faixas
ou cinco folds como réplicas independentes para obter IC/significância; a
dependência na CV exige tratamento específico. Ver [Bengio e Grandvalet (2004)](https://www.jmlr.org/papers/v5/grandvalet04a.html).

O script 23 foi executado e concluído: métricas/contrastes e as 30 partes foram
reproduzidos, sem novo treino/IC. Seu protocolo foi preparado depois das métricas
globais, e os diagnósticos permanecem exploratórios. Qualquer inferência adicional
precisa declarar estimando, hipóteses e dependência do treinamento/validação.

## Diagnósticos concluídos e material para a monografia

- Combinado menor que Baseline nos cinco folds: deltas de -0,2724 a -0,2070.
  A ordem principal Baseline/Tradicional/Profundo/Combinado se mantém nas cinco
  partições. Os folds não são réplicas independentes para testes de significância.
- Os cinco contrastes mantiveram delta negativo ao retirar qualquer componente
  da avaliação, com pesos iguais e originais. Combinado−Baseline varia de
  -0,238056 a -0,235877; Combinado−Profundo de -0,013815 a -0,013159. São extremos
  condicionais a modelos/previsões fixos, não IC nem validação com retreino.
- Faixas 80-100: n=128, MAE Baseline 30,9294 e Combinado 29,3711. O modelo não
  deve ser descrito como igualmente preciso em toda a distribuição da resposta.
- Status de idioma estimado: redução Combinado/Baseline de 0,1561 no inglês
  (n=56.908) e 0,4693 no não inglês (20.447); nos incertos (180), piora de 0,4204.
  Não atribuir diferenças apenas ao idioma nem excluir esse grupo da análise.
- Combinado melhor em 59 dos 76 gêneros com métricas publicadas, não em todos.
  Houve 116 células publicadas e 77 com métricas omitidas por limiares, mantendo
  seus casos no global. Quatro chaves históricas indeterminadas continuam registradas.

O script 24 consolidou somente esses agregados pequenos em um trecho parcial de
métodos/resultados/discussão: reports/overleaf_dominio_observado_200k_v1/ e ZIP,
seis tabelas e quatro figuras PNG/SVG. main.tex compilado no editor integrado.
PDF de leitura separado em output/pdf/resultados_dominio_observado_200k_v1.pdf,
sete páginas renderizadas/revisadas. O PDF usa ReportLab, não é exportação da
compilação TeX; paginação pode diferir. A integração ao texto completo aguarda
identificação do arquivo principal; os dois pacotes parciais ficam preservados.
