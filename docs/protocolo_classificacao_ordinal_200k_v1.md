# Classificação ordinal — v1, 05/11/2026 (D-026)

## Escopo e fontes

Continuidade autorizada em D-025. Diagnóstico 31 real concluído e suporte aprovado;
piloto 32 real concluído, com revisão semântica ainda pendente. Triagem técnica 33
é limitada às 133 fichas preparadas: nenhum vínculo é corrigido ou removido. Não
usar concordância automática de metadados como medida de precisão semântica.

Reutilizar as 77.535 observações, 21.893 componentes, 21 descritores, 384 dimensões
E5 e folds agrupados 5×3 selados. Loader da regressão é reutilizado sem alteração,
validando hashes/manifestos e alinhando vetores existentes. Não abre encoder,
letras, modelos antigos ou dump; não cria splits. A variante E5 com espaço
adicional permanece explicitamente a representação operacional utilizada.

Resposta principal: classes 0/1/2 com limites 20/40 aprovados em D-025. Nenhuma
busca de limites por desempenho. Sensibilidade 40/60 permanece nos diagnósticos
31; treino adicional desse alvo não é disparado nesta rotina. Avaliação da mesma
família nos quatro blocos Baseline, Tradicional, Profundo e Combinado.

## Modelo e implementação numérica

Chances proporcionais: P(C≤j|x)=sigmoid(theta_j−xβ), j=0,1. Limiar inferior a,
superior a+exp(d); três probabilidades ordenadas, sem pressupor distâncias iguais
entre níveis. Sem intercepto adicional em X; limiares não penalizados.

Objetivo: média da log-verossimilhança negativa por faixa + lambda ||β||²/2.
Pesos iguais no ajuste. Grade lambda = 0,001 / 0,01 / 0,1 / 1. L-BFGS-B com
gradiente analítico, até 1.000 iterações, gtol=1e-6 e ftol=1e-12. Restrição
numérica d∈[-8,8]; atingir borda ou gradiente final acima de 1e-4 bloqueia o
ajuste, assim como falta de convergência, probabilidades incoerentes ou avisos.
Não substituir silenciosamente candidato que falhou. Duas threads de álgebra.

Log-probabilidade da classe intermediária calculada de forma estável, evitando
subtrair sigmoides saturadas. Núcleo validado com diferenças finitas do gradiente,
verossimilhança independente baseada diretamente em diferenças de CDF e modelo
sem preditores que reproduz proporções. Implementação própria de verossimilhança;
otimização usa SciPy existente, sem adicionar biblioteca ou algoritmo externo.

Chances proporcionais é hipótese assumida, não conclusão do smoke nem teste
formal já aprovado. Reportar calibração por classe e limitações; eventual modelo
multinomial só com justificativa posterior e protocolo separado, sem fallback
automático para melhorar o resultado. Coeficientes penalizados não sustentam
causalidade, p-valores convencionais ou inferência de importância por magnitude.

## Pré-processamento e seleção interna

Em cada treino: numéricas Baseline com mediana/StandardScaler; categorias com
constante de ausência/one-hot e categorias novas ignoradas. Texto/embeddings em
bloco numérico separado, com mediana e padronização. Constantes removidas dentro
do treino. Nenhum peso/ID/grupo/idioma/status de vinculação entra como preditor.

Duas opções para as onze numéricas Baseline: sem PCA ou PCA retendo 95% de
variância padronizada, solver completo. PCA não atua nas categorias, descritores
ou embeddings. Imputação, escalas, PCA, constantes e vocabulário são ajustados
somente no treino interno/externo correspondente. Não escolher eixos na coorte toda.

Em cada treino externo, comparar oito configurações nos três folds internos.
Selecionar pela acurácia balanceada da matriz de confusão interna somada: média
das sensibilidades das três classes, sem média ingênua dos folds. Tolerância de
empate 1e-12; preferir penalização maior, depois ausência de PCA. Reajustar a
configuração escolhida no treino externo e avaliar uma vez na sua parte externa.
Decisão de classe por argmax; empate pela menor classe. Não ajustar limiares
de decisão no teste. Referência: probabilidades de classes do treino externo,
que também produz a classe majoritária por argmax.

Produção: 480 ajustes internos e vinte reajustes externos para quatro blocos,
além de cinco referências sem otimização. As opções de PCA são escolhas internas,
não novas famílias apresentadas como experimentos independentes. Grade não é
ótima demonstrada nem deve ser expandida após olhar métricas externas.

## Métricas, saídas e limites

Acurácia balanceada primária, com acurácia, macro-F1, precisão/sensibilidade por
classe e frequência de erros 0↔2. Complementares probabilísticas: log-loss com
piso 1e-15 na avaliação, Brier multiclasse e calibração descritiva em dez intervalos
fixos. Nenhum calibrador é ajustado nas previsões externas. Modelos e tabelas
individuais ficam privados; relatórios públicos contêm só agregados.

Sensibilidade: mesmas probabilidades/observações/folds com pesos amostrais originais
somente na avaliação; não selecionar modelo por ela nem interpretar como correção
da cobertura textual. Folds são descritos, não réplicas independentes. Sem IC ou
declaração de significância integral. Nova rodada informada pelos resultados
anteriores é exploratória; novo algoritmo/sorteio não restaura confirmação inédita.

## Execução, retomada e gates

Agente testa somente fixtures pequenas. Pesquisador executa script 34 smoke:
subcoorte determinística já definida na rotina selada de regressão, componentes
inteiros e seleção sem alvo. Apenas externo 0 e quatro blocos; até 96 ajustes
internos. Exige três classes nas avaliações internas; não trocar seed após erro.
Smoke não publica métricas de desempenho global. Recarga das quatro partes deve
reproduzir probabilidades com diferença máxima ≤1e-10.

Produção somente depois de gate do smoke da mesma assinatura e revisão de sua
saída. Primeiro lote com --limit-outer-blocks 1 mede custo; nova execução retoma.
SQLite registra cada ajuste interno concluído, com checksum, e partes externas
usam modelos/Parquets/JSON por hash. Protocolo/código/fontes incompatíveis bloqueiam
reuso. Ctrl+C preserva ajustes já confirmados; modelo interrompido é reajustado.
Não retomar alterando a grade ou apagando owner para contornar validação.

Relatório completed=true só após conferência final, recarga no smoke ou cobertura
integral na produção. Erro mantém completed=false; código 2 é parcial por limite.
Nenhum treino real é executado pelo agente para conferir a organização.

Fundamentos consultados em 05/11/2026: Harrell,
[logística ordinal](https://hbiostat.org/rmsc/ordinal);
SciPy, [L-BFGS-B](https://docs.scipy.org/doc/scipy/reference/optimize.minimize-lbfgsb.html);
scikit-learn, [PCA](https://scikit-learn.org/stable/modules/generated/sklearn.decomposition.PCA.html)
e [prevenção de vazamento](https://scikit-learn.org/stable/common_pitfalls.html#data-leakage).
Escolhas de limites/grade/PCA/tolerâncias são deste estudo, não prescrições dessas fontes.
