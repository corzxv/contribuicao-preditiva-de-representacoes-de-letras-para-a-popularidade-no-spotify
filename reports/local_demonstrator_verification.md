# Entrega aplicada — demonstrador local dos modelos congelados

Verificação realizada em 2026-10-14. O experimento V0.6 permanece encerrado.
Esta entrega é uma interface de inferência sobre o mesmo holdout, não uma nova
avaliação independente. Nenhum alvo entrou nos inputs; nenhuma letra foi
consultada, nenhum descritor/embedding foi recalculado e nenhum modelo foi
treinado, ajustado, calibrado ou selecionado novamente.

## Arquivos criados

- `apps/streamlit_demo.py`: interface local Streamlit;
- `src/tcc_music_popularity/local_demo.py`: catálogo, inferência, integridade e
  estado independente de estimar/revelar;
- `src/tcc_music_popularity/local_demo_delivery.py`: CLI de conferência numérica,
  preservação científica, privacidade Git e empacotamento dos PNGs existentes;
- `tests/test_local_demo.py`: 16 testes/casos sintéticos do serviço e pacote;
- `tests/test_local_demo_ui.py`: três testes funcionais sintéticos da interface;
- `.streamlit/config.toml`: loopback, telemetria desativada, sem file watcher;
- `requirements-demo.txt` e `constraints-demo.txt`: dependência da interface e
  versões científicas preservadas;
- `docs/demonstrador_local.md`: instruções Windows, escopo, dependências e limites;
- `reports/legendas_figuras_monografia_v0_6.md`: legendas sugeridas;
- `reports/local_demonstrator_verification.md`: este registro;
- `reports/figuras_monografia_v0_6.zip`: quatro PNGs originais e legendas;
- `.tmp/demo_ui_checked.jpg`: evidência visual local da inspeção, ignorada pelo
  Git e não incluída no ZIP.

Alterações em arquivos existentes: uma dependência opcional `demo` em
`pyproject.toml` e regras de proteção para modelos/vetores/temporários em
`.gitignore`. Alterações pessoais preexistentes foram preservadas. Não foram
alterados os arquivos da pipeline científica ou seus manifestos.

## Conferência real das previsões

Foram reproduzidas, somente com `predict`, as quatro previsões para cada uma das
2.592 composições do holdout. A junção da referência usa composition_key,
track_id e spotify_row_id, com validação 1:1 e ordem preservada. Dimensões de
input congelado: 23, 219, 407 e 603, respectivamente. O candidato continua
`elastic_net__traditional`. Não foi lido o alvo nem calculada qualquer métrica
nessa conferência numérica.

| Modelo | Maior diferença absoluta contra a previsão salva V0.6 |
|---|---:|
| Baseline | 0 |
| Tradicional | 7,105427357601002 × 10⁻¹⁵ |
| Profundo | 0 |
| Combinado | 1,4210854715202004 × 10⁻¹⁴ |

Critério: `abs(atual - salva) <= 1e-8 + 1e-10 * abs(salva)`. Todas passaram.
Também há conferência automática em cada inferência individual da aplicação.
As previsões são brutas, sem clipping; arredondamento é apenas de apresentação.

Os hashes SHA-256 de 52 artefatos científicos foram conferidos antes/depois da
inferência, incluindo dados e splits congelados, todos os nove modelos originais,
features, previsões salvas, relatórios, código congelado e quatro gráficos.
Nenhum mudou. MAE/R² exibidos são exclusivamente os oficiais da V0.6.

## Comandos finais e resultados

Todos os comandos abaixo foram executados na raiz do projeto, no ambiente
existente. A instalação adicionou 22 pacotes e não alterou a versão de nenhum
pacote previamente instalado, inclusive todas as bibliotecas científicas.

| Comando | Saída / resultado | Código |
|---|---|---:|
| `.\.venv\Scripts\python.exe -m pip install -r requirements-demo.txt` | Streamlit 1.65.0 e dependências novas instalados | 0 |
| `.\.venv\Scripts\python.exe -m pip check` | No broken requirements found | 0 |
| `.\.venv\Scripts\python.exe -m pytest tests/test_local_demo.py tests/test_local_demo_ui.py -o addopts='' -q -p no:cacheprovider --basetemp .tmp/demo_tests_02` | 17 aprovados na rodada inicial | 0 |
| `.\.venv\Scripts\python.exe -m pytest -o addopts='' -q -p no:cacheprovider --basetemp .tmp/demo_full_tests_02` | 146 aprovados; 0 falhos; 104,63 segundos, incluindo 19 casos novos | 0 |
| `.\.venv\Scripts\python.exe -m ruff check src tests apps` | All checks passed | 0 |
| `.\.venv\Scripts\python.exe -m ruff format --check src tests apps` | 48 arquivos já formatados | 0 |
| `.\.venv\Scripts\python.exe -m tcc_music_popularity.local_demo_delivery --verify --package` | 2.592 × 4 previsões compatíveis; 52 artefatos preservados; ZIP válido | 0 |
| `git diff --check` | Sem problemas de whitespace | 0 |
| `git diff --cached --name-only` | Stage vazio | 0 |

Ruff format foi aplicado somente aos cinco arquivos Python novos. A suíte nova
testa inputs sem alvo, rejeição de três colunas proibidas, schema, junção/ordem,
previsões brutas fora da escala, preservação dos modelos, divergência de previsão,
arquivos ausentes/adulterados, versão científica divergente, composição externa,
busca determinística completa e empacotamento não destrutivo. Os três testes
Streamlit verificam fluxo completo, busca sem resultados e erro explicativo
quando os arquivos privados estão ausentes. Os fixtures são exclusivamente
sintéticos; nenhum artefato real foi escrito pelos testes novos.

As tentativas iniciais de Streamlit/AppTest dentro do sandbox ficaram bloqueadas
em `socket.accept` durante a criação do loopback do asyncio; foram interrompidas
(código 1). A execução local autorizada fora desse isolamento funcionou e os
testes finais retornaram 0. Isso foi uma restrição do ambiente de inspeção, não
uma falha dos pipelines. Não foram alteradas proteções do Windows.

## Inspeção funcional efetiva

O servidor foi iniciado no Windows apenas em `127.0.0.1:8501`, com telemetria
desativada. A inspeção de navegador, orientada pela habilidade de controle do
computador, verificou o catálogo completo, seleção inicialmente vazia, botões
desabilitados, metadados sem observado, quatro estimativas por `predict`, clique
separado de revelação, observado e quatro erros absolutos. A composição usada
foi a primeira da ordenação determinística, sem consulta prévia a erros/acertos.
Também foram verificadas buscas por título e artista e o reset de previsões/
observado após mudança da seleção. Não houve erros no console do navegador
durante a inspeção. O servidor temporário foi encerrado após a conferência.

## Privacidade e ZIP

A auditoria real encontrou zero artefatos privados tracked e zero staged;
12 caminhos de modelos/dados/ZIP foram confirmados como ignorados. Nenhum commit,
push, stage, publicação ou upload de dados foi realizado. HEAD permaneceu
`a37946ae2ddb211abe85d67a9b69fc7e88a71b86`.

ZIP: `C:\Users\Concursos Felipe\Documents\UnB\TCC\reports\figuras_monografia_v0_6.zip`.
Tamanho: 177.996 bytes. SHA-256:
`1a780c84a81b22c5b1fffd3d01c3894e1e2f28f0507f0cee3027df90c24e6394`.
Contém somente elastic_net_metrics.png, observed_predicted_aggregated.png,
primary_mae_adjusted_intervals.png, residual_distributions.png e
legendas_figuras_monografia_v0_6.md. Todos os PNGs são byte a byte idênticos aos
originais V0.6, confirmados por hash. Nenhum gráfico/métrica foi regenerado.

## Limitações

Somente composições estudadas, sem upload, áudio, busca externa, novas letras ou
features. Requer os arquivos privados locais originais e o ambiente científico
exato (incluindo Python 3.13.15); clone do Git sozinho não executa a aplicação.
Não foi testada hospedagem, acesso remoto ou outras máquinas: são fora do escopo.
Não é estimativa prospectiva de sucesso nem demonstração causal. MAE agregado
não é intervalo individual, probabilidade ou porcentagem de acerto.

Para abrir, consulte `docs/demonstrador_local.md`; basta executar Streamlit no
ambiente existente e acessar `http://127.0.0.1:8501` no navegador local.
