#!/usr/bin/env python3
"""Curitiba: listas definitivas x populacao ocupada no Censo 2010 (SIDRA 3592) e no Censo 2022 (SIDRA 10264), ano a ano.
Mesma regra de analise_aprofundada.py (B): grandes grupos da COD, ocupacoes maldefinidas fora, indice de dissimilaridade
de Duncan so para listas com profissao em ao menos 70% das entradas. Censo 2010: pessoas de 10 anos ou mais; 2022: 14 ou mais.
Saida agregada: data/resultado_censo2010_curitiba.csv"""
import csv, json
from collections import Counter, defaultdict
from codificar_profissoes import classificar
from analise_perfil import CENSO as C22
C10 = {k: v for k, v in json.load(open("referencias/dados_ibge/SIDRA_3592_Curitiba_grupos_ocupacao_2010.json"))["pessoas"].items() if k in C22}
assert set(C10) == set(C22)
p10 = {g: C10[g] / sum(C10.values()) for g in C10}; p22 = {g: C22[g] / sum(C22.values()) for g in C22}
P = defaultdict(list)
for r in csv.DictReader(open("data/base_listas.csv", encoding="utf-8")):
    if r["tipo"] == "definitiva": P[(r["vara"], int(r["ano"]))].append(r["profissao"])
print("Populacao ocupada (% sem maldefinidas): grupo  2010  2022")
for g in sorted(C22): print(f"  {g[:45]:45} {100*p10[g]:5.1f} {100*p22[g]:5.1f}")
print("Dissimilaridade entre os dois censos:", round(50 * sum(abs(p10[g] - p22[g]) for g in C22), 1))
out = []
print("\nvara ano info%  D_2010  D_2022  g2_lista  g2/2010  g2/2022  g9_lista  g9/2010  g9/2022")
for (v, a) in sorted(P):
    profs = P[(v, a)]; info = sum(1 for p in profs if p.strip()) / len(profs)
    if info < .7: continue
    cat = Counter(classificar(p)[0] for p in profs); occ = {g: cat[g] for g in C22}; to = sum(occ.values())
    pl = {g: occ[g] / to for g in C22}
    d10 = round(50 * sum(abs(pl[g] - p10[g]) for g in C22), 1); d22 = round(50 * sum(abs(pl[g] - p22[g]) for g in C22), 1)
    g2, g9 = "2 Profissionais das ciencias e intelectuais", "9 Ocupacoes elementares"
    row = [v, a, round(100 * info), d10, d22, round(100 * pl[g2], 1), round(pl[g2] / p10[g2], 2), round(pl[g2] / p22[g2], 2),
           round(100 * pl[g9], 1), round(pl[g9] / p10[g9], 2), round(pl[g9] / p22[g9], 2)]
    out.append(row); print(*row, sep="\t")
with open("data/resultado_censo2010_curitiba.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f); w.writerow(["vara", "ano", "pct_com_profissao", "dissimilaridade_censo2010", "dissimilaridade_censo2022", "pct_grupo2",
                                   "razao_grupo2_2010", "razao_grupo2_2022", "pct_grupo9", "razao_grupo9_2010", "razao_grupo9_2022"]); w.writerows(out)
