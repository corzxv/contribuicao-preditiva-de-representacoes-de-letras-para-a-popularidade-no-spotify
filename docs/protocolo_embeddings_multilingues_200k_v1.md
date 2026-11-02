# Encoder multilingue — protocolo v1 (01/11/2026)

Extensão do contrato textual v1; não editar o contrato/código do script 19 já
selado e executado. Coorte mantida: 77.535 linhas, 77.051 inputs normalizados
únicos, 21 descritores finitos, 21.893 componentes (maior=186), zero chaves não
resolvidas. São resultados da execução manual de 19, não novo processamento.
A flag `text_no_lexical_segments` é constante zero na coorte; não excluir linhas
nem refazer descritores. Constantes/pré-processamento serão tratados dentro dos
treinos. A CV agrupada aninhada 5×3 já foi aprovada; folds ainda não gerados.

## Escolha técnica e revisão

Encoder `intfloat/multilingual-e5-small`, commit
`614241f622f53c4eeff9890bdc4f31cfecc418b3`, CPU float32, 384 dimensões.
Escolha pela cobertura multilingue e custo/dimensão compatíveis com a infraestrutura;
não escolhida por métricas de popularidade. O [repositório oficial](https://huggingface.co/intfloat/multilingual-e5-small/tree/main)
informa licença MIT, arquivos safetensors/tokenizer e dimensão/contexto na config.
O [commit congelado](https://huggingface.co/intfloat/multilingual-e5-small/commit/614241f622f53c4eeff9890bdc4f31cfecc418b3)
foi conferido no provedor; a inferência nunca usa revisão mutável `main`.
O model card declara suporte multilingue e limitações em idiomas de poucos
recursos, sem garantia de adequação a letras ou ganho preditivo. Não excluir
idiomas não cobertos/incertos; não traduzir automaticamente.

Download manual somente de config, model.safetensors, tokenizer.json,
tokenizer_config.json, special_tokens_map.json e README. Evitar outros formatos
dos mesmos pesos (bin/ONNX/OpenVINO). Manifesto local registra SHA-256 de cada
arquivo, modelo/revisão/caminho. Hash local não é assinatura independente do autor.
Não enviar letras ao provedor. Nenhum download foi executado pelo agente.

## Input e cálculo

Mesmo input `normalize_lyrics_text(accepted_text)` do script 19; conferir hash
contra `text_input_sha256` antes de codificar. Não receber artista, título, gênero,
idioma, popularidade, peso, split ou qualidade de matching no encoder.

Conforme [instruções do modelo](https://huggingface.co/intfloat/multilingual-e5-small),
prefixar cada janela com `query: `, inclusive línguas não inglesas. Tokenizer fast
local, sem dependência automática de sentencepiece nem código remoto. Reservar
tokens do prefixo e especiais dentro do limite total de 512. Não truncar: tokenizar
conteúdo completo, janelas com 32 tokens de sobreposição e validação de cobertura
pelos utilitários existentes. Peso da janela = número de tokens de conteúdo novos;
a soma dos pesos precisa ser exatamente o tamanho do conteúdo tokenizado.

Pooling por média mascarada de tokens válidos (inclui prefixo/especiais), L2 em
cada janela; média dos vetores ponderada pelos tokens novos, seguida de L2 final.
Essa agregação é adaptação operacional para letras longas, não receita validada
de performance do modelo; reduz peso relativo do overlap, não remove toda sua
influência contextual. Preservar palavras, ordem/repetição no input original.

Seed 20261101; eval/inference_mode, sem gradiente/fine-tuning; operações determinísticas
PyTorch, CPU float32. Batch de 8 janelas, 2 threads padrão. Batch/threads são
operacionais e registrados por vetor/execução; cache é compartilhado dentro da
tolerância numérica 1e-5, com revisão/dtype/device/normalização fixos. Qualquer
alteração científica dessas regras/fontes exige nova versão e pasta, não edição
dos selos. Nenhum vetor MiniLM antigo é importado por ID ou dimensão igual.

## Teste pequeno antes da escala

Modo smoke seleciona até 24 inputs únicos, sem alvo: dois em cada um dos oito
idiomas estimados mais frequentes, três maiores textos, três menores e até dois
com classificação incerta; empates por hash e ordem estável. Duplicação entre
critérios reduz o total. Plano é privado, não probabilístico nem avaliação de
precisão semântica. A linguagem só orienta cobertura do teste, não a codificação.

Critérios: todos os inputs selecionados, dimensão 384, vetores finitos, norma L2
unitária até 1e-5; nenhum input acima de 512 tokens; cobertura integral sem perder
cauda; reprodução de um vetor de controle com diferença máxima ≤1e-5. Asserções
e resumos registram o que foi verificado. O teste técnico não demonstra melhoria
em MAE/RMSE nem valida todos os idiomas. Tempo extrapolado ao corpus é grosseiro,
afetado pela seleção de extremos, aquecimento, cache e comprimento dos textos.

## Escala, retomada e produtos

Modos separados download / smoke / all; all exige smoke verificado com o mesmo
selo. Não é acionado ao terminar o teste. Inferência só local, trust_remote_code=false,
use_safetensors=true e nenhum arquivo de código do modelo baixado. Falha/interrupção
preserva vetores concluídos; retomar repete o comando e confere hashes/checkpoints.
`--limit-texts` limita novos inputs, não validação/carregamento do modelo/exports.

Cache privado SQLite reutiliza schema/funções de integridade do encoder anterior,
em `private_embeddings_200k_v1`, separado dos dados históricos. Um vetor por hash
do input; índice privado mantém uma linha por faixa, com query_id, componente e
metadados diagnósticos, sem alvo. Os mesmos 77.535 casos alimentarão os quatro
blocos por join 1:1; controles nunca entram nos preditores. Exportação Parquet
verifica cache, dimensão/norma e vínculos sem multiplicar faixas.

Públicos somente resumo e relatório agregados em subpastas smoke/integral de
`reports/embeddings_multilingues_200k_v1`. Privados: snapshot/manifesto, SQLite,
plano, vetores e índices. Não há lyrics, tokens, hashes individuais, IDs ou vetores
nos relatórios/logs públicos. Grupos, matrizes e alvos existentes permanecem.
Não se geram PCA, folds, previsões nem modelos preditivos nesta etapa.
