#!/usr/bin/env python3
"""Perfil do eleitorado (TSE, perfil_eleitorado_2024) de Curitiba e Cascavel: genero, faixa etaria, escolaridade.
Universo de comparacao principal: eleitores de 18 a 69 anos (art. 436: maiores de 18; art. 437, IX: 70+ podem pedir dispensa).
Compara o % de mulheres com data/resultado_sexo.csv. Saida: data/resultado_tse.csv e data/resultado_sexo_vs_tse.csv"""
import csv, io, re, zipfile, unicodedata
from collections import Counter, defaultdict
def n(t): return unicodedata.normalize("NFKD", t).encode("ascii", "ignore").decode().upper().strip()
MUN = {"CURITIBA", "CASCAVEL"}
z = zipfile.ZipFile("referencias/dados_tse/perfil_eleitorado_2024.zip")
arq = "perfil_eleitorado_2024_PR.csv"
g = defaultdict(Counter); e = defaultdict(Counter); fx = defaultdict(Counter)
def idade_min(ds):
    m = re.search(r"(\d+)", ds); return int(m.group(1)) if m else -1
with z.open(arq) as f:
    for r in csv.DictReader(io.TextIOWrapper(f, encoding="latin-1"), delimiter=";"):
        if r["SG_UF"] != "PR" or n(r["NM_MUNICIPIO"]) not in MUN: continue
        m = n(r["NM_MUNICIPIO"]).title(); q = int(r["QT_ELEITORES"]); fa = r["DS_FAIXA_ETARIA"].strip()
        im = idade_min(fa); apto = 18 <= im <= 69 if im >= 0 else False
        fx[m][fa] += q
        for uni, ok in (("todos", True), ("18-69", apto)):
            if not ok: continue
            g[(m, uni)][n(r["DS_GENERO"])] += q; e[(m, uni)][n(r["DS_GRAU_ESCOLARIDADE"])] += q
rows = []
for (m, uni), c in sorted(g.items()):
    tot = sum(c.values())
    for k, v in c.most_common(): rows.append([m, uni, "genero", k, v, round(100 * v / tot, 2)])
    te = sum(e[(m, uni)].values())
    for k, v in e[(m, uni)].most_common(): rows.append([m, uni, "escolaridade", k, v, round(100 * v / te, 2)])
for m, c in fx.items():
    tot = sum(c.values())
    for k, v in sorted(c.items()): rows.append([m, "todos", "faixa_etaria", k, v, round(100 * v / tot, 2)])
with open("data/resultado_tse.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f); w.writerow(["municipio", "universo", "variavel", "categoria", "eleitores", "pct"]); w.writerows(rows)
for r in rows:
    if r[2] != "faixa_etaria": print(*r, sep="\t")
# comparacao com o sexo inferido
fem = {}
for (m, uni), c in g.items():
    F = sum(v for k, v in c.items() if k.startswith("FEM")); M = sum(v for k, v in c.items() if k.startswith("MASC"))
    fem[(m, uni)] = 100 * F / (F + M)
out = []
for r in csv.DictReader(open("data/resultado_sexo.csv", encoding="utf-8")):
    m = "Cascavel" if r["vara"] == "Cascavel" else "Curitiba"
    if r["pct_F_entre_classificados"]:
        pf = float(r["pct_F_entre_classificados"]); ref = fem[(m, "18-69")]
        out.append([r["vara"], r["tipo"], r["ano"], r["n"], r["pct_classificados"], pf, round(ref, 1), round(pf / ref, 2)])
with open("data/resultado_sexo_vs_tse.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f); w.writerow(["vara", "tipo", "ano", "n", "pct_classificados", "pct_mulheres_lista", "pct_mulheres_eleitorado_18_69", "razao"]); w.writerows(out)
print("\nvara tipo ano n %class %F_lista %F_eleit razao")
for o in out: print(*o, sep="\t")
