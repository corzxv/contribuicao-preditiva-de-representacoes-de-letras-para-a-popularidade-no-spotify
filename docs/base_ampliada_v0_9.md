# Base ampliada e curvas de aprendizagem V0.9

Revisão exploratória no desenvolvimento original, sem nova avaliação independente e sem abrir alvos do holdout. Não altera o demonstrador, os splits, os modelos ou os resultados anteriores.

## Execução no Windows

No PowerShell, na pasta do projeto, usando o ambiente existente:

```powershell
.\.venv\Scripts\python.exe -m tcc_music_popularity.training_expansion_v090 prepare
.\.venv\Scripts\python.exe -m tcc_music_popularity.training_expansion_v090 benchmark
.\.venv\Scripts\python.exe -m tcc_music_popularity.training_expansion_v090 run
.\.venv\Scripts\python.exe -m tcc_music_popularity.training_expansion_v090 verify
.\.venv\Scripts\python.exe -m tcc_music_popularity.training_expansion_delivery_v090
```

`prepare` e `benchmark` recusam sobrescrever suas execuções seladas. Não repetir esses comandos se já concluídos. `run` retoma checkpoints completos e compatíveis; recusa modelos parciais, código/protocolo alterado ou entradas divergentes. `verify` reconstrói as partições e reproduz as previsões dos modelos persistidos. Não remover selos para forçar uma retomada.

O último comando ajusta somente a apresentação dos gráficos a partir do CSV agregado já calculado: rótulos de eixo sem sobreposição e legenda em português. Confere o hash do CSV antes/depois e não ajusta modelos, não recalcula métricas e não altera o código científico selado. Se repetir `verify`, repita essa etapa de apresentação.

## Desenho

- Alvos lidos somente após filtro para `development_train`.
- Matriz por faixa com o alvo da própria faixa; visão experimental com um representante por composição operacional, usando a regra target-free V0.4.
- 23 inputs Baseline e 196 descritores LFM2b adicionais. Letra integral e embedding não são critérios de inclusão.
- Validações externas V0.5/V0.8 mantidas exatamente. Excluir artistas, composições, grupos operacionais e hashes conhecidos da validação e do holdout de todo treino.
- Dois Elastic Net com configurações finais V0.5 fixas. Transformações e coeficientes reaprendidos somente em cada treino; PCA90 exclusivamente no bloco LFM2b.
- Subconjuntos aninhados de grupos inteiros, duas sementes predefinidas e máximo único. Referência comum original reajustada com a mesma configuração; não equivale à OOF com tuning por fold da V0.5.
- Todas as previsões brutas, sem clipping, calibração, seleção de sementes ou exclusão pelo erro.

## Artefatos e privacidade

Relatórios, CSVs agregados e gráficos ficam em `reports`, identificados por `v0_9`. Matrizes, planos com identificadores, hashes de letras já existentes, modelos e previsões individuais ficam exclusivamente em `data/derived/private_training_expansion_v0_9`, ignorado pelo Git.

O protocolo é `reports/protocolo_ampliacao_treino_v0_9.md`. O dicionário e a proveniência estão em `reports/base_analitica_ampliada_v0_9.md`. O relatório do experimento é `reports/experimento_ampliacao_v0_9.md`, acompanhado de `reports/run_summary_ampliacao_v0_9.json`.

Ausência de hash não comprova texto diferente. Year é o ano informado pela fonte, não ano original de lançamento certificado. Chaves e flags são operacionais; diferenças de versão continuam possíveis. Melhora na validação comum, condicionada à disponibilidade de letras, não demonstra generalização para toda a base ampliada. Não interpretar associações como causas.

## Verificação sintética

Use um diretório temporário novo, sem apagar os diretórios de testes anteriores:

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_training_expansion_v090.py tests/test_statistical_revision_v080.py -p no:cacheprovider --basetemp=.tmp/pytest_v090_novo
.\.venv\Scripts\python.exe -m ruff check src/tcc_music_popularity/training_expansion_v090.py src/tcc_music_popularity/training_expansion_report_v090.py tests/test_training_expansion_v090.py
.\.venv\Scripts\python.exe -m ruff format --check src/tcc_music_popularity/training_expansion_v090.py src/tcc_music_popularity/training_expansion_report_v090.py tests/test_training_expansion_v090.py
```

Comandos efetivamente executados, códigos de saída, contagens e preservação são registrados no run summary da entrega. Nenhum commit ou push faz parte desta execução.

## Resultado da execução concluída

Foram preparados 83.817 tracks e 83.559 representantes; executados 140 ajustes completos (mais dois de benchmark), sem warnings. Os 140 modelos recarregados reproduziram 28 vetores OOF com diferença máxima zero. Os 372 hashes anteriores e os metadados de 18.349 arquivos de dados permaneceram idênticos.

O máximo ampliado reduziu erros >20 de 279 para 236 no Baseline e de 274 para 221 no Tradicional. Frente ao treino comum original, MAE aumentou 1,08% no Baseline e ficou praticamente estável no Tradicional (−0,073%). Comparados sobre o mesmo treino máximo, o Tradicional reduziu MAE em 1,64% frente ao Baseline. O relatório científico documenta as curvas completas, os limites e as previsões extremas dos treinos pequenos, que não foram removidas.

| Comando executado | Código | Resultado |
| --- | --- | --- |
| `.\.venv\Scripts\python.exe -m tcc_music_popularity.training_expansion_v090 prepare` | 0 | Base/partições/selo |
| `.\.venv\Scripts\python.exe -m tcc_music_popularity.training_expansion_v090 benchmark` | 0 | Dois ajustes técnicos |
| `.\.venv\Scripts\python.exe -m tcc_music_popularity.training_expansion_v090 run` | 0 | 140 ajustes |
| `.\.venv\Scripts\python.exe -m tcc_music_popularity.training_expansion_v090 verify` | 0 | Previsões, alinhamento, grupos e preservação |
| `.\.venv\Scripts\python.exe -m tcc_music_popularity.training_expansion_delivery_v090` | 0 | Apresentação dos quatro gráficos |
| `.\.venv\Scripts\python.exe -m pytest tests/test_training_expansion_v090.py tests/test_statistical_revision_v080.py tests/test_final_study_v040.py -p no:cacheprovider --basetemp=.tmp/pytest_v090_d` | 0 | 50 passed in 7.74s |
| `.\.venv\Scripts\python.exe -m ruff check src/tcc_music_popularity/training_expansion_v090.py src/tcc_music_popularity/training_expansion_report_v090.py src/tcc_music_popularity/training_expansion_delivery_v090.py tests/test_training_expansion_v090.py` | 0 | All checks passed |
| `.\.venv\Scripts\python.exe -m ruff format --check src/tcc_music_popularity/training_expansion_v090.py src/tcc_music_popularity/training_expansion_report_v090.py src/tcc_music_popularity/training_expansion_delivery_v090.py tests/test_training_expansion_v090.py` | 0 | 4 files already formatted |
| `.\.venv\Scripts\python.exe -m ruff check .` | 1 | B018 preexistente em `exp_base.py:8`, preservado |
| `git diff --check` | 0 | Sem erro de whitespace |

Todos os testes acima usam dados sintéticos; não foram executados testes antigos que abrissem bases reais fora do escopo. Os quatro gráficos finais foram inspecionados visualmente. A revisão de eixos está isolada do código científico selado e preservou o hash do CSV de métricas.
