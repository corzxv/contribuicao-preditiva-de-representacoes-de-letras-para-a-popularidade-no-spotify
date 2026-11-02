# Auditoria do catálogo Spotify anterior ao matching

Preparação de 31/10/2026. A base real **não foi processada nesta etapa**: somente
o cabeçalho e o tamanho do CSV foram inspecionados. O processamento será executado
pelo pesquisador no PowerShell. Não há seleção de amostra nem alteração de splits.

## Fonte localizada e grau de confirmação

| Questão | Evidência local / conclusão |
| --- | --- |
| Entrada original | `data/raw/spotify/spotify_data.csv`, configurado em `configs/data_sources.example.yaml`; presente, 175.822.041 bytes. |
| Arquivo compactado | `data/raw/spotify/spotify-1million-tracks.zip`, presente; não reaberto nesta etapa. |
| Origem documentada | [Kaggle: amitanshjoshi/spotify-1million-tracks](https://www.kaggle.com/datasets/amitanshjoshi/spotify-1million-tracks). Registro local em `docs/provenance.md` e `data/raw/manifest.json`; sem nova verificação da página remota. |
| Contagem anterior | README e `reports/tables/spotify_audit.json` registram **1.159.764** linhas e IDs distintos; a auditoria anterior leu a camada normalizada. Não é uma recontagem atual do CSV. O manifesto está com `record_count: null`. Não assumir 1,6 milhão. |
| Versão | Número de versão Kaggle: **não confirmado**. `docs/provenance.md` registra última atualização informada pela API em `2023-06-21T12:27:55.677Z`; não confundir com data da popularidade. |
| Identidade histórica | SHA-256 documentado `42fff9e85d1b26c3653b4668959d1be395fab8956848f0478bf28f726b3d5897`. Será recalculado na execução, não nesta preparação. |
| Download | **Não confirmado**. Proveniência diz aquisição em 18/08/2026 UTC; manifesto registra `obtained_or_verified_at: 2026-08-18T01:54:30.425097+00:00` e `reused_existing_configured_file`, que comprovam verificação/reutilização, não download nessa data. Data de modificação do arquivo também não comprova aquisição. |
| Licença | Texto documentado: “Database: Open Database; Contents: © Original Authors”. Não foi reconfirmado remotamente nem convertido em licença mais específica. |
| Data da popularidade | **Não confirmado**; não há timestamp correspondente no cabeçalho. |
| Significado de `year` | **Não confirmado**; não assumir ano original de lançamento. É o único campo temporal identificado no cabeçalho original. |

O código de aquisição (`acquisition.py`) extrai os bytes do CSV do ZIP, sem
reescrever os campos. Isso descreve o procedimento implementado, não prova que o
arquivo histórico nunca sofreu alterações. A nova execução compara seu hash com
o registro local. Transformações anteriores ao arquivo distribuído: não confirmado.

O normalizador (`spotify.py`) produz arquivos separados: remove índice, converte
tipos, cria `spotify_row_id`, renomeia `popularity` para `spotify_popularity`, deriva
coortes, chaves textuais e flags de qualidade/versão. Há conversões de campos na
camada derivada anterior; **este novo auditor lê o CSV bruto e preserva os valores
originais em sua tabela textual**, acrescentando campos analíticos temporários.
Não utiliza `spotify_lfm_matches.parquet` nem a base integrada de 111.758 registros.

## Execução

Execute o comando abaixo. A pasta de saída não pode existir; numa repetição,
troque seu nome. Os caminhos absolutos permitem executar de qualquer diretório,
usando o ambiente existente do projeto (não instala dependências).

```powershell
& "C:\Users\Concursos Felipe\Documents\UnB\TCC\.venv\Scripts\python.exe" "C:\Users\Concursos Felipe\Documents\UnB\TCC\scripts\11_auditar_catalogo_spotify.py" --input "C:\Users\Concursos Felipe\Documents\UnB\TCC\data\raw\spotify\spotify_data.csv" --output "C:\Users\Concursos Felipe\Documents\UnB\TCC\reports\auditoria_catalogo_spotify_20261031"
```

CLI offline: Python, DuckDB, PyYAML e Matplotlib já declarados no projeto. DuckDB
usa armazenamento temporário dentro da pasta de saída, buffer configurado em 1 GB
e duas threads; esse limite não é um teto para toda a memória do processo. As
tabelas ficam em disco e as análises usam views/projeções; somente agregados vão
para objetos Python e relatórios. É necessário espaço para o banco temporário e
spill; eles são removidos ao encerrar normalmente ou por exceção tratada. Uma
interrupção forçada do sistema pode deixar a subpasta `.catalog_audit_*`, que não
é relatório compartilhável e pode conter registros temporários.

Nenhuma conexão externa, leitura do LRCLIB, letra, embedding, treinamento,
alteração da interface, monografia, commit ou push faz parte do script.

## O que cada seção responde

| Seção | Pergunta e leitura |
| --- | --- |
| Estrutura | Quantas linhas/colunas existem? Quais tipos lógicos são inferidos e quais campos faltam? CSV não tem tipos físicos: as colunas são preservadas como VARCHAR e os tipos numéricos são inferidos sobre todos os valores não ausentes. |
| Identidade e duplicação | Quantos IDs distintos, ausentes, repetidos iguais ou conflitantes? Duplicatas exatas incluem o índice; igualdade substantiva desconsidera apenas cabeçalho vazio, `index` e `unnamed:*`. “Excess rows” conta repetições além da primeira; “involved rows” inclui todas as linhas envolvidas. Conflitos por campo são sobrepostos. |
| Popularidade | Qual a distribuição do snapshot? Válidos são inteiros finitos 0–100; ausentes e inválidos são contados separadamente. Quantis contínuos/interpolação linear; desvio-padrão amostral, n−1. Os dez intervalos aparecem mesmo com frequência zero. Limiares ≥60/70/80/90 se sobrepõem. |
| Tempo | Quais anos/datas estão presentes e válidos? Detecção por nomes `year`, `date`, `timestamp` e sufixo `_at`. Parser estrito ISO YYYY, YYYY-MM ou YYYY-MM-DD; outros formatos são inválidos/não suportados. Regra local de plausibilidade: 1900–2030, registrada no JSON. Valores parciais são ancorados em dia/mês 1 somente para cálculo; contagens de precisão impedem interpretá-los como datas exatas. Décadas e cruzamentos usam `year`. |
| Gêneros e artistas | Frequências, popularidade por gênero, distribuição do número de faixas por string de artista e concentração top 1/10/100/1000. Células de gênero não são divididas; delimitadores e IDs com gêneros diferentes são contados para revisão. Nomes de artistas não são publicados. |
| Versões | Heurísticas explícitas de palavras no título para live, remaster, remix, acoustic, demo, radio edit, instrumental, mono/stereo, extended e karaoke. Não são rótulos validados, podem se sobrepor e não excluem versões. O cabeçalho original não contém flags nativas de versão. |
| Acústica | Ausências, falhas de parse/não finitos, violações dos domínios locais e quantis. JSON/CSV trazem resumos dos valores válidos e de todos os finitos, inclusive fora do domínio. `loudness` não recebe limite inventado. Duração é `duration_ms`, em milissegundos. |
| Planejamento | Quantas células de período × gênero e período × gênero × popularidade existem e qual seu tamanho? Células vazias são o complemento do produto cartesiano das categorias marginais observadas. Limiares <5/<20 são diagnósticos de esparsidade, não garantia de poder/tamanho suficiente. |

## Regras, denominadores e exceções

- Originais são preservados; campos temporários derivados recebem prefixo
  `audit_`. Nomes de cabeçalho são mapeados para minúsculas sem espaços externos,
  com o nome original registrado no JSON. Cabeçalhos duplicados ou prefixo
  reservado causam erro útil, assim como ausência das seis colunas essenciais.
- Ausências analíticas: NULL ou, após trim, `""`, `NA`, `N/A`, `null`, `None`, com
  diferenciação de maiúsculas. `NaN` em campo numérico é inválido/não finito. As
  comparações de registros usam valores textuais originais; diferenças somente
  na grafia dos valores também podem sinalizar conflito.
- `linha`: todas as observações. `track_id_sem_conflito`: uma observação por ID
  aparado com um único registro substantivo distinto. Não são escolhidos
  representantes de IDs conflitantes; nem ausências nem conflitos desaparecem
  da base por linha. `track_id` isolado é usado no CSV para contagens de IDs com
  conflito por campo.
- O subconjunto por ID sem conflito é uma descrição provisória, **não uma regra
  definitiva de elegibilidade**. O JSON registra quantos IDs/linhas ficaram fora.
  Proposta pendente: investigar origem dos conflitos e aprovar regra independente
  da popularidade antes de construir a moldura. Não eleger o maior alvo.
- Sem arquivos de rejeitados: valores/linhas continuam na entrada e nas contagens
  aplicáveis; exclusões de estatísticas válidas são explicitadas. Nenhum registro,
  `track_id`, título, nome de artista ou letra é publicado individualmente.
- Artistas e pares artista+título são strings aparadas, sem desambiguar homônimos,
  aliases ou colaborações. Não são contagens de pessoas nem composições verdadeiras.
  Faixa, gravação e composição operacional não são intercambiáveis.
- `spotify_popularity` é o nome conceitual de `popularity` nesta fonte. Não é
  combinado com `genius_lyrics_views` ou `lfm_playcount`.

## Saídas e decisões pendentes

Na pasta nova serão gravados:

1. `auditoria_catalogo_spotify.md`: leitura humana, tabelas, limitações e proposta.
2. `resumo_catalogo_spotify.json`: resultados completos, entrada/hash/tamanho,
   hashes do código/configuração, Git HEAD como informação complementar,
   versão do auditor, comando em vetor de argumentos, duração, alertas e status.
3. `distribuicoes_catalogo_spotify.csv`: formato longo; cada linha identifica
   `scope`, `section`, até três pares `dimension_N`/`value_N`, `metric`, `value`
   e `denominator`. `fraction` é 0–1; `denominator` é a população da distribuição,
   não necessariamente o `n_valid` dos momentos. Vazios não são zeros. Nos
   cruzamentos só há células observadas; no histograma univariado os dez
   intervalos de popularidade incluem zeros explícitos.
4. Seis PNGs: `popularidade`, `ano`, `genero`, `concentracao_artista`, `versoes`
   e `popularidade_periodo`. Base indicada no título; usam IDs sem conflito ou,
   se nenhum existir, linhas com alerta. Gráfico de gênero mostra os 20 maiores;
   tabelas incluem todos. Barras de popularidade por período mostram mediana e
   segmento P25–P75, não intervalo de confiança.

Só interpretar uma execução com `status: completed` e `completed: true`. Erros ou
Ctrl+C, após iniciar a pasta, deixam status incompleto no JSON; mensagens de
parser contendo registros não são copiadas para os relatórios. Se o processo
for encerrado à força, o último checkpoint permanece incompleto.

Ainda decidir: significado e origem de `year`, data do snapshot de popularidade,
versão upstream/data efetiva de aquisição; regra de conflitos; tratamento de
gêneros múltiplos/ausentes; limites dos períodos; tamanho da amostra e eventual
sobreamostragem com probabilidades/pesos. A proposta inicial é sorteio aleatório
estratificado sem reposição, proporcional por período e gênero; popularidade só
se a esparsidade permitir. Não há cotas iguais automáticas, busca de seed,
PCA/k-means para selecionar músicas ou garantia via margem de erro de proporção.

Separar sorteio do catálogo, disponibilidade/aceitação de letras e splits
posteriores. LFM2b não condiciona elegibilidade; cobertura LRCLIB anterior não é
extrapolada. `reports/run_summary_final_holdout_v0_6.json` registra abertura em
`2026-10-14T16:12:27.567600+00:00`. Um novo sorteio não restaura independência;
será preciso reconciliar registros e grupos já usados, agrupando por artista e
chave operacional de composição. Nenhum split é lido ou modificado pelo auditor.

## Verificação limitada

Fixture sintética de 15 linhas em `tests/fixtures/spotify_catalog_audit.csv`, com
duplicatas exatas, repetição só de índice, conflitos de popularidade/gênero,
ID/artista/ano ausentes, datas impossíveis, NaN/texto/valores fora do domínio e
diversos marcadores de versão. Os testes exercitam a CLI, denominadores, quantis,
conflitos, cruzamentos, preservação da entrada, saída agregada, recusa de
sobrescrita e status incompleto. Há ainda minifixtures para esquema incompatível
e ausência total de IDs sem conflito. Não se roda a suíte completa.

```powershell
& ".venv\Scripts\python.exe" -m pytest "tests/test_catalog_audit.py" -q -p no:cacheprovider --basetemp ".tmp/pytest_catalog_audit"
& ".venv\Scripts\python.exe" -m ruff check "src/tcc_music_popularity/catalog_audit.py" "scripts/11_auditar_catalogo_spotify.py" "tests/test_catalog_audit.py"
& ".venv\Scripts\python.exe" -m ruff format --check "src/tcc_music_popularity/catalog_audit.py" "scripts/11_auditar_catalogo_spotify.py" "tests/test_catalog_audit.py"
```

Após executar a base real, envie ao ChatGPT o Markdown, o JSON, o CSV longo e,
se possível, os seis PNGs. Não envie o CSV bruto nem a pasta temporária.
