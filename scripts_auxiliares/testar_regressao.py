"""Teste de regressao da leitura dos editais do Diario (listas e convocacoes), depois das correcoes da auditoria.
1) Casos de teste (auditoria/casos_teste.json, so identificadores pseudonimizados, sem nomes): nomes nas posicoes
   conferidas pelo pesquisador, entradas que estavam perdidas, profissoes conferidas, sorteados conferidos.
2) Comparacao com a versao congelada (auditoria/baseline_2026-10-12/data): por lista, entradas perdidas,
   ganhas, com identificador ou profissao alterados. Nao imprime nomes.
Uso: python3 scripts_auxiliares/testar_regressao.py [pasta_dados]   (padrao: data/)"""
import csv, json, os, re, sys, unicodedata
from collections import defaultdict, Counter
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DADOS = sys.argv[1] if len(sys.argv) > 1 else os.path.join(BASE, "data")
CONG = os.path.join(BASE, "auditoria", "baseline_2026-10-12", "data")
def nz(s): return re.sub(r"[^a-z0-9 ]", " ", "".join(c for c in unicodedata.normalize("NFD", (s or "").lower()) if unicodedata.category(c) != "Mn")).split()
def ler(p): return list(csv.DictReader(open(p, encoding="utf-8")))
g = json.load(open(os.path.join(BASE, "auditoria", "casos_teste.json"), encoding="utf-8"))
N = ler(os.path.join(DADOS, "comarcas_pr_entradas.csv"))
pos = {(r["comarca"], r["data_dje"], r["seq"]): r for r in N}
res = Counter(); falhas = []
def ok_prof(lido, esperado): return nz(lido)[:len(nz(esperado))] == nz(esperado) if esperado else not nz(lido) or True
for cat in ("listas_nomes", "listas_presentes"):
    for c in g[cat]:
        r = pos.get((c["comarca"], c["data"], c["seq"]))
        if r is None: res[cat + " FALHA ausente"] += 1; falhas.append((cat, c["comarca"], c["data"], c["seq"], "ausente")); continue
        if "h" in c and r["pessoa_id"] != c["h"] and c.get("divergencia_conhecida"): res[cat + " divergencia conhecida (grafia)"] += 1; continue
        if "h" in c and r["pessoa_id"] != c["h"]: res[cat + " FALHA identificador"] += 1; falhas.append((cat, c["comarca"], c["data"], c["seq"], "identificador")); continue
        if c.get("prof") and nz(r["profissao"])[:len(nz(c["prof"]))] != nz(c["prof"]): res[cat + " FALHA profissao"] += 1; falhas.append((cat, c["comarca"], c["data"], c["seq"], "profissao")); continue
        if "prof" in c and not c["prof"] and nz(r["profissao"]): res[cat + " FALHA profissao inventada"] += 1; falhas.append((cat, c["comarca"], c["data"], c["seq"], "profissao inventada")); continue
        res[cat + " ok"] += 1
for c in g["listas_profissoes"]:
    r = pos.get((c["comarca"], c["data"], c["seq"]))
    a, b = nz(r["profissao"]) if r else None, nz(c["prof_base"])
    if r is None: res["listas_profissoes FALHA ausente"] += 1; falhas.append(("profissoes", c["comarca"], c["data"], c["seq"], "ausente")); continue
    # aceita a mesma profissao ou a base sem o lixo do fim (rodape, art. 436); recusa qualquer outra mudanca
    if a == b or (a and b[:len(a)] == a and len(a) >= 1): res["listas_profissoes ok"] += 1
    elif not a and not b: res["listas_profissoes ok"] += 1
    else: res["listas_profissoes FALHA mudou"] += 1; falhas.append(("profissoes", c["comarca"], c["data"], c["seq"], "mudou"))
CV = ler(os.path.join(DADOS, "convocacoes_entradas.csv"))
cv = defaultdict(dict)
for r in CV: cv[(r["comarca"], r["data_dje"])][r["pessoa_id"]] = r["papel"]
for c in g["conv_nomes"]:
    d = cv.get((c["comarca"], c["data"]), {})
    if c["h"] not in d: res["conv " + c["papel"] + (" (ultimo)" if c["ultimo_titular"] else "") + " FALHA ausente"] += 1; continue
    if d[c["h"]] != c["papel"]: res["conv " + c["papel"] + " FALHA papel"] += 1; continue
    res["conv " + c["papel"] + (" (ultimo)" if c["ultimo_titular"] else "") + " ok"] += 1
print("== Casos de teste ==")
for k in sorted(res): print(f"  {k}: {res[k]}")
for f in falhas: print("   falha:", *f)
# comparacao com a versao congelada
if os.path.abspath(DADOS) != os.path.abspath(CONG):
    B = ler(os.path.join(CONG, "comarcas_pr_entradas.csv"))
    def por_lista(rows):
        d = defaultdict(dict)
        for r in rows: d[(r["comarca"], r["data_dje"], r["edicao"], r["tipo"], r["ano"])][r["seq"]] = (r["pessoa_id"], r["profissao"])
        return d
    PB, PN = por_lista(B), por_lista(N)
    print("\n== Comparacao com a versao congelada (listas) ==")
    print(f"  listas: antes {len(PB)}, agora {len(PN)}; so antes {len(set(PB)-set(PN))}, so agora {len(set(PN)-set(PB))}")
    tot = Counter(); piores = []
    for k in set(PB) & set(PN):
        b, n = PB[k], PN[k]
        perd = [s for s in b if s not in n]; ganh = [s for s in n if s not in b]
        idm = [s for s in b if s in n and b[s][0] != n[s][0]]
        prm = [s for s in b if s in n and b[s][0] == n[s][0] and nz(b[s][1]) != nz(n[s][1])]
        tot["entradas antes"] += len(b); tot["perdidas"] += len(perd); tot["ganhas"] += len(ganh)
        tot["identificador mudou"] += len(idm); tot["profissao mudou"] += len(prm)
        if perd or len(idm) > 2: piores.append((len(perd), len(idm), k[0], k[1], k[3], len(b), len(n)))
    for x, v in tot.items(): print(f"  {x}: {v}")
    print("  listas com entrada perdida ou 3+ identificadores mudados (perdidas, id mudados, comarca, data, tipo, antes, agora):")
    for p in sorted(piores, reverse=True)[:40]: print("   ", p)
    for x in sorted(set(PB) - set(PN))[:20]: print("   lista so antes:", x)
    for x in sorted(set(PN) - set(PB))[:20]: print("   lista so agora:", x)
