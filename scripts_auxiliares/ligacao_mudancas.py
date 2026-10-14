"""Para as entradas cujo identificador mudou em relacao a versao congelada: o identificador antigo e o novo
reaparecem em outra edicao da mesma comarca? Reaparecer indica nome lido igual em outra publicacao (sem nomes)."""
import csv, os, sys
from collections import defaultdict, Counter
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
def ler(p): return list(csv.DictReader(open(p, encoding="utf-8")))
B = ler(os.path.join(BASE, "auditoria/baseline_2026-10-12/data/comarcas_pr_entradas.csv")); N = ler(os.path.join(BASE, "data/comarcas_pr_entradas.csv"))
k = lambda r: (r["comarca"], r["edicao"], r["tipo"], r["ano"], r["seq"])
def onde(rows):
    d = defaultdict(set)
    for r in rows: d[(r["comarca"], r["pessoa_id"])].add(r["edicao"])
    return d
OB, ON = onde(B), onde(N); bk = {k(r): r for r in B}
c = Counter()
for r in N:
    b = bk.get(k(r))
    if not b or b["pessoa_id"] == r["pessoa_id"]: continue
    vo = bool(OB[(b["comarca"], b["pessoa_id"])] - {b["edicao"]}); vn = bool(ON[(r["comarca"], r["pessoa_id"])] - {r["edicao"]})
    c[("antigo reaparece" if vo else "antigo isolado", "novo reaparece" if vn else "novo isolado")] += 1
    if vo and not vn: print("  piorou:", k(r))
for x, v in c.most_common(): print(v, x)
