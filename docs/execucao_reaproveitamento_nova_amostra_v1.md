# Reaproveitar letras da nova amostra — um comando

**Atualização de 06/11: etapa real concluída/conferida.** 682 aceitas, 87
instrumentais, 8.757 pendentes; zero erros. Não repetir. Próximo comando em
execucao_busca_nova_amostra_v1.md, com SSD conectado. As instruções abaixo
registram a execução histórica de 41.

A amostra real de **9.526 faixas** foi sorteada pelo pesquisador e conferida.
Os metadados avaliados ficaram próximos ao catálogo. Não repetir o sorteio.

Execute:

```powershell
& "C:\Users\Concursos Felipe\Documents\UnB\TCC\.venv\Scripts\python.exe" "C:\Users\Concursos Felipe\Documents\UnB\TCC\scripts\41_reaproveitar_letras_nova_amostra.py"
```

Esta passagem usa os caches antigos no C:, em modo somente leitura. **Não
precisa conectar o SSD.** Consulta por chave; não varre o dump, constrói índice,
acessa internet ou recalcula descritores/embeddings.

Reutiliza apenas decisões vinculadas aos mesmos metadados completos: artista,
título, duração e qualificadores de versão. Confere SHA-256/fingerprint do texto
efetivamente aceito e o identificador LRCLIB escolhido. Uma coincidência apenas
de ID Spotify ou de título normalizado não basta. A decisão v2 tem prioridade;
v1 só é usado se a consulta não existir no v2. Não se flexibilizam regras para
melhorar a cobertura.

`accepted` significa aceitação automática anterior íntegra, não validação humana.
`instrumental` preserva a indicação no vínculo anterior. Ambiguidade, ausência
de texto ou qualquer outro status antigo não aceito permanece `pending_search`,
com sua origem registrada. **Ausência no cache não é ausência de letra.**

Cada consulta concluída é gravada no novo checkpoint. Se interromper, repita o
comando. Para acompanhar, acrescente `--status` em outra janela. Para reavaliar
erros técnicos, há `--retry-errors`; inconsistência de fonte/selo exige investigar
antes, sem apagar arquivos. Não rodar dois escritores no mesmo workspace.

Saída esperada:

```text
{"etapa": "resumo_cache", "status_por_faixa": {...}}
[4/4] Cache concluído; buscas restantes ainda pendentes. Agregados em ...
```

Pasta pública: `reports/reaproveitamento_nova_amostra_v1/`:

- `resumo_reaproveitamento.json`: conclusão desta passagem e contagens;
- `status_cache.csv` e `cobertura_cache.csv`: totais e distribuição por
  gênero/período/faixa de popularidade, sem letras ou identificação individual.

Pasta privada nova: `data/derived/private_nova_amostra_cache_v1/`:

- `state.sqlite` e `progress.json`: checkpoint por consulta e progresso;
- `resultados_faixas.parquet`: todos os sorteados, campos/pesos originais intactos;
- `letras_aceitas.parquet`: uma linha por consulta aceita, texto efetivo separado
  dos campos originais plain/synced e proveniência;
- `pendencias_busca.parquet`: faixas ainda não aceitas nem instrumentais.

Não versionar esses produtos individuais. Os arquivos históricos continuam nos
mesmos locais. O processo não os copia integralmente nem reescreve seus estados.
Caches de gigabytes são identificados por caminho/tamanho/mtime e leitura sem
WAL ativo; não há novo hash integral deles. Cada texto importado é conferido
individualmente, sem alegar verificação criptográfica integral dos bancos.

O resumo distingue `concluido: true` desta passagem de
`recuperacao_integral_concluida: false`. Ainda não conhecemos a quantidade de
letras que será reaproveitada. Após sua execução, avaliar pendências e preparar
busca dirigida com os índices locais existentes. Sem substituir faixas perdidas
ou assumir que os pesos corrigem automaticamente a disponibilidade das letras.
