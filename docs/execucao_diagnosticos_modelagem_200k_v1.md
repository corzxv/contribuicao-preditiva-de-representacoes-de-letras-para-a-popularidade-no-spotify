# Resultados Ridge concluídos — diagnósticos sem novo treino

**Concluído pelo pesquisador:** 0,608 s; 77.535 faixas, 30 partes/métricas
reproduzidas, 21.893 componentes, sem treino/IC. 116 células publicadas e 77
com métricas omitidas. O comando abaixo é reprodução histórica; não repetir
para continuar. Próximo: integração/escrita, material em
execucao_publicacao_resultados_200k_v1.md.

Script 22 integral concluído: 20/20 partes Ridge e dez referências, zero pendências,
77.535 previsões externas por variante. Última retomada: 651,372 s, 19 novas partes
e uma reutilizada. Não repetir 22 para continuar; modelos/grade/folds preservados.

As métricas globais já existem e a primeira interpretação foi registrada em
`reports/interpretacao_modelagem_200k_v1.md`. Os ganhos são descritivos, sem IC
ou p-valor. O próximo script agrega diagnósticos de estabilidade das previsões
existentes; não treina, retuna, gera embeddings ou altera predições.

```powershell
& "C:\Users\Concursos Felipe\Documents\UnB\TCC\.venv\Scripts\python.exe" "C:\Users\Concursos Felipe\Documents\UnB\TCC\scripts\23_diagnosticar_resultados_200k.py"
```

## O que será verificado

1. Vínculos das previsões com IDs, resposta, pesos, componentes e folds da base 21.
2. Igualdade entre previsões globais e as 30 partes; métricas/contrastes/alphas
   reproduzidos, referências coerentes com o treino externo, arquivos preservados.
3. Métricas por fold/idioma estimado, faixa de popularidade, período, gênero e
   exposição histórica do componente. Mesmas observações entre modelos em cada célula.
4. Influência da retirada de um componente **da avaliação**, mantendo modelos e
   previsões fixos. É diagnóstico condicional, não novo treino, IC ou teste estatístico.
5. Previsões fora de 0..100 e escolhas de alpha nos extremos da grade, sem corrigir
   ou trocar o protocolo depois de conhecer os resultados.

Publica métricas de subgrupos somente com >=100 faixas e >=20 componentes; células
menores ficam em celulas_pequenas.csv com contagens/motivo. Não exclui casos da
análise global. Não interpretar esses limiares como garantia de poder/precisão.
Os cortes e o protocolo foram preparados após ver as métricas globais e antes
de examinar erros por subgrupo; diagnósticos são exploratórios, sem p-valores.

## Saídas e conclusão

Públicos em `C:\Users\Concursos Felipe\Documents\UnB\TCC\reports\diagnosticos_modelagem_200k_v1\`:
resumo_diagnosticos.json, relatorio_diagnosticos.md, metricas_reproduzidas.csv,
diagnosticos_subgrupos.csv, sensibilidade_remocao_componente.csv,
previsoes_fora_intervalo.csv e celulas_pequenas.csv (quando houver).

Privado: `data/derived/private_results_diagnostics_200k_v1/perdas_componentes.parquet`,
com somas de perdas/contagens/pesos por componente e fold, sem letras. IDs de
componentes não são publicados. Não duplica quatro matrizes nem novos modelos.

Esperado: completed=true, cohort_rows=77.535, verified_parts=30, models=6,
components=21.893, metrics_reproduced=true, models_trained=false e
confidence_intervals_computed=false. Contagens de células e sensibilidade por
componente ainda são desconhecidas até execução. Avise com a saída para revisão.

É processamento de diagnóstico sobre a coorte inteira, reservado à execução
manual. Sem internet/SSD LRCLIB/encoder; uma instância por vez. Se interromper,
repetir este comando refaz apenas diagnóstico, sem alterar modelos/previsões.
Divergência bloqueia para investigação, sem exclusões/retreino automáticos.

Depois desses agregados: consolidar figuras/tabelas e texto de resultados da
monografia, distinguindo magnitude observada, sensibilidade e incerteza ainda
não quantificada. Qualquer método inferencial adicional deve declarar hipóteses
e dependência da CV; não produzir IC ingênuo a partir de cinco folds.
