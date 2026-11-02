# Gerar descritores e componentes — execução manual

Pré-requisito concluído: auditoria 17, `completed: true`, 77.535 aceitas. Não
repetir busca/índices nem auditoria para continuar. Regras em
`contrato_representacoes_200k_v1.md`. Esta geração real ainda não foi executada
pelo agente; testes foram somente com textos/SQLite/Parquet sintéticos.

```powershell
& "C:\Users\Concursos Felipe\Documents\UnB\TCC\.venv\Scripts\python.exe" "C:\Users\Concursos Felipe\Documents\UnB\TCC\scripts\19_preparar_descritores_200k.py"
```

Funciona de qualquer pasta. Entradas:

- `C:\Users\Concursos Felipe\Documents\UnB\TCC\data\derived\private_readiness_200k_v1\linhagem_aceitas.parquet`
- `C:\Users\Concursos Felipe\Documents\UnB\TCC\data\derived\private_sample_lyrics_200k_v2\letras_aceitas_200k.parquet`
- `C:\Users\Concursos Felipe\Documents\UnB\TCC\reports\prontidao_dados_200k_v1\resumo_prontidao.json`

O comando valida os textos contra hashes/referências, extrai 21 descritores
lexicais/estruturais, guarda cache por hash do texto normalizado e constrói
componentes por artista/composição/texto. Lê textos em lotes, preserva originais,
pesos e todas as 77.535 linhas. Não aplica filtro de idioma ou instrumento e não
usa popularidade para extração/grupos. Não requer SSD, rede, modelos ou downloads.
Não gera embeddings, folds, previsões ou treinamento.

Após interrupção, repita o comando. Os hashes de fonte/contrato/código precisam
continuar iguais; caso contrário, bloqueia reuso. SQLite guarda cada texto concluído.
`--limit-texts 100` permite lote limitado de textos novos, mas a preparação/hashes
iniciais continuam. Código de saída 0 = concluído; 2 = limitado/parcial; falha de
integridade interrompe sem remover faixa. Não alterar os selos manualmente.
O terminal informa etapas e contagens; `progress.json` privado é um checkpoint,
não prova que o processo continua ativo.

Públicos em
`C:\Users\Concursos Felipe\Documents\UnB\TCC\reports\descritores_textuais_200k_v1\`:

- `resumo_descritores.json`
- `relatorio_descritores.md`
- `resumo_variaveis.csv`
- `tamanhos_componentes.csv`

Ao terminar, avise aqui; o agente pode conferir esses quatro agregados diretamente.
Não enviar `owner.json` nem dados individuais.

Privados em
`C:\Users\Concursos Felipe\Documents\UnB\TCC\data\derived\private_text_descriptors_200k_v1\`:
`state.sqlite`, `progress.json`, `coorte_descritores.parquet` e `indice_textos.parquet`.
Manter ignorados pelo Git. A matriz conserva campos de controle e alvo para
rastreabilidade, mas o treinamento futuro receberá somente a lista autorizada de
preditores; IDs, hashes, grupos, pesos e matching não são preditores desta etapa.

Critérios de conclusão: cardinalidade/IDs preservados, referências completas,
descritores finitos, nenhum campo original/peso alterado e componentes presentes.
Analisar grupos muito grandes/chaves não resolvidas antes de gerar folds. CV
aninhada agrupada 5×3 já foi aprovada, mas nenhum fold é criado por este comando.
Depois preparar o encoder multilingue com revisão congelada e teste pequeno;
nada deve ser executado automaticamente em escala.
