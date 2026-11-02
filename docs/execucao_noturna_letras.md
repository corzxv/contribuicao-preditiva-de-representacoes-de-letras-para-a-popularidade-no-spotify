# Continuar após o índice, sem esperar diante do computador

O script 07 encadeia as funções do script 06. Não altera o código selado do índice, critérios, splits ou modelos. Não faz rede, embeddings ou treinamento. O usuário inicia a execução manualmente; não há tarefa agendada nem serviço instalado.

Com o índice já em execução, abra **outro terminal PowerShell** e execute:

```powershell
Set-Location "C:\Users\Concursos Felipe\Documents\UnB\TCC"
.\.venv\Scripts\python.exe scripts\07_continuar_apos_indice.py --run
$LASTEXITCODE
```

Sequência:

1. Aguarda `complete: true` no índice e a liberação do bloqueio real do workspace pelo script 06. Consulta a cada 15 segundos, por no máximo 12 horas. Não inicia outro indexador.
2. Executa até 50 pendências e confere código de saída, resumo novo, número processado e ausência de erros técnicos locais. É uma conferência operacional, não substitui revisão humana de qualidade científica. Ambiguidades e ausências são resultados válidos; continuam sem aceitação arbitrária.
3. Se a conferência passar, executa todas as pendências restantes. Se já não houver pendências, encerra sem outro lote.
4. Se houver erro, interrompe e preserva o progresso. Não retenta erros técnicos automaticamente nem reinicia a indexação. Se o índice parar incompleto, o sequenciador também para após duas sondagens sem trabalhador ativo.

O limite de 12 horas vale **somente para aguardar o índice**; a busca completa pode ultrapassar esse prazo. Não há garantia de concluir durante a noite. O limite pode ser informado com `--wait-hours 12`.

Deixe os dois terminais abertos, o SSD conectado e o computador na tomada, sem suspensão. Não feche a tampa do notebook se isso o suspender. A tela pode apagar; o computador precisa continuar acordado. O script não modifica as configurações de energia nem impede reinicializações do Windows. Não execute outro `--all` ou `--limit` em paralelo.

Para acompanhar ou verificar ao acordar:

```powershell
.\.venv\Scripts\python.exe scripts\07_continuar_apos_indice.py --status
.\.venv\Scripts\python.exe scripts\06_buscar_letras_local.py --status
```

O primeiro mostra `waiting_index`, `sample_50`, `all_pending`, `complete`, `stopped` ou `failed`. O segundo mostra as contagens reais. O status do sequenciador é o último salvo, não um detector de processo ativo. Seu checkpoint fica em `data/derived/private_local_lyrics_v1/local_sequence/progress.json`, ignorado pelo Git. O progresso de cada consulta continua no SQLite do script 06.

Após interrupção, repita o comando `--run`: ele executa um novo lote de até 50 **pendências**, sem refazer as consultas concluídas. Se houver erros locais pendentes, a sequência não avança para o lote completo; traga os dois status para revisão. Códigos: `0` concluído sem pendências locais; `2` interrompido/limite/erro de lote; `1` falha de preparação ou execução.

Verificações sintéticas realizadas:

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_local_sequence.py tests/test_local_lyrics.py -p no:cacheprovider --basetemp=.tmp/pytest_sequence_a
.\.venv\Scripts\python.exe -m ruff check src/tcc_music_popularity/local_sequence.py scripts/07_continuar_apos_indice.py tests/test_local_sequence.py
.\.venv\Scripts\python.exe -m ruff format --check src/tcc_music_popularity/local_sequence.py scripts/07_continuar_apos_indice.py tests/test_local_sequence.py
```

31 testes passaram (10 de sequência e 21 de busca local), com código 0. Incluem espera e bloqueio, falha/resumo antigo no lote, prazo máximo, interrupção e pular lote completo quando não há pendências. Nenhuma coleta ou indexação real foi iniciada pelo assistente. Sem dependências novas, commit ou push.
