#!/usr/bin/env python3
"""Analises complementares (11/10/2026), so com dados pseudonimizados e saidas agregadas:
 A. permanencia e perfil ano a ano (2009-2026) e teste da reforma de 2011 da 2a Vara;
 B. indice de dissimilaridade (Duncan) lista x Censo 2022, ano a ano;
 C. entradas em bloco (novatos por profissao);
 D. concentracao das convocacoes (editais 2015-2026);
 E. sobrevivencia na lista (Kaplan-Meier).
Saidas em data/aprof_*.csv."""
import csv, re, io, contextlib
from collections import Counter, defaultdict
from codificar_profissoes import classificar, norm
from analise_perfil import CENSO
with contextlib.redirect_stdout(io.StringIO()):
    import analise_vinculo_publico as VP
VARAS = ["Curitiba 1a Vara", "Curitiba 2a Vara"]
ANOS = range(2009, 2027)
L = defaultdict(set); P = defaultdict(list)
for r in csv.DictReader(open("data/base_listas.csv", encoding="utf-8")):
    if r["tipo"] != "definitiva": continue
    k = (r["vara"], int(r["ano"])); L[k].add(r["pessoa_id"]); P[k].append(r["profissao"])
tc = sum(CENSO.values()); pc = {g: CENSO[g] / tc for g in CENSO}
def w(nome, cab, linhas):
    with open(f"data/aprof_{nome}.csv", "w", newline="", encoding="utf-8") as f:
        x = csv.writer(f); x.writerow(cab); x.writerows(linhas)

# A + B. serie anual
serie = []
print("=== A/B. Serie anual das definitivas ===")
print("vara ano n perm% perm2% info% D_duncan g2% g5% g789% estud% apos% lar% pubativo%")
for v in VARAS:
    for a in ANOS:
        if (v, a) not in L: continue
        cur, ant = L[(v, a)], L.get((v, a - 1))
        perm = round(100 * len(cur & ant) / len(cur), 1) if ant else ""
        ant2 = (ant or set()) | L.get((v, a - 2), set())
        perm2 = round(100 * len(cur & ant2) / len(cur), 1) if ant else ""
        profs = P[(v, a)]; info = sum(1 for p in profs if p.strip()) / len(profs)
        cat = Counter(classificar(p)[0] for p in profs)
        occ = {g: cat[g] for g in CENSO}; to = sum(occ.values()) or 1
        D = round(50 * sum(abs(occ[g] / to - pc[g]) for g in CENSO), 1)
        g = lambda *ks: round(100 * sum(occ[k] for k in CENSO if k[0] in ks) / to, 1)
        # vinculo publico: mesma definicao da secao 4.5 (analise_vinculo_publico.py): entre profissoes informadas,
        # excluidos estudantes, aposentados, do lar e desempregados
        nn = [VP.norm(p) for p in profs]
        den = [x for x in nn if x not in VP.VAZIO and not (VP.EST.search(x) or VP.APOS.search(x) or re.search(r"DO LAR|DONA DE CASA|PRENDAS|DESEMPREG", x))]
        pubat = sum(1 for x in den if VP.PUB.search(x) and not VP.NAO.search(x)); ativos = len(den) or 1
        pct = lambda c: round(100 * cat[c] / len(profs), 1)
        row = [v, a, len(cur), perm, perm2, round(100 * info), D if info >= .7 else "", g("2") if info >= .7 else "", g("5") if info >= .7 else "",
               g("7", "8", "9") if info >= .7 else "", pct("Estudante ou estagiario"), pct("Aposentado"), pct("Do lar"),
               round(100 * pubat / ativos, 1) if info >= .7 else ""]
        serie.append(row); print(*row[1:], sep="\t") if True else None
w("serie_anual", ["vara", "ano", "n", "pct_permanencia_ano_anterior", "pct_em_alguma_das_2_anteriores", "pct_com_profissao", "indice_dissimilaridade_duncan",
                  "pct_grupo2", "pct_grupo5", "pct_grupos789", "pct_estudantes", "pct_aposentados", "pct_do_lar", "pct_vinculo_publico_ocup_ativa"], serie)

# C. entradas em bloco
print("\n=== C. Entradas em bloco: profissao muito concentrada entre os novatos ===")
bloco = []
for v in VARAS:
    hist = set()
    for a in ANOS:
        if (v, a) not in L: continue
        if a == 2009: hist |= L[(v, a)]; continue
        ids = {}
        for r in zip(P[(v, a)]): pass
        nov = L[(v, a)] - hist
        hist |= L[(v, a)]
        bloco.append([v, a, len(nov), round(100 * len(nov) / len(L[(v, a)]), 1)])
# perfis dos novatos por profissao exige casar id e profissao:
ID = defaultdict(list)
for r in csv.DictReader(open("data/base_listas.csv", encoding="utf-8")):
    if r["tipo"] == "definitiva": ID[(r["vara"], int(r["ano"]))].append((r["pessoa_id"], norm(r["profissao"])))
blocos = []
for v in VARAS:
    hist = set()
    for a in ANOS:
        if (v, a) not in ID: continue
        nov = [p for i, p in ID[(v, a)] if i not in hist]; vet = [p for i, p in ID[(v, a)] if i in hist]
        hist |= {i for i, _ in ID[(v, a)]}
        if a == 2009 or len(nov) < 50: continue
        cn, cv = Counter(nov), Counter(vet)
        for prof, n in cn.most_common(4):
            if not prof or n < 30 or classificar(prof)[0] == "Nao informada": continue
            sn = n / len(nov); sv = cv[prof] / len(vet) if vet else 0
            if sn >= .05 and (sv == 0 or sn / sv >= 2):
                blocos.append([v, a, len(nov), prof, n, round(100 * sn, 1), round(100 * sv, 1)])
for b in blocos: print(*b, sep="\t")
w("novatos", ["vara", "ano", "novatos", "pct_novatos"], bloco)
w("entradas_em_bloco", ["vara", "ano", "novatos", "profissao", "n_novatos_com_profissao", "pct_entre_novatos", "pct_entre_veteranos"], blocos)

# D. concentracao das convocacoes
print("\n=== D. Concentracao das convocacoes (2015-2026) ===")
C = defaultdict(Counter); meses = defaultdict(set)
for r in csv.DictReader(open("data/convocacoes.csv", encoding="utf-8")):
    if r["ano"] and 2015 <= int(r["ano"]) <= 2026:
        C[r["vara"]][r["pessoa_id"]] += 1; meses[r["vara"]].add((r["ano"], r["mes"]))
conc = []
def gini(xs):
    xs = sorted(xs); n = len(xs); s = sum(xs)
    return sum((2 * i - n + 1) * x for i, x in enumerate(xs)) / (n * s)
for v in VARAS:
    c = C[v]; tot = sum(c.values()); vals = sorted(c.values(), reverse=True); n = len(vals)
    top10 = sum(vals[:max(1, n // 10)]) / tot
    faixas = Counter("1" if x == 1 else "2" if x == 2 else "3-5" if x <= 5 else "6-10" if x <= 10 else "11+" for x in vals)
    na_lista = Counter()
    for a in range(2015, 2027):
        for p in L.get((v, a), ()): na_lista[p] += 1
    hab = [p for p, k in na_lista.items() if k >= 5]
    nunca = sum(1 for p in hab if c[p] == 0)
    alguma = set(na_lista); sorteados = sum(1 for p in alguma if c[p] > 0)
    row = [v, len(meses[v]), tot, n, round(tot / n, 2), round(100 * top10, 1), round(gini(vals), 3),
           faixas["1"], faixas["2"], faixas["3-5"], faixas["6-10"], faixas["11+"], max(vals),
           len(alguma), round(100 * sorteados / len(alguma), 1), len(hab), nunca, round(100 * nunca / len(hab), 1) if hab else ""]
    conc.append(row); print(row)
w("concentracao_convocacoes", ["vara", "editais_mes", "convocacoes", "pessoas_convocadas", "media_por_pessoa", "pct_convocacoes_top10pct",
    "gini_entre_convocados", "conv_1x", "conv_2x", "conv_3a5", "conv_6a10", "conv_11mais", "max_convocacoes_pessoa",
    "pessoas_em_alguma_lista_2015_2026", "pct_dessas_ja_convocadas", "pessoas_5mais_anos_de_lista", "dessas_nunca_convocadas", "pct_nunca"], conc)

# E. sobrevivencia (Kaplan-Meier) em spells iniciados de 2010 a 2025
print("\n=== E. Sobrevivencia na lista (Kaplan-Meier) ===")
km = []; res = []
for v in VARAS:
    anos = [a for a in ANOS if (v, a) in L]
    falta = {2023} if v.endswith("1a Vara") else set()   # 1a Vara 2023: lista incompleta; ponte entre 2022 e 2024
    pres = lambda p, a: (p in L[(v, a)]) if a not in falta else (p in L[(v, a - 1)] and p in L.get((v, a + 1), set()))
    dur = []  # (anos observados, evento: 1 saiu, 0 censurado em 2026)
    for a0 in range(2010, 2026):
        if (v, a0) not in L or a0 in falta: continue
        for p in L[(v, a0)] - L.get((v, a0 - 1), set()):
            if (v, a0 - 1) in L and a0 - 1 in falta and p in L.get((v, a0 - 2), set()): continue
            t, a = 1, a0 + 1
            while a <= 2026 and pres(p, a): t += 1; a += 1
            dur.append((t, 0 if a > 2026 else 1))
    S, curva = 1.0, {}
    for t in range(1, 17):
        risco = sum(1 for d, e in dur if d >= t); sai = sum(1 for d, e in dur if d == t and e == 1)
        if risco == 0: break
        S *= 1 - sai / risco; curva[t] = S; km.append([v, t, risco, sai, round(S, 3)])
    med = next((t for t, s in curva.items() if s <= .5), ">16")
    res.append([v, len(dur), round(100 * curva.get(1, 0), 1), round(100 * curva.get(3, 0), 1), round(100 * curva.get(5, 0), 1), round(100 * curva.get(10, 0), 1) if 10 in curva else "", med])
    print(res[-1])
w("sobrevivencia_km", ["vara", "anos_na_lista", "em_risco", "saidas", "S"], km)
w("sobrevivencia_resumo", ["vara", "entradas_2010_2025", "pct_continua_apos_1_ano", "pct_apos_3", "pct_apos_5", "pct_apos_10", "mediana_anos"], res)
