"""Conta alistados de categorias isentas pelo art. 437 do CPP nas listas definitivas (2014-2026)
e verifica quantos foram sorteados (editais de convocação). Saída agregada, sem nomes."""
import csv, re, unicodedata, collections

def norm(s):
    s = s or ""
    try: s = s.encode("latin1").decode("utf-8")   # corrige mojibake (Ã§ etc.)
    except Exception: pass
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode().upper()
    return re.sub(r"\s+", " ", s).strip()

APOS = re.compile(r"APOSENT|RESERVA|REFORMAD|INATIV")
EXCLUIR = re.compile(r"ESTUDANTE|ESTAGI|RESIDENTE|PARTICULAR|BOMBEIRO CIVIL|PERIT[OA] JUDICIAL|PERITO VEICULAR|GRAFOT|PROMOTOR[A]? (DE )?(VENDA|COMERC|MERCH)")
CATS = [
 ("VII - Polícia Militar",            r"POLICIA(L)? MILITAR|\bPM\b"),
 ("VII - Polícia Civil",              r"POLICIA(L)? CIVIL|INVESTIGADOR|ESCRIVAO DE POLICIA|DELEGAD|PERITO CRIMINAL|PERICIA CRIMINAL"),
 ("VII - Polícia Penal / agente penitenciário", r"PENITENCI|POLICIA(L)? PENAL|CARCERAR|CADEIA PUBLICA"),
 ("VII - Polícias federais",          r"POLICIA(L)? (RODOVIARI[OA] )?FEDERAL"),
 ("VII - Bombeiro militar",           r"BOMBEIRO"),
 ("VII? - Guarda municipal",          r"GUARDA MUNICIPAL"),
 ("VII? - Agente socioeducativo",     r"SOCIOEDUCATIV"),
 ("VIII - Militar (Forças Armadas ou sem especificação)", r"\bMILITAR\b|EXERCITO|MARINHA|AERONAUTICA"),
 ("VI - Servidor do Judiciário",      r"JUDICIARI|SERVENTUARI|OFICIAL DE JUSTICA|ASSISTENTE( III)? DE (JUIZ|MAGISTRAD|DES)|AS?C?SESSOR(A)? (DE |NO )?(JUIZ|MAGISTRAD|DESEMBARG|TJ|TRIBUNAL)|\bTJPR\b|TRIBUNAL DE JUSTICA"),
 ("VI - Servidor do MP/Defensoria",   r"ASSESSOR(A)? DE PROMOTOR|MPPR|MINISTERIO PUBLICO|DEFENSORIA"),
]
CATS = [(n, re.compile(p)) for n, p in CATS]

def classe(p):
    if not p or EXCLUIR.search(p): return None
    for n, rx in CATS:
        if rx.search(p):
            return (n + " (aposentado/reserva)") if APOS.search(p) else n
    return None

sorteados = collections.defaultdict(set)   # (vara, ano) -> pessoas
for r in csv.DictReader(open("data/convocacoes.csv", encoding="utf-8")):
    sorteados[(r["vara"], r["ano"])].add(r["pessoa_id"])

ent = collections.Counter(); pes = collections.defaultdict(set); sort = collections.defaultdict(set)
tot = collections.Counter()
for r in csv.DictReader(open("data/base_listas.csv", encoding="utf-8")):
    if r["tipo"] != "definitiva" or not ("2014" <= r["ano"] <= "2026"): continue
    tot[r["vara"]] += 1
    c = classe(norm(r["profissao"]))
    if not c: continue
    k = (r["vara"], c)
    ent[k] += 1; pes[k].add(r["pessoa_id"])
    # sorteado no ano de vigência da lista (lista de ano X vale para X)
    if r["pessoa_id"] in sorteados[(r["vara"], r["ano"])]: sort[k].add((r["pessoa_id"], r["ano"]))

with open("data/resultado_isentos.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f); w.writerow(["vara", "categoria", "entradas", "pessoas", "sorteios_no_ano_da_lista"])
    for k in sorted(ent): w.writerow([k[0], k[1], ent[k], len(pes[k]), len(sort[k])])
print("total entradas definitivas 2014-2026:", dict(tot))
for k in sorted(ent): print(f"{k[0][9:]:8} | {k[1]:62} | ent {ent[k]:4} | pes {len(pes[k]):4} | sort {len(sort[k]):3}")
