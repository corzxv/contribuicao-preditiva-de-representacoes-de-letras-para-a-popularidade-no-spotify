# Publicação e conservação do repositório

A publicação e a renomeação foram autorizadas pelo pesquisador. O endereço
da edição atual é `corzxv/contribuicao-preditiva-de-representacoes-de-letras-para-a-popularidade-no-spotify`, ramo `master`.
O repositório é privado. Novos commits e comentários usam português.

## Conteúdo versionado

Código Python, entradas CLI, testes sintéticos, configurações de exemplo,
protocolos, dicionário, decisões, proveniência, agregados e materiais acadêmicos.
O PDF, o ZIP para Overleaf e as fontes da edição em
`reports/monografia_template_overleaf` são os pontos de entrada. As versões
anteriores já publicadas documentam a trajetória no Git. Cópias editoriais
intermediárias e o pacote local de preservação permanecem no computador.
Os scripts antigos usados para formar os insumos atuais preservam a
proveniência e as dependências da análise final.

Os dados brutos/individuais, letras, respostas integrais de APIs, SQLite, vetores,
modelos e credenciais são locais. Também são locais planilhas de revisão com
casos individuais, prévias, interface auxiliar e pacotes de TCCs de terceiros.
`.gitignore` e a lista de publicação do módulo `git_publication.py` registram essa
distinção. Arquivos excluídos do índice não são apagados do computador.

## Conferência antes de publicar

```powershell
# Planeja somente; não adiciona arquivos.
.\.venv\Scripts\python.exe scripts\30_auditar_publicacao_git.py --planejar

# Depois da seleção explícita no Git, audita os blobs do índice.
.\.venv\Scripts\python.exe scripts\30_auditar_publicacao_git.py
```

A auditoria limita tamanho por arquivo/total, verifica caminhos e pacotes,
identificadores individuais em tabelas/JSONs e padrões de credenciais. Somente
categorias de problema são exibidas, sem imprimir segredos ou letras. Não é prova
universal de ausência de informação indevida; complementa a seleção e revisão
dos arquivos. Os testes verificam esses controles em fixtures sintéticas.

Dados e saídas individuais não foram lidos para montar a publicação. A varredura
é de arquivos candidatos de código, documentação e agregados, sem execução do
pipeline ou varredura do LRCLIB. O fluxo GitHub Actions usa apenas Python, Ruff,
pytest, Polars e testes leves de publicação/normalização; não instala o encoder ou
executa treinamento real.

## Histórico e hashes

Os oito arquivos retirados da versão atual continuam no disco e, quando antes
versionados, nos commits anteriores. Não houve expurgo ou reescrita do histórico.
Os códigos/protocolos selados e os resultados científicos são mantidos. A regra
`* -text` de `.gitattributes` conserva quebras de linha e hashes dos arquivos,
inclusive ao clonar em outro sistema; ver a documentação oficial de
[gitattributes](https://git-scm.com/docs/gitattributes).

A política de teste leve segue a separação entre tarefas de desenvolvimento e
execução integral manual. A estrutura do workflow usa a documentação de
[testes Python do GitHub Actions](https://docs.github.com/en/actions/tutorials/build-and-test-code/python).
Os resultados de auditoria/publicação são registrados nos relatórios do projeto;
não se confunde commit de código com execução científica dos scripts.
