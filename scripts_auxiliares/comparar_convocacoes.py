"""Compara as convocacoes atuais com a versao congelada: editais novos/sumidos, titulares e suplentes por edital,
e pessoas (pseudonimos) que estavam em um edital e sairam. Sem nomes."""
import csv, os
from collections import Counter, defaultdict
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
def ler(p): return list(csv.DictReader(open(p, encoding="utf-8")))
CG = os.path.join(BASE, "auditoria/baseline_2026-10-12/data")
EB, EN = ler(os.path.join(CG, "convocacoes_editais.csv")), ler(os.path.join(BASE, "data/convocacoes_editais.csv"))
PB, PN = ler(os.path.join(CG, "convocacoes_entradas.csv")), ler(os.path.join(BASE, "data/convocacoes_entradas.csv"))
k = lambda r: (r["comarca"], r["data_dje"], r["edicao"], r["pagina"])
kb, kn = {k(r): r for r in EB}, {k(r): r for r in EN}
print(f"editais antes {len(kb)}, agora {len(kn)}; so antes {len(set(kb)-set(kn))}, so agora {len(set(kn)-set(kb))}")
t = Counter()
for x in sorted(set(kb) & set(kn)):
    b, n = kb[x], kn[x]
    dt, ds = int(n["titulares"]) - int(b["titulares"]), int(n["suplentes"]) - int(b["suplentes"])
    t["titulares +" if dt > 0 else "titulares -" if dt < 0 else "titulares ="] += 1
    t["suplentes +" if ds > 0 else "suplentes -" if ds < 0 else "suplentes ="] += 1
    if dt < 0 or ds < 0: print("  diminuiu:", x, (b["titulares"], b["suplentes"]), "->", (n["titulares"], n["suplentes"]))
print(dict(t))
for x in sorted(set(kb) - set(kn)): print("  so antes:", x, kb[x]["titulares"], kb[x]["suplentes"])
for x in sorted(set(kn) - set(kb)): print("  so agora:", x, kn[x]["titulares"], kn[x]["suplentes"])
# pessoas: por (comarca, data) quem estava e saiu, e mudancas de papel
pb, pn = defaultdict(dict), defaultdict(dict)
for r in PB: pb[(r["comarca"], r["data_dje"])][r["pessoa_id"]] = r["papel"]
for r in PN: pn[(r["comarca"], r["data_dje"])][r["pessoa_id"]] = r["papel"]
c = Counter()
for x in pb:
    for h, p in pb[x].items():
        if h not in pn.get(x, {}): c["pessoa saiu"] += 1; saiu = True
        elif pn[x][h] != p: c[f"papel {p} -> {pn[x][h]}"] += 1
        else: c["igual"] += 1
for x in pn:
    for h in pn[x]:
        if h not in pb.get(x, {}): c["pessoa nova"] += 1
print(dict(c))
