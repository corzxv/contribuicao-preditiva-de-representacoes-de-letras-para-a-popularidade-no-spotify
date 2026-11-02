# Executar a rodada de recuperação v2

Código preparado e testado com fixtures; recuperação real não executada pelo
assistente. Os caminhos padrão são absolutos. O comando não precisa ser iniciado
na pasta do projeto. Mantenha o SSD conectado em D: e espaço disponível em C: e D:.

## Iniciar

```powershell
& "C:\Users\Concursos Felipe\Documents\UnB\TCC\.venv\Scripts\python.exe" "C:\Users\Concursos Felipe\Documents\UnB\TCC\scripts\14_recuperar_letras_amostra_200k.py" --all
```

Ele valida a amostra e a busca anterior, copia decisões protegidas, diagnostica
perdas, reavalia o cache, constrói/retoma um índice auxiliar e faz uma rodada de
consultas restritas. Depois exporta resultados e comparações. Não altera v1,
amostra, dump, índices anteriores ou pesos. Não instala dependências nem baixa
modelos. O hash do estado v1 de aproximadamente 6,2 GB pode demorar na etapa 1;
não interpretar ausência temporária de linhas no terminal como travamento.

Entrada principal anterior:
`C:\Users\Concursos Felipe\Documents\UnB\TCC\data\derived\private_sample_lyrics_200k_v1\state.sqlite`.
Os demais caminhos confirmados estão no protocolo e nos defaults da CLI.

## Retomar

Após Ctrl+C ou fechamento do terminal, repita o comando inicial. Decisões já
concluídas e lotes de índice já gravados são reutilizados. Não apagar checkpoints.

Depois de erro técnico/desconexão, reconecte o SSD, corrija a causa e execute:

```powershell
& "C:\Users\Concursos Felipe\Documents\UnB\TCC\.venv\Scripts\python.exe" "C:\Users\Concursos Felipe\Documents\UnB\TCC\scripts\14_recuperar_letras_amostra_200k.py" --all --retry-errors
```

Retentativas limitadas a três por consulta técnica; não flexibilizam matching.
Não modificar código/protocolo/entradas durante a rodada, pois os selos impedem
reutilização incompatível. `--limit N` limita apenas consultas locais novas;
diagnóstico, cache e construção do índice podem ser executados integralmente.

## Acompanhar

O terminal imprime fase, contagens e checkpoints aproximadamente a cada dez
segundos nas etapas de importação, cache, índice e consultas. Em outra janela:

```powershell
& "C:\Users\Concursos Felipe\Documents\UnB\TCC\.venv\Scripts\python.exe" "C:\Users\Concursos Felipe\Documents\UnB\TCC\scripts\14_recuperar_letras_amostra_200k.py" --status
```

Exibe o último checkpoint do workspace e do índice, com horários. Não comprova
que um processo permanece ativo. `complete` do índice só conclui a indexação;
conclusão da rodada exige `completed: true` no resumo público. Código de saída
0 = completo; 2 = parcial/interrompido/erros técnicos; 1 = falha de preparação.
Ambiguidades e perdas documentadas são resultados finais válidos.

## Saídas públicas para enviar ao ChatGPT

Pasta:
`C:\Users\Concursos Felipe\Documents\UnB\TCC\reports\recuperacao_letras_200k_v2\`.

Enviar estes 12 arquivos (o CSV de perdas só existe se houver não aceitas):

- `resumo_recuperacao_letras_200k.json`
- `relatorio_recuperacao_letras_200k.md`
- `protocolo_recuperacao_letras_200k_v2.md`
- `diagnostico_perdas_inicial_200k.csv`
- `transicoes_status_200k.csv`
- `recuperacoes_por_regra_200k.csv`
- `perdas_restantes_200k.csv`
- `comparacao_cobertura_recuperacao_200k.csv`
- `comparacao_instrumentais_200k.csv`
- `cobertura_popularidade_200k.png`
- `cobertura_genero_200k.png`
- `cobertura_periodo_200k.png`

Em falha, enviar o resumo incompleto e a mensagem do terminal. `owner.json` é
controle interno de compatibilidade. Os produtos só contêm agregados.

## Saídas privadas

`C:\Users\Concursos Felipe\Documents\UnB\TCC\data\derived\private_sample_lyrics_200k_v2\`:

- `state.sqlite`, lock e `progress.json`;
- `diagnostico_inicial_privado.parquet`;
- `resultados_faixas_200k.parquet`, uma linha por faixa, pesos originais;
- `letras_aceitas_200k.parquet`, textos originais e texto efetivamente aceito;
- `amostra_inspecao_novas_aceitacoes.json`, até três consultas por regra, para
  inspeção humana local. Não é validação de precisão nem deve ser publicada.

Índice separado em `D:\TCC_LRCLIB\tcc_lookup_sample_200k_v2\lookup.sqlite`.
Não enviar/versionar estado, letras, Parquets privados, índice ou dump.

## Verificações rápidas da preparação

Na pasta do projeto:

```powershell
& ".venv\Scripts\python.exe" -m pytest "tests/test_lyrics_recovery.py" "tests/test_sample_lyrics.py" "tests/test_local_lyrics.py" -q -p no:cacheprovider --basetemp ".tmp/pytest_recovery_v2_delivery"
& ".venv\Scripts\python.exe" -m ruff check "src/tcc_music_popularity/lyrics_recovery.py" "scripts/14_recuperar_letras_amostra_200k.py" "tests/test_lyrics_recovery.py"
& ".venv\Scripts\python.exe" -m ruff format --check "src/tcc_music_popularity/lyrics_recovery.py" "scripts/14_recuperar_letras_amostra_200k.py" "tests/test_lyrics_recovery.py"
```

Os testes usam SQLite/textos sintéticos e bloqueiam rede. Não há previsão de
quantas letras serão recuperadas; a execução real produzirá essas contagens.
