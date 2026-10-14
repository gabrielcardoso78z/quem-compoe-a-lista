#!/usr/bin/env python3
"""Testes de robustez pedidos pelos pareceres externos (14/10/2026). So agregados; nenhum nome e lido ou impresso.
Rodar da raiz do projeto: python3 auxiliares/_robustez_2026-10-14.py
1. Curitiba: limites de pior caso (Manski) para a profissao ausente; so listas com 90%+ de profissao.
2. Denominador alternativo: grupo 2 da lista x eleitores de 18 a 69 anos com superior completo (TSE 2024), Curitiba e comarcas.
3. Comarcas: dissimilaridade esperada num sorteio do mesmo tamanho (simulacao multinomial, 2.000 repeticoes, semente fixa).
4. Fluxo de exclusao das listas do estado (667 -> 661 -> 644).
5. 1a Vara: perfil das entradas com profissao em anos de alta x baixa completude.
"""
import csv, io, os, re, sys, zipfile, random, unicodedata
from collections import Counter, defaultdict
sys.path.insert(0, os.getcwd())
from codificar_profissoes import classificar
from analise_perfil import CENSO
G = sorted(CENSO); pc = {g: CENSO[g] / sum(CENSO.values()) for g in G}
G2, G789 = "2 Profissionais das ciencias e intelectuais", ("7 Operarios e artesaos", "8 Operadores de maquinas e montadores", "9 Ocupacoes elementares")
def D(cnt, ref):
    t = sum(cnt[g] for g in ref); return 50 * sum(abs(cnt[g] / t - ref[g]) for g in ref)
L = defaultdict(list)
for r in csv.DictReader(open("data/base_listas.csv", encoding="utf-8")):
    if r["tipo"] == "definitiva": L[(r["vara"], int(r["ano"]))].append(r["profissao"])
print("== 1. Curitiba: profissao ausente (limites de pior caso), listas usadas no perfil (>= 70%) ==")
for v in sorted({k[0] for k in L}):
    for lim in (0.7, 0.9):
        occ = Counter(); miss = 0; anos = []
        for (vv, a), profs in L.items():
            if vv != v or not 2014 <= a <= 2026: continue
            inf = sum(1 for p in profs if p.strip()) / len(profs)
            if inf < lim: continue
            anos.append(a)
            for p in profs:
                if not p.strip(): miss += 1; continue
                c = classificar(p)[0]
                if c in CENSO: occ[c] += 1
        n = sum(occ.values()); base = n + miss
        g2 = occ[G2]; g789 = sum(occ[g] for g in G789)
        print(f"{v} | listas >= {int(lim*100)}%: {len(anos)} ({min(anos)}-{max(anos)}) | classificadas {n} | sem profissao {miss}"
              f" | D = {D(occ, pc):.1f} | grupo 2 = {100*g2/n:.1f}% [pior caso {100*g2/base:.1f}% a {100*(g2+miss)/base:.1f}%] contra {100*pc[G2]:.1f}%"
              f" | grupos 7-9 = {100*g789/n:.1f}% [pior caso {100*g789/base:.1f}% a {100*(g789+miss)/base:.1f}%] contra {100*sum(pc[g] for g in G789):.1f}%")
print("\n== 5. 1a Vara: entradas com profissao, anos de alta x baixa completude ==")
for a in (2019, 2020, 2021, 2022, 2023, 2024, 2025, 2026):
    profs = L.get(("Curitiba 1a Vara", a))
    if not profs: continue
    inf = sum(1 for p in profs if p.strip()) / len(profs); occ = Counter(c for c in (classificar(p)[0] for p in profs if p.strip()) if c in CENSO)
    n = sum(occ.values())
    if n: print(f"{a}: {100*inf:.0f}% com profissao | classificadas {n} | grupo 2 {100*occ[G2]/n:.1f}% | grupos 7-9 {100*sum(occ[g] for g in G789)/n:.1f}% | D {D(occ, pc):.1f}")
# TSE
def nn(t): return re.sub(r"\s+", " ", unicodedata.normalize("NFKD", t).encode("ascii", "ignore").decode().upper()).strip()
CODJ = {nn(r["comarca"]): r for r in csv.DictReader(open("data/codj_comarcas.csv", encoding="utf-8"))}
mun2com = {nn(m): nn(r["comarca"]) for r in CODJ.values() for m in r["municipios"].split(";") if m}
tse = defaultdict(Counter)
with zipfile.ZipFile("referencias/dados_tse/perfil_eleitorado_2024.zip").open("perfil_eleitorado_2024_PR.csv") as f:
    for r in csv.DictReader(io.TextIOWrapper(f, encoding="latin-1"), delimiter=";"):
        m = re.search(r"(\d+)", r["DS_FAIXA_ETARIA"]); im = int(m.group(1)) if m else -1
        if not 18 <= im <= 69: continue
        k = "CURITIBA" if nn(r["NM_MUNICIPIO"]) == "CURITIBA" else mun2com.get(nn(r["NM_MUNICIPIO"]))
        if k: tse[k]["tot"] += int(r["QT_ELEITORES"]); tse[k]["sup"] += int(r["QT_ELEITORES"]) if nn(r["DS_GRAU_ESCOLARIDADE"]) == "SUPERIOR COMPLETO" else 0
print("\n== 2. Denominador alternativo (eleitorado de 18 a 69 anos, superior completo, TSE 2024) ==")
print(f"Curitiba: {100*tse['CURITIBA']['sup']/tse['CURITIBA']['tot']:.1f}% dos eleitores com superior completo; grupo 2 no Censo de ocupados: {100*pc[G2]:.1f}%")
# comarcas: reaproveita o calculo do censo estadual
_out = sys.stdout; sys.stdout = io.StringIO()
ns = {"__name__": "censo", "__file__": os.path.abspath("analise_censo_estadual.py")}
try:
    exec(open("analise_censo_estadual.py", encoding="utf-8").read(), ns)
except BaseException as ex:
    sys.stdout = _out; print("ERRO no exec:", repr(ex)); raise
sys.stdout = _out
random.seed(20261014)
rows = []
for c in ns["coms"]:
    k = nn(c)
    ks = sorted([kk for kk in ns["ult"] if kk[0] == c], key=lambda kk: (kk[2], kk[1] == "definitiva"))
    inteiras = [kk for kk in ks if not ns["parcial"](ns["ult"][kk])]
    e = ns["ult"][(inteiras or ks)[-1]]
    if not (e["pct_profissao"] and float(e["pct_profissao"]) >= 50 and ns["censo"].get(k)): continue
    cnt = Counter()
    for p in ns["prof_lista"][(c, e["edicao"])]:
        m = re.match(r"(\d) ", classificar(p)[0])
        if m: cnt[int(m.group(1))] += 1
    tl = sum(cnt.values()); cz = ns["censo"][k]; tc = sum(cz.values())
    if tl < 50: continue
    ref = {g: cz[g] / tc for g in range(10)}
    obs = 50 * sum(abs(cnt[g] / tl - ref[g]) for g in range(10))
    sims = []
    gs = list(range(10)); ws = [ref[g] for g in gs]
    for _ in range(2000):
        s = Counter(random.choices(gs, ws, k=tl)); sims.append(50 * sum(abs(s[g] / tl - ref[g]) for g in gs))
    sims.sort(); exp, p95 = sum(sims) / len(sims), sims[int(0.95 * len(sims))]
    sup = 100 * tse[k]["sup"] / tse[k]["tot"] if tse[k]["tot"] else None
    rows.append([c, tl, round(obs, 1), round(exp, 1), round(p95, 1), round(100 * cnt[2] / tl, 1), round(100 * ref[2], 1), round(sup, 1) if sup else ""])
print("\n== 3. Comarcas: dissimilaridade observada x esperada num sorteio do mesmo tamanho ==")
acima = sum(1 for r in rows if r[2] > r[4]); print(f"{len(rows)} comarcas com dissimilaridade; observada acima do percentil 95 do sorteio em {acima}")
exps = sorted(r[3] for r in rows); p95s = sorted(r[4] for r in rows); obs = sorted(r[2] for r in rows)
print(f"esperada: mediana {exps[len(exps)//2]} (de {exps[0]} a {exps[-1]}); p95: mediana {p95s[len(p95s)//2]} (max {p95s[-1]}); observada: mediana {obs[len(obs)//2]} (min {obs[0]})")
ratio = [r[5] / r[7] for r in rows if r[7]]; acima_tse = sum(1 for r in rows if r[7] and r[5] > r[7])
print(f"grupo 2 da lista acima da proporcao de eleitores com superior completo em {acima_tse} de {len(ratio)} comarcas; razao mediana {sorted(ratio)[len(ratio)//2]:.1f}")
with open("data/resultado_robustez_comarcas.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f); w.writerow(["comarca", "classificadas", "dissimilaridade_obs", "esperada_sorteio", "p95_sorteio", "pct_grupo2_lista", "pct_grupo2_censo", "pct_superior_completo_eleitores"]); w.writerows(rows)
print("\n== 4. Fluxo das listas do estado ==")
V = list(csv.DictReader(open("data/verificacao_comarcas_listas.csv", encoding="utf-8")))
print(f"examinadas {len(V)}; resultado das verificacoes: {dict(Counter(r['falhas'] for r in V))}")
print(f"validas apos filtros de nomes, carater, ano e comarca verificada: {len(ns['validos'])}; listas por % de profissao (n=644): ver saida do censo")
