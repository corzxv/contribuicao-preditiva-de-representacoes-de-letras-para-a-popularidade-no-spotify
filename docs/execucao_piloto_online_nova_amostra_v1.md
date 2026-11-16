# Piloto online do LRCLIB nas pendências

O piloto sorteou, sem reposição, 100 das 4.155 faixas que seguem sem candidato
após a etapa 48. A seleção foi selada antes da consulta, com semente 20261107
e 100 consultas distintas. O tamanho foi escolhido para medir o rendimento
operacional antes de discutir uma rodada maior.

Com internet disponível, execute o comando no PowerShell.

```powershell
& "C:\Users\Concursos Felipe\Documents\UnB\TCC\.venv\Scripts\python.exe" "C:\Users\Concursos Felipe\Documents\UnB\TCC\scripts\49_pilotar_busca_online_lrclib.py"
```

Se houver interrupção, repita o mesmo comando. Se a API pedir uma pausa, espere
até o horário mostrado. Cada resposta concluída fica registrada no checkpoint.
O JSON final informa `completed`, `pending_tracks`, `provisional_tracks` e os
desfechos. O resumo completo é salvo em
`reports/piloto_online_nova_amostra_v1/resumo_piloto_online.json`. A seleção e
o checkpoint com as evidências individuais ficam em
`data/derived/private_piloto_online_nova_amostra_v1`.

O script envia título e artista para `/api/search`, em série, com intervalo
de meio segundo entre consultas. Aplica localmente os critérios de artista,
título, participações e versão, com diferença máxima de dois segundos na
duração. Também exige consistência das letras elegíveis. Resultados no teto
de 20 da API ficam inconclusivos. Resposta vazia, incompatibilidade, conflito
textual e falha operacional são contabilizados separadamente. [Documentação do LRCLIB](https://lrclib.net/docs)

O resultado positivo é uma candidatura provisória, guardada à parte dos
vínculos locais. A revisão seguinte verifica a faixa e a procedência do
resultado. Uma candidata encontrada online pode já estar no dump sob outra
chave, por isso o ganho do piloto é do método online aplicado às pendências.

O pesquisador concluiu as 100 consultas. O checkpoint confirmou 93 respostas
vazias, cinco sem candidato compatível, uma indicação instrumental e uma no
teto de resultados. Zero candidatas. O resultado encerra a rodada pelo mesmo
protocolo. [Verificação do piloto](../reports/piloto_online_nova_amostra_v1/verificacao_resultado_piloto.json)
