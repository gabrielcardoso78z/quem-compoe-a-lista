# Testes de robustez (14/10/2026)

Script: `auxiliares/_robustez_2026-10-14.py`. Saída: `data/saida_robustez_2026-10-14.txt` e `data/resultado_robustez_comarcas.csv`.

1. **Profissão ausente (limites de pior caso).** Todas as entradas sem profissão das listas usadas no perfil foram atribuídas ao grupo em questão (teto) ou a nenhum (piso).
   - 1ª Vara (2014 a 2024): grupo 2 = 49,7%, entre 46,4% e 53,1%, contra 24,0% da população ocupada; grupos 7 a 9 = 10,3%, entre 9,6% e 16,2%, contra 25,5%.
   - 2ª Vara, só listas com 90% ou mais de profissão (2015 a 2020): grupo 2 = 38,5%, entre 35,7% e 43,0%; grupos 7 a 9 = 15,4%, entre 14,2% e 21,6%.
2. **Critério de completude mais exigente.** Só listas com 90% ou mais de profissão: dissimilaridade de 25,7 (1ª Vara) e 21,4 (2ª Vara), contra 26,0 e 22,0 com o critério de 70%.
3. **Censo 2010 em todos os anos.** A dissimilaridade em relação ao Censo 2010 é maior que em relação ao de 2022 em todos os anos, em cerca de 4 pontos (`data/resultado_censo2010_curitiba.csv`).
4. **Denominador alternativo.** Entre os eleitores de 18 a 69 anos (TSE, 2024), 24,5% têm superior completo em Curitiba, praticamente a mesma proporção do grupo 2 entre os ocupados (24,0%). Nas 67 comarcas com dissimilaridade, o grupo 2 da lista supera a proporção de eleitores com superior completo em todas, com razão mediana de 4,4.
5. **Tamanho das listas.** Num sorteio simulado do mesmo tamanho (multinomial, 2.000 repetições, semente 20261014), a dissimilaridade esperada tem mediana de 8,7 (de 2,2 a 13,7), e o percentil 95 tem mediana de 13,2 (máximo de 20,4). A observada tem mediana de 56,8 (mínimo de 18,9) e fica acima do percentil 95 nas 67 comarcas.
6. **Completude na 1ª Vara.** Nos anos de baixa completude (2023: 35%; 2025: 21%; 2026: 10%), as entradas com profissão têm grupo 2 de 54,7%, 55,1% e 58,0%, contra 50,4% a 53,7% nos anos de alta completude. A direção é a mesma, mas a magnitude é só indicativa.
7. **Fluxo das listas do estado.** São 672 editais localizados e 667 listas examinadas. Delas, 661 foram aprovadas nas verificações (5 reprovadas por coerência de data e 1 por duplicidade), o que resulta em 644 listas distintas: das 17 republicações da mesma comarca, fase e ano, fica a última.
