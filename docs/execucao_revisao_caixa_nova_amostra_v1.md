# Revisão de caixa em textos concorrentes

O pesquisador escolheu continuar a recuperação antes de modelar. A revisão
abrange as 831 consultas classificadas como `substantively_distinct_texts` em 43.
Em doze exemplos diagnósticos, cinco passaram a ter textos iguais após
uniformização de caixa e espaços, com a tipografia vigente. A seleção desses
exemplos foi determinística. O ganho será medido na execução das 831 consultas.

Cada consulta usa os candidatos dos índices já conferidos. O classificador de
origem verifica identidade, participações, versão, duração, completude e
consistência plain/LRC. A revisão trata o caso em que resta somente a divergência
entre textos de candidatos compatíveis. Compara exatamente a sequência de
caracteres após conversão para minúsculas, uniformização de espaços e a mesma
normalização tipográfica de 43. Diferenças de palavras, acentos e pontuação
além da tipografia vigente continuam em revisão. A escolha entre textos
equivalentes segue a prioridade existente de duração, completude e identificador.
O texto escolhido e suas fontes plain/LRC são gravados na forma original.

Com o SSD conectado em D:, execute o comando.

```powershell
& "C:\Users\Concursos Felipe\Documents\UnB\TCC\.venv\Scripts\python.exe" "C:\Users\Concursos Felipe\Documents\UnB\TCC\scripts\46_revisar_caixa_textos_concorrentes.py"
```

`--status` consulta o progresso. Repita o comando para retomar após interrupção.
O resumo em `reports/revisao_caixa_nova_amostra_v1` informa os resultados e a
contagem combinada. O complemento privado em
`data/derived/private_revisao_caixa_nova_amostra_v1` guarda vínculos por faixa
e os textos recém-aceitos por consulta. Os artefatos selados de 43 são a base
da combinação. Sete testes passaram em dados sintéticos. Execução real pendente.

As 13 consultas com variações de grafia de artista receberam fichas privadas
com 16 pares de metadados. Em todas elas há pelo menos um campo textual
preenchido no registro consultado. A identidade da gravação e a adequação do
texto estão em revisão. Fichas em
`data/derived/private_consolidacao_nova_amostra_v1/fichas_variantes_artista.csv`.
