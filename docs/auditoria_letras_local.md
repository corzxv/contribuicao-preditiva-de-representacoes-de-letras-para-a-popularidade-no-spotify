# Auditoria antes dos embeddings

Execute manualmente na raiz do projeto, após concluir a busca local:

```powershell
Set-Location "C:\Users\Concursos Felipe\Documents\UnB\TCC"
.\.venv\Scripts\python.exe scripts\08_auditar_letras_local.py --all
$LASTEXITCODE
```

Entrada: checkpoints original e local e caches referenciados pelas consultas aceitas. Operação: leitura de cada cache aceito, conferência SHA-256/candidato selecionado/texto, comparação de IDs e metadados dos manifestos, contagem de textos distintos e compartilhamentos de hashes/artistas/composições entre splits. Não consulta popularidade, dump, rede ou encoder; não gera embeddings. A função `read_accepted_text` existente é reaproveitada, assim como bloqueios e leitores de checkpoint.

Saída: nova pasta com timestamp em `data/derived/private_local_lyrics_audit/`, privada e ignorada pelo Git. Contém `summary.json`, `provenance.json`, `issues_private.json` e `accepted_text_index.jsonl`. Não salva letras nesses relatórios; IDs e hashes detalhados continuam privados. O terminal mostra contagens a cada 250 consultas e o resumo final.

Os dois checkpoints são abertos em modo somente leitura e bloqueados contra execução concorrente dos scripts do projeto. Os hashes dos arquivos de entrada são comparados antes/depois. Cada invocação cria uma pasta nova, sem sobrescrever auditorias ou dados existentes. Após Ctrl+C, a saída é marcada incompleta; repetir o comando faz uma auditoria nova desde o início, não altera nem repete a coleta.

Códigos: **0** = auditoria completa sem alertas automáticos; **2** = há pontos para revisão ou a auditoria foi interrompida; **1** = não foi possível concluir a execução. Código 2 não significa que a coleta foi perdida. Compartilhar um hash entre splits é um alerta de dependência/possível vazamento, não prova de match incorreto. Não há exclusão automática ou alteração de split.

Esta auditoria não comprova a correção humana do match, não detecta toda semelhança textual aproximada, não avalia idiomas/representatividade e não escolhe encoder. As contagens de textos são por hash estrito e pela normalização já existente; consultas e faixas não equivalem a textos distintos. Um retorno sem alertas não é autorização para reabrir o holdout científico encerrado.

Traga o resumo final e `$LASTEXITCODE`. A escolha da rede de embeddings permanece em aberto.

Verificação sintética (28/10/2026):

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_local_lyrics_audit.py tests/test_local_lyrics.py -p no:cacheprovider --basetemp=.tmp/pytest_local_audit_a
.\.venv\Scripts\python.exe -m ruff check src/tcc_music_popularity/local_lyrics_audit.py scripts/08_auditar_letras_local.py tests/test_local_lyrics_audit.py
.\.venv\Scripts\python.exe -m ruff format --check src/tcc_music_popularity/local_lyrics_audit.py scripts/08_auditar_letras_local.py tests/test_local_lyrics_audit.py
```

27 testes passaram (6 novos e 21 da busca local), com código 0. Incluem hashes compartilhados, falha na leitura de cache, split alterado, interrupção, preservação dos arquivos e bloqueio de coleta incompleta. Ruff e formatação passaram com código 0. A auditoria real não foi executada pelo assistente. Nenhuma dependência adicional, commit ou push.
