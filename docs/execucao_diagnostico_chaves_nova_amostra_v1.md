# Diagnosticar as 4.164 consultas sem candidato

43 REAL concluído e conferido: **3.647 letras aceitas (38,28%)**, aumento de
2.222 sobre 42. As 1.425 anteriores permanecem; 54 novas indicações instrumentais
elevam esse grupo a 416. Restam 1.298 ambiguidades, 4.164 sem candidato e uma
sem texto; zero erro técnico ou pendência. Não repetir 42/43.

O próximo passo investiga os casos sem candidato usando os índices nativos já
existentes no dump. Exemplo pontual demonstrado: “Secret & Whisper”/“Secret and
Whisper”, mesmo título e duração próxima. Isso é um indício de diferença de
cadastro, não uma regra universal de identidade de artistas.

Com SSD em **D:**, execute:

```powershell
& "C:\Users\Concursos Felipe\Documents\UnB\TCC\.venv\Scripts\python.exe" "C:\Users\Concursos Felipe\Documents\UnB\TCC\scripts\44_diagnosticar_consultas_sem_candidato.py"
```

**É diagnóstico de metadados: não altera as 3.647 aceitações nem aceita letras
automaticamente.** Identifica candidatos para decidir a próxima recuperação.
Não reconstrói índices, varre 33 milhões de registros, acessa rede, lê corpos
de letras ou treina modelos. Não exige smoke ou comandos em paralelo.

## Consultas e limites

Usa nome de faixa exato, nome de artista exato e frases do título com termos do
artista na busca textual FTS5, incluindo o título-base operacional quando
aplicável. Restringe duração à tolerância existente de dez segundos.
Planos SQL conferidos antes da execução: B-trees de nome/artista e índice
virtual textual com acesso ao registro por ID. O `SCAN ... VIRTUAL TABLE INDEX`
do plano FTS é acesso ao índice textual, não uma varredura da tabela tracks.
Referência da sintaxe: [documentação oficial FTS5](https://www.sqlite.org/fts5.html).

Até cem registros por método, cinquenta candidatos guardados por consulta e
dois segundos no conjunto de métodos de cada consulta. Limites/esgotamento
ficam explícitos: não autorizam concluir ausência de letra. As consultas usam
parâmetros; a busca textual usa termos literais delimitados. Sem distância
aproximada para aceitar, exclusão de palavras para forçar equivalência ou uso
de popularidade/gênero/pesos na busca.

Categorias públicas são diagnósticas, em prioridade:

| Categoria | Significado |
|---|---|
| strict_profile_compatible | Existe metadado compatível com o perfil vigente; investigar a recuperação anterior |
| artist_key_variant | Chave conservadora de artista coincide, perfil estrito não; indício para revisão |
| same_artist_other_title | Mesmo artista, outro título com duração próxima; não significa mesma música |
| same_title_other_artist | Mesmo título, outro artista; não é aceitação de cover |
| other_metadata_candidates | Outros registros sugeridos pelos métodos |
| no_candidates_under_these_methods | Nenhum candidato nos métodos/limites utilizados; não prova ausência no dump |

A categoria escolhida tem prioridade, e os indicadores privados podem se
sobrepor. `last_lyrics_id` apenas indica referência a um registro: não comprova
texto disponível. Diferenças `&`/`and` ou acentos são indícios para revisão,
não aliases universais validados. A amostra original permanece integral.

## Resultados e retomada

Públicos em `reports/diagnostico_chaves_nova_amostra_v1/`: resumo JSON e
categorias_diagnostico.csv. **Os candidatos individuais ficam privados** no
checkpoint `data/derived/private_diagnostico_chaves_nova_amostra_v1/state.sqlite`:
metadados, métodos, indicadores e limites, sem corpos de letras.

Pode interromper e retomar pelo mesmo comando. `--status` mostra progresso.
Depois de erro técnico/reconexão, repetir o comando retoma os não concluídos;
resultados limitados por tempo/candidatos são diagnósticos incompletos explícitos.
Não alterar entradas/código durante essa passagem ou executar dois escritores.

Código preparado/testado com SQLite sintético: artista com variante `&`/`and`,
outro artista com mesmo título, limites e retomada sem modificar 43. Execução
real 44 pendente manual. Após a saída, interpretar causas e definir busca/revisão
dirigida; não iniciar nova modelagem com aceitação de candidatos apenas por título.
