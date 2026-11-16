# Preparação da classificação ordinal e triagem do piloto — 05/11/2026

## Confirmado

Pesquisador concluiu 32 v1.1: 133 consultas, população de 199.998 consultas com
chave e duas faixas sem consulta. Evidência em cache para 130; três payloads
acima do limite/nulos; 22 listas truncadas na ficha. Nenhuma busca nova, índice,
letra exportada ou decisão antiga modificada. Fonte/versão/selos conferidos.

Triagem técnica 33 sobre manifesto privado de 790.616 bytes, no máximo cinquenta
candidatos por ficha, sem ler o banco ou dump novamente. Quarenta casos aceitos:
35 com candidato selecionado disponível e metadados compatíveis sob verificações
v3; cinco sem candidato selecionado disponível na ficha. Os outros 93 são status
anteriores não aceitos. Isso não mede precisão semântica, recall ou erros humanos.
Fichas/anotações originais preservadas; resultados individuais de triagem privados.

Alocação de consultas da cauda ≥80: 128 aceitas, 367 ambíguas, duas não encontradas
e duas instrumentais. Há evidência para priorizar ambiguidade/qualidade antes de
novo cruzamento integral. Esse quadro não diz que todas as ambíguas são resolvíveis
ou têm letra correta. Não aplicar aceitações automaticamente.

## Próximo ajuste preparado, não executado no corpus

Logística ordinal regularizada com chances proporcionais nos quatro blocos e
mesmos dados/folds. Oito configurações internas: quatro penalizações × numéricas
originais ou PCA com 95% da variância. Demais categorias/texto mantêm blocos
próprios. Seleção interna por acurácia balanceada; sem mudar cortes 20/40.
Hipótese de chances proporcionais assumida, sem teste formal concluído.

Implementação numericamente validada com gradiente por diferenças finitas,
verossimilhança independente, caso sem preditores, estabilidade de extremos e
384 dimensões sintéticas com penalização mínima. Fluxo validado com PCA só no
treino, probabilidades, métricas ponderadas apenas na avaliação, smoke/lote/retomada,
interrupção por Ctrl+C e bloqueio de parte corrompida. Não instala pacotes.

53 testes selecionados aprovados em 12,34 s; lint completo e formatação dos oito
arquivos Python novos conferidos. Só fixtures sintéticas de até 90 observações
nos testes de treinamento; nenhum ajuste real executado pelo agente. Inspeções
reais limitadas a agregados, hashes/selos e às 133 fichas de metadados.

## Ação do pesquisador

Executar somente 34 smoke e enviar a última saída. Conferir a reprodução após
recarga e revisar resumo antes do primeiro lote de produção. Comandos/retomada
em docs/execucao_classificacao_ordinal_200k_v1.md. Preservar as primeiras métricas
Ridge e PDFs; não há novo resultado preditivo ordinal para interpretar ainda.
