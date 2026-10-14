"""Teto do vínculo público nas listas: soma ao piso (analise_vinculo_publico.py) todas as ocupações
em que o setor público é empregador relevante, mas que a lista não identifica (professor, saúde, etc.).
Mesmo universo e mesmas regras do piso. Saída agregada, sem nomes."""
import csv, re, collections, sys
sys.path.insert(0, ".")
import importlib.util
spec = importlib.util.spec_from_file_location("v", "analise_vinculo_publico.py")
src = open("analise_vinculo_publico.py", encoding="utf-8").read().split("c = collections.defaultdict")[0]
ns = {}; exec(src, ns)
norm, PUB, NAO, APOS, EST, VAZIO, inclui = (ns[k] for k in ["norm","PUB","NAO","APOS","EST","VAZIO","inclui"])
AMB = {
 "professor": re.compile(r"PROFESSOR|DOCENTE|EDUCADOR|PEDAGOG|MAGISTERIO"),
 "saude": re.compile(r"MEDIC[OA]\b|ENFERM|TECNIC[OA] (DE|EM) ENFERM|AUXILIAR DE ENFERM|AGENTE COMUNITARI|DENTISTA|ODONTOLOG|FISIOTERAP|FARMACEUT|NUTRICION|PSICOLOG|ASSISTENTE SOCIAL"),
 "agente_analista_tecnico": re.compile(r"\bAGENTE\b|ANALISTA JUDICI|TECNICO JUDICI|ESCRIVAO|OFICIAL DE JUSTICA|INSPETOR|CARTEIRO|BANCARI"),
}
c = collections.defaultdict(collections.Counter)
for r in csv.DictReader(open("data/base_listas.csv", encoding="utf-8")):
    if r["tipo"] != "definitiva" or not inclui(r["vara"], r["ano"]): continue
    p = norm(r["profissao"]); k = c[r["vara"]]
    if p in VAZIO: continue
    if EST.search(p) or APOS.search(p) or re.search(r"DO LAR|DONA DE CASA|PRENDAS|DESEMPREG", p): continue
    k["ocup_ativa"] += 1
    if PUB.search(p) and not NAO.search(p): k["piso"] += 1; continue
    for nome, rx in AMB.items():
        if rx.search(p): k[nome] += 1; break
for v, k in sorted(c.items()):
    oa = k["ocup_ativa"]; amb = sum(k[n] for n in AMB)
    print(v, "| ocup_ativa", oa, "| piso", round(100*k["piso"]/oa,1),
          "|", " ".join(f"{n} {round(100*k[n]/oa,1)}" for n in AMB),
          "| teto", round(100*(k["piso"]+amb)/oa,1))
