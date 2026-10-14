"""Piso da participação de servidores/empregados públicos declarados nas listas definitivas,
para comparação com Brochado Neto (2016). Mesmo universo da seção 4.5. Saída agregada."""
import csv, re, unicodedata, collections
def norm(t):
    t = t or ""
    try: t = t.encode("latin1").decode("utf-8")
    except Exception: pass
    t = unicodedata.normalize("NFKD", t).encode("ascii", "ignore").decode().upper()
    return re.sub(r"\s+", " ", re.sub(r"[^A-Z0-9 ]", " ", t)).strip()
PUB = re.compile(r"\bSERVIDOR|\bFUNC(IONARI[OA])? PUB|\bFUNCIONARI[OA] PUBLIC|\bSERVICO PUBLICO|\bPUBLIC[OA] (MUNICIPAL|ESTADUAL|FEDERAL)|\bMUNICIPAL\b|\bESTADUAL\b|\bFEDERAL\b|\bPREFEITURA|\bSECRETARIA (DE|DA|DO|MUNICIPAL|ESTADUAL)|\bTRIBUNAL|\bJUDICIARI|\bJUIZ|\bMAGISTRAD|\bDESEMBARG|\bSERVENTUARI|\bMINISTERIO PUBLICO|\bMPPR|\bDEFENSORIA|\bASSEMBLEIA LEGISLATIVA|\bCAMARA (MUNICIPAL|DOS DEPUTADOS|DE VEREADORES)|\bCOPEL|\bSANEPAR|\bCAIXA ECONOMICA|\bBANCO DO BRASIL|\bUFPR|\bUTFPR|\bINSS|\bRECEITA FEDERAL|\bPOLICIA|\bPOLICIAL|\bMILITAR|\bBOMBEIRO MILITAR|\bGUARDA MUNICIPAL|\bDETRAN|\bCORREIOS|\bPENITENCIARI|\bCADEIA PUBLICA|\bAUDITOR FISCAL|\bFISCAL DE TRIBUTOS")
NAO = re.compile(r"PUBLICIT|RELACOES PUBLICAS|BOMBEIRO CIVIL|EX SERVIDOR|SERVIDORA? DE (REDE|TI|SISTEMA)")
APOS = re.compile(r"APOSENT|INATIV|RESERVA|REFORMAD|PENSIONIST")
EST = re.compile(r"ESTUDANT|ESTAGI|ACADEMIC|UNIVERSITARI")
VAZIO = {"", "NAO INFORMADA", "NAO INFORMADO", "SEM PROFISSAO"}
inclui = lambda v, a: (v.endswith("1a Vara") and "2014" <= a <= "2024" and a != "2023") or (v.endswith("2a Vara") and "2014" <= a <= "2026")
c = collections.defaultdict(collections.Counter)
for r in csv.DictReader(open("data/base_listas.csv", encoding="utf-8")):
    if r["tipo"] != "definitiva" or not inclui(r["vara"], r["ano"]): continue
    p = norm(r["profissao"]); k = c[r["vara"]]
    if p in VAZIO: k["sem_profissao"] += 1; continue
    k["informadas"] += 1
    if not (EST.search(p) or APOS.search(p) or re.search(r"DO LAR|DONA DE CASA|PRENDAS|DESEMPREG", p)):
        k["ocup_ativa"] += 1; k["pub_ocup_ativa"] += bool(PUB.search(p) and not NAO.search(p))
    est = bool(EST.search(p)); k["estudantes"] += est
    pub = bool(PUB.search(p)) and not NAO.search(p)
    if pub and APOS.search(p): k["pub_aposentado"] += 1
    elif pub: k["pub_ativo"] += 1
    if pub and re.search(r"^(SERVIDOR|SERVIDORA|FUNC|FUNCIONARI)", p) and not re.search(r"JUDICI|PROFESSOR|ANALISTA|TECNICO|AGENTE|ASSISTENTE|AUXILIAR|ENGENHEIR|MEDIC|ENFERM|ADVOGAD|CONTADOR|ADMINISTRAD", p): k["pub_generico"] += 1
with open("data/resultado_vinculo_publico.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f); w.writerow(["vara", "informadas", "pub_ativo", "pub_aposentado", "pub_generico", "estudantes", "pct_pub_ativo", "pct_pub_total", "pct_pub_total_sem_estudantes", "ocup_ativa", "pct_pub_ocup_ativa"])
    for v, k in sorted(c.items()):
        tot = k["pub_ativo"] + k["pub_aposentado"]
        row = [v, k["informadas"], k["pub_ativo"], k["pub_aposentado"], k["pub_generico"], k["estudantes"],
               round(100 * k["pub_ativo"] / k["informadas"], 1), round(100 * tot / k["informadas"], 1),
               round(100 * tot / (k["informadas"] - k["estudantes"]), 1), k["ocup_ativa"], round(100 * k["pub_ocup_ativa"] / k["ocup_ativa"], 1)]
        w.writerow(row); print(row)
