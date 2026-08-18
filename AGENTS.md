# Regras duráveis do projeto

## Objetivo científico

Avaliar associação e contribuição preditiva incremental de descritores de letras para estimar a popularidade Spotify observada no snapshot da fonte, em conjunto com descritores acústicos e metadados. Não fazer afirmações causais.

## Engenharia e dados

- Usar Python; não usar R.
- Preservar dados brutos imutáveis e nunca versionar bases brutas, derivados volumosos, letras ou credenciais.
- Toda normalização cria colunas novas e preserva campos originais.
- Documentar regras, quantidades antes/depois, exceções e destino de rejeitados.
- Separar sempre `spotify_popularity`, `genius_lyrics_views` e `lfm_playcount`.
- Atualizar dicionário de dados, decisões e proveniência quando o schema mudar.
- Não usar notebooks como única fonte da lógica; a pipeline deve ser reproduzível por CLI.
- Executar testes e lint antes de concluir alterações.
- Não fazer scraping massivo nem treinar modelos na Base v0.1.

## Modelagem futura

- Evitar leakage por artista, composição e versões da mesma faixa.
- Exigir splits agrupados por artista e por chave operacional de composição.
- Não tratar a chave normalizada como identificador universal.

