# PCA exploratória dos embeddings de letras — v0.2

Esta PCA é exclusivamente exploratória, usa somente as 1441 composições aceitas de `development_train`, centraliza os embeddings e não padroniza cada dimensão separadamente. Popularidade não participou do ajuste. Componentes não são interpretados causalmente e a transformação não foi salva como etapa definitiva.

## Resumo

- Componentes para 80%: 112.
- Componentes para 90%: 168.
- Componentes para 95%: 215.
- Effective rank: 148.420884.
- Comparação por hashes únicos: idêntica, pois não foram observados hashes duplicados.

## Primeiros componentes

| componente | variancia | acumulada |
| --- | --- | --- |
| 1 | 0.070244673 | 0.070244673 |
| 2 | 0.048372662 | 0.118617336 |
| 3 | 0.031131033 | 0.149748368 |
| 4 | 0.029429005 | 0.179177373 |
| 5 | 0.022204403 | 0.201381777 |
| 6 | 0.019223842 | 0.220605619 |
| 7 | 0.018667217 | 0.239272836 |
| 8 | 0.014853229 | 0.254126065 |
| 9 | 0.014431784 | 0.268557849 |
| 10 | 0.013133343 | 0.281691192 |
| 11 | 0.012822406 | 0.294513598 |
| 12 | 0.012422411 | 0.306936009 |
| 13 | 0.011554259 | 0.318490268 |
| 14 | 0.011517022 | 0.33000729 |
| 15 | 0.011249778 | 0.341257068 |
| 16 | 0.011051768 | 0.352308836 |
| 17 | 0.010365962 | 0.362674797 |
| 18 | 0.009971498 | 0.372646296 |
| 19 | 0.009770814 | 0.38241711 |
| 20 | 0.009407484 | 0.391824594 |

## Regra para modelagem futura

A PCA definitiva dos modelos será ajustada somente dentro dos dados de treinamento de cada split/fold, nunca utilizando validação ou teste.

Esta exploração não substitui a análise sugerida pelo orientador para a modelagem final e não demonstra capacidade preditiva.

## Validação final

| command | exit_code | result |
| --- | --- | --- |
| [fase A] pytest completo | 0 | 58 passed antes do checkpoint v0.1.3 |
| [fase A] pytest tests/test_lyrics_pilot_v013.py | 0 | 8 passed |
| [fase A] ruff check src tests + format + git diff --check | 0 | aprovados |
| [fase A] hashes, privacidade, 2.000 resultados/caches e holdout | 0 | preservados; privado tracked/staged 0; holdout 0 |
| [fase B] pytest completo | 0 | 68 passed |
| [fase B] pytest tests/test_lyrics_embeddings_v020.py | 0 | 10 passed |
| python -m ruff check src tests | 0 | All checks passed |
| python -m ruff format --check . | 0 | 60 files already formatted |
| git diff --check | 0 | sem erros; somente avisos LF/CRLF |
| reexecução idempotente real | 0 | Parquets e resumo mantiveram mtime e SHA-256 |
| auditoria de 1.441x384, dtype, NaN/inf, target, holdout e vazamento | 0 | todas as verificações aprovadas |
| git status + tracked/staged privado + HEAD/tag/origin | 0 | privado 0; HEAD=tag=origin/master=812ba35; sem commit/push pós-embeddings |
| python -m ruff check . | 1 | único B018 preexistente em exp_base.py:8; fora do escopo e não staged |
