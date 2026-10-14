"""Teste rápido de H3 (14/10/2026): a permanência da lista se associa ao desvio ocupacional?
Entrada agregada: data/resultado_censo_comarcas_entrancia.csv (sem dados pessoais).
Saída: correlação entre permanência mediana por comarca e dissimilaridade; casos de renovação integral."""
import csv, statistics as st
r = list(csv.DictReader(open('data/resultado_censo_comarcas_entrancia.csv')))
def perm(x): return [float(a) for a in x['permanencias'].split(';') if a.strip()]
rows = [x for x in r if x['dissimilaridade_censo'] not in ('', 'nan') and perm(x)]
pairs = [(st.median(perm(x)), float(x['dissimilaridade_censo'])) for x in rows]
n = len(pairs); mx = st.mean(p for p, _ in pairs); my = st.mean(d for _, d in pairs)
cov = sum((p - mx) * (d - my) for p, d in pairs) / n
print('comarcas', n, 'r(permanencia, dissimilaridade) =', round(cov / (st.pstdev([p for p, _ in pairs]) * st.pstdev([d for _, d in pairs])), 2))
for c in ['Jacarezinho', 'Paranaguá', 'Pato Branco', 'Terra Roxa', 'Arapongas', 'Cambé']:
    for x in r:
        if x['comarca'] == c: print(c, x['entrancia'], x['dissimilaridade_censo'] or 'sem dissimilaridade', x['permanencias'])
