# Base comum e folds 5x3 — execução concluída

**Concluído pelo pesquisador:** 8,323 s; 77.535 faixas, 77.051 vetores auditados,
21.893 componentes, maior 186, zero metadados inválidos/ausentes. Folds externos
de 15.507, internos de 20.676 em avaliação; grupos separados. O comando abaixo
é registro de reprodução, não repetir para continuar. Próximo: script 22 smoke,
conforme execucao_regressao_200k_v1.md.

As representações terminaram: 77.051 vetores, 77.535 referências de faixas e zero
pendências. Não repetir scripts 17/19/20, download ou smoke. O próximo script
reutiliza tudo; não baixa/carrega encoder, gera letras/embeddings ou treina modelos.

```powershell
& "C:\Users\Concursos Felipe\Documents\UnB\TCC\.venv\Scripts\python.exe" "C:\Users\Concursos Felipe\Documents\UnB\TCC\scripts\21_preparar_base_modelagem_200k.py"
```

Pode executar a partir de System32: os caminhos são absolutos. Não precisa de
internet nem do SSD do dump. Executar uma instância; não rodar 19/20 simultaneamente.
Essa etapa faz auditoria/montagem/folds, não as horas de inferência do encoder.
A duração real ainda não foi medida nesta coorte; acompanhar os cinco estágios.

O script confere fontes/selos, o alinhamento de todas as faixas e hashes dos
vetores por lotes; preserva as colunas/pesos e acrescenta spotify_popularity e
15 model_*. Metadados inválidos viram nulos apenas nas colunas novas, com contagens
e registro privado; não há exclusão automática. A política de pesos aprovada é
registrada, sem aplicá-los na preparação. As transformações aprendidas ficam
para o treino futuro. Descritores/vetores anteriores permanecem intactos.

Reutiliza/audita os componentes da etapa 19 e produz folds externos/internos
comuns aos quatro blocos, sem usar popularidade para dividir. Protocolo em
protocolo_base_modelagem_200k_v1.md; método/ponderação em
metodologia_modelagem_200k_v1.md (D-017).

## Ao terminar

Agregados em `C:\Users\Concursos Felipe\Documents\UnB\TCC\reports\base_modelagem_200k_v1\`:

- resumo_base_modelagem.json e relatorio_base_modelagem.md;
- folds_agregados.csv e qualidade_metadados.csv.

Avise com a saída para revisão. Esperado: completed=true, 77.535 faixas, 77.051
vetores, dimensão 384, 21.893 componentes, maior 186, CV 5x3 e auditorias de
separação/alinhamento aprovadas. models_trained=false. Contagens de inválidos
de metadados ainda são desconhecidas; verificar o relatório antes de modelar.

Privados, não publicar: `data/derived/private_modeling_200k_v1/` contém
coorte_modelagem.parquet (originais + campos novos), folds_5x3.parquet,
blocos.json (listas explícitas e referências aos vetores), metadados_invalidos.parquet
e owner.json. As quatro matrizes não são copiadas; todos usam o mesmo alinhamento.

## Interrupção ou divergência

Ctrl+C interrompe sem alterar fontes/embeddings. Repetir este comando recomeça
apenas as auditorias/montagem/folds determinísticos, sem recalcular representações.
completed=false não libera treinamento. Divergência de selo, índice, vetor ou
grupo interrompe e preserva dados; não apagar o checkpoint de embeddings nem
trocar faixas para desbloquear a etapa. Se código/protocolo mudar, a saída antiga
fica preservada e o script exige diagnóstico, não sobrescreve silenciosamente.

Depois da revisão dos agregados: preparar o runner de regressões pareadas e o
plano de custo, mantendo treino manual, MAE primário não ponderado, RMSE/R²
complementares e MAE ponderado de sensibilidade nas mesmas previsões externas.
Nenhum treino inicia ao concluir o script 21.
