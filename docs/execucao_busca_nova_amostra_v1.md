# Buscar letras da nova amostra no SSD — um comando

41 real concluído/conferido: **682 aceitas, 87 instrumentais e 8.757 pendentes**,
sem erros. Os 7,16% aceitos são reaproveitamento do cache, não a cobertura final
do LRCLIB. Não repetir 39, 40 ou 41 para iniciar esta etapa.

Conecte o SSD como **D:** e execute:

```powershell
& "C:\Users\Concursos Felipe\Documents\UnB\TCC\.venv\Scripts\python.exe" "C:\Users\Concursos Felipe\Documents\UnB\TCC\scripts\42_buscar_letras_nova_amostra.py"
```

O programa preserva as aceitas/instrumentais de 41. Também reaproveita decisões
negativas anteriores apenas quando comprovadamente resultantes da mesma busca
controlada v2 completa, sem limite operacional, no mesmo snapshot. Isso evita
repetir consultas idênticas; `not_found` continua restrito às chaves controladas.
Os demais casos seguem para busca, sem flexibilizar artista, duração ou versão.

Usa o índice v2 já concluído, com 24.330 chaves de artista. Para artistas ainda
fora desse universo, identifica a necessidade e constrói **somente um complemento**
em `D:\TCC_LRCLIB\tcc_lookup_nova_amostra_v1`. Nenhum índice antigo é refeito.
O complemento requer uma passagem pelos metadados dos 33.714.178 registros do
dump: essa pode ser a parte mais demorada. O terminal informa quantos artistas
precisam dele antes de começar. Se não houver artistas adicionais, pula a passagem.

Depois consulta as faixas por índice e aplica o classificador v2 existente:
mesmos critérios de versões, créditos, duração e equivalência dos textos.
Nenhuma busca na internet, novo encoder ou modelo preditivo. Não é preciso
aprovar uma etapa smoke ou executar comandos em paralelo.

## Retomada e acompanhamento

Pode interromper com Ctrl+C e depois repetir o comando. Índice é gravado em
lotes; decisões são gravadas por consulta. Não apagar estado, WAL ou pastas.
Não alterar código/entradas nem repetir 41 durante essa execução.

Para acompanhar em outra janela:

```powershell
& "C:\Users\Concursos Felipe\Documents\UnB\TCC\.venv\Scripts\python.exe" "C:\Users\Concursos Felipe\Documents\UnB\TCC\scripts\42_buscar_letras_nova_amostra.py" --status
```

Após erro técnico corrigido/reconexão, acrescente `--retry-errors` ao comando
principal. Até três tentativas por consulta com erro; ambiguidades não são
relaxadas automaticamente. Conclusão de índice não significa conclusão da busca.

## Saídas

Públicas: `reports/busca_local_nova_amostra_v1/`:

- `resumo_busca_local.json`: conclusão, contagens, origem e selos;
- `status_busca.csv` e `cobertura_busca.csv`: totais e cobertura após a busca local;
- `transicoes_status.csv`: passagem de 41 para o resultado local.

Privadas: `data/derived/private_nova_amostra_local_v1/`:

- `state.sqlite` e `progress.json`: decisões, evidência e retomada;
- `resultados_faixas.parquet`: todas as 9.526 faixas, campos e pesos preservados;
- `letras_aceitas.parquet`: textos originais e `accepted_text` efetivamente aceito;
- `pendencias_revisao.parquet`: demais faixas, com motivo explícito.

Evidência de candidatos rejeitados guarda metadados, IDs e hashes dos textos,
sem duplicar seus corpos. O dump selado permite recuperá-los por ID para revisão.
Textos aceitos conservam as representações originais plain/synced separadas do
texto efetivo, inclusive plain ausente quando derivado de LRC. Produtos individuais
continuam privados. Caches, resultados, amostra e monografias anteriores intactos.

`completed: true` significa consultas previstas concluídas sob essas regras;
não significa que todas as faixas têm letras ou que houve revisão humana. Envie
as últimas linhas. O próximo passo será avaliar cobertura/seleção e pendências,
antes de escolher qualquer modelagem. Não substituir músicas sem letras.
