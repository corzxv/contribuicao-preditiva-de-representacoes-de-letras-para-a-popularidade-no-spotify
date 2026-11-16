# Sensibilidade da decisão — execução manual

Atualização 06/11: 36 já concluído pelo pesquisador e conferido. 37 consolidação
de agregados/cauda delimitada/figuras concluída pelo agente. Não repetir comandos
para avançar à escrita. Relatório interpretacao_sensibilidade_decisao_ordinal_v1.md.
As instruções abaixo documentam a execução realizada, não nova tarefa pendente.

34 produção e 35 análise de agregados concluídos. Não repetir treinos. Resultados
principais preservados em reports/classificacao_ordinal_200k_v1/integral/.

Combinado obteve 60,58% de acurácia balanceada e sensibilidade elevada de 40,75%.
Próximo diagnóstico examina o compromisso entre classes mudando apenas a decisão
final, sem treinar ou recalibrar. Protocolo_sensibilidade_decisao_ordinal_v1.md.

```powershell
& "C:\Users\Concursos Felipe\Documents\UnB\TCC\.venv\Scripts\python.exe" "C:\Users\Concursos Felipe\Documents\UnB\TCC\scripts\36_avaliar_sensibilidade_decisao.py"
```

Execução manual porque lê as 77.535 linhas individuais de probabilidades. Não
exige internet/SSD/encoder ou novo pacote. Reproduz as métricas principais antes
de aplicar argmax original e argmax p/pi, com proporções pi dos treinos externos.
Esses escores ajustados não são novas probabilidades. Sem grade de custos ou
seleção por desempenho do teste; sem mudanças no modelo ou na resposta.

Conclusão: [3/3] Concluído; resumo em
reports/sensibilidade_decisao_ordinal_200k_v1/resumo_sensibilidade.json,
completed=true, original_metrics_reproduced=true, models_trained=false,
probabilities_changed=false e main_results_replaced=false.

Análise exploratória condicionada às probabilidades existentes. Configurações
dos modelos foram selecionadas para a regra original; esta sensibilidade não é
avaliação independente de treinamento otimizado para o custo novo. Pesos amostrais
continuam somente na avaliação de sensibilidade, sem correção de cobertura textual.

Se interromper, repetir o comando igual. Selo incompatível bloqueia reuso, sem
apagar resultados. Não há próximo treinamento automático após este diagnóstico.
