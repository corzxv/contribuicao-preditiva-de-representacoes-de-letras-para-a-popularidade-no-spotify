# Execução manual da classificação ordinal — 05/11/2026

Estado vigente D-027: produção integral concluída e conferida. NÃO repetir 34.
35 agregados/PCA/figuras e 36 sensibilidade concluídos; 37 consolidou os resultados.
Próximo é escrita/discussão, sem novo comando pesado. Comandos de 34 abaixo são históricos.

Estado mais recente: primeiro lote real concluído e conferido em 105,42 s,
1/20 partes. Próximo é o comando all sem limite para retomar as dezenove restantes.
Para deixar rodando: notebook na tomada e sem suspensão/hibernação automática;
internet e SSD LRCLIB não são necessários. Ao concluir deve aparecer [4/4] Concluído.
Se houver interrupção, repetir o comando inalterado reutiliza checkpoints.

Atualização: smoke real concluído e conferido, 318 faixas, quatro partes e recarga
exata (diferença 0,0). Gate aprovado. Próxima execução: primeiro lote de produção
com all --limit-outer-blocks 1, conforme comando abaixo. Não repetir smoke.

31 e 32 concluídos pelo pesquisador; triagem 33 executada pelo agente em 133
fichas pequenas. Não repetir essas etapas. Vínculos atuais preservados; revisão
semântica humana permanece pendente. Código 34 preparado/testado com fixtures.

## Próximo comando: somente smoke

```powershell
& "C:\Users\Concursos Felipe\Documents\UnB\TCC\.venv\Scripts\python.exe" "C:\Users\Concursos Felipe\Documents\UnB\TCC\scripts\34_classificar_niveis_popularidade.py" smoke
```

Este é o primeiro ajuste real do novo classificador. O pesquisador executa.
Reutiliza dados/vetores locais; não exige rede, SSD LRCLIB, encoder ou pacote
novo. Até 1.200 faixas de componentes inteiros, sem seleção pelo alvo, seguindo
subcoorte determinística do smoke anterior. Quatro blocos e externo 0; seleciona
penalização e opção PCA dentro dos folds internos. Tem logs por ajuste concluído.

Critérios: resumo completed=true, quatro partes externas concluídas,
global_metrics_available=false e reload_max_abs_difference≤1e-10. Não interpretar
o desempenho dessa subcoorte como resultado científico. Enviar a última saída e
conferir reports/classificacao_ordinal_200k_v1/smoke/resumo_classificacao.json.
Agente analisa antes de iniciar produção. Se houver erro, preservar arquivos e
enviar traceback; não mudar parâmetros nem apagar owner/estado.

## Produção posterior, após conferir o smoke

Primeiro lote limitado:

```powershell
& "C:\Users\Concursos Felipe\Documents\UnB\TCC\.venv\Scripts\python.exe" "C:\Users\Concursos Felipe\Documents\UnB\TCC\scripts\34_classificar_niveis_popularidade.py" all --limit-outer-blocks 1
```

Medir custo/convergência antes da escala. Parcial por limite retorna código 2,
com completed=false, mantendo resultados. Depois de analisar esse lote, retomada:

```powershell
& "C:\Users\Concursos Felipe\Documents\UnB\TCC\.venv\Scripts\python.exe" "C:\Users\Concursos Felipe\Documents\UnB\TCC\scripts\34_classificar_niveis_popularidade.py" all
```

Cada ajuste interno confirmado é reutilizado pelo SQLite. Cada parte externa
inclui modelo/transformador, probabilidades e JSON com hashes. Ctrl+C pode perder
apenas o ajuste em andamento, não os já confirmados. Repetir comando inalterado.
Código/protocolo/configuração/fontes diferentes bloqueiam reuso; não contornar.

## Saídas e alcance

Privados: data/derived/private_ordinal_classification_200k_v1/, com estado,
modelos e probabilidades. Públicos: reports/classificacao_ordinal_200k_v1/,
somente configurações e agregados. Produção completa: vinte partes externas
ordinais e cinco referências, 77.535 previsões por variante. Sem ajuste ponderado,
sem retreino de embeddings, sem seleção de cortes por resultado.

Acurácia balanceada primária; probabilidades e calibração complementares.
Ponderação original apenas na avaliação das mesmas previsões. Protocolo:
protocolo_classificacao_ordinal_200k_v1.md. Resultados Ridge, PDFs e folds anteriores
permanecem. Classificação ordinal não certifica causalidade, cobertura do catálogo
ou validade semântica de todos os vínculos. Chances proporcionais é hipótese do
modelo, não achado já demonstrado. Novo algoritmo não restaura teste independente.
