# Recuperação dirigida por gênero

A revalidação 53 confirmou 42 vínculos históricos. `minimal-techno` passou a
ter 151 faixas com letra válida para uma cota de 125. Os três gêneros com
capacidade abaixo das cotas do sorteio original seguem na busca 55.

| Gênero | Cota | Vínculos verificados | Déficit | Faixas a consultar |
|---|---:|---:|---:|---:|
| `sleep` | 147 | 5 | 142 | 13.983 |
| `romance` | 54 | 12 | 42 | 5.278 |
| `detroit-techno` | 32 | 11 | 21 | 3.182 |

54 selecionou essas faixas do catálogo selado entre os artistas cobertos
pelos índices existentes. O plano exclui os IDs dos sorteios de 9.526 e
200 mil e os vínculos já conhecidos. Cada consulta usa o artista, o título
e a duração para revisar gravações compatíveis pelas mesmas regras de 50.
O total de consultas é uma medida de alcance dos índices e o rendimento será
medido pelos vínculos aceitos.

Com o SSD LRCLIB conectado em D:, execute no PowerShell.

```powershell
& "C:\Users\Concursos Felipe\Documents\UnB\TCC\.venv\Scripts\python.exe" "C:\Users\Concursos Felipe\Documents\UnB\TCC\scripts\55_buscar_letras_generos_deficitarios.py"
```

Após uma interrupção, repita o comando para retomar as consultas pendentes.
O progresso aparece a cada 250 consultas. O resumo final traz os novos
vínculos e a diferença em relação à cota de cada gênero.

## Resultado verificado

55 concluiu as 22.443 consultas com 179 vínculos aceitos. `detroit-techno`
passou a 62 faixas disponíveis, `romance` a 122 e `sleep` a 23. Em `sleep`,
a busca trouxe 18 letras em 13.983 consultas. Foram registradas 616 indicações
instrumentais nesse gênero. Uma consulta pontual a 48 das 680 faixas
de `sleep` de artistas fora dos índices trouxe 17 indicações instrumentais
e zero campos textuais compatíveis por chave exata.

A etapa 56 produziu a candidata v2 de 9.526 a partir de 80.943 faixas com
letra aceita. As 23 faixas elegíveis de `sleep` entraram na seleção. A
alocação mantém as cinco bandas marginais de popularidade e aproxima as
cotas dos gêneros dentro das capacidades. Como resultados de seleção,
`sleep` ficou com 23 de 147 e `indie-pop` com 81 de 82. A média de
instrumentalidade da candidata é 0,135. A do catálogo é 0,252.
[Resumo da candidata v2](../reports/amostra_com_letras_candidata_v2/resumo_amostra_candidata.json)
