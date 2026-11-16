# Revisão local das consultas barradas pelo limite de candidatos

O piloto online concluiu 100 buscas e produziu zero candidatas. Esta etapa
trata uma pendência distinta, identificada no estado local. Em 40 consultas,
o teto de 500 resultados foi aplicado antes da elegibilidade dos metadados.
Dos sete casos inspecionados, seis apresentaram candidatos compatíveis
depois de aplicar os critérios de artista, título, participações, versão e
duração. Os sete casos são diagnósticos, escolhidos em ordem determinística.

O script usa os índices existentes para buscar até 2.500 metadados por
consulta e aplica o teto de 500 aos candidatos elegíveis. Se o conjunto
ultrapassar um teto, a consulta segue inconclusiva. A leitura textual respeita
os limites de tamanho vigentes e compara as letras pelas regras de 43, 46
e 47. As letras aceitas são gravadas na forma original, com os vínculos em
complemento separado. A etapa acessa apenas as 40 consultas em questão.

Com o SSD conectado em D:, execute o comando no PowerShell.

```powershell
& "C:\Users\Concursos Felipe\Documents\UnB\TCC\.venv\Scripts\python.exe" "C:\Users\Concursos Felipe\Documents\UnB\TCC\scripts\50_revisar_limite_de_candidatos.py"
```

Repita o comando para retomar após interrupção. O JSON informa
`new_accepted_tracks`, `accepted_tracks_with_overlays` e os desfechos. O
relatório completo fica em `reports/revisao_limites_nova_amostra_v1`, e o
checkpoint e os novos vínculos ficam em
`data/derived/private_revisao_limites_nova_amostra_v1`. Oito testes e uma
verificação do fluxo com as 40 consultas simuladas passaram. O pesquisador
concluiu a execução real e acrescentou 25 letras verificadas por ID no dump.
O total consolidado de 3.869 consta nos [agregados de cobertura](../reports/recuperacao_consolidada_nova_amostra_v1/resumo_cobertura.json).
