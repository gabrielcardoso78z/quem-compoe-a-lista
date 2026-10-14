# Quem compõe a lista?

Código, regras de classificação, protocolo e resultados agregados da pesquisa **"Quem compõe a lista? Perfil ocupacional e renovação das listas gerais de jurados em Curitiba e no Paraná"**, de Gabriel Pinto Cardoso, com orientação de Khalil Aquim (Faculdade Inspirar, Curitiba). A pesquisa está em andamento; este repositório acompanha a versão de outubro de 2026.

A pesquisa compara as listas gerais de jurados, que o art. 426 do Código de Processo Penal manda publicar com a profissão de cada alistado, com a estrutura ocupacional da população (Censo 2022). O material cobre as duas Varas do Tribunal do Júri de Curitiba (2009 a 2027) e os editais de lista geral das demais comarcas do Paraná publicados no Diário da Justiça (2022 a 2026), além dos editais de convocação de jurados.

## O que está aqui

| Pasta ou arquivo | Conteúdo |
| --- | --- |
| `PROTOCOLO.md` | Capítulo de metodologia e notas metodológicas (coleta, leitura, pseudonimização, codificação, validação, auditoria, medidas, limites) |
| `ROBUSTEZ.md` | Testes de robustez feitos depois dos pareceres externos (outubro de 2026) |
| `coletar_*.py`, `baixar_dje.py` | Coleta das listas no site do TJPR e das edições do Diário da Justiça Eletrônico |
| `processar_*.py`, `leitores_listas.py`, `dje_comum.py`, `buscar_dje.py`, `montar_base.py` | Leitura dos documentos, extração das entradas e pseudonimização na leitura |
| `verificar_comarcas.py`, `auditar_anomalias_comarcas.py`, `scripts_auxiliares/` | Verificações automáticas, auditoria manual e teste de regressão |
| `codificar_profissoes.py` | Regras de classificação das profissões nos grandes grupos da COD (IBGE) |
| `codificacao_profissoes.csv` | Tabela grafia → categoria, só com grafias formadas por palavras frequentes (781 grafias, cerca de 95% das entradas; ver "Proteção de dados") |
| `analise_*.py`, `rodar_tudo.py`, `auxiliares/` | Análises: perfil ocupacional, dissimilaridade, renovação, sorteados, sexo pelo prenome, censo estadual, Buenos Aires, testes de Duren, robustez |
| `validacao/` | Validação da classificação: 1ª rodada (amostra, gabarito, cálculo do kappa) e 2ª rodada (regras congeladas por hash; amostra nova; aguardando codificação) |
| `data/` | Somente resultados agregados (`resultado_*.csv`, `saida_*.txt`, `aprof_*.csv`, `verificacao_*.csv`) |

## O que não está aqui, e por quê

As listas de jurados trazem nome e profissão de pessoas físicas. Embora sejam publicadas por força de lei, o repositório não redistribui dados pessoais (Lei nº 13.709/2018, art. 6º, I e III, e art. 7º, §§ 3º e 7º). Por isso ficam de fora:

- os documentos originais (páginas do site, PDFs e textos do Diário da Justiça);
- as bases com uma linha por alistado, mesmo pseudonimizadas;
- a chave secreta da pseudonimização;
- as grafias raras de profissão, nas quais a leitura automática pode ter colado parte do nome de outra entrada.

Quem quiser reproduzir a pesquisa pode coletar de novo os documentos públicos com os próprios scripts (`rodar_tudo.py`). Para isso, crie na raiz um arquivo `.chave_secreta` com uma sequência aleatória própria (por exemplo, `python3 -c "import secrets; print(secrets.token_hex(32))" > .chave_secreta`). Os identificadores gerados serão outros, mas todas as medidas agregadas independem da chave.

## Proteção de dados

- Os nomes são pseudonimizados na leitura: o nome normalizado, concatenado à chave secreta, passa por SHA-256, e só o identificador resultante circula nas bases de análise (art. 13, § 4º, da LGPD).
- Pseudonimização não é anonimização: quem tiver a chave e uma lista de nomes pode refazer os identificadores. Por isso a chave e os originais ficam só no computador do pesquisador e não são publicados.
- O identificador também não distingue homônimos, limite descrito no protocolo.
- Só se publicam resultados agregados; categorias com menos de cinco pessoas são reunidas.
- A tabela `codificacao_profissoes.csv` publicada mantém só grafias cujas palavras somam ao menos 50 ocorrências no conjunto. Assim ficam de fora as grafias raras em que a leitura automática pode ter colado parte do nome de outra entrada.
- Nas amostras de validação (`validacao/amostra_para_codificar.csv` e `validacao/rodada2/amostra_r2.csv`), as palavras que não aparecem no vocabulário frequente da tabela de codificação foram substituídas por "[…]" (42 palavras em 32 entradas), pelo mesmo motivo. As categorias atribuídas e o cálculo do kappa não dependem dessas palavras.

## Como rodar

Requer Python 3.10 ou superior, `pdftotext` (poppler) e as bibliotecas `requests`, `beautifulsoup4` e `openpyxl`. Na raiz, `python3 rodar_tudo.py` refaz a coleta, a leitura e as análises. Os dados externos de referência (IBGE, SIDRA 10264 e 3592; TSE, perfil do eleitorado 2024; tabela de prenomes do Censo 2010, Brasil.io) são públicos e baixados pelos scripts ou indicados no protocolo.

## Como citar

CARDOSO, Gabriel Pinto; AQUIM, Khalil. **Quem compõe a lista?** Código, protocolo e resultados agregados. Curitiba, 2026. Repositório de pesquisa.

## Licença

Código sob a licença MIT (`LICENSE`). Documentação e resultados agregados sob CC BY 4.0.
