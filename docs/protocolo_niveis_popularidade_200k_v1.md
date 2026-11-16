# Níveis de popularidade — etapa exploratória v1 (04/11/2026)

## Autoridade, pergunta e preservação

D-025: após discutir as sugestões do orientador, o pesquisador autorizou condução
autônoma do plano, preservando a primeira regressão e a execução manual de tarefas
pesadas. Este protocolo inicia uma etapa nova; não modifica a D-017 ou os resultados
da regressão. Investigar a contribuição preditiva incremental das letras para o
nível operacional de popularidade observada no snapshot, sem linguagem causal.

População analítica inicial: as mesmas 77.535 faixas aceitas e 21.893 componentes.
Preservar a amostra probabilística de 200 mil, seus pesos e estratos. Não reduzir
a coorte para 10 mil sem necessidade de desenho/custo demonstrada. Não presumir
inferência para o catálogo de 1.159.764 faixas ou para todo o Spotify.

## Resposta operacional definida antes do diagnóstico de classificação

Configuração canônica: configs/niveis_popularidade_200k_v1.json.

- Principal: baixo = 0–19; intermediário = 20–39; elevado operacional = 40–100.
- Sensibilidade única: baixo = 0–39; intermediário = 40–59; elevado = 60–100.
- Cauda extrema ≥80 mantida separadamente para diagnóstico.

São reagrupamentos das bandas já existentes, escolhidos a partir do objetivo e
do suporte descritivo conhecido, antes de calcular acurácia/matrizes categorizadas.
Os limites são decisões do estudo, não definições oficiais de hit nem divisões
naturalmente demonstradas. A denominação elevada é relativa ao recorte operacional.
O principal não será substituído pelo esquema que produzir melhor resultado.
Não usar tercis da coorte aceita para atribuir significado de popularidade absoluta.

Formalmente, C(y)=0 se y<c1; C(y)=1 se c1≤y<c2; C(y)=2 se y≥c2. Valores observados
devem ser inteiros finitos em 0..100. Previsões antigas são categorizadas sem
arredondamento. Extrapolações pertencem às classes extremas; clipping a 0..100
não muda a classe sob esses limites. Não descartar previsões negativas.

## Diagnóstico 31: preparação, não novo treinamento

Modo agregados: lê somente alocação e cobertura publicadas, reconciliando totais.
Conta catálogo, amostra, aceitas sem peso e aceitas com pesos originais. Não
interpolar bandas que atravessem limites novos; bloquear nesse caso. Não soma
componentes publicados por banda, pois um componente pode abranger várias bandas.

Modo previsoes (execução manual): confere o hash das previsões no resumo integral,
assinatura do resumo, hash dos folds e os 15 selos científicos registrados na
publicação anterior. Confere IDs 1:1, alinhamento de componentes/folds e separação
externa e interna. Não lê pesos do encoder, modelos serializados ou letras.

Produz suporte por classe em cinco treinos/testes externos e quinze treinos/testes
internos. Cem faixas e vinte componentes por classe/partição são alertas
operacionais prévios, não cálculos de poder ou prova de precisão. Ausência de classe
bloqueia interpretação de balanced accuracy/macro-F1: a métrica agregada é ausente,
em vez de calcular silenciosamente a média apenas das classes presentes.

Categorização das seis variantes existentes: quatro Ridge, média e mediana do
treino externo. Acrescenta referência da classe majoritária calculada somente no
respectivo treino externo, empate pela classe de menor índice. Calcula acurácia,
acurácia balanceada (média das três sensibilidades), macro-F1, erro extremo 0↔2,
precisão/sensibilidade por classe e matrizes de confusão. Métricas principais por
faixa com peso igual; sensibilidade com pesos originais apenas na avaliação.
Apresenta contrastes Combinado−Baseline e Combinado−Profundo sem IC/p-valores.

São resultados exploratórios condicionados às previsões antigas. Os regressores
não foram treinados/selecionados para classificar e não fornecem probabilidades
de classe. Não calcular log-loss/calibração a partir desses escores discretizados.
A cauda ≥80 indica quantas previsões caem em cada uma das três classes; acerto na
classe elevada não equivale a detectar um hit ≥80.

## Direção da modelagem posterior — condicionada aos diagnósticos

Família inicialmente indicada: logística ordinal regularizada, com duas fronteiras
ordenadas e probabilidades coerentes. Avaliar adequação da hipótese de chances
proporcionais dentro do desenvolvimento; alternativa multinomial se houver motivo
documentado. Não implementar uma sucessão de famílias até encontrar maior ganho.
Implementação, testes numéricos e comando de treino serão preparados após avaliar
o diagnóstico 31. Nenhum treinamento é requisito para executar 31 ou 32.

Quatro blocos e observações comuns. Mesmos folds agrupados 5×3 quando a coorte e
suas identidades permanecerem. Critério primário da nova classificação: acurácia
balanceada. Complementares: macro-F1, precisão/sensibilidade por classe, erros
extremos, log-loss e calibração das probabilidades de classificadores reais.
Pesos iguais no treino; ponderação de classe/custo é opção posterior justificada,
sem confundi-la com pesos de desenho. Não escolher pela sensibilidade ponderada.

PCA: comparação delimitada entre numéricas padronizadas originais e PCA dessas
numéricas com retenção de 95% da variância, como opção de pré-processamento dentro
dos treinos. Categorias não são tratadas como números contínuos. Não fazer PCA
conjunta de metadados, descritores e embeddings nem eliminar variáveis a partir
de toda a coorte. Seleção entre opções/regulação pertence aos folds internos.
PCA é não supervisionada: variância explicada não implica capacidade preditiva.

Embeddings existentes podem ser reutilizados com o manifesto textual, dimensão e
versão selada, registrando a variante operacional E5 com espaço adicional. Não
regenerar apenas para experimentar classificação. Log1p da resposta fica como
opção de regressão futura, sem execução automática; não é necessário para a
resposta categórica e não se compara MAE em escalas diferentes.

Nenhum novo sorteio restaura teste independente depois da exposição anterior.
Não tratar cinco folds como réplicas independentes; eventual incerteza deve
considerar componentes, ajuste/seleção e caráter exploratório desta rodada.

## Conclusão e próximos passos

Concluir 31 exige completed=true, fontes preservadas e reconciliação dos grupos.
Suporte operacional aprovado permite preparar o classificador; não comprova
qualidade semântica de todos os vínculos. Diagnóstico 32 audita a viabilidade de
revisar vínculos separadamente. Novo cruzamento integral depende de evidência de
recuperações corretas e de uma população operacional explicitamente definida.

Referências consultadas em 04/11/2026:

- Harrell, *Regression Modeling Strategies*, [logística ordinal](https://hbiostat.org/rmsc/ordinal).
- James et al., *An Introduction to Statistical Learning with Applications in Python*,
  capítulos de classificação, validação, redução de dimensão e regularização,
  [página dos autores](https://www.statlearning.com/).
- Documentação oficial de [PCA/PCR](https://scikit-learn.org/stable/auto_examples/cross_decomposition/plot_pcr_vs_pls.html),
  [acurácia balanceada](https://scikit-learn.org/stable/modules/model_evaluation.html#balanced-accuracy-score)
  e [vazamento](https://scikit-learn.org/stable/common_pitfalls.html#data-leakage).
