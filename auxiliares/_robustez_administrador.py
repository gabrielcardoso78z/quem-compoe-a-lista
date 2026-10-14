#!/usr/bin/env python3
"""Robustez: efeito de classificar "administrador(a)" no grupo 1 (diretores e gerentes) em vez do grupo 2,
como fez a codificacao manual da 2a rodada. Mesmo recorte de analise_perfil.py (definitivas 2014-2026, listas
com >=70% de profissao). So agregados. Rodar da raiz do projeto."""
import csv, os, sys, re
from collections import Counter, defaultdict
sys.path.insert(0, os.getcwd())
from codificar_profissoes import classificar, norm
import importlib.util
src = open("analise_perfil.py", encoding="utf-8").read()
CENSO = eval(re.search(r"CENSO = (\{.*?\})", src, re.S).group(1)); tc = sum(CENSO.values())
G1 = "1 Diretores e gerentes"
listas = defaultdict(list)
for r in csv.DictReader(open("data/base_listas.csv", encoding="utf-8")):
    a = int(r["ano"])
    if r["tipo"] == "definitiva" and 2014 <= a <= 2026: listas[(r["vara"], a)].append(r["profissao"])
def perfil(variante):
    g = defaultdict(Counter); nadm = Counter()
    for (v, a), profs in listas.items():
        if sum(1 for p in profs if p.strip()) / len(profs) < 0.7: continue
        for p in profs:
            c, _ = classificar(p)
            if not c[0].isdigit(): continue
            adm = norm(p) in ("ADMINISTRADOR", "ADMINISTRADORA")
            if adm: nadm[v] += 1
            if variante and adm: c = G1
            g[v][c] += 1
    return g, nadm
base, nadm = perfil(False); alt, _ = perfil(True)
print("vara | adm (% das classificadas) | grupo1 base->alt | grupo2 base->alt | grupos1+2 | dissimilaridade base->alt")
for v in sorted(base):
    tb, ta = sum(base[v].values()), sum(alt[v].values())
    pct = lambda G, k, t: 100 * G[v][k] / t
    dis = lambda G, t: 50 * sum(abs(G[v][k] / t - CENSO[k] / tc) for k in CENSO)
    g2 = "2 Profissionais das ciencias e intelectuais"
    print(f"{v} | {nadm[v]} ({100*nadm[v]/tb:.1f}%) | {pct(base,G1,tb):.1f} -> {pct(alt,G1,ta):.1f} | {pct(base,g2,tb):.1f} -> {pct(alt,g2,ta):.1f} | {pct(base,G1,tb)+pct(base,g2,tb):.1f} | {dis(base,tb):.1f} -> {dis(alt,ta):.1f}")
print(f"Censo 2022 Curitiba: grupo 1 {100*CENSO[G1]/tc:.1f}%, grupo 2 {100*CENSO['2 Profissionais das ciencias e intelectuais']/tc:.1f}%")
