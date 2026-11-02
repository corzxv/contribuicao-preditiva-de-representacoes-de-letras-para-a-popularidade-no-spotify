# Execução manual da amostra Spotify 200k

Código preparado; não executado sobre o catálogo real pelo assistente.
O protocolo está em `docs/plano_amostral_200k.md` e será copiado para a saída.
Python e dependências já existentes; nenhuma instalação ou consulta externa na CLI.

```powershell
& "C:\Users\Concursos Felipe\Documents\UnB\TCC\.venv\Scripts\python.exe" "C:\Users\Concursos Felipe\Documents\UnB\TCC\scripts\12_sortear_amostra_spotify_200k.py" --input "C:\Users\Concursos Felipe\Documents\UnB\TCC\data\raw\spotify\spotify_data.csv" --audit "C:\Users\Concursos Felipe\Documents\UnB\TCC\reports\auditoria_catalogo_spotify_20261031\resumo_catalogo_spotify.json" --output "C:\Users\Concursos Felipe\Documents\UnB\TCC\reports\amostra_spotify_200k_20261031"
```

A CLI fixa 200.000 e seed 20261031, sem opções para buscar outras combinações.
Lê o CSV como strings para preservar todos os campos, mantém uma projeção
analítica estreita e converte uma variável numérica de cada vez nas comparações.
A ordenação do sorteio usa somente ID/estrato/posição; não ordena cópias de todo
o catálogo. Usa memória RAM proporcional ao CSV; reserve espaço/memória para a
tabela textual e a amostra. Falta de recurso não autoriza diminuir o total.

O processamento confere hash/tamanho contra o JSON da auditoria, reconta e
reconcilia população, IDs e 499 faixas ≥80, valida domínios e só então sorteia.
Não executa novamente a auditoria completa, nem usa seus classificadores de versão.
O Parquet mantém todas as colunas originais como texto, inclusive cabeçalho vazio;
os nomes do desenho e campos `sampling_*` são adicionais.

Produtos na pasta `reports/amostra_spotify_200k_20261031/`:

- `plano_amostral_200k.md`: protocolo e referências.
- `alocacao_amostra_200k.csv`: uma linha por estrato, reservas/restos, N_h/n_h,
  probabilidades e pesos.
- `amostra_spotify_200k.parquet`: dados individuais locais; não enviar nem versionar.
- `comparacao_catalogo_amostra_200k.csv`: agregados longos em três escopos.
- `relatorio_amostra_200k.md`: resultados reais, contagens complementares e limites.
- `resumo_amostra_200k.json`: configuração, hashes, versões, verificações e status.
- `comparacao_popularidade_200k.png`, `comparacao_genero_200k.png`,
  `comparacao_periodo_200k.png`: comparação de percentuais; gênero mostra os
  20 maiores e o CSV contém todos. Popularidade inclui tabela das faixas raras.

`count` é soma dos pesos (contagem simples nos escopos com pesos 1);
`n_observed` nunca é inflado. `fraction` está em 0–1. Nos momentos,
`weight_observed` é o denominador válido; o campo `denominator` é a população
total de referência do escopo. Células sem valor não são zero. Categorias de
popularidade 0–100, anos e bandas têm zeros explícitos quando não observadas.
O CSV não contém nomes de artistas, títulos ou IDs individuais.

No JSON, exigir `status: completed` e `completed: true`. Uma reexecução
idêntica na mesma pasta verifica os hashes e preserva a amostra; divergências
bloqueiam. Não apagar nem substituir saídas para buscar melhor equilíbrio.

Após executar, compartilhar protocolo, alocação, comparação, relatório, JSON e
os três PNGs; manter o Parquet individual local. Se falhar, enviar a mensagem
do terminal e o JSON incompleto quando existir. Nenhum arquivo real é gerado
como resultado observado durante a preparação do código.

Verificação limitada a fixtures:

```powershell
& ".venv\Scripts\python.exe" -m pytest "tests/test_catalog_sampling.py" -q -p no:cacheprovider --basetemp ".tmp/pytest_catalog_sampling"
& ".venv\Scripts\python.exe" -m ruff check "src/tcc_music_popularity/catalog_sampling.py" "scripts/12_sortear_amostra_spotify_200k.py" "tests/test_catalog_sampling.py"
& ".venv\Scripts\python.exe" -m ruff format --check "src/tcc_music_popularity/catalog_sampling.py" "scripts/12_sortear_amostra_spotify_200k.py" "tests/test_catalog_sampling.py"
```
