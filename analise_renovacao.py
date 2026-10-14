#!/usr/bin/env python3
"""Etapa 1: renovacao das listas e mudancas entre provisoria e definitiva (2014-2027)."""
import csv, os
from collections import defaultdict, Counter
L = defaultdict(set)
for r in csv.DictReader(open("data/base_listas.csv", encoding="utf-8")):
    L[(r["vara"].replace("Curitiba ", ""), r["tipo"], int(r["ano"]))].add(r["pessoa_id"])
VARAS = ["1a Vara", "2a Vara"]
out = []
print("=== PERMANENCIA: parte da lista definitiva do ano que ja estava na definitiva do ano anterior ===")
for v in VARAS:
    for a in range(2014, 2027):
        cur, ant = L.get((v, "definitiva", a)), L.get((v, "definitiva", a - 1))
        if cur and ant:
            p = len(cur & ant) / len(cur)
            hist = set().union(*[L[(v, "definitiva", y)] for y in range(2009, a) if (v, "definitiva", y) in L])
            ph = len(cur & hist) / len(cur)
            print(f"{v} {a}: n={len(cur):5}  no ano anterior {100*p:5.1f}%  em algum ano anterior (desde 2009) {100*ph:5.1f}%")
            out.append([v, a, "definitiva", len(cur), round(100*p, 1), round(100*ph, 1)])
    cur, ant = L.get((v, "provisoria", 2027)), L.get((v, "definitiva", 2026))
    if cur and ant:
        p = len(cur & ant) / len(cur); print(f"{v} 2027 (provisoria): n={len(cur):5}  na definitiva 2026 {100*p:5.1f}%")
        out.append([v, 2027, "provisoria", len(cur), round(100*p, 1), ""])
print("\n=== QUANTOS ANOS CADA PESSOA APARECE NAS DEFINITIVAS 2014-2026 ===")
for v in VARAS:
    c = Counter()
    for a in range(2014, 2027):
        for p in L.get((v, "definitiva", a), ()): c[p] += 1
    dist = Counter(min(n, 10) for n in c.values())
    tot = len(c); faixas = {"1 ano": dist[1], "2 anos": dist[2], "3 a 5": sum(dist[k] for k in (3,4,5)), "6 a 9": sum(dist[k] for k in (6,7,8,9)), "10 ou mais": dist[10]}
    print(f"{v}: {tot} pessoas distintas; " + "; ".join(f"{k}: {n} ({100*n/tot:.1f}%)" for k, n in faixas.items()))
    # vagas ocupadas por quem aparece 5+ anos
    vagas = sum(c.values()); rep = sum(n for n in c.values() if n >= 5)
    print(f"   {100*rep/vagas:.1f}% das {vagas} vagas de 2014-2026 foram ocupadas por pessoas presentes em 5 anos ou mais")
print("\n=== PROVISORIA -> DEFINITIVA (mesmo ano) ===")
for v in VARAS:
    for a in range(2014, 2027):
        p, d = L.get((v, "provisoria", a)), L.get((v, "definitiva", a))
        if p and d:
            print(f"{v} {a}: prov {len(p):5} def {len(d):5} | sairam {len(p-d):5} ({100*len(p-d)/len(p):4.1f}% da prov) | entraram {len(d-p):5} ({100*len(d-p)/len(d):4.1f}% da def)")
print("\n=== MESMA PESSOA NAS DUAS VARAS NO MESMO ANO (definitivas) ===")
for a in range(2014, 2027):
    x, y = L.get(("1a Vara", "definitiva", a)), L.get(("2a Vara", "definitiva", a))
    if x and y: print(f"{a}: {len(x & y)}")
with open("data/resultado_renovacao.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f); w.writerow(["vara","ano","tipo","n","pct_no_ano_anterior","pct_em_algum_ano_anterior"]); w.writerows(out)
