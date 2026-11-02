# Protocolo de busca local LRCLIB — amostra Spotify 200k

Preparado para execução manual. Nenhuma cobertura ou duração da busca das
200.000 faixas é afirmada antes da execução. Não há rede, APIs, tradução,
embeddings, descritores textuais, splits, modelos ou alteração da interface.

## Entradas e evidências inspecionadas

- Amostra e selo: `reports/amostra_spotify_200k_20261031/`, com Parquet,
  `resumo_amostra_200k.json` e `alocacao_amostra_200k.csv`.
- Dump: `D:\TCC_LRCLIB\lrclib-db-dump-20261012T090639Z.sqlite3`,
  261.755.867.136 bytes. Checkpoint `dump_progress.json` pronto, CRC verificado,
  `sqlite_quick_check: ok`, hash local registrado
  `e8682b6f1807ca0671e6ae8206dd60f0363f70ca67d352a4ddecbe896500c0d3`.
  Esse hash é o calculado na preparação anterior, não assinatura independente
  do publicador nem novo hash completo calculado a cada retomada.
- Índice existente: `D:\TCC_LRCLIB\tcc_lookup_v1\lookup.sqlite`.
- Manifesto anterior: `data/derived/private_local_lyrics_v1/state.sqlite`.
- Implementações reutilizadas: `local_lyrics.py` (scripts 06/07), normalização,
  diagnósticos e fingerprint estrito existentes; comparação da amostra em
  `catalog_sampling.py`; detector offline existente em `lyrics_embeddings_v020.py`
  (somente função de idioma, sem executar embeddings).

Na preparação foram inspecionados arquivos de código/documentação, metadados
SQLite do índice/checkpoint, o progresso salvo e o footer/schema do Parquet.
O footer registra 200.000 linhas; unicidade e hashes serão conferidos pela CLI.
Não houve busca de faixas reais, nova indexação ou leitura de letras reais.

## Por que 33.714.178 percorridos e 12.757.266 indexados

O código `build_index` percorre a tabela `tracks` em lotes de 5.000 IDs,
guardando apenas registros cujo artista normalizado pertence ao conjunto de
artistas das consultas do manifesto antigo. Os números constam do progresso
concluído em 28/10/2026. A diferença de 20.956.912 registros corresponde aos
metadados não retidos por esse filtro; não é evidência de erro ou de ausência de
letras. O contador não mede aceitações.

O índice contém ID LRCLIB, artista/título originais, chaves normalizadas de
artista/título/título-base, álbum, duração e `last_lyrics_id`. Não filtra idioma,
presença de texto, gênero ou popularidade. Não restringe títulos aos antigos:
permite qualquer faixa **dos artistas cobertos**. Porém esse conjunto provém do
manifesto anterior, associado ao universo antigo, e não garante cobrir todos os
artistas da nova amostra. LFM2b não participa da nova elegibilidade.

A CLI reconstrói o conjunto de artistas do checkpoint antigo, confere seu hash
com o selo do índice e verifica dump/código/progresso. Artistas da nova amostra
que faltarem formam um índice suplementar em
`D:\TCC_LRCLIB\tcc_lookup_sample_200k_v1\`. Reutiliza o mesmo construtor, com
uma única varredura de **metadados**, checkpoint transacional e retomada por ID;
não faz varredura do dump por música. O índice antigo e o dump não são escritos.
Após interrupção, a varredura suplementar continua do checkpoint.

Dump e índices completos são abertos em `mode=ro&immutable=1`, com
`PRAGMA query_only=ON`. Exige-se WAL ausente/vazio antes de leitura imutável dos
artefatos anteriores; se houver escritor ativo, parar e aguardar seu fechamento,
nunca apagar o WAL. Mudanças de tamanho/mtime/caminho/selo bloqueiam reutilização.
A validação não repete a leitura integral de 262 GB a cada invocação.

## Amostra, consultas e aceitação

Antes de buscar, conferir SHA-256 do Parquet e da alocação contra o resumo,
200.000 IDs únicos, schema, alocação realizada, probabilidades/pesos e soma dos
pesos. A projeção entregue ao matcher contém somente ID, artista, título e
duração. ID só liga resultados; popularidade, gênero, estrato e peso não entram
na consulta, escolha ou aceite. Não há filtro por idioma/gênero, deduplicação de
faixas, escolha de versão mais popular nem reposição de faixas sem letra.

Consultas idênticas (mesmos metadados/flags/duração) podem compartilhar trabalho;
todas as faixas continuam na saída 1:1. Nenhuma chave de composição ou split é
criada. O título completo é preservado. A função antiga de título-base é usada
apenas para enumerar candidatos, junto das flags existentes, nunca para colapsar
as faixas ou pressupor que letra de estúdio serve para live/remix.

Regras herdadas: igualdade conservadora de artista e título ou título-base;
flags de versão compatíveis; diferença de duração ≤10 segundos quando ambas
as durações são conhecidas; somente `plain_lyrics` não vazio é elegível. Duração
Spotify ausente/não finita/não positiva é tratada como desconhecida, sem excluir
a faixa e sem transformar a busca em consulta só por artista. Artista/título
ausentes ou vazios após normalização produzem `insufficient_metadata`.

**Guarda adicional explícita desta adaptação:** se algum marcador de versão
existente estiver presente, exigir também igualdade do título completo
normalizado. Duas flags `live` iguais não identificam a mesma apresentação.
Essa guarda pode reduzir cobertura; não muda o índice nem cria classificador.
Não há fuzzy automático ou uso de fingerprint flexível.

Aceitar candidato elegível único, ou vários elegíveis quando **todos** têm
texto simples e o mesmo fingerprint estrito. O fingerprint herdado aplica NFC,
remove BOM, padroniza quebras de linha e espaços/tabs horizontais e remove
linhas vazias externas; mantém caixa, palavras, pontuação e linhas internas.
O texto armazenado é o original, sem essas transformações. Textos distintos,
payloads conflitantes do mesmo ID, versões incompatíveis e conjuntos incompletos
permanecem ambíguos. Ausência de texto em parte dos elegíveis impede afirmar
equivalência do conjunto.

Só depois de comprovar equivalência, escolher representante por menor diferença
de duração, maior completude de metadados e menor ID, usando o desempate antigo.
A lista de IDs equivalentes e a regra ficam na proveniência privada. Duração
nunca resolve textos diferentes. O ponteiro `tracks.last_lyrics_id` é conferido
contra `lyrics.track_id`; revisão inconsistente é erro técnico.

Limites herdados: até 500 candidatos, 2 milhões de caracteres por candidato,
8 milhões no conjunto e orçamento de consulta de 30 segundos, com handler
SQLite. Limite de conjunto/texto produz ambiguidade por incompletude; timeout
é erro técnico. I/O bloqueado no sistema pode ultrapassar o orçamento.

## Status mutuamente exclusivos por faixa

| Status | Significado |
| --- | --- |
| `accepted` | Texto simples aceito automaticamente pelo protocolo; não validação humana individual. |
| `ambiguous` | Textos/identidade/versão conflitantes ou incompletude que impede decisão. |
| `not_found` | Nenhum candidato no conjunto de metadados normalizados desse snapshot. |
| `no_text` | Há candidato compatível, mas nenhum texto simples elegível; sincronização pode estar disponível. |
| `instrumental` | Todos os candidatos compatíveis indicam instrumental e não contêm texto; evidência da fonte, nunca mera falta de letra. |
| `insufficient_metadata` | Artista/título insuficientes; nenhuma consulta ampla é feita. |
| `technical_error` | Falha de SQLite, SSD, referência, leitura ou orçamento; não é ausência de letra. |
| `pending` | Ainda não processado; só aparece em execução incompleta. |

Indicação instrumental em conflito com texto/outros elegíveis é ambiguidade.
O adaptador local existente não converte sincronização em texto simples; esta
etapa também não remove timestamps. `synced_lyrics` é preservado, quando há
letra aceita, e sua disponibilidade é registrada separadamente.

## Estado privado, proveniência e retomada

Workspace exclusivo: `data/derived/private_sample_lyrics_200k_v1/`. Usa SQLite,
lock de processo e commits por consulta, seguindo o padrão já existente. Guarda
consulta, candidatos/evidência, decisão, tentativas, duração e execução de origem.
Letras ficam na tabela privada `lyrics` e no Parquet privado; nenhum texto vai
para relatórios. Não importa status/caches antigos: o universo e a guarda de
versão não são idênticos. Reutiliza apenas consultas concluídas **deste workspace**
quando amostra, fonte, regras, idioma e configuração mantêm o mesmo selo.

Ctrl+C mantém transações concluídas. Queda do SSD registra erro técnico e para
o lote, sem classificar milhares de ausências falsas. Após reconectar, usar
`--retry-errors`; retentativas técnicas são explícitas e limitadas a três por
consulta. Erros esgotados continuam visíveis, nunca viram `not_found`. Consulta
interrompida antes do commit continua pendente. Não apagar locks/checkpoints.

O mesmo comando retoma pendências e pula concluídas. `--limit` permite lote
pequeno, depois da preparação do índice; `--report-only` recompõe agregados sem
buscar, mas ainda exige fontes disponíveis/compatíveis. `--status` só lê o
resumo público, que é um checkpoint e não prova que um processo segue ativo.
Resultados anteriores incompatíveis bloqueiam execução, sem sobrescrita.

## Comparação de cobertura e idioma

Apresentar amostra completa, aceitas, não aceitas e cada status sem/com pesos
originais. Taxas de status usam todas as faixas do grupo; taxas de candidato/texto
explicitam denominador conhecido e quantidade de desconhecidos. Não converter
erros/pendências em evidência de ausência. O gráfico mostra aceitas/total real
por categoria; popularidade separa 80–89 e 90–100, dentro das 499 faixas ≥80
registradas no desenho. Não aceitações incluem `no_text` e, em saída provisória,
pendências/erros.

Para cada variável numérica, usar apenas valores finitos e publicar contagem
real e soma de pesos válidos. Reutilizar quantis pela inversa da CDF ponderada e
desvio com divisor soma(w) do protocolo amostral. Resumir também ausências e
violações das regras locais acústicas, sem retirar faixas. Diferença padronizada:
(média aceita − média não aceita) / sqrt((variância aceita + variância não aceita)/2).
Se faltar grupo/valor válido ou o denominador for zero, não interpretar como
diferença zero; publicar vazio/não disponível. Diferenças de proporções são
aceitas menos não aceitas, nas distribuições de cada grupo. Sem p-valores,
recalibração ou sorteio adicional. Créditos distintos são contagens observadas;
concentração ponderada é resumo dos créditos observados, não estimativa de riqueza.

A taxa ponderada estima a cobertura do catálogo sob este protocolo/snapshot;
os pesos originais não corrigem automaticamente a seleção adicional por letras.
Sem letra e instrumental são situações diferentes. Idioma usa o `langid` 1.1.6
já instalado, sem instalação/download: detector existente com score normalizado,
limiar 0,80 e incerteza registrada. Score não é probabilidade calibrada. Falta
do detector/falha de idioma é `not_evaluated`, sem rejeitar letra. Idioma não é
inferido pelo gênero. Nenhum modelo de embeddings é carregado.

O teste V0.6 já foi aberto. Esta etapa não apaga exposição anterior nem cria
splits; agrupamento por artista/composição operacional e reconciliação com o
estudo anterior continuam pendentes.

## Produtos e interpretação

Públicos em `reports/busca_local_200k_20261031/`: este protocolo, relatório,
comparação CSV longa, resumo JSON e três PNGs (popularidade, gênero, período).
Só agregados: sem letras, trechos, tokens, IDs LRCLIB/Spotify ou hashes de texto.
Hashes públicos identificam arquivos de entrada/código/dump, nunca letras.
No CSV, `count`/`total` são somas de pesos no escopo ponderado; `n`/`n_observed`
são casos reais; `fraction`/`rate` estão em 0–1. O denominador numérico válido
está em `weight_observed`, além do denominador total do escopo.

Privados no workspace: `state.sqlite`, evidências e
`resultados_faixas_200k.parquet` (exatamente uma linha por faixa, campos originais,
desenho e resultado); `letras_aceitas_200k.parquet` (uma linha por consulta aceita,
texto original e proveniência). Vínculo por `lyrics_text_ref` → `query_id`,
sem multiplicar linhas da amostra. Validar hashes das letras e referências na
exportação. Arquivos sob `data/derived` são ignorados pelo Git e não devem ser
enviados junto dos relatórios.

O JSON diferencia consultas novas e reutilizadas, faixas consultadas, status,
índices e tempo acumulado de consultas (indexação/relatórios têm custo separado).
Somente `status: completed` / `completed: true` indica ausência de pendências e
erros técnicos. Não interpreta uma execução interrompida como cobertura final.
