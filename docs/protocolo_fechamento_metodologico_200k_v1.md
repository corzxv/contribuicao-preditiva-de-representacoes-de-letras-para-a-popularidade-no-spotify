# Diagnósticos auxiliares de fechamento — 02/11/2026

Solicitados após a leitura do PDF parcial; análise exploratória, não pré-registro.
Preservar PDF/ZIP, fontes, coorte, pesos, folds, previsões e modelos 19–24. Sem
treino, download, LRCLIB ou novos embeddings. Escopo leve: duas tabelas privadas
já existentes, cada uma com no máximo 80.000 linhas e 32 MiB; projeção de colunas
numéricas/controle. Sem letras, nomes de artistas/faixas ou saída individual.
Conferir hashes com resumo concluído de 23 e reproduzir perdas por componente.
Interromper se exceder orçamento; não contornar a execução manual de tarefas pesadas.

## Resíduos e clipping

Resíduo = previsão − popularidade observada: negativo significa subestimação.
Descrever os 128 casos com y≥80 por quatro blocos: quantis, viés médio, dispersão,
frações subestimadas, somas de erros absoluto/quadrático e contribuição no MAE
global. Contagens por fold apenas, sem procurar subgrupos favoráveis ou excluir
casos. Quantis NumPy lineares, DP descritivo com divisor n. Não são inferência
para todos os hits do catálogo; cortes definidos pelo próprio alvo condicionam
a interpretação e podem acentuar a aparência de regressão ao centro.

Avaliar projeção fixa clip(p,0,100) como sensibilidade pós-resultado, nos mesmos
casos/previsões/pesos, sem alterar resultado principal, selecionar pelo clipping
ou refazer ajustes. Para y em [0,100], essa projeção não aumenta erro absoluto
ou quadrático ponto a ponto; melhora não é evidência de nova informação textual.
Documentar previsões negativas e separar redução de erro na borda inferior de
desempenho na cauda superior. Nunca truncar y.

## Incerteza auxiliar — hipóteses e estimando

Na distribuição empírica finita de casos/previsões observados, as diferenças
são números conhecidos, sem erro Monte Carlo. Para discutir outras avaliações
hipotéticas, é preciso um modelo de amostragem de componentes que não é garantido
pelo sorteio original de faixas nem pela aceitação das letras.

Usar modelo AUXILIAR de componentes operacionais independentes, muitos grupos,
momentos finitos e nenhum grupo dominante. Condicionar separadamente no treino
de cada fold, incluindo seleção interna e modelos. Para contraste Combinado −
referência (Baseline ou Profundo), definir D_g=soma das diferenças pareadas de
perda absoluta no grupo e N_g=número de faixas; delta=sum(D_g)/sum(N_g).
Variância aproximada G/(G−1) * sum[(D_g−delta*N_g)^2]/sum(N_g)^2. Não dar pesos
iguais aos MAEs dos grupos, pois isso muda o estimando por faixa. Na sensibilidade
ponderada usar diferenças multiplicadas pelos pesos originais e N_g=sum(w_i).
Esses pesos continuam sem corrigir seleção textual.

Gerar aproximação normal marginal por fold e limites Bonferroni para família de
dois contrastes × cinco folds, separada para cada política de avaliação. Combinar
extremos dos limites com pesos N_fold/N_total. A união de Bonferroni não exige
folds independentes; sua validade nominal ainda depende da adequação das
aproximações marginais e do modelo de componentes. Não somar variâncias nem
dividir DP dos cinco folds por sqrt(5). O condicionamento é fold a fold, NÃO
conjunto em todos os modelos (outros treinos contêm os casos deste teste).

O alvo auxiliar combinado é a média ponderada de riscos condicionais dos cinco
pares de modelos ajustados, em avaliações hipotéticas compatíveis com seus
domínios. Não é a incerteza integral da pipeline CV, do ajuste em todos os dados,
da seleção de famílias, da coleta/matching ou do catálogo. Folds equilibrados por
tamanho e SHA não são sorteios independentes; generalização do modelo auxiliar
exige estabilidade de composição/tamanho e independência entre grupos. Chaves
operacionais não demonstram independência estatística: pseudônimos, versões não
ligadas, dependência temporal/colaborações residuais podem invalidá-la.

Bootstrap pareado de componentes dentro de cada fold, mantendo todo componente
e reavaliando razão de totais, é alternativa à linearização, não correção da
dependência dos treinos. Bootstrap agrupado direto das perdas OOF agrupadas
estima apenas variação de composição com previsões congeladas; não divulgar como
IC do procedimento completo. Não executar reamostragem extensa nesta etapa.

Para a incerteza INTEGRAL seria preciso desenho adicional que refaça seleção,
pré-processamento e ajuste dentro de cada repetição, mantendo duplicatas de um
componente na mesma partição. Repetir seeds só mede variação de partições no mesmo
corpus. NCV para estimação de erro da CV (Bates et al.) não é automaticamente a
CV 5×3 usada aqui para tuning; requer adaptação/validação para grupos, perdas
pareadas e seleção. Sem justificativa para novo ciclo de treinamento agora.

Referências primárias e parecer interpretativo em
reports/parecer_fechamento_metodologico_200k_v1.md. Os resultados auxiliares não
substituem as métricas principais e não autorizam declarar confirmação independente.
