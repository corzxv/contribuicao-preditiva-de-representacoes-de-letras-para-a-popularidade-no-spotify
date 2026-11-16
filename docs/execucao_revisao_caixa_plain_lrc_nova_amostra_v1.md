# Revisão de caixa entre letra simples e sincronizada

A etapa 46 acrescentou 130 vínculos e levou a recuperação a 3.777 das 9.526
faixas (39,65%). A etapa 47 trata 108 pendências separadas. Nelas, as regras de
origem encontraram divergência entre a letra simples e a sincronizada (LRC).
Em 12 consultas examinadas, cinco ficaram inteiramente equivalentes com a
normalização de caixa já usada em 46. Os exemplos são diagnósticos e servem
para justificar a revisão dirigida.

A etapa 47 usa a lista de candidatos gravada em 43 e consulta por ID o texto
dos candidatos elegíveis. Verifica os hashes dos textos, usa o analisador LRC
vigente para remover as marcas de tempo e compara as representações em
minúsculas, com espaços uniformizados e a mesma tipografia. Todos os textos
elegíveis precisam concordar. O texto aceito, suas versões simples e
sincronizada e os identificadores de origem são gravados em complemento privado.

Com o SSD em D:, execute o comando.

```powershell
& "C:\Users\Concursos Felipe\Documents\UnB\TCC\.venv\Scripts\python.exe" "C:\Users\Concursos Felipe\Documents\UnB\TCC\scripts\47_revisar_caixa_plain_lrc.py"
```

O JSON final informa `new_accepted_tracks` e `accepted_tracks_with_overlays`.
O relatório completo fica em `reports/revisao_caixa_plain_lrc_nova_amostra_v1`.
O complemento fica em `data/derived/private_revisao_caixa_plain_lrc_nova_amostra_v1`.
O script grava o lote após concluir a revisão. Se houver interrupção, repita
o comando para reavaliar as mesmas consultas sem duplicar vínculos.

Quinze testes dos módulos 43, 46 e 47 passaram. O lote real de 108 consultas
está pendente de execução manual. As variantes de artista têm revisão separada.
