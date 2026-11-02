# Trecho da linha recente do TCC

Projeto parcial de métodos, resultados e discussão do domínio observado de
77.535 faixas. Usa apenas agregados já concluídos; não inclui letras, bases,
modelos, previsões individuais ou credenciais. A integração Spotify-LFM2b antiga
permanece no pacote histórico separado; suas métricas não foram misturadas.

Upload do ZIP no Overleaf: main.tex como principal, pdfLaTeX/UTF-8, duas passagens.
Nenhum Python ou dado externo é necessário para compilar. Bibliografia incluída.
Para integrar ao TCC maior, copiar sections/tables/images/references e adaptar
apenas a hierarquia/pacotes; consolidar bibliografia, sem sobrescrever capítulos
anteriores. A aparência segue o trecho histórico, sem afirmar classe oficial UnB.

Quatro figuras em PNG 300 dpi e SVG editável. Dados agregados em source_data/,
proveniência/hashes em PROVENIENCIA.json. manuscrito.json é fonte compartilhada
para TeX e PDF de leitura. O PDF de leitura opcional é gerado por ReportLab;
não é exportação da compilação TeX e pode ter paginação diferente. O preview
LaTeX é verificado separadamente no editor integrado.

Gerador reproduzível: scripts/24_consolidar_resultados_monografia.py. Opera
somente em agregados públicos pequenos. Recusa sobrescrever projeto editado
manualmente: após revisar texto no editor, usar outro destino para regeneração.
Nenhum código/protocolo/modelo 19-23 foi modificado. Não é a monografia completa;
introdução, fundamentação/fontes completas, revisão dirigida de matching e
adequação ao template institucional ainda precisam ser integradas.
