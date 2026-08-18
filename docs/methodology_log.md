# Registro metodológico — Base v0.1

## Escopo científico

A etapa constrói dados para análise posterior de associação e contribuição preditiva incremental. Não estima efeitos causais e não treina modelos.

## Transformações observadas

| Etapa | Antes | Depois | Regra | Exceções/destino |
| --- | ---: | ---: | --- | --- |
| Spotify: ingestão | 1.159.764 linhas, 20 colunas | 1.159.764 linhas, 61 colunas | coluna de índice sem nome removida apenas da camada normalizada; `popularity` → `spotify_popularity`; originais preservados | 0 linhas removidas; flags em `data/rejected/spotify_quality_exceptions.csv` |
| Spotify: normalização | 1.159.764 | 1.159.764 | Unicode NFC, casefold, variante sem diacríticos, artista principal, título-base e tags de versão | 15 artistas e 1 título ausente preservados; 145 chaves operacionais nulas |
| LFM2b: JSONL gzip | 582.759 linhas lidas | 582.759 registros Parquet | leitura incremental em 24 lotes; flatten determinístico e `union_by_name` | 0 JSON inválido; arquivo de exceções criado em `data/rejected` |
| LFM2b: datas | 573.829 ISO + 8.930 `$numberLong` | 582.759 anos derivados | ISO ou epoch em milissegundos, preservando ambos os campos originais | 127 anos <1850 sinalizados; nenhum excluído |
| Matching | 1.159.764 Spotify + 582.759 LFM2b | 111.758 pares aceitos | raw, estrito, conservador e título-base com versão compatível; apenas pares únicos | 12.135 pares ambíguos, 3.457 fuzzy pendentes, 1.036.804 Spotify sem candidato |

## Normalização v0.1.0

Informações entre parênteses/colchetes só são removidas do título-base se classificadas como remaster, remix, live, acoustic, radio edit, mono/stereo, instrumental ou demo. O título e artista originais permanecem em `*_raw`. A chave de composição é operacional e não substitui ISRC nem outro identificador universal.

## Matching v0.1.0

Ordem: igualdade bruta; normalização estrita; normalização conservadora; chave de composição/título-base com compatibilidade de versões; geração fuzzy dentro do mesmo artista conservador. Um par é aceito somente se a relação determinística for um-para-um e as tags de versão forem compatíveis. Fuzzy nunca é aceito automaticamente.

## Viés de seleção

Matched significa status aceito (`accepted_high_confidence` ou `accepted_with_rules`). A comparação com os demais registros mede cobertura: média de `spotify_popularity` 27,1641 versus 17,4467; mediana 26 versus 14; zeros 0,6997% versus 15,0389%. Essas diferenças não demonstram que descritores de letras expliquem popularidade.

