# Diagnósticos descritivos das previsões externas — v1 (02/11/2026)

## Ordem e alcance

Protocolo escrito **depois da leitura das métricas globais do script 22**, antes
de calcular os diagnósticos por fold/subgrupo. Não é pré-registro da comparação
principal. Não modifica os 77.535 casos, resposta, modelos, pesos, grade ou folds.
Executa somente auditoria/reprodução de métricas e diagnósticos condicionais às
previsões externas existentes. Sem ajuste, encoder, novo split, bootstrap, IC ou
p-valor. A execução integral permanece manual pelo pesquisador.

## Integridade e reprodução

Exigir 22 integral concluído, 20 partes Ridge, dez referências, zero pendências,
77.535 previsões por variante e fontes/selos preservados. Conferir hash do arquivo
global e códigos/protocolo 22, igualdade 1:1 por track_id entre previsão e base 21,
componentes, resposta, pesos e folds. Auditar grupos dos folds existentes.

Ler partes e conferir hashes de modelos/previsões sem desserializar joblib:
previsão global deve ser idêntica à previsão da parte externa correspondente.
Conferir alpha publicado contra manifesto/grade e referências contra média/mediana
do respectivo treino externo. Reproduzir MAE/RMSE/R², MAE ponderado e cinco
contrastes publicados, tolerância absoluta 1e-9 para arredondamento numérico.
Sem aplicar clipping às previsões ou corrigir resultados silenciosamente.

## Estabilidade empírica

Resumir métricas dos seis modelos por fold externo (mesmas faixas entre blocos).
Não usar cinco números como réplicas independentes para teste t ou IC ingênuo.
Persistir privadamente, por componente: fold, n, soma de pesos, soma dos erros
absolutos e dos erros absolutos ponderados de cada variante. IDs de componentes
nunca são preditores nem aparecem em relatórios públicos.

Para cada um dos cinco contrastes pré-fixados em 22, calcular o delta global de
MAE e seu mínimo/máximo ao retirar **um componente da avaliação**, mantendo todos
os modelos e previsões fixos. Fórmula não ponderada: (D-d_g)/(N-n_g), onde D é
soma das diferenças de erros absolutos, d_g a parcela do componente e N/n_g as
contagens. Ponderada: (D_w-d_wg)/(W-W_g), com somas de pesos correspondentes.
Isso avalia influência dos casos observados, não retreina/retuna modelos.
Não chamar esse intervalo de IC ou validação leave-one-group-out. Não resolve
incerteza do treinamento ou correlação entre predições de ajustes sobrepostos.

## Subgrupos exploratórios

Dimensões fixadas antes de ler os seus erros: lyrics_language_status,
lyrics_detected_language, sampling_popularity_band, sampling_period, model_genre
e status de exposição por componente. Manter níveis originais; nulo recebe nível
__MISSING__. Não excluir idiomas/casos, redefinir faixas de popularidade ou
escolher cortes pelos resultados. Idioma é estimativa automática.

Status por componente: detected_collision se houver qualquer flag de ID avaliado,
colisão de composição ou artista v0.6 em qualquer membro; caso contrário,
unknown_key se qualquer membro tiver readiness_unknown_group; nos demais,
no_detected_collision. Não confundir chave desconhecida com ausência de colisão,
nem ausência de detecção com independência garantida. As flags originais são
preservadas na base; esse diagnóstico não restaura teste independente nem cria
novo universo principal. A exposição histórica continua declarada.

Métricas de subgrupos são publicadas apenas com >=100 faixas e >=20 componentes;
células abaixo disso têm somente identificação do nível/contagens/motivo em
celulas_pequenas.csv. Limiares são regra operacional de legibilidade/estabilidade,
não certificado de precisão/poder estatístico. Não se aplicam aos folds completos.
Todas as faixas continuam na métrica global. Não fazer testes múltiplos ou
concluir superioridade populacional por subgrupo nesta etapa.

Contar previsões abaixo de zero/acima de 100 e seus extremos, sem alterar o
estimador congelado. Contar seleções de alpha nos extremos da grade, sem expandi-la
com base em desempenho externo já conhecido. São limites/diagnósticos, não novas
oportunidades de escolher retrospectivamente a melhor métrica.

## Inferência e saídas

O domínio é observado, não representativo presumido do catálogo. MAE ponderado
permanece sensibilidade dos mesmos modelos/previsões, não correção de disponibilidade
textual. Resultados dos diagnósticos são descritivos/exploratórios. Eventual
inferência posterior deverá declarar estimando e hipóteses e respeitar dependência
da CV. [Bengio e Grandvalet (2004)](https://www.jmlr.org/papers/v5/grandvalet04a.html)
mostram limitações de estimadores de variância de K-fold CV e o risco de ignorar
correlações dos erros; isso não impede todo método aproximado, mas impede tratar
os folds como independentes por conveniência.

Workspace privado novo: perdas_componentes.parquet e owner.json. Públicos:
resumo_diagnosticos.json, relatorio_diagnosticos.md, metricas_reproduzidas.csv,
diagnosticos_subgrupos.csv, sensibilidade_remocao_componente.csv,
previsoes_fora_intervalo.csv e celulas_pequenas.csv (quando houver). Não versionar
previsões individuais, modelos, letras ou IDs. Selo próprio de fontes/código/
protocolo, sem editar os selos anteriores. Nenhum treino/experimento é iniciado
ao finalizar. Resumo concluído publicado por último; divergência bloqueia.
