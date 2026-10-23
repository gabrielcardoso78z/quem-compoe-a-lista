# Piloto de ausências (22/10/2026)

**Pergunta.** Quando o extrator diz que a lista de uma comarca não foi localizada no Diário, o edital de fato não existe na coleta, ou existe e o extrator não o achou?

## População e amostra
- Obrigações: comarca × tipo de lista (provisória, definitiva) × ano da lista (2023 a 2026).
- Comarcas: as 161 do CODJ (`data/codj_comarcas.csv`) menos Curitiba e Cascavel, mais Paiçandu (tem edital localizado e não consta do CODJ): 160 comarcas, 1.280 obrigações.
- Situação no extrator (mesma regra de `analise_censo_estadual.py`: comarca, tipo e ano legíveis, ano coerente com a data, última veiculação, prazo tolerante até o dia 10): 202 `no_prazo`, 419 `fora_do_prazo`, 659 `nao_localizada`.
- Amostra estratificada, semente 20261022: 10 `nao_localizada`, 5 `fora_do_prazo`, 5 `no_prazo` (os dois últimos estratos servem de controle).
- Janela de busca de cada obrigação: 1º de agosto do ano anterior à lista até 30 de setembro do ano da lista (a mesma regra de coerência da análise).

## Cobertura da coleta
- 971 edições baixadas entre 01/08/2022 e 30/09/2026; 117 dias úteis sem edição, concentrados em dezembro e janeiro (recesso) e em feriados. Os dias faltantes que não forem feriado ou recesso devem ser conferidos no portal antes de concluir que algo "não foi publicado".

## Pré-busca (`buscar_candidatos.py`)
- Texto de cada edição por `pdftotext -layout`; cache fora do repositório (`~/piloto_cache`), só com as páginas que contêm "jurad".
- Página candidata: menciona o nome da comarca (sem acento, palavra inteira) na janela.
- Sinais contados num trecho de 800 caracteres em torno de cada menção: "lista geral", "alistad", "alistamento", "art. 425", "art. 426", "provisori", "definitiv" e sinais de sessão (sorteio, reunião, convocação, suplente). `candidata_forte` = algum sinal de alistamento no trecho.
- Limite já observado: a lista de controle P16 (localizada no prazo pelo extrator) aparece como candidata, mas **não** como forte. Portanto a conferência manual deve abrir **todas** as páginas candidatas, não só as fortes. P02 não tem nenhuma página candidata: conferir também por outras grafias e pelo índice da edição.
- Nenhum nome de pessoa é gravado ou impresso; o cache contém texto integral e não deve ser publicado.

## Conferência manual (`piloto_obrigacoes.csv`)
Para cada obrigação, abrir no PDF todas as páginas de `piloto_candidatos.csv` com o mesmo `id` e preencher:
- `edital_existe_no_dje`: sim / não / incerto
- `edicao_encontrada`, `data_disponibilizacao`, `pagina`
- `tipo_correto` e `comarca_correta` (para os controles: o extrator acertou?)
- `edicoes_examinadas`: quantas páginas candidatas foram abertas
- `classificacao_final`: `ausencia_real` | `falha_do_extrator` | `erro_de_tipo` | `erro_de_comarca` | `correto` | `incerto`
- `observacao`, `conferido_por`, `data_conferencia`

## O que o piloto pode e não pode dizer
- Pode mostrar que o falso "não localizada" existe nos dados e dar uma ordem de grandeza.
- Com 10 casos, não estima taxa com precisão; serve de prova de existência e para calibrar o gabarito do mestrado.

## Triagem assistida (22/10/2026, antes da conferência humana)
Método: para cada página candidata, o texto em ordem de leitura (`pdftotext` sem `-layout`) das páginas vizinhas foi dividido nas matérias do Diário (marcadores `IDMATERIA`); cada matéria que menciona a comarca e contém "jurad" ou "alistad" teve título, fecho ("Comarca de ...") e sinais lidos e classificados (lista geral de qual comarca, convocação, intimação etc.). Nos controles, a matéria do extrator foi lida para conferir comarca, caráter (provisório/definitivo) e ano. Resultado em `piloto_triagem.csv` (sugestão e evidência por obrigação). A classificação final continua sendo a da conferência humana.

Resultado da triagem:
- Não localizadas (P01 a P10): em nenhuma das 10 há edital de lista geral da obrigação na coleta. As listas que apareciam como candidatas eram de comarcas vizinhas na ordem alfabética do Diário (Matelândia, Jaguariaíva, Alto Piquiri, Congonhinhas, Santa Isabel do Ivaí), já capturadas pelo extrator. Com 0 em 10, o limite superior de 95% para a taxa de falso "não localizada" é de cerca de 31% (Clopper-Pearson): o piloto não detecta o problema, mas é pequeno demais para descartá-lo.
- Controles (P11 a P20): 10 em 10 com comarca, caráter e ano corretos.
- Achado lateral: em 4 dos 5 controles "fora do prazo" (P12 a P15), o edital foi assinado no último dia do prazo (10/10 ou 10/11) e disponibilizado de 2 a 6 dias depois. O atraso está entre a assinatura e a disponibilização, o que põe em questão se o prazo do art. 426 se refere ao ato do juiz ou à publicação.
- Pontos a conferir na leitura humana: P02 (comarca sem nenhuma menção na janela: verificar se tem Vara do Júri própria), P04 (lista da Vara do Júri de Congonhinhas com atos de Cornélio Procópio ao lado) e P10 (lista de 2022-10-14_ed3305 atribuída a Santo Antônio da Platina com confiança "diverge").

## Segunda leitura independente (22/10/2026)
Um segundo leitor automático, sem acesso à triagem anterior, releu as matérias das páginas candidatas (decidindo a comarca pelo cabeçalho e pelo fecho de cada edital), buscou "alistad" + nome da comarca em todas as edições de cada janela e conferiu os controles na edição do extrator. Resultado em `piloto_segunda_leitura.csv`.
- Concordância com a triagem: 20 em 20 classificações (10 `ausencia_real`, 10 `correto`).
- Dúvidas da triagem resolvidas: P04, as listas são da Vara do Júri de Congonhinhas, e de Cornélio Procópio só há convocação para sessão; P10, a lista de 2022-10-14_ed3305 é mesmo a provisória de 2023 de Santo Antônio da Platina, publicada sem fecho; P02, nenhuma publicação do Júri de São João do Triunfo na janela (726 páginas com "Triunfo", nenhuma de lista).
- Observações para o extrator e o método: lista republicada (Ibaiti, definitiva de 2025, em 17/02 e 23/09/2025); edital sem fecho (Santo Antônio da Platina) e com dia em branco no fecho (São João); Rolândia é Foro Regional, não comarca (afeta o denominador).
- Rótulo do resultado: triagem automatizada com dupla leitura independente, sem conferência humana.

## Cobertura conferida (22/10/2026)
- Numeração das edições baixadas (julho de 2022 a setembro de 2026): contínua, sem nenhum salto entre edições consecutivas e sem dia com duas edições. Logo, nenhuma edição do período falta na coleta.
- Os 117 dias úteis sem edição: 51 de recesso forense (20/12 a 6/1), 50 de feriados nacionais, estaduais, municipais de Curitiba ou forenses (incluídos Carnaval, Cinzas, Quinta e Sexta Santas e Corpus Christi) e 16 de ponte junto a feriado (sexta depois de quinta-feira de feriado, segunda antes de terça de feriado, 18/12 antes da Emancipação do Paraná). Nesses dias o Diário não circulou.
