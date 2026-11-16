# Executar a nova amostra — um comando

**Atualização de 06/11/2026: sorteio real concluído pelo pesquisador e conferido.**
Não repetir esta etapa. Interpretação em reports/interpretacao_nova_amostra_catalogo_v1.md;
próximo comando está em execucao_reaproveitamento_nova_amostra_v1.md.

## Comando histórico

O dimensionamento **já foi executado pelo agente somente em agregados**:
9.526 faixas, alocação proporcional nos 82 gêneros. O sorteio real ainda não foi
executado. A amostra anterior, letras, modelos e monografias estão preservados.

Execute no PowerShell:

```powershell
& "C:\Users\Concursos Felipe\Documents\UnB\TCC\.venv\Scripts\python.exe" "C:\Users\Concursos Felipe\Documents\UnB\TCC\scripts\40_preparar_nova_amostra.py" sortear
```

O comando lê o CSV Spotify local, sorteia e gera os comparativos. Não acessa
LRCLIB, internet, encoder ou modelos. Não precisa repetir 39, dimensionar,
executar smoke ou rodar comandos em paralelo.

Conclusão esperada:

```text
[4/4] Concluído. Comparativos em ...\reports\nova_amostra_catalogo_v1
```

Saídas:

- `data/processed/nova_amostra_catalogo_v1/amostra_spotify.parquet`: amostra
  individual privada, campos originais e novas colunas de seleção/peso.
- `reports/nova_amostra_catalogo_v1/resumo_sorteio.json`: conclusão, contagens
  e selos; `comparacao_metadados.csv` e `comparacao_categorias.csv`: agregados.
- Na mesma pasta já existem plano, alocação, precisão e cenários dimensionados.

Se repetir após conclusão, o programa confere as saídas e reutiliza a amostra.
Se parar antes de gravar o Parquet, o mesmo comando reproduz o sorteio de
semente fixa. Parquet gravado sem resumo de conclusão ou arquivo alterado
gera interrupção para investigação, preservando os arquivos existentes.

Envie a saída final. A próxima ação será interpretar o comparativo e organizar
a recuperação das letras **dessas faixas**, começando por evidências locais
existentes. Nenhuma busca de letras está embutida neste comando.

Fundamento e limites em `plano_nova_amostra_catalogo_v1.md`.
