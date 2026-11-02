# Executar busca local da amostra 200k

Implementação: `scripts/13_buscar_letras_amostra_200k.py`. Reutiliza indexação,
consulta SQLite e regras conservadoras existentes, com estado exclusivo para a
amostra. Leia `docs/protocolo_busca_local_200k.md` para as decisões de matching,
denominadores e limitações. O assistente não executou a busca real.

Os defaults são absolutos e correspondem aos caminhos confirmados neste projeto.
O comando pode ser executado de qualquer pasta. Mantenha o SSD conectado como
D:, reserve espaço livre nos dois volumes e não inicie dois trabalhadores sobre
o mesmo workspace. A indexação suplementar pode ser demorada: percorre uma vez
os metadados e registra progresso, sem ler letras durante a construção.

## Iniciar

```powershell
& "C:\Users\Concursos Felipe\Documents\UnB\TCC\.venv\Scripts\python.exe" "C:\Users\Concursos Felipe\Documents\UnB\TCC\scripts\13_buscar_letras_amostra_200k.py" --all
```

O comando valida a amostra contra os hashes do resumo, verifica o índice antigo,
constrói/retoma o suplemento se necessário, consulta as pendências e exporta
resultados privados e agregados. Não requer instalação, download nem novo
serviço. Não executa scripts de embeddings/modelos.

Entradas fixadas pelos defaults:

- `C:\Users\Concursos Felipe\Documents\UnB\TCC\reports\amostra_spotify_200k_20261031\amostra_spotify_200k.parquet`
- Resumo e alocação na mesma pasta.
- `D:\TCC_LRCLIB\lrclib-db-dump-20261012T090639Z.sqlite3`
- `D:\TCC_LRCLIB\tcc_lookup_v1\lookup.sqlite`
- `C:\Users\Concursos Felipe\Documents\UnB\TCC\data\derived\private_local_lyrics_v1\state.sqlite`

O `--help` lista opções de caminhos. Não usar os diretórios anteriores como
destinos e não mudar configurações no meio da execução.

## Retomar

Após Ctrl+C/interrupção, repetir o comando inicial. Ele reaproveita consultas
concluídas e retoma a indexação suplementar a partir do checkpoint.

Se houve erro técnico ou desconexão, reconecte o SSD no mesmo caminho, corrija
a causa e execute:

```powershell
& "C:\Users\Concursos Felipe\Documents\UnB\TCC\.venv\Scripts\python.exe" "C:\Users\Concursos Felipe\Documents\UnB\TCC\scripts\13_buscar_letras_amostra_200k.py" --all --retry-errors
```

Esse comando inclui pendências e erros técnicos com menos de três tentativas.
Uma falha interrompe o lote para não transformar problemas do SSD em ausências.
Se o mesmo erro persistir, não apagar o checkpoint; enviar resumo e mensagem do
terminal para revisão. Índice e resultados incompatíveis não são sobrescritos.

## Acompanhar ou gerar só relatórios

```powershell
& "C:\Users\Concursos Felipe\Documents\UnB\TCC\.venv\Scripts\python.exe" "C:\Users\Concursos Felipe\Documents\UnB\TCC\scripts\13_buscar_letras_amostra_200k.py" --status
```

O status é o último resumo publicado, não monitoramento contínuo de processo.
O terminal da execução mostra avanços da indexação e das consultas; checkpoints
da fase de consultas também ficam no `progress.json` privado, sem letras.
`--limit 50` limita consultas por invocação, não a indexação inicial.
`--report-only` recompõe resultados/agregados sem novas consultas, mantendo as
validações de entradas e fontes (SSD ainda necessário).

Códigos de saída: 0 = processamento completo sem pendências/erros técnicos;
2 = parcial/interrompido/erros ou lote limitado; 1 = falha de preparação/validação.
Ambiguidade, instrumental, ausência e metadados insuficientes são resultados
terminais válidos; não impedem, sozinhos, `completed: true`.

## Saídas privadas — não enviar nem versionar

Em `C:\Users\Concursos Felipe\Documents\UnB\TCC\data\derived\private_sample_lyrics_200k_v1\`:

- `state.sqlite` e eventuais arquivos WAL/SHM: consultas, vínculo de todas as
  faixas, decisões/evidências e textos privados, com commits por consulta.
- `resultados_faixas_200k.parquet`: uma linha por faixa, incluindo pendências se
  a execução estiver incompleta; todos os originais e pesos preservados.
- `letras_aceitas_200k.parquet`: uma linha por consulta aceita; texto-fonte,
  sincronização original quando existente e proveniência. Referência via
  `lyrics_text_ref`/`query_id`; não multiplica a amostra.
- `progress.json` e `execution.lock`: controle desta execução.

Índice suplementar separado:
`D:\TCC_LRCLIB\tcc_lookup_sample_200k_v1\lookup.sqlite`, com `progress.json`.
O dump e o índice anterior permanecem preservados.

## Saídas públicas — enviar para revisão

Em `C:\Users\Concursos Felipe\Documents\UnB\TCC\reports\busca_local_200k_20261031\`:

- `protocolo_busca_local_200k.md`
- `relatorio_busca_local_200k.md`
- `comparacao_cobertura_letras_200k.csv`
- `resumo_busca_local_200k.json`
- `cobertura_popularidade_200k.png`
- `cobertura_genero_200k.png`
- `cobertura_periodo_200k.png`

Envie esses sete arquivos. Se a execução falhar, envie o JSON incompleto e a
mensagem do terminal; não envie dump, caches, Parquets privados, letras ou
trechos. `owner.json` é apenas o selo de posse/compatibilidade da pasta pública.

## Verificação da preparação

Testes somente com SQLite, metadados e textos sintéticos, bloqueando conexões
de rede. Cobrem equivalência estrita, conflitos de texto/versão, instrumental,
sincronização sem texto simples, limites, falta de metadados, índice suplementar,
erro técnico, retomada, join 1:1, preservação de pesos e ausência de texto/IDs/
hashes de letras nos agregados. Não há execução das 200 mil faixas nesta etapa.

```powershell
& ".venv\Scripts\python.exe" -m pytest "tests/test_sample_lyrics.py" "tests/test_local_lyrics.py" -q -p no:cacheprovider --basetemp ".tmp/pytest_sample_lyrics_final"
& ".venv\Scripts\python.exe" -m ruff check "src/tcc_music_popularity/sample_lyrics.py" "scripts/13_buscar_letras_amostra_200k.py" "tests/test_sample_lyrics.py"
& ".venv\Scripts\python.exe" -m ruff format --check "src/tcc_music_popularity/sample_lyrics.py" "scripts/13_buscar_letras_amostra_200k.py" "tests/test_sample_lyrics.py"
```
