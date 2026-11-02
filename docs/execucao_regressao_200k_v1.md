# Ridge nos quatro blocos — execução manual

**Atualização 02/11/2026:** integral concluída: 20/20 partes Ridge, dez referências,
77.535 previsões por variante, zero pendências. Última retomada 651,372 s, sem
avisos. Os comandos abaixo são registro de reprodução; não repetir 22 para
continuar. Próximo: script 23 conforme execucao_diagnosticos_modelagem_200k_v1.md.
Resultados em reports/interpretacao_modelagem_200k_v1.md, sem IC/p-valores.

Script 21 concluído: 77.535 faixas, zero células ausentes/inválidas nos 15 campos
Baseline, 77.051 vetores auditados, 21.893 componentes. Cinco folds externos
equilibrados de 15.507 faixas. Não repetir dados, embeddings ou folds.

Script 22 smoke executado pelo pesquisador e revisado: 318 faixas, 1,843 s,
quatro blocos/duas referências, reprodução exata e sem avisos nos 72 ajustes
internos. Gate técnico verificado. Nenhum ajuste real executado pelo agente.
Registro intermediário: primeiro lote Combinado externo 0 em 67,775 s, 1/20
partes naquele ponto, sem avisos. A continuação da seção 3 já foi concluída;
o próximo comando atual é o script 23, conforme a atualização no início do guia.
Código/protocolo 22 preservados.

## 1. Teste técnico limitado — concluído

```powershell
& "C:\Users\Concursos Felipe\Documents\UnB\TCC\.venv\Scripts\python.exe" "C:\Users\Concursos Felipe\Documents\UnB\TCC\scripts\22_modelar_dominio_observado_200k.py" smoke
```

Usa componentes inteiros selecionados deterministicamente, até 1.200 faixas, e
as atribuições já congeladas. Não redesenha splits. Testa externo 0/três internos,
seis alphas, quatro blocos Ridge e referências média/mediana, com até 78 ajustes
pequenos. Recarrega modelos e confere reprodução de previsões. Não é avaliação
científica ou estimativa confiável de duração integral; não concluir ganho pelo smoke.

Os logs inner_fit indicam externo/bloco/interno/alpha e tempo; outer_block marca
parte externa salva. Nenhuma rede, encoder, SSD do LRCLIB ou novo vetor; usa CPU
com duas threads. Não exige instalação/download de dependências nesta execução.

Ao terminar, envie a saída. Agregados em
`C:\Users\Concursos Felipe\Documents\UnB\TCC\reports\modelagem_200k_v1\smoke\`:
resumo_modelagem.json e relatorio_modelagem.md. Esperado completed=true, quatro
partes Ridge concluídas, reload_max_abs_difference<=1e-8, global_metrics_available=false.
As duas referências também ficam salvas. Isso só libera o gate técnico para all;
não inicia escala nem transforma o smoke em resultado da monografia.

## 2. Primeiro lote de produção — concluído

```powershell
& "C:\Users\Concursos Felipe\Documents\UnB\TCC\.venv\Scripts\python.exe" "C:\Users\Concursos Felipe\Documents\UnB\TCC\scripts\22_modelar_dominio_observado_200k.py" all --limit-outer-blocks 1
```

Executa uma nova parte externa Ridge, começando pelo Combinado no fold externo 0:
18 ajustes internos, um refit externo e duas referências. A ordem usa primeiro
o bloco de maior dimensão para medir custo na coorte real. Não extrapolar seu
tempo como garantia; os outros folds/blocos podem ter convergência diferente.
O lote é parte da execução definitiva e fica salvo. completed=false e saída 2
são esperados com 19 partes pendentes; não é falha.

Resultado revisado: 18 ajustes internos salvos (máximo 352 iterações, sem avisos),
refit e duas referências; 15.507 previsões por parte, treino externo 62.028.
Hashes dos modelos/previsões e selo conferidos; não foram desserializados pelo
agente. Extrapolação simples: 19 × 67,775 / 60 = 21,46 min restantes se cada parte
tivesse o mesmo custo; blocos/folds/carga podem alterar duração. Não é garantia
ou intervalo estatístico. Seguir pela seção 3 para retomar sem limite.

Outputs em reports/modelagem_200k_v1/integral. Tempo do lote revisado;
não publica métricas globais parciais com observações diferentes entre blocos.
Os ajustes do smoke ficam em cache separado, não são misturados à escala real.

## 3. Continuação integral — concluída

```powershell
& "C:\Users\Concursos Felipe\Documents\UnB\TCC\.venv\Scripts\python.exe" "C:\Users\Concursos Felipe\Documents\UnB\TCC\scripts\22_modelar_dominio_observado_200k.py" all
```

Total previsto: 360 ajustes internos, 20 refits Ridge e dez referências. Usa as
mesmas 77.535 faixas/folds entre blocos; grade fixa, imputação/escala/categorias
aprendidas só em cada treino. Sem PCA, ajuste de encoder, clipping de previsões
ou seleção pelo resultado externo. MAE não ponderado primário, RMSE/R² complementares;
MAE ponderado original calculado nas mesmas previsões, sem treino ponderado.

Ao concluir: 20/20 partes Ridge, 77.535 previsões externas por variante, seis
variantes (quatro blocos + duas referências) e cinco contrastes incrementais.
Públicos: resumo_modelagem.json, relatorio_modelagem.md, metricas_externas.csv,
incrementos_pareados.csv e alphas_selecionados.csv. Delta negativo de MAE indica
menor erro no primeiro bloco do contraste. Sem intervalos/p-valores nesta etapa;
não tratar faixas/folds como réplicas independentes para inventar significância.

## Interromper e retomar

Ctrl+C uma vez; aguardar o prompt PowerShell antes de fechar/desligar. Checkpoints
SQLite por ajuste interno concluído e modelos/previsões por parte externa. O
ajuste em andamento pode ser refeito; os anteriores confirmados são reutilizados.
Repita o mesmo modo; para completar o lote parcial use all sem limite.
Uma instância por vez; manter computador sem suspensão durante a execução.

Privados em data/derived/private_regression_200k_v1: state.sqlite, gate/owner,
smoke/parts, integral/parts e integral/predicoes_externas.parquet. Modelos joblib,
previsões, IDs e checkpoints não devem ser publicados/versionados. Preservar cache;
hash divergente interrompe para diagnóstico, não apagar partes para desbloquear.

Protocolo novo: protocolo_regressao_200k_v1.md. Código/protocolo entram no selo;
depois da execução real, atualizar status neste guia/estado sem editar os arquivos
selados. Estudo do domínio observado e exposição histórica continuam explícitos.
