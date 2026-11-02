# Regras duráveis do projeto

## Objetivo científico

Avaliar associação e contribuição preditiva incremental de descritores de letras para estimar a popularidade Spotify observada no snapshot da fonte, em conjunto com descritores acústicos e metadados. Não fazer afirmações causais.

## Engenharia e dados

- Usar Python; não usar R.
- Preservar dados brutos imutáveis e nunca versionar bases brutas, derivados volumosos, letras ou credenciais.
- Toda normalização cria colunas novas e preserva campos originais.
- Documentar regras, quantidades antes/depois, exceções e destino de rejeitados.
- Separar sempre `spotify_popularity`, `genius_lyrics_views` e `lfm_playcount`.
- Atualizar dicionário de dados, decisões e proveniência quando o schema mudar.
- Não usar notebooks como única fonte da lógica; a pipeline deve ser reproduzível por CLI.
- Executar testes e lint antes de concluir alterações.
- Não fazer scraping massivo nem treinar modelos na Base v0.1.

## Modelagem futura

- Evitar leakage por artista, composição e versões da mesma faixa.
- Exigir splits agrupados por artista e por chave operacional de composição.
- Não tratar a chave normalizada como identificador universal.

## Continuidade e autoridade (consolidação de 01/11/2026)

- Este é o TCC existente, não um projeto novo. Atuar como agente técnico principal;
  concluir tarefas autorizadas e manter contexto no repositório.
- Ler, nesta ordem, `docs/ESTADO_ATUAL.md`, `docs/CONTEXTO_TCC.md`,
  `docs/PLANO_EXECUCAO.md` e `docs/MAPA_ARTEFATOS.md`. O registro canônico de
  decisões é `docs/decisions.md` (equivale a DECISOES_METODOLOGICAS; não duplicar).
- Não inferir execução pela existência de um script. Relacionar resultados a
  resumos/checkpoints, schemas e verificações; distinguir confirmado de pendente.
- Antes de editar, inspecionar Git; preservar alterações pessoais. Não fazer
  commit/push sem instrução explícita. Não mover arquivos com consumidores sem
  análise; movimentações incompatíveis/destrutivas exigem autorização concreta.
- Preservar toda a história; organizar primeiro por documentação e entradas.
  Não excluir resultados, mover dump LRCLIB, duplicar bases ou reconstruir índices
  sem necessidade demonstrada. Não coletar letras para pequenas metas de cobertura.

## Regra obrigatória de execução manual

- O agente prepara/revisa Python, comandos PowerShell, entradas/saídas, logs,
  checkpoints, retomada e critérios de conclusão. O pesquisador executa trabalhos
  pesados. Parar antes de executá-los, mesmo com permissão técnica disponível.
- Isso inclui varreduras extensas, buscas em larga escala no LRCLIB, grandes
  índices, processamento integral de centenas de milhares de registros, geração
  massiva de descritores/embeddings, treinamento e experimentos custosos.
- Não contornar a regra com processos em segundo plano. Não assumir que um
  artefato foi produzido sem evidência. Aguardar resultados do usuário, analisá-los
  e continuar. Inspeções limitadas de metadados, amostras pequenas, testes com
  fixtures e lint são permitidos; interromper inspeção que se torne custosa.
- Não executar comandos históricos `all`, scripts 01–16 ou treinos apenas para
  verificar organização. Usar testes específicos; registrar exatamente o executado.

## Decisão científica aprovada em 01/11/2026

- Priorizar o domínio analítico observado de faixas com letras aceitas da amostra
  de 200 mil. Não presumir amostra representativa do catálogo nem de todas as
  músicas com letras. Não reiniciar recuperação sem evidência concreta.
- Preservar as 200 mil faixas e pesos para descrição/cobertura/seleção. Os pesos
  não corrigem automaticamente disponibilidade de letras. D-017 aprovada:
  ajuste/métricas principais com pesos iguais por faixa, MAE primário/seleção;
  RMSE/R² complementares. Sensibilidade com MAE ponderado pelos pesos originais,
  mesmas observações/folds/previsões externas e sem retreinar ponderado. Não
  selecionar modelos pela sensibilidade. Preservar pesos/estratos para descrição.
- Comparar Baseline, Tradicional, Profundo e Combinado nas mesmas observações e
  divisões. Prevenir vazamento por artista, composição operacional, versões e
  textos iguais; reconciliar exposições históricas antes de definir validação.
- CV agrupada aninhada 5 folds externos × 3 internos aprovada pelo pesquisador
  em 01/11/2026 (D-015). Componentes/base/folds reais concluídos no script 21,
  com separação auditada; não redesenhar splits para melhorar resultados.
  Script 22 smoke real concluído: 318 faixas, reprodução exata, sem avisos.
  Produção 22 concluída, conferida em 02/11: 20 partes Ridge + dez referências, 77.535
  previsões por variante. Não alterar código/protocolo/modelos/folds por resultado.
  Diagnósticos 23 concluídos, métricas reproduzidas sem refit/IC. Material parcial
  24 para monografia gerado de agregados leves, sem dados individuais/modelos.
  Próximo: integração/escrita, não retreino automático. Não declarar significância
  com métricas pontuais ou tratar cinco folds como réplicas independentes.
- O teste V0.6 foi aberto em 14/10/2026. Novo sorteio/split não restaura confirmação
  independente. Não carregar alvos históricos em auditorias apenas de linhagem.
- Não transportar descritores LFM2b ou embeddings antigos por simples track_id.
  Demonstrar compatibilidade de texto/versão/normalização/modelo e dimensão.
- Idioma automático não é verdade humana e não autoriza exclusão silenciosa.
  Alterar população, amostragem, resposta, desenho de validação ou alcance de
  inferência requer participação do pesquisador. Correções leves e documentação
  dentro do escopo autorizado não exigem nova aprovação.
- Após etapa relevante: atualizar estado, decisões e plano; manter rastreabilidade
  e limitações para a monografia. Não alegar suficiência preditiva pelo tamanho.

## Encerramento principal e revisão acadêmica (02/11/2026)

- O pesquisador determinou congelar a avaliação existente e produzir a monografia
  completa (D-022). Não iniciar novos treinamentos, LRCLIB ou embeddings massivos
  como continuação automática. Manter resultados, modelos, previsões e folds.
- A entrada acadêmica atual é reports/monografia_template_200k_v2/main.tex (D-023),
  com ZIP e PDF TeX de 34 páginas no template fornecido. Versão de 57 páginas e
  dois trechos anteriores preservados. Orientador: **Leandro Tavares Correia**,
  grafia confirmada explicitamente pelo pesquisador. Próximo: revisão acadêmica.
- Template/Ana e TCCs de Estatística da BDM orientam apresentação; citar fontes
  originais pertinentes e verificadas. Engenharia e pendências administrativas
  ficam fora do PDF acadêmico; não apagar seus registros nem PDFs históricos.
- Texto registra token adicional de espaço do E5 e limites auxiliares condicionais;
  não afirmar receita canônica exata, significância integral ou inferência de catálogo.
- Requisitos institucionais/datas não confirmadas não devem ser inventados. Não
  confundir versão completa para revisão com documento homologado para depósito.


## Publicação e idioma (02/11/2026, D-024)

- O pesquisador autorizou organizar e publicar esta consolidação no GitHub.
  Preservar a visibilidade privada existente e verificar o remoto após push.
- Novos commits, comentários e documentação devem ser escritos em português.
  Preservar os bytes de códigos/protocolos selados e o histórico já publicado;
  não traduzir APIs/colunas ou reescrever commits por estética.
- Usar scripts/30_auditar_publicacao_git.py antes de publicar. Dados individuais,
  letras, dump, modelos, embeddings e credenciais ficam locais. Remoções do índice
  preservam o arquivo local; não apagar experimentos/resultados como limpeza.
