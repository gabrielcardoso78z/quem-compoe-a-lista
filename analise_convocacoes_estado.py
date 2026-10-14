#!/usr/bin/env python3
"""Sorteados no estado: editais de convocacao (processar_convocacoes_dje.py) cruzados com as listas gerais
(processar_comarcas_dje.py). So agregados; nenhum nome.

Edital confirmado: 50%+ dos sorteados estao na lista da propria comarca para o ano do sorteio (lista "para o ano Y"
e sorteio em Y). Sorteios sem lista do ano na base nao sao confirmaveis e ficam fora dos agregados (mas sao contados).
Editais com menos de 10 sorteados lidos ficam fora (leitura incompleta).
Saidas: data/resultado_convocacoes_comarca_ano.csv e data/saida_analise_convocacoes_estado.txt (via rodar_tudo)."""
import csv, os, statistics
from collections import Counter, defaultdict
D = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
E = [e for e in csv.DictReader(open(os.path.join(D, "convocacoes_editais.csv"), encoding="utf-8"))
     if e["data_dje"] >= "2023-01-01" and int(e["sorteados"]) >= 10]
N = list(csv.DictReader(open(os.path.join(D, "convocacoes_entradas.csv"), encoding="utf-8")))
LE = list(csv.DictReader(open(os.path.join(D, "comarcas_pr_entradas.csv"), encoding="utf-8")))
VL = {(r["comarca"], r["edicao"], r["tipo"], r["ano"]) for r in csv.DictReader(open(os.path.join(D, "verificacao_comarcas_listas.csv"), encoding="utf-8")) if r["falhas"] == "ok" and r.get("parcial") != "sim"}
lista, sexo_l = defaultdict(set), defaultdict(Counter)
for r in LE:
    if (r["comarca"], r["edicao"], r["tipo"], r["ano"]) in VL:
        if r["pessoa_id"] not in lista[(r["comarca"], r["ano"])]:
            sexo_l[(r["comarca"], r["ano"])][r["sexo_prenome"]] += 1
        lista[(r["comarca"], r["ano"])].add(r["pessoa_id"])
sor, sexo = defaultdict(set), {}
for r in N:
    sor[(r["comarca"], r["edicao"], r["pagina"])].add(r["pessoa_id"]); sexo[r["pessoa_id"]] = r["sexo_prenome"]
cat = Counter(); conf = []
for e in E:
    s = sor[(e["comarca"], e["edicao"], e["pagina"])]; y = e["data_dje"][:4]
    L = lista.get((e["comarca"], y))
    if not L: cat["sem lista do ano"] += 1; continue
    p = len(s & L) / len(s)
    if p >= 0.5: cat["confirmado"] += 1; conf.append((e, p))
    else: cat["nao confirmado"] += 1
print(f"Editais de convocacao 2023-2026 com 10+ sorteados: {len(E)}; {dict(cat)}")
print(f"Nos confirmados, sorteados presentes na lista do ano: mediana {100*statistics.median(p for _, p in conf):.0f}%")
# por comarca e ano
ca = defaultdict(list)
for e, p in conf: ca[(e["comarca"], e["data_dje"][:4])].append(e)
linhas = []
for (c, y), es in sorted(ca.items()):
    cont = Counter(x for e in es for x in sor[(c, e["edicao"], e["pagina"])])
    distintos = set(cont)
    rep = sum(1 for v in cont.values() if v >= 2)
    prox = set().union(*[sor[(c, e2["edicao"], e2["pagina"])] for e2, _ in conf if e2["comarca"] == c and e2["data_dje"][:4] == str(int(y) + 1)] or [set()])
    tem_prox = any(e2["comarca"] == c and e2["data_dje"][:4] == str(int(y) + 1) for e2, _ in conf)
    L = lista[(c, y)]
    fs = Counter(sexo.get(x, "?") for x in distintos); fl = sexo_l[(c, y)]
    pf_s = 100 * fs["F"] / max(1, fs["F"] + fs["M"]); pf_l = 100 * fl["F"] / max(1, fl["F"] + fl["M"])
    linhas.append([c, y, len(es), len(distintos), round(100 * rep / len(distintos), 1), len(L),
                   round(100 * len(distintos & L) / len(L), 1),
                   round(100 * len(distintos & prox) / len(distintos), 1) if tem_prox else "",
                   round(pf_s, 1), round(pf_l, 1)])
with open(os.path.join(D, "resultado_convocacoes_comarca_ano.csv"), "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f); w.writerow(["comarca", "ano", "editais", "sorteados_distintos", "pct_sorteados_2mais_vezes_no_ano",
                                   "tamanho_lista", "pct_da_lista_sorteada", "pct_sorteados_de_novo_no_ano_seguinte",
                                   "pct_mulheres_sorteados", "pct_mulheres_lista"]); w.writerows(linhas)
def med(i, filtro=lambda l: True):
    xs = [float(l[i]) for l in linhas if l[i] != "" and filtro(l)]
    return (round(statistics.median(xs), 1), len(xs)) if xs else ("-", 0)
print(f"Comarca-ano com sorteios confirmados: {len(linhas)} em {len({l[0] for l in linhas})} comarcas")
print("Editais (sessoes) por comarca-ano, mediana:", med(2))
print("% dos sorteados do ano sorteados 2+ vezes no mesmo ano, mediana:", med(4))
print("% da lista sorteada ao menos uma vez no ano, mediana:", med(6))
print("% dos sorteados de um ano sorteados de novo no ano seguinte, mediana:", med(7))
print("Mulheres entre sorteados x na lista (medianas):", med(8), med(9))
dif = [float(l[8]) - float(l[9]) for l in linhas]
print("Diferenca sorteados - lista (pontos), mediana:", round(statistics.median(dif), 1), "| comarca-ano com |dif|>10:", sum(abs(d) > 10 for d in dif))
# por entrancia (CODJ, Anexo I de 2018)
import re, unicodedata
def nn(t): return re.sub(r"\s+", " ", unicodedata.normalize("NFKD", t).encode("ascii", "ignore").decode().upper()).strip()
ENT = {nn(r["comarca"]): r["entrancia"] for r in csv.DictReader(open(os.path.join(D, "codj_comarcas.csv"), encoding="utf-8"))}
print("\nPor entrancia (medianas por comarca-ano): sessoes | % da lista sorteada | % sorteados de novo no ano seguinte | tamanho da lista")
for ent in ("final", "intermediaria", "inicial"):
    f = lambda l, ent=ent: ENT.get(nn(l[0]), "nao_classificada") == ent
    print(f"  {ent}: comarcas {len({l[0] for l in linhas if f(l)})} | {med(2, f)} | {med(6, f)} | {med(7, f)} | {med(5, f)}")
# comarcas sem lista publicada: o que os sorteios mostram
sem = defaultdict(list)
for e in E:
    if not any(c == e["comarca"] for c, _ in lista): sem[e["comarca"]].append(e)
print("\nComarcas sem lista na base, com editais de convocacao (2023-2026, 10+ sorteados):")
for c, es in sorted(sem.items()):
    cont = Counter(x for e in es for x in sor[(c, e["edicao"], e["pagina"])])
    fs = Counter(sexo.get(x, "?") for x in cont)
    print(f"  {c}: {len(es)} editais, {len(cont)} pessoas, {sum(1 for v in cont.values() if v >= 2)} em 2+ editais, "
          f"mulheres {100*fs['F']/max(1, fs['F']+fs['M']):.1f}%")
# comparacao com a 4.4 (Curitiba): sorteados do ano Y que continuam na lista de Y+1, contra a permanencia da lista inteira
pares = []
for l in linhas:
    c, y = l[0], l[1]; L1 = lista.get((c, str(int(y) + 1)))
    if not L1: continue
    es = ca[(c, y)]
    dist = set().union(*[sor[(c, e["edicao"], e["pagina"])] for e in es])
    L0 = lista[(c, y)]; nao = L0 - dist
    pares.append((c, y, ENT.get(nn(c), "?"), 100 * len(dist & L1) / len(dist), 100 * len(nao & L1) / max(1, len(nao))))
print("\nSorteados do ano que continuam na lista do ano seguinte x nao sorteados (medianas por comarca-ano):")
for ent in ("final", "intermediaria", "inicial", None):
    ps = [p for p in pares if ent is None or p[2] == ent]
    if ps: print(f"  {ent or 'todas'}: n={len(ps)} | sorteados {statistics.median(p[3] for p in ps):.1f}% | nao sorteados {statistics.median(p[4] for p in ps):.1f}%")
