"""Classifica as profissoes que mudaram entre a versao congelada e a atual (mesma entrada, mesmo identificador)."""
import csv, os, re
from collections import Counter, defaultdict
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
def ler(p): return list(csv.DictReader(open(p, encoding="utf-8")))
B = ler(os.path.join(BASE, "auditoria/baseline_2026-10-12/data/comarcas_pr_entradas.csv")); N = ler(os.path.join(BASE, "data/comarcas_pr_entradas.csv"))
k = lambda r: (r["comarca"], r["edicao"], r["tipo"], r["ano"], r["seq"])
bk = {k(r): r for r in B}
# tudo mascarado: na versao congelada, o campo profissao as vezes continha o nome da entrada seguinte
mk = lambda s: re.sub(r"[a-z\u00df-\u00ff]", "a", re.sub(r"[A-Z\u00c0-\u00dd]", "A", s))
JUNK = r"(?i)curitiba|edi..o|di.rio|eletr.nico|tribunal|art\.?\s*4\d\d|edital|para que|dado e passado|na forma"
cat = Counter(); ex = defaultdict(list)
for r in N:
    b = bk.get(k(r))
    if not b or b["pessoa_id"] != r["pessoa_id"] or b["profissao"] == r["profissao"]: continue
    o, n = b["profissao"], r["profissao"]
    if re.search("[\u00c2\u00c3\u00e2\u00e3][\u0080-\u00bf]", o) and not re.search("[\u00c2\u00c3\u00e2\u00e3][\u0080-\u00bf]", n): c = "acento reparado"
    elif o.startswith(n) and re.search(JUNK, o[len(n):]): c = "cauda de texto do DJe/edital removida"
    elif o.startswith(n) and re.fullmatch(r"[\s\-–.\d]*", o[len(n):]): c = "numero/pontuacao final removido"
    elif o.startswith(n) and re.match(r"\s*\d{1,4}\s*[.\u2013)]", o[len(n):]): c = "entrada seguinte (numero + nome) removida da profissao"
    elif o.startswith(n): c = "cauda removida (outra)"
    elif n.startswith(o): c = "profissao completada"
    elif re.fullmatch(r"[\d\s.\-–]*", o) and not n: c = "numero de pagina lido como profissao (F7) removido"
    elif not o and n: c = "profissao nova (antes vazia)"
    elif o and not n: c = "profissao esvaziada"
    else: c = "outro"
    cat[c] += 1
    if len(ex[c]) < 8: ex[c].append((r["comarca"], r["edicao"], r["seq"], mk(o)[:80], mk(n)[:80]))
for c, v in cat.most_common(): print(f"  {c}: {v}")
for c in ex:
    print("\n--", c)
    for e in ex[c]: print("   ", e)
