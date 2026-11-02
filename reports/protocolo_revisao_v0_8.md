# Protocolo pré-execução — revisão estatística exploratória V0.8

## Autoridade, escopo e isolamento

Autoridade: solicitação específica V0.8. A proposta antiga da V0.7 não orienta esta execução. Rodada exploratória motivada depois da abertura do teste V0.6, mesmo usando exclusivamente desenvolvimento; não é confirmação independente nem nova avaliação do holdout. Não substituir o candidato Tradicional, os modelos congelados ou o demonstrador.

Usar exatamente as 7.648 composições, representantes, alvos e grupos da matriz V0.5. Ler dados tabulares exclusivamente de `data/derived/private_final_development_v0_5/development_matrix.parquet`, `fold_assignments.parquet` e das cinco colunas de previsões de referência, chaves, grupos, alvo e fold de `oof_predictions.parquet`. Não carregar dados, previsões individuais ou alvos do holdout, casos individuais V0.7, bases anteriores ou novos alvos. Manifestos, código e relatórios públicos V0.5–V0.7 são documentação. Nenhuma coleta ou rede.

Congelar SHA-256 deste protocolo e do código executor antes do primeiro ajuste, inclusive o teste técnico. Congelar hashes das três entradas e do manifesto V0.5. Conferir referências contra as métricas V0.5 (tolerância absoluta 1e-10, relativa zero). Preservar arquivos preexistentes rastreados/pessoais e relatórios por SHA-256; modelos congelados V0.5 por SHA-256; inventário de tamanho/mtime_ns de todos os dados preexistentes, sem abrir holdout ou letras. Hash de bytes não desserializa modelos. Nenhuma escrita em caminhos antigos, commit, push ou staging. Novas saídas privadas somente em `data/derived/private_statistical_revision_v0_8/`, já ignorado pelo Git.

## Coorte, folds e transformações

Reutilizar os cinco folds externos **e os três internos de cada treino externo já persistidos** na V0.5 (`inner_outer_0` a `inner_outer_4`, sentinela -1 fora do treino). Seed V0.5: 20261013; geração histórica interna: 20261013 + 1000 + fold. Nenhum novo sorteio. Verificar alinhamento por composição, representante, grupo e alvo; unicidade; disjunção de grupos de artista e de composição; cobertura completa e finita. O alvo é separado de X antes de toda transformação.

Listas e ordem exatas de `reports/final_model_manifest_v0_5.json`: Baseline 23; Tradicional 23+196; Profundo 23+384; Combinado 23+196+384. Identificadores, artista, título, proxies de sucesso, matching e variáveis técnicas não entram em X. Flags de versão são as oito semânticas já autorizadas na V0.5; não recalculá-las. Não recalcular descritores nem embeddings.

Reutilizar somente as **fábricas não ajustadas** de transformação da V0.5/V0.3.1. Numéricas Baseline: mediana com indicadores e keep_empty_features, StandardScaler. Categorias genre/key/time_signature: moda e one-hot denso float64, categorias desconhecidas ignoradas. Mode/flags binárias. LFM2b: mediana com indicadores, remoção de constantes, StandardScaler, PCA full SVD com n_components=0.90, StandardScaler dos scores. MiniLM: igual, sem indicadores. PCAs separadas. Remover constantes depois de concatenar. Fit/fit_transform de cada transformação **somente** nas linhas do treino interno ou externo pertinente; validações só recebem transform. Nunca carregar transformadores já ajustados na V0.5.

Para boosting usar a mesma representação densa, inclusive one-hot e PCAs, com year linear antes das árvores; `categorical_features=None`, pois categorias já estão explicitamente codificadas. Não introduzir encoder nativo alternativo. Escalonamento preservado para manter a representação. Matrizes densas float64 finitas, sem informação adicional. Para spline, retirar somente year do ramo numérico e adicionar mediana (keep_empty_features), SplineTransformer cúbico e StandardScaler das bases. Year não tem ausentes nesta coorte; isso é condição verificada, evitando diferença de indicadores. `knots='uniform'`, `include_bias=False`, `extrapolation='constant'`; nós derivados exclusivamente do treino.

## Grades fechadas e seleção

Família `spline_en`, por bloco: produto ordenado n_knots=(3,5), alpha=(0.003,0.03,0.3), l1_ratio=(0.8,0.95), total 12 configurações. ElasticNet fit_intercept=True, tol=0.001, selection='cyclic', seed=20261013, max_iter=50000, precompute=True. Se houver ConvergenceWarning, repetir a mesma configuração com max_iter=200000 e depois 500000; registrar todos os warnings. Recusar ajuste ainda não convergido. Sem interações manuais, warm start ou outra grade.

Família `hist_gb`, por bloco: produto ordenado loss=('squared_error','absolute_error'), max_leaf_nodes=(15,31), l2_regularization=(1,10), total oito configurações. learning_rate=0.05, max_iter=200, min_samples_leaf=20, early_stopping=False, random_state=20261013, categorical_features=None. Demais padrões da versão instalada registrados no resumo; nenhuma adaptação de grade após resultados.

Seleção por menor média aritmética dos três MAEs internos, pesos iguais entre folds; empate exato pela ordem fixa acima. Configuração com erro, previsão não finita ou falha de convergência em qualquer fold interno fica inelegível e é registrada, sem trocar dados ou remover observações. Se nenhuma elegível, interromper o bloco e relatar, sem ampliar grade. Falha de refit externo interrompe a execução, sem substituição orientada pelo resultado externo.

Orçamento: 720 ajustes internos spline (12×4×5×3) + 480 boosting (8×4×5×3), mais 40 refits externos (2×4×5). Retentativas numéricas de convergência são contadas separadamente. Persistir 40 pipelines de folds e previsões completas; não selecionar nem ajustar novo modelo final no desenvolvimento completo. As quatro referências Elastic Net e o Dummy usam somente OOF salvas, sem refit.

## Teste técnico e recursos

Antes da execução integral, no treino interno 0 do fold externo 0, bloco Combinado: três ajustes técnicos fixos, spline n_knots=5/alpha=0.003/l1_ratio=0.8 e boosting max_leaf_nodes=31/l2_regularization=1 para cada uma das duas perdas. Registrar somente tempo, dimensões, warnings e finitude, sem usar desempenho para modificar o desenho. Extrapolar custo aproximadamente; variação entre blocos/folds e carga da máquina impedem garantia de prazo.

Execução sequencial dos blocos/folds; candidatos internos em até quatro processos loky, um thread numérico por processo. Processos separados isolam captura de warnings. Paralelismo não modifica grade, seed ou seleção. Reutilizar representações somente no mesmo conjunto exato de treino/validação, bloco e n_knots, com hashes das entradas/código/protocolo. Cache em memória do treino corrente; checkpoints privados por modelo/fold possibilitam retomada validada por selo, sem reaproveitar ajuste global ou misturar folds. Registrar tempos de pré-processamento, ajuste, inferência e tempo de parede; somas de CPU/tempos de tarefas paralelas não são tempo de parede.

## Métricas, comparações e regra operacional

Para todos os 13 vetores (oito novos, quatro Elastic Net e Dummy): métricas globais OOF e por fold, n, MAE, RMSE, R², mediana/P90/P95 de |erro| (quantis NumPy, interpolação linear), proporções |erro|≤5, ≤10, ≤20 e >20; contagem >20 e previsões fora de 0–100. Previsões brutas, sem clipping, calibração, pesos pelo alvo, oversampling ou exclusões. MAE não é intervalo individual, probabilidade ou porcentagem de acerto.

Oito comparações de algoritmo: cada novo pipeline menos Elastic Net V0.5 do **mesmo bloco**. Seis comparações incrementais: Tradicional, Profundo e Combinado menos Baseline **da própria nova família**. Deltas positivos de erro significam piora. Distinguir esses dois tipos; redução por algoritmo não prova contribuição das letras.

Promissor para avaliação posterior: redução de MAE OOF ≥2% contra a referência correspondente, MAE estritamente melhor em ≥4/5 folds, RMSE e P95 não mais de 2% piores. Comparações incrementais também mostram os componentes da regra, mas a classificação de candidato usa a referência V0.5 correspondente. Limiar operacional, não universal, não teste de significância, não garantia de utilidade. Reportar todos os modelos e explicitar reduções de MAE acompanhadas de piora de RMSE, P95 ou frequência de erros >20. Não encerrar cedo por resultado de um modelo.

Análises exclusivamente descritivas, definidas antes: faixas do alvo [0,10), ...,[80,90),[90,100]; períodos year <2000, 2000–2004, 2005–2009, 2010–2014, 2015–2019, 2020–2023, ≥2024; presença/ausência de qualquer das oito flags e de cada flag individualmente. Mostrar n, grupos de artista, identificar n<30 (inclusive n=0) e reportar as mesmas métricas **sem R² por estrato**. Grupos pequenos não sustentam comparação estável. Year é o campo da fonte, não data original da composição certificada. Flags não são rótulos humanos de versão. Não usar estratos para selecionar modelos ou casos.

Não calcular intervalos, p-valores ou bootstrap nesta rodada. Validação aninhada limita vazamento no ajuste, mas não desfaz a motivação pós-holdout nem torna escolhas exploratórias confirmação independente. Nenhum exemplo individual selecionado por erro.

## Entregas e verificação

Gerar `revisao_estatistica_v0_8.md`, `revisao_estatistica_metricas_v0_8.csv`, `revisao_estatistica_comparacoes_v0_8.csv` e `run_summary_revisao_v0_8.json` em reports. CSV de métricas inclui global/fold/estratos e contagens; JSON público contém somente agregados, hashes, configurações, auditorias e execução. Predições, índices, identificação de linhas, modelos, eventos de ajuste e checkpoints ficam privados. Não alterar .gitignore ou forçar inclusão de CSV (regra preexistente ignora CSV); nenhum dado privado deve estar rastreado ou staged.

Testes sintéticos: grades fixas, factory de modelos, input sem alvo, transformações train-only inclusive nós/categorias/PCA, isolamento de grupos e alinhamento, seleção exclusiva pelo MAE interno, regra operacional e limites, política de falhas, integridade de selo, bloqueio de leitura tabular externa e escrituras fora das saídas V0.8. Verificação real: referências reproduzidas, 7.648 linhas×oito previsões finitas, uma validação externa por linha, 40 modelos de fold preservados e conferência das suas previsões OOF, hashes/metadata anteriores intactos e privacidade Git. Executar Ruff, formatação e testes pertinentes; registrar comandos e códigos de saída.
