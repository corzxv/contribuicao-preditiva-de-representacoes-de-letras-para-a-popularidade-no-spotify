# Plano de revisão estatística — V0.7

## Estado e limites

Este é um plano, não uma execução. A V0.6 permanece a primeira avaliação concluída; modelos, features, split e resultados não foram modificados. O Tradicional continua candidato predefinido. Nenhuma proposta abaixo foi treinada, calibrada ou validada nesta etapa.

Objetivo mantido: contribuição preditiva incremental de descritores líricos para a popularidade observada no snapshot, além de áudio/metadados. A unidade operacional é uma composição representada por um track_id; o alvo pertence a essa faixa, não a todas as suas versões. Não inferir causalidade nem sucesso comercial futuro.

## Até três intervenções prioritárias

### 1. Qualidade de identificação, versões e cobertura, antes de novos algoritmos

- Problema: somente 111.758 de 1.159.764 faixas têm matching aceito (9,64%); a preferência por original atua somente entre esses aceitos. São consultadas 15.000 de 111.422 composições elegíveis e aceitas 10.240 letras. A maior perda dentro do universo integrado é a limitação amostral; a maior perda desde a fonte é anterior, no matching. As duas não são corrigidas por trocar o regressor.
- Evidência: taxa de aceite decresce entre chaves com uma e muitas versões. Há contexto de versão sem flags em 1.246 títulos da fonte, 78 integrados e 4 finais (candidatos a revisão, não erros adjudicados). A regex live reconhece a palavra também quando faz parte do título. `year` não identifica inequivocamente primeiro lançamento; o registro lírico genérico live não confirma a apresentação específica. Os detalhes dos três casos estão privados.
- Proposta posterior: revisão cega ao alvo de uma amostra de pares e versões, com rótulos humanos e critérios documentados; distinguir composição, gravação, lançamento e letra; corrigir regras de flags/aliases em uma NOVA versão com proveniência. Não simplesmente relaxar o 1:1: qualquer adjudicação de múltiplos candidatos deve ter critério verificável e preservar rejeitados. Manter análises de sensibilidade entre matches mais fortes e o universo comum, sem excluir retrospectivamente casos por erro.
- Custo aproximado: moderado, da ordem de 2–4 dias de trabalho humano para desenhar e revisar um primeiro lote pequeno; estimativa de planejamento, não tempo medido nem compromisso. As verificações de metadados locais são baratas; estabelecer verdade de gravação pode exigir documentação hoje ausente. Nenhuma consulta externa autorizada por este plano.
- Critério: concordância entre revisores, proporção de pares confirmados/duvidosos, recuperação de cobertura por estrato e preservação do agrupamento, medidos sem observar y. Antes de modelar, congelar nova elegibilidade e registrar quantidades. Não otimizar regras para os três casos relatados.

### 2. Uma alternativa não linear compacta para o Baseline

- Problema: year entra linearmente; os dados têm forte estrutura por gênero/período e cobertura desigual. Erros aumentam nos alvos altos e no período mais recente; categorias estão conhecidas e os três casos não extrapolam limites univariados, portanto não se explicam simplesmente por categoria inédita ou imputação.
- Evidência: MAE Tradicional no teste 8,6411 em 2020–2023 (n=77) versus 7,0209 em 2000–2009 (n=713); a decomposição privada mostra peso relevante de year/genre. Essas comparações não isolam um efeito temporal causal e não provam que a relação verdadeira seja não linear.
- Proposta posterior: um único braço com spline de baixa dimensão para year, mantendo características acústicas, categóricas e controle Elastic Net congelado como referência. Fixar antecipadamente uma grade pequena de complexidade e penalização e ajustar qualquer transformação somente nos treinos pertinentes. Avaliar eventual interação só se pré-especificada; não abrir busca ilimitada de algoritmos.
- Custo aproximado: baixo a moderado, uma implementação de 1–2 dias e execução de ordem semelhante a poucos ajustes lineares, com teto de recursos definido antes. Não há benchmark de tempo deste braço.
- Critério: MAE OOF agrupado por artista/composição como primário; RMSE, R², P90/P95, frequência >20, estabilidade por fold e por período como secundários. Comparação pareada na mesma coorte; não mudar a elegibilidade para favorecer o braço. Exigir ganho previamente definido como útil e incerteza agrupada, não apenas uma diferença numérica favorável.

Boosting não é prioridade automática: já foi considerado nos pilotos e excluído como principal no protocolo final. Os dados atuais não demonstram que novo boosting superaria um braço não linear compacto. Uma comparação futura só deve substituir, e não multiplicar, braços deste orçamento, mediante justificativa documentada independente do resultado do holdout.

### 3. Alinhar a função de ajuste à métrica primária e limitar a revisão textual

- Problema: Elastic Net ajusta perda quadrática, mas o modelo foi selecionado por MAE. A alta correlação entre blocos e os pequenos incrementos indicam que repetir embeddings mais caros sem hipótese específica pode ter baixo retorno.
- Evidência: no teste, correlações Baseline–Tradicional/Profundo/Combinado = 0,9842 / 0,9810 / 0,9689; mudanças médias absolutas de previsão = 1,4654 / 1,5240 / 1,9860 pontos. Tradicional melhora MAE em apenas 0,019798 ponto. A dispersão prevista é menor que a observada, mas médias condicionadas à previsão acompanham razoavelmente a identidade nas faixas centrais. Condicionar pelo alvo alto não basta para justificar calibrador.
- Proposta posterior: um braço linear regularizado de regressão quantílica τ=0,5 (perda absoluta), com o mesmo desenho de features e transformação ajustada dentro do treino. Comparar primeiro no Baseline e, apenas se o critério pré-definido permitir, no Tradicional; uma grade pequena. A mediana condicional é coerente com MAE, mas pode não melhorar RMSE ou a cauda. Não usar calibração ad hoc no holdout e não aplicar clipping para ocultar extremos.
- Custo aproximado: moderado; 1–2 dias de implementação/checagem e potencial custo de otimização maior que o Elastic Net. Definir timeout e limite de iterações; não estimar ganho ou horas de CPU sem benchmark.
- Critério: MAE OOF agrupado, com piso de relevância definido antes, acompanhado de RMSE, quantis de erro e proporção >20. Eventual benefício deve persistir entre folds, sem escolher exemplos ou cortes retrospectivos.

Representação textual: não recalcular embeddings agora. PCA90 conserva variância de X, não diretamente sinal de y; isso é limitação, não evidência de que remover PCA ou trocar encoder melhoraria resultados. Primeiro confirmar alinhamento lírico da intervenção 1. Um ensaio textual posterior precisaria de hipótese limitada e substituir um braço deste plano, sem inflar tentativas. Também não se justifica ponderar observações pelo alvo alto apenas porque os casos discutidos erraram: isso alteraria o objetivo da estimação e exigiria protocolo próprio.

## Ampliar a amostra: o que pode e não pode resolver

Mais registros do mesmo processo podem reduzir variância e aumentar n de gêneros raros, mas repetem o filtro de matching e disponibilidade. Não recuperam músicas ausentes da fonte nem provam correspondência entre gravações/letras. A coorte contém 10.117 letras em inglês de 10.240, conforme relatório V0.4, outra limitação de generalização.

Mesmo recuperar todos os 657 request_error, se todos viessem a ser aceitos, seria um teto de 657 composições adicionais naquela coleta, não solução para 1.048.006 faixas sem matching aceito. Isso é limite aritmético, não previsão de recuperação. Não reconsultar nesta etapa. Expansão deve ser target-free, versionada e motivada por cobertura, com denominadores por estrato e sem seleção por popularidade conhecida.

## Avaliação futura e independência

1. OOF V0.5 e holdout V0.6 já informaram este diagnóstico. Resultados de revisões no mesmo material serão exploratórios. A V0.6 original permanece válida como registro da primeira avaliação pré-especificada; não usar novamente suas métricas para afirmar confirmação independente das revisões.
2. O inventário sem alvos encontrou 25.213 representantes em 8.341 grupos sem uso conhecido nos pilotos/modelos finais ou no preview histórico de 100 linhas, após excluir componentes compartilhados. Excluindo também os grupos de toda a coorte/reserva V0.4, restam 17.275 representantes em 7.102 grupos: 12.304/5.161 no split de desenvolvimento e 4.971/1.941 no split de holdout. Do preview foi lida exclusivamente a coluna track_id, sem alvos/proxies. Nenhum alvo dos candidatos foi aberto nesta etapa e nenhum novo teste foi sorteado.
3. Esses números NÃO certificam um holdout virgem. A fonte e a base foram perfiladas agregadamente nas etapas iniciais; as regras de integração também foram desenhadas com esse catálogo. Existem ainda workbooks de preview/revisão e JSON de head anteriores: foram inventariados, mas seus alvos não foram abertos nesta etapa; a extensão de inspeções manuais não está certificada. Inspeção agregada não equivale automaticamente a treino individual, mas requer histórico de exposição e ressalvas antes de alegar independência. Reshuffle dos registros já examinados não restaura independência.
4. Preferência: validação externa ou prospectiva com protocolo, universo elegível, orçamento, famílias de modelos, transformação, métricas e regra de decisão congelados antes da abertura. Resolver IDs/aliases e sobreposição por artista, composição e gravação sem olhar y. Se possível, separar custódia dos alvos da equipe de desenvolvimento. O snapshot do alvo precisa ser comparável; mudança temporal pode mudar o próprio estimando.
5. Alternativa local condicional: somente grupos com inventário de uso e exposição auditado, regra de elegibilidade pré-registrada e alvo sob custódia independente. Sem essa evidência, rotular a avaliação como exploratória. Não inferir que toda exposição agregada invalida necessariamente uma avaliação, nem prometer independência não demonstrada.
6. Dentro do material de desenvolvimento já autorizado, usar CV agrupada/nested para limitar otimismo de seleção. Registrar todos os braços e falhas; não iterar indefinidamente até um resultado favorável. Fixar antes o limiar de relevância prática, métricas secundárias, tolerâncias e método de incerteza por artista. Nenhuma escolha aqui habilita novo treinamento sem autorização.

## Especificação futura de navegação — não implementada

- Filtros encadeados: gênero da fonte → artista em ordem alfabética determinística → música/versão, também em ordem determinística. Manter busca livre por artista ou título, com mesma normalização de caixa/acentos.
- Usar o catálogo completo do holdout congelado, sem ordenar por acerto, popularidade ou erro. Mostrar versões e rótulo explícito “ano informado pela fonte”, sem alegar ano original. Permitir limpar filtros e ver quantidade de resultados.
- Mudanças de filtro/seleção apagam previsão e observado. Primeiro estimar, depois revelar em botão separado; nunca incluir o alvo nas features.
- Separar visualmente “métricas globais oficiais V0.6” de “erro absoluto desta faixa”. MAE não é intervalo individual, chance de sucesso nem porcentagem de acerto.
- Preservar aviso acadêmico, execução local e ausência de upload/coleta para músicas novas. Sem letras completas, caches ou vetores expostos.

## Evidências e decisão de prosseguir

O diagnóstico agregado, CSV, run summary e dossiê privado são a referência. Não há garantia de melhoria por nenhuma das três intervenções. Antes de executar uma nova rodada, aprovar um protocolo curto com universo, prioridade, orçamento e custódia do próximo teste. Nenhum artefato científico V0.4–V0.6 deve ser sobrescrito.
