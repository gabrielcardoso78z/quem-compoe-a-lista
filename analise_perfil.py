#!/usr/bin/env python3
"""Etapa 2: perfil ocupacional das listas x Censo 2022 (Curitiba, tabela SIDRA 10264)."""
import csv
from collections import Counter, defaultdict
from codificar_profissoes import classificar
CENSO = {  # pessoas ocupadas de 14 anos ou mais, Curitiba, Censo 2022 (SIDRA 10264)
 "1 Diretores e gerentes": 76535, "2 Profissionais das ciencias e intelectuais": 216075,
 "3 Tecnicos e profissionais de nivel medio": 101076, "4 Trabalhadores de apoio administrativo": 94522,
 "5 Trabalhadores dos servicos e vendedores": 170237, "6 Agropecuaria": 5115, "7 Operarios e artesaos": 86129,
 "8 Operadores de maquinas e montadores": 55948, "9 Ocupacoes elementares": 87751,
 "0 Forcas armadas, policiais e bombeiros militares": 6148}
tc = sum(CENSO.values())
listas = defaultdict(list)
for r in csv.DictReader(open("data/base_listas.csv", encoding="utf-8")):
    a = int(r["ano"])
    if r["tipo"] == "definitiva" and 2014 <= a <= 2026: listas[(r["vara"], a)].append(r["profissao"])
grupos = defaultdict(Counter); fora = defaultdict(Counter); usadas = defaultdict(list)
for (v, a), profs in listas.items():
    inf = sum(1 for p in profs if p.strip()) / len(profs)
    if inf < 0.7: continue                       # listas sem profissao ficam fora do perfil
    usadas[v].append(a)
    for p in profs:
        c, _ = classificar(p)
        (grupos if c[0].isdigit() else fora)[v][c] += 1
out = []
for v in sorted(grupos):
    tg = sum(grupos[v].values()); tt = tg + sum(fora[v].values())
    print(f"\n=== {v} (definitivas {min(usadas[v])}-{max(usadas[v])}, {len(usadas[v])} listas; {tg} entradas com ocupacao classificada) ===")
    print(f"{'grupo':50} {'lista':>7} {'Censo':>7} {'razao':>6}")
    for g in sorted(CENSO):
        pl, pc = 100 * grupos[v][g] / tg, 100 * CENSO[g] / tc
        print(f"{g:50} {pl:6.1f}% {pc:6.1f}% {pl/pc:6.2f}"); out.append([v, g, round(pl, 1), round(pc, 1), round(pl / pc, 2)])
    print("fora do universo ocupado (% de todas as entradas dessas listas):", "; ".join(f"{k}: {100*n/tt:.1f}%" for k, n in fora[v].most_common()))
with open("data/resultado_perfil.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f); w.writerow(["vara", "grupo_COD", "pct_lista", "pct_censo2022", "razao"]); w.writerows(out)
