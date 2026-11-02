# Protocolo pré-ajuste — base ampliada e curvas de aprendizagem V0.9

## Escopo e autoridade

Revisão exploratória solicitada após V0.6–V0.8; não é confirmação independente. Investigar tamanho **e composição** do treinamento já disponível, sem interface, monografia, coleta, novos embeddings ou novas famílias de modelos. Preservar bases, splits, matching, flags, resultados, modelos e alterações pessoais anteriores. Não realizar commit, push ou staging.

Alvos podem ser lidos somente de `development_train` original. A leitura da base V0.1.1 será lazy, com filtro `split == 'development_train'` antes da projeção/coleta de alvos; a alocação será reconciliada por track_id, spotify_row_id e lfm_record_key com o split congelado. Do holdout original, ler apenas chaves/grupos e hashes já existentes, sem popularidade, proxies ou previsões. Não carregar alvos de registros do holdout que ficaram fora da V0.6. Nenhuma transferência de popularidade entre versões.

## Elegibilidade, identidade e representação

Matriz privada por faixa Spotify (track_id único), com alvo da própria faixa, IDs de origem, composição operacional, grupos, 23 inputs Baseline, 196 inputs LFM2b e indicadores documentais. Auditar ausência/duplicação de identificadores, relações entre chaves, ausência/não finitude de variáveis e alvos. Não imputar alvo nem excluir casos por popularidade alta/baixa ou erro. Registros sem composition_key ficam na matriz por faixa, com motivo de inelegibilidade para a visão por composição. Outros problemas de identidade ou alvo não finito devem ser registrados e interrompem ajustes quando afetarem uma comparação justa; não excluir silenciosamente.

Uma linha por composição na visão experimental, usando exatamente a função target-free de representantes V0.4: preferência sem live/remix/acoustic/karaoke, confiança do matching (status/método/score), completude de artista/título/duração, menor spotify_row_id e track_id. Aplicar somente a metadados sem alvo. Não exigir letra integral, cache, embedding ou status de coleta aceito. Reconciliar os representantes comuns com V0.5 e os selecionados com V0.4.

Track_id identifica a faixa/gravação da fonte; composition_key é chave operacional, não identidade universal da obra; flags são indícios de versão, não adjudicação humana. Year é somente ano informado pela fonte, não lançamento original certificado. Genre conserva a semântica limitada da fonte. Indicadores técnicos/matching/disponibilidade permanecem fora dos preditores. Listas e ordem vêm do manifesto V0.5: Baseline 23, Tradicional 219; lfm_entropy e proxies continuam proibidos.

## Validação e controles contra contaminação

Exatamente as 7.648 observações e as cinco atribuições externas V0.5/V0.8 constituem a validação fixa, uma vez por observação. Não redesenhar esses folds.

Para cada fold, treino comum original = todas as observações comuns dos outros quatro folds. Universo ampliado = todos os representantes elegíveis do desenvolvimento, excluindo grupos de artista, composition_key, composition_group_id e split_group_id da validação. Excluir também hashes de letra conhecidos na validação, tanto fingerprint estrito V0.4 quanto hash normalizado já registrado na matriz comum, sem abrir textos ou recalcular hashes. Grupos e hashes conhecidos do holdout original ficam fora de todo treino. Ausência de hash não causa exclusão: impossibilidade de detectar duplicação textual desconhecida será limitação explícita.

Auditar todas as partições **antes** do benchmark e dos ajustes. Treino comum original precisa permanecer completo e livre dessas sobreposições; discrepância interrompe em vez de alterar a referência. O máximo ampliado deve conter integralmente o treino comum original. As versões adicionais da mesma composição não viram novas observações de treino.

## Configuração fixa dos dois modelos

Elastic Net Baseline e Tradicional: valores dos ajustes finais V0.5, ambos alpha=0.003 e l1_ratio=0.95; fit_intercept=True, tol=0.001, selection='cyclic', random_state=20261013, precompute=True, max_iter=50000. Retentativas exclusivamente numéricas, na mesma configuração: max_iter=200000 e 500000 em ConvergenceWarning. Registrar warnings, falhas e tempos; persistência de não convergência bloqueia o resultado. Nenhuma busca de hiperparâmetros, spline, boosting ou novo encoder.

Transformações V0.5 criadas novamente em cada treino: numéricas Baseline → mediana, indicadores de ausência, keep_empty_features, StandardScaler; genre/key/time_signature → moda, one-hot denso, desconhecidas ignoradas; year linear, mode e flags binárias. LFM2b → mediana com indicadores, remoção de constantes, StandardScaler, PCA full SVD com 90% da variância do treino, StandardScaler dos scores. Remoção de constantes após concatenação. Todas as estatísticas e categorias ajustadas somente no treino correspondente; nunca reutilizar PCA/imputação global. Features não finitas serão auditadas antes dos ajustes, sem correção silenciosa.

## Subconjuntos, sementes e orçamento

Sementes fixas dos subconjuntos: **20261015 e 20261016**. Ordenar grupos de artista por SHA-256 de `v0.9|seed|artist_group_id`, desempate por ID. Nada de popularidade, nome conhecido, letra, resultado ou desempenho participa da ordenação.

Em cada universo elegível do fold, selecionar prefixos de grupos completos, com número cumulativo de composições mais próximo dos tamanhos solicitados; empate pela menor quantidade de grupos. A mesma permutação produz subconjuntos aninhados. Não cortar grupo para obter tamanho exato. Reportar n efetivo e número de grupos.

- Universo ampliado: aproximadamente 2.000, 5.000, 10.000, 20.000 e máximo elegível.
- Universo comum: controles de aproximadamente 2.000 e 5.000, além do treino comum original completo.
- Duas sementes para tamanhos parciais. Máximo ampliado e comum original completo executados uma vez quando idênticos entre sementes.
- Mesmas linhas de treino e validação para Baseline e Tradicional em cada condição.

O treino comum completo é a referência inicial. Os pontos de 2.000/5.000 são necessariamente menores que essa referência. Os prefixos do universo ampliado investigam quantidade/composição e não exigem conter todo o treino comum a cada tamanho parcial; **o máximo ampliado contém todo ele**. Comparações comum versus ampliado em 2.000/5.000 são controles de tamanho aproximado, não pareamento causal ou identidade de composição. Reportar diferenças efetivas de tamanho e sobreposição. Se um tamanho ultrapassar o universo, marcá-lo inviável, sem fabricar dados; não duplicar máximo disfarçado de tamanho parcial.

Orçamento esperado: por fold, 4 subconjuntos comuns (2 tamanhos×2 sementes), 8 ampliados (4×2), comum original e máximo ampliado = 14 condições×2 blocos×5 folds = **140 ajustes**, sem seleção. Não interromper por resultado favorável/desfavorável e não escolher a melhor semente.

## Benchmark, persistência e preservação

Antes dos ajustes integrais, executar dois testes técnicos fixos no fold 0: Baseline ampliado de aproximadamente 2.000, semente 20261015; Tradicional no máximo ampliado. Registrar tempos, dimensões e warnings, sem métricas de validação orientando protocolo. Estimar custo sem garantia de prazo. Execução sequencial, dois threads numéricos, checkpoints privados por condição/bloco/fold, retomada somente com hashes de protocolo, código, entradas, índices e configuração coincidentes.

Selar SHA-256 deste protocolo, configuração extraída do manifesto, código, entradas e plano de partições antes do primeiro ajuste real. Hashes anteriores: arquivos públicos/pessoais, dados de origem autorizados, matrizes/folds/predições/modelos de desenvolvimento V0.5–V0.8; demais dados por inventário tamanho/mtime_ns sem abrir letras, caches ou alvos do holdout. Distinguem-se hashes binários de leitura tabular de alvos. Todas as escritas ficam em novos artefatos V0.9.

## Cobertura e métricas

Comparar desenvolvimento integrado por faixa, representantes elegíveis, coorte principal V0.4, reserva disponível, principal+reserva efetivamente consultada, letras aceitas, matriz comum e composições adicionais. Discriminar seleção amostral, ambiguidades, not_found, instrumental e request_error. Identificadores/grupos individuais e distribuições por artista ficam privados; publicar distribuição de tamanhos dos grupos e número de artistas.

Distribuições: faixas [0,10),…,[90,100], limiares sobrepostos **≥60, ≥70 e ≥80**, gênero, ano informado, presença e cada flag, tamanho de grupo de artista e status de coleta. Informar denominadores e ausências; não somar os limiares sobrepostos nem grupos de flags. Nenhuma afirmação causal.

Métricas em cada validação fixa: MAE, RMSE, R², mediana/P90/P95 do erro absoluto (quantis lineares), proporções |e|≤5, ≤10, ≤20 e >20; contagem >20. Previsões brutas, sem clipping, calibração, pesos pelo alvo ou exclusão retrospectiva. Resultados por fold/condição/semente e OOF global reunindo exatamente as mesmas 7.648 observações. Reportar tamanhos de treino mínimo/médio/máximo entre folds, não somá-los como amostras independentes.

Curvas agregadas para cada semente e média de métricas entre sementes como resumo descritivo, sem escolher a melhor e sem intervalo de confiança a partir de apenas duas sementes. Máximos únicos serão identificados como tal. Descrever faixas do alvo com n e grupos pequenos (<30), sem R² nesses estratos. Reportar comparação com o treino comum original e Tradicional menos Baseline em condições idênticas. Nunca atribuir às letras um ganho devido a mais observações.

Interpretar tendência/estabilização pela sequência completa, variação entre sementes/folds e múltiplas métricas; nenhuma regra pós-hoc de promoção automática. A validação permanece condicionada à disponibilidade de letras: melhora nela não prova generalização para toda a base ampliada. Esta rodada não fornece confirmação independente pós-holdout.

## Entregas

Novos artefatos públicos solicitados em reports; gráficos agregados em `reports/figures/ampliacao_v0_9/`. Dados, planos com IDs, grupos, alvos, checkpoints e previsões somente em `data/derived/private_training_expansion_v0_9/`, ignorado pelo Git. Documentar dicionário e proveniência novos sem editar anteriores. Testes sintéticos, auditoria real dos grupos/inputs/transformações/OOF, integridade, Ruff e formatação; registrar comandos e códigos reais. Não executar testes antigos que leiam alvos fora do escopo.
