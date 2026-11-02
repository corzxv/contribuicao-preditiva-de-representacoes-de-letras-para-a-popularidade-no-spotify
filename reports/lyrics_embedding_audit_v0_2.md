# Piloto de embeddings das letras — auditoria v0.2

## Escopo

Foram processadas exclusivamente 1441 composições aceitas do `development_train`. Nenhuma variável de popularidade, métrica Genius/LFM, observação de holdout ou texto foi fornecida aos relatórios públicos. Não houve fine-tuning ou treinamento preditivo.

## Encoder e protocolo

- Modelo: `sentence-transformers/all-MiniLM-L6-v2`.
- Revision imutável: `1110a243fdf4706b3f48f1d95db1a4f5529b4d41`.
- Tokenizer: `BertTokenizerFast`.
- Dispositivo/dtype: `cpu` / `float32`.
- Limite: 256 tokens incluindo 2 especiais; capacidade de conteúdo 254.
- Overlap: 32 tokens de conteúdo.

Para chunks normalizados $z_j$, intervalo $[s_j,e_j)$ e fim anterior $e_{j-1}$, o peso é $w_1=e_1-s_1$ e $w_j=e_j-e_{j-1}$. O vetor da música é $v=\operatorname{L2}(\sum_j w_j z_j / \sum_j w_j)$. Assim, tokens de overlap não recebem peso duplicado.

## Auditoria agregada dos textos

- Hashes estritos únicos: 1441.
- Composições adicionais em hashes duplicados: 0.
- Letras vazias: 0.
- Muito curtas (< 20 tokens): 1.
- Acima de um chunk: 773.
- Caracteres: `{"maximum": 5871.0, "mean": 1218.929216, "median": 1102.0, "minimum": 74.0, "n": 1441, "q1": 759.0, "q3": 1489.0, "std": 690.893482}`.
- Linhas: `{"maximum": 158.0, "mean": 43.62526, "median": 40.0, "minimum": 1.0, "n": 1441, "q1": 28.0, "q3": 54.0, "std": 21.897578}`.
- Tokens: `{"maximum": 1713.0, "mean": 306.541291, "median": 269.0, "minimum": 16.0, "n": 1441, "q1": 181.0, "q3": 369.0, "std": 192.117614}`.
- Chunks: `{"maximum": 8.0, "mean": 1.747398, "median": 2.0, "minimum": 1.0, "n": 1441, "q1": 1.0, "q3": 2.0, "std": 0.905252}`.

## Idioma

- Status: `{"english": 1421, "non_english": 20, "uncertain": 0}`.
- Idiomas detectados: `{"af": 1, "cy": 1, "de": 1, "en": 1421, "es": 2, "fi": 1, "id": 1, "ja": 2, "ko": 7, "la": 2, "sv": 1, "sw": 1}`.
- Confiança: `{"maximum": 1.0, "mean": 0.999999, "median": 1.0, "minimum": 0.9993601784413697, "n": 1441, "q1": 1.0, "q3": 1.0, "std": 1.8e-05}`.
- Detector: `langid 1.1.6` com probabilidade normalizada e limiar 0.8.

Nenhuma letra foi excluída por idioma.

## Validação numérica

- Forma: 1441 × 384.
- Dtype: `float32`.
- NaN/infinito: 0/0.
- Normas L2: `{"maximum": 1.0, "mean": 1.0, "median": 1.0, "minimum": 0.9999999403953552, "n": 1441, "q1": 1.0, "q3": 1.0, "std": 0.0}`.
- Maior desvio de norma: 5.960464477539063e-08.
- Dimensões constantes/quase constantes: 2/3.
- Reexecução determinística: maior diferença absoluta 0.0.
- Cobertura integral sem truncamento: True.

## Similaridade

`{"excessive_difference_threshold": 0.0, "excessive_similarity_threshold": 0.95, "excessively_different_pairs": 25, "excessively_similar_pairs": 0, "maximum": 0.7507521352918074, "mean": 0.33153, "median": 0.333305, "minimum": -0.06349408405003326, "n": 10000, "q1": 0.241111, "q3": 0.425557, "sample_size": 10000, "seed": 20261007, "std": 0.129011}`

Diagnóstico de colapso: `nenhum sinal agregado de colapso`.

## Privacidade e limites

Os artefatos públicos contêm apenas estatísticas agregadas. A análise é descritiva e não causal. A disponibilidade e o idioma das letras limitam a população para a qual análises futuras poderão generalizar.

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
