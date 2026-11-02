# Embeddings multilingues — execução manual e retomada

Script 19 concluído: 77.535 faixas, 77.051 inputs únicos, 21 descritores e
21.893 componentes. Não repetir descritores, auditorias ou recuperação.
Encoder congelado no protocolo `protocolo_embeddings_multilingues_200k_v1.md`.
Não editar o contrato textual anterior: ele faz parte do selo do script 19.

**Estado em 01/11/2026:** geração integral concluída: 77.051 vetores de dimensão
384 para 77.535 faixas; zero pendências, 91.156 janelas até 512. Comandos abaixo
são registro de reprodução; não repetir 20 para continuar. Próximo script: 21,
conforme execucao_base_modelagem_200k_v1.md, sem encoder ou treinamento.

## 1. Download manual do modelo

```powershell
& "C:\Users\Concursos Felipe\Documents\UnB\TCC\.venv\Scripts\python.exe" "C:\Users\Concursos Felipe\Documents\UnB\TCC\scripts\20_preparar_embeddings_multilingues.py" download
```

Essa é a única operação com rede, aproximadamente 0,5 GB de pesos/tokenizer e
metadados públicos. Não envia letras. Baixa somente formatos necessários,
registra hashes e reutiliza cache incompleto em retomadas. Repositório público,
sem credencial obrigatória; não colocar tokens em comandos. Se falhar por rede,
corrija a conexão e repita. Nenhuma dependência é instalada automaticamente.

## 2. Teste limitado, após o download terminar

```powershell
& "C:\Users\Concursos Felipe\Documents\UnB\TCC\.venv\Scripts\python.exe" "C:\Users\Concursos Felipe\Documents\UnB\TCC\scripts\20_preparar_embeddings_multilingues.py" smoke
```

Executar em sequência, não simultaneamente. Smoke usa até 24 inputs únicos,
com cobertura dirigida de idiomas, incerteza e extremos de extensão. Apenas CPU,
duas threads, batch de oito janelas. Não é validação de precisão ou de ganho em
popularidade. Não requer SSD D:, treinamento ou novo split. CPU pode ficar
ocupada durante inferência; o agente não executa essa etapa real.

Tokenizer fast JSON e safetensors são usados localmente, sem código remoto ou
fallback automático. O ambiente inspecionado possui torch 2.8.0, transformers
4.57.1 e huggingface-hub 0.36.2. Se houver incompatibilidade, preservar logs e
relatório incompleto; não trocar revisão/instalar modelos silenciosamente.

Conferir os dois agregados em
`C:\Users\Concursos Felipe\Documents\UnB\TCC\reports\embeddings_multilingues_200k_v1\smoke\`:

- `resumo_embeddings.json`
- `relatorio_embeddings.md`

Ao terminar, avise para revisão. Sucesso exige completed=true, dimensão 384,
finitude/L2, cobertura de tokens, limite total 512 e reprodução do controle
≤1e-5. Relatório traz tempo do teste e extrapolação grosseira, sem promessa
de duração total. O modelo não foi carregado nem baixado pelo agente na preparação.

## Retomar

Repetir o comando que foi interrompido. Vetores concluídos permanecem em SQLite;
não apagar estado/cache. `--limit-texts N` limita somente novos textos, não
checagem de fontes/modelo ou exportação. Mudar batch/threads é operacional e
registrado; entradas/revisão/dtype/device/regras precisam permanecer compatíveis.
Smoke revalida a reprodução antes de liberar novamente a escala.

## Resultado real do smoke — concluído

Resumo completed=true: 24 vetores de dimensão 384, 68 janelas, 55,26 s e diferença
máxima de reprodução 0,0. Entradas efetivas até 512 tokens. Leitura limitada dos
24 metadados do checkpoint confirmou cobertura integral e texto máximo com
9.193 tokens de conteúdo. Aviso 546 > 512 foi emitido na tokenização do conteúdo
integral antes da divisão; nenhuma janela enviada ao modelo excedeu 512. A nota
sobre __call__ é sugestão de desempenho. Não há motivo para repetir o teste ou
alterar código/protocolo selados por esses avisos.

## 3. Primeiro lote da geração definitiva — executado

```powershell
& "C:\Users\Concursos Felipe\Documents\UnB\TCC\.venv\Scripts\python.exe" "C:\Users\Concursos Felipe\Documents\UnB\TCC\scripts\20_preparar_embeddings_multilingues.py" all --limit-texts 1000
```

Gera até 1.000 novos vetores, reaproveita os 24 existentes e preserva o checkpoint
para a continuação. O limite não reduz as checagens iniciais de fontes/modelo nem
a exportação. Não rodar duas instâncias em paralelo sobre o mesmo estado.

Ao atingir o limite com pendências, saída 2 e completed=false indicam lote parcial
esperado. Os vetores concluídos permanecem salvos. Revisar tempo, new_vectors,
reused_vectors e unencoded_unique_texts em `integral/resumo_embeddings.json`
antes de continuar. O lote segue os primeiros inputs inéditos na ordem da fonte;
não é uma amostra probabilística nem uma avaliação científica. O smoke foi dirigido a extremos:
sua extrapolação grosseira não é previsão confiável do tempo total.

Resultado real revisado: 1.000 vetores novos + 24 reutilizados em 296,25 s;
1.024 salvos, 76.027 pendentes, 1.055 referências de faixas no índice parcial.
Dimensão 384, 1.246 janelas acumuladas, max_input_tokens=512; nenhum erro registrado.
Checkpoint smoke_verified=true e código/protocolo compatíveis com o mesmo selo.
Estimativa linear restante: 76.027 × 296,25 / 1.000 / 3.600 = 6,26 h (~6h15).
Reservar 6–8 h nas mesmas condições é orientação operacional, sem garantia ou
intervalo estatístico; carga da máquina e extensão dos textos podem alterar o ritmo.

## 4. Continuação integral — executada e concluída

```powershell
& "C:\Users\Concursos Felipe\Documents\UnB\TCC\.venv\Scripts\python.exe" "C:\Users\Concursos Felipe\Documents\UnB\TCC\scripts\20_preparar_embeddings_multilingues.py" all
```

Reutiliza os 1.024 vetores salvos; mantém um vetor por input (77.051 esperados) e índice
de 77.535 faixas, preservando alinhamento. Não calcula MAE/RMSE ou gera modelos
supervisionados. Os agregados da escala ficam em subpasta `integral` do mesmo
diretório público. Repetir `all` retoma pendências. Saída 0 = modo concluído;
2 = lote limitado; falha/interrupção deixa resumo incompleto e checkpoints.
Não rodar instâncias simultâneas. Manter o computador ligado e sem suspensão
durante a execução. Se interromper, repetir este comando retoma o trabalho salvo.
Conferir ao terminar: completed=true, unencoded_unique_texts=0, 77.051 vetores e
private_index_rows=77.535. A mensagem inicial deve mostrar 1.024 reutilizados e
76.027 pendentes, se nenhum outro lote tiver sido executado.

## Caminhos privados

- Cache do modelo: `data/raw/lyrics_private/huggingface_cache/`, revisão
  `614241f622f53c4eeff9890bdc4f31cfecc418b3`.
- Estado: `data/derived/private_embeddings_200k_v1/`, com snapshot.json, state.sqlite,
  progress.json e plano_smoke.json.
- Vetores: embeddings_smoke.parquet / embeddings.parquet; índices: indice_smoke.parquet /
  indice_embeddings.parquet. Não enviar/versionar dados, vetores, índices ou letras.
- Fontes: coorte_descritores.parquet do script 19 e letras_aceitas_200k.parquet v2.
  Texto padronizado precisa conferir com o hash da etapa anterior.

Depois da escala: conferência de vínculos, montagem dos quatro blocos e folds
comuns conforme CV 5×3 aprovada. A exposição antiga e a definição de pesos nas
métricas continuam explícitas. Não treinar automaticamente ao terminar embeddings.
