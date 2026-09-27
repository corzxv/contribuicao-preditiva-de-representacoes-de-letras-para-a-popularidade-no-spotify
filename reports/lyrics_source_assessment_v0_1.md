# Avaliação da fonte de letras — Piloto v0.1

Data de acesso documental: 2026-09-04.

## Fonte e acesso

- Fonte exclusiva: LRCLIB (`https://lrclib.net`).
- Documentação oficial: `https://lrclib.net/docs`.
- Endpoints GET implementados: `/api/get` (consulta por metadados) e `/api/search` (busca estruturada por artista e faixa).
- Os GET documentados são públicos e não exigem chave de API.
- A documentação informa que `/api/search` retorna no máximo 20 resultados e não oferece paginação.
- User-Agent identificador: `UnB-TCC-MusicPopularity-LyricsPilot/0.1 (academic research; https://github.com/corzxv/tcc-popularidade-musical)`.
- O coletor aplica cache local, timeout, tentativas limitadas, backoff e intervalo mínimo entre requisições.

## Licenças e direitos

O repositório oficial do servidor LRCLIB (`https://github.com/tranxuanthang/lrclib`) licencia o **código da plataforma** sob MIT. Essa licença de software não confirma licença aberta para reprodução ou redistribuição do **conteúdo das letras**. Não foi localizada, na documentação oficial consultada, uma licença aberta inequívoca que autorize redistribuir em massa as letras retornadas.

Consequentemente, este piloto trata o texto como material privado de pesquisa: respostas brutas e textos permanecem somente em `data/raw/lyrics_private/`, caminho ignorado pelo Git; nenhum trecho é gravado em relatórios, testes, logs, CSVs ou Parquets processados. Artefatos processados expõem apenas metadados técnicos, contagens e SHA-256. A ampliação além do smoke test depende de nova avaliação técnica e jurídica.
