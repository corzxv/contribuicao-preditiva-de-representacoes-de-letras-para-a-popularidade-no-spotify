# Parecer estatístico — critérios congelados (01/11/2026)

Escopo inicial: resultado completo v2, sem consultas ao SSD; atualizar separadamente
depois de aplicação completa v3. Os mil casos diagnósticos não aprovam o conjunto.
Conhecemos resultados anteriores: este protocolo não cria confirmação independente.

Primários: médias de popularidade, danceability, energy, loudness, speechiness,
acousticness, instrumentalness, liveness, valence, tempo, duração e ano; proporções
de todos os gêneros, períodos e bandas de popularidade (80–89/90–100 separadas).
Sem excluir categorias raras. Médias usam valores finitos; ausências e violações
dos domínios locais são reportadas separadamente. Key/mode/time_signature são
atributos discretos descritos, não médias contínuas primárias.

Margens: ±1 ponto na popularidade (pequena diferença na escala 0–100); ±0,10 DP
populacional do catálogo em médias contínuas/ano (diferença relativa à dispersão);
min(0,01; 0,20 p_cat) em proporções (limita discrepância absoluta e protege raras).
Escolhas práticas do estudo, não limites universais ou garantias de modelos.
Não ajustá-las para obter aprovação depois de observar a rodada.

Catálogo é população finita conhecida por agregados auditados, sem erro amostral
nessa comparação. Para domínio D (aceitas/não aceitas), variável válida I_V e
estrato h, a razão ponderada é R=sum(w I_D I_V y)/sum(w I_D I_V), w=N_h/n_h.
Resíduo z_i=I_D I_V(y_i-R), zero fora do domínio, calculado em TODA a amostra.
Taylor: V(R)=sum_h[N_h²(1-n_h/N_h)s²_zh/n_h]/[sum(w I_D I_V)]².
Censo tem contribuição zero; n_h<2 não censitário torna variância não estimável.
Graus de liberdade Satterthwaite: (sum V_h)²/sum[V_h²/(n_h-1)].
O parâmetro é a média/proporção populacional no domínio de aceitação sob protocolo
fixo; não a média de letras não observadas. Supõe AAS sem reposição em cada estrato,
domínio e características fixos, independência entre estratos e linearização válida.
Erro de matching, incerteza do snapshot e mudança de protocolo não entram no EP.

Sem pesos: finalidade descritiva do conjunto observado. EP também respeita desenho,
mas estima razão da população inclinada pela alocação (fator fixo n_h/N_h por
estrato); no numerador da variância substituir N_h² por n_h². Esse parâmetro NÃO
é o domínio populacional do catálogo; não sustenta o parecer primário.

TOST de Wald/Taylor a 5%: IC90% da diferença inteiramente dentro da margem apoia
equivalência. IC95% inteiramente além de uma margem apoia diferença relevante
individual; caso contrário, inconclusivo. Ausência de equivalência não é prova de
diferença. Informar EP, graus de liberdade, IC90/95, diferença relativa/padronizada,
margem, n real, denominador e p-TOST. Não fazer teste de duas amostras independentes.

Multiplicidade: conclusão conjunta de equivalência é interseção de TODOS os testes
primários ponderados (intersection-union, cada TOST a 5%, sem votação por maioria).
Para declarar incompatibilidade por alguma diferença relevante, exigir intervalo
Bonferroni simultâneo 95% além da margem; informar também inferências individuais.
ICs aproximados são frágeis em células esparsas: domínio válido <20, proporção com
<5 positivos fora de censo ou variância estimada zero fora de censo ficam
inconclusivos, sem fingir precisão. Estratos n<20, aceitas<5 e cobertura zero recebem
flags descritivas; nenhum registro é excluído. Variância zero fora de censo pode
ser consequência de amostra sem eventos, não evidência de certeza.

Outputs: CSV diagnóstico/equivalência, cobertura por estrato, quantis/distribuições/
qualidade por status, agregados catálogo/amostra de referência, status/motivos,
resumo e parecer Markdown A–E. Todos os campos originais/pesos são validados e
preservados. Resultado parcial/erros técnicos impede parecer favorável. Usar uma
das três conclusões exigidas; listar todas as falhas/inconclusivos no CSV e síntese
no parecer. Concordância marginal não prova equilíbrio multivariado, precisão do
matching, representatividade genérica ou suficiência preditiva. Não recalibrar pesos,
preencher cotas, substituir faixas ou excluir instrumentais. Modelagem futura requer
alcance declarado, revisão de matching e splits agrupados com histórico V0.6 exposto.

Referências verificadas: [Lohr, Sampling: Design and Analysis, 3ª ed. (2022)](https://www.sharonlohr.com/sampling-design-and-analysis-3e),
desenho, razões e domínios; [Lohr (2023), Assuming a Nonresponse Model Does Not Make
It True](https://hdsr.mitpress.mit.edu/pub/sqinvh4c/release/1), DOI
10.1162/99608f92.2b901b7f, hipóteses de seleção não garantidas pelos pesos;
[Lakens (2017)](https://pure.tue.nl/ws/portalfiles/portal/80918653/lakeequi2017.pdf),
DOI 10.1177/1948550617697177, TOST e margens explícitas. A adaptação da incerteza ao
desenho é nossa implementação Taylor; não atribuímos fórmulas de survey ou nossas
margens a Lakens, nem páginas não verificadas a Lohr.
