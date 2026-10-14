#!/usr/bin/env python3
"""Buenos Aires x Curitiba: tamanho, renovacao e sexo das listas anuais de jurados (so agregados).

Le data/ar_entradas.csv (processar_argentina.py). Grava data/resultado_argentina_*.csv.
Renovacao = proporcao dos alistados do ano t que ja constavam da lista de t-1 (mesma medida de analise_renovacao.py),
pela chave principal (DNI completo pseudonimizado) e, como teste de sensibilidade, so pelo nome.
Tambem: terminacoes de DNI sorteadas em cada ano e entradas por terminacao.
"""
import csv, os
from collections import defaultdict, Counter

D = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
E = list(csv.DictReader(open(os.path.join(D, "ar_entradas.csv"), encoding="utf-8")))
anos = sorted({r["ano"] for r in E})

# 1. tamanho por ano e departamento
tam = Counter((r["ano"], r["departamento"]) for r in E)
deps = sorted({r["departamento"] for r in E})
with open(os.path.join(D, "resultado_argentina_tamanho.csv"), "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f); w.writerow(["departamento"] + anos)
    for d in deps: w.writerow([d] + [tam[(a, d)] for a in anos])
    w.writerow(["TOTAL"] + [sum(tam[(a, d)] for d in deps) for a in anos])
print("Tamanho:", {a: sum(tam[(a, d)] for d in deps) for a in anos})

# duplicidade dentro do ano
for a in anos:
    c = Counter(r["pessoa_id"] for r in E if r["ano"] == a)
    print(f"  {a}: {sum(1 for v in c.values() if v > 1)} chaves repetidas dentro da propria lista")

# 2. renovacao
def conj(a, campo, dep=None):
    return {r[campo] for r in E if r["ano"] == a and (dep is None or r["departamento"] == dep)}

linhas = []
for i in range(1, len(anos)):
    a0, a1 = anos[i - 1], anos[i]
    for campo in ("pessoa_id", "id_nome"):
        s0, s1 = conj(a0, campo), conj(a1, campo)
        linhas.append(["PROVINCIA", a1, campo, len(s1), len(s1 & s0), round(100 * len(s1 & s0) / len(s1), 2)])
    for d in deps:
        s0, s1 = conj(a0, "pessoa_id", d), conj(a1, "pessoa_id", d)
        linhas.append([d, a1, "pessoa_id", len(s1), len(s1 & s0), round(100 * len(s1 & s0) / max(1, len(s1)), 2)])
# em todos os anos
todos = set.intersection(*[conj(a, "pessoa_id") for a in anos])
with open(os.path.join(D, "resultado_argentina_renovacao.csv"), "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f); w.writerow(["unidade", "ano", "chave", "alistados", "ja_na_lista_anterior", "pct_permanencia"]); w.writerows(linhas)
for l in linhas:
    if l[0] == "PROVINCIA": print("Permanencia", l[1], l[2], f"{l[5]}% ({l[4]} de {l[3]})")
print(f"Presentes nas {len(anos)} listas: {len(todos)}")
dep_perm = [l[5] for l in linhas if l[0] != "PROVINCIA"]
print(f"Permanencia por departamento: de {min(dep_perm)}% a {max(dep_perm)}%")

# terminacoes
for a in anos:
    c = Counter(r["terminacao"] for r in E if r["ano"] == a)
    print(f"Terminacoes {a}: {len(c)} ->", ", ".join(f"{k}: {v}" for k, v in sorted(c.items())))
comuns = set.intersection(*[{r["terminacao"] for r in E if r["ano"] == a} for a in anos[:2]])
print("Terminacoes repetidas entre anos consecutivos:", [sorted({r["terminacao"] for r in E if r["ano"] == a0} & {r["terminacao"] for r in E if r["ano"] == a1}) for a0, a1 in zip(anos, anos[1:])])

# 3. sexo pelo prenome (tabela brasileira de nomes; cobertura informada)
with open(os.path.join(D, "resultado_argentina_sexo.csv"), "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f); w.writerow(["ano", "entradas", "F", "M", "ambiguo", "nao_encontrado", "pct_classificado", "pct_F_entre_classificados"])
    for a in anos:
        c = Counter(r["sexo_prenome"] for r in E if r["ano"] == a); n = sum(c.values()); cl = c["F"] + c["M"]
        w.writerow([a, n, c["F"], c["M"], c["ind"], c["nf"], round(100 * cl / n, 1), round(100 * c["F"] / cl, 1)])
        print(f"Sexo {a}: {100*cl/n:.1f}% classificados; mulheres {100*c['F']/cl:.1f}% dos classificados")
