# Changelog — Base v0.1 → v0.1.1

- A Base v0.1 foi recarregada do Parquet e permaneceu imutável.
- Criados identificadores determinísticos de artista, composição e grupo de split.
- Criado split agrupado 75/25 com `random_state=42`.
- Confirmados 209 descritores; corrigida documentalmente a classificação preliminar de 231 campos.
- Removidas 12 preditoras constantes da matriz controlada, sem apagar as colunas da auditoria.
- Separadas matriz de modelagem, atribuições de split e auditoria de matching.
- Criado manifesto definitivo e amostra de revisão humana com campos vazios.
- Nenhuma linha foi excluída; nenhuma ausência foi imputada; nenhum modelo, PCA, embedding ou coleta de letras foi executado.
