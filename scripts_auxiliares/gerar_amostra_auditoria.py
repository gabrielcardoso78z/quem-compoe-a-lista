"""Gera a amostra para a auditoria manual da leitura automatica dos editais do Diario (secoes 5.2 e 5.3).

Amostra (semente fixa 20261012):
  A) aleatoria: 14 listas por entrancia (final, intermediaria, inicial) entre as 640 que entraram no censo;
  B) proposital: casos dificeis (formatos especiais, lacunas, listas parciais, atribuicao incerta);
  C) convocacoes: 10 editais de convocacao de 2023 a 2026 com ao menos 10 sorteados.
So o grupo A estima a taxa de erro; B confere os casos dificeis; C confere a leitura dos sorteados.
A planilha nao contem nomes. A profissao lida em tres posicoes e truncada em 60 caracteres e o
arquivo fica so no computador do pesquisador. Saida: auditoria/auditoria_editais.xlsx"""
import csv, os, random, re, subprocess, unicodedata
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment
from openpyxl.worksheet.datavalidation import DataValidation

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
D = lambda *p: os.path.join(BASE, *p)
SEMENTE = 20261012
GATILHO = r"(?i)foram\s+alistad|procedido\s+o\s+alistamento\s+dos\s+jurados|torna\s+p[uú]blica\s+a\s+(?:lista|rela)"
CONV = r"(?i)ficam\s+convocad|foram\s+sorteados|jurados\s+sorteados|sorteou"

def norm(s):
    s = unicodedata.normalize("NFD", s or "")
    return re.sub(r"\s+", " ", "".join(c for c in s if unicodedata.category(c) != "Mn")).lower().strip()

_cache = {}
def paginas(pdf):
    if pdf not in _cache:
        t = subprocess.run(["pdftotext", "-layout", pdf, "-"], capture_output=True, text=True).stdout
        _cache[pdf] = [norm(p) for p in t.split("\f")]
    return _cache[pdf]

def pdf_de(data, ed):
    p = D("dje", f"{data}_ed{ed}.pdf")
    return p if os.path.exists(p) else None

def acha_pagina(pdf, comarca, gatilho):
    if not pdf: return "PDF nao encontrado"
    pgs = paginas(pdf); c = norm(comarca)
    com = [k + 1 for k, p in enumerate(pgs) if re.search(gatilho, p) and c in p]
    if com: return ", ".join(map(str, com[:3]))
    so = [k + 1 for k, p in enumerate(pgs) if re.search(gatilho, p)]
    viz = [k for k in so if any(c in pgs[j] for j in (k - 2, k) if 0 <= j < len(pgs))]   # nome na pagina anterior
    if viz: return ", ".join(map(str, viz[:3])) + " (cabeçalho pode estar na página anterior)"
    jur = [k + 1 for k, p in enumerate(pgs) if c in p and re.search(r"jurad|profiss", p)]
    if jur: return ", ".join(map(str, jur[:3])) + " (fórmula partida; conferir)"
    return ("procurar pelo cabecalho; editais nas p. " + ", ".join(map(str, so[:6]))) if so else "nao localizada"

ed = list(csv.DictReader(open(D("data", "comarcas_pr_editais.csv"), encoding="utf-8")))
cen = list(csv.DictReader(open(D("data", "resultado_censo_editais.csv"), encoding="utf-8")))
ent = {r["comarca"]: r["entrancia"] for r in csv.DictReader(open(D("data", "codj_comarcas.csv"), encoding="utf-8"))}
chave = lambda r: (r["comarca"], r["data_dje"], r["ano"], r["validas"])
idx = {chave(r): r for r in ed}

# entradas por edital: seq e profissao (sem pessoa_id na planilha)
porED = {}
for r in csv.DictReader(open(D("data", "comarcas_pr_entradas.csv"), encoding="utf-8")):
    porED.setdefault((r["comarca"], r["data_dje"], r["edicao"], r["ano"], r["tipo"]), []).append(r)

rnd = random.Random(SEMENTE)
PROP = [("Rolândia", "2025-11-06", "tabela sem número de ordem"), ("Grandes Rios", "2025-11-19", "uma linha por alistado"),
        ("Cândido De Abreu", "2025-11-24", "uma linha por alistado"), ("Capitão Leônidas Marques", "2025-11-06", "uma linha por alistado"),
        ("Campina Grande Do Sul", "2025-11-12", "lista antes trocada com Cidade Gaúcha"), ("Ipiranga", "2025-11-10", "parágrafo corrido"),
        ("Marmeleiro", "2026-01-16", "parágrafo corrido"), ("Cambé", "2025-11-05", "todas numeradas 1.; caráter deduzido"),
        ("Maringá", "2025-01-10", "lacunas na publicação"), ("Londrina", "2026-10-09", "lacunas na publicação"),
        ("Pontal Do Paraná", "2024-11-11", "começa no nº 30"), ("Araucária", "2025-11-07", "lista parcial"),
        ("Telêmaco Borba", "2025-09-24", "lista parcial"), ("Toledo", "2024-11-28", "leitura tolerante após salto"),
        ("Icaraíma", "2025-10-29", "caráter deduzido")]
prop = []
for com, data, motivo in PROP:
    m = [r for r in ed if r["comarca"] == com and r["data_dje"] == data]
    if m: prop.append((m[0], motivo))
for conf, motivo in (("coluna_anterior", "comarca pela coluna anterior"), ("diverge", "cabeçalho diverge do fecho"),
                     ("reatribuida_por_identidade", "comarca atribuída por identidade")):
    m = sorted([r for r in ed if r["confianca"] == conf and int(r["validas"] or 0) >= 20], key=lambda r: (r["comarca"], r["data_dje"]))
    if m: prop.append((rnd.choice(m), motivo))
ja = {(r["comarca"], r["data_dje"]) for r, _ in prop}

alea = []
for e in ("final", "intermediaria", "inicial"):
    pool = sorted([r for r in cen if ent.get(r["comarca"]) == e and (r["comarca"], r["data_dje"]) not in ja],
                  key=lambda r: (r["comarca"], r["data_dje"], r["tipo"], r["ano"]))
    for r in rnd.sample(pool, 14):
        m = idx.get(chave(r)) or next((x for x in ed if x["comarca"] == r["comarca"] and x["data_dje"] == r["data_dje"] and x["ano"] == r["ano"]), None)
        if m: alea.append((m, "aleatória " + e))

conv = sorted([r for r in csv.DictReader(open(D("data", "convocacoes_editais.csv"), encoding="utf-8"))
               if "2023" <= r["data_dje"][:4] <= "2026" and int(r["sorteados"]) >= 10], key=lambda r: (r["comarca"], r["data_dje"], r["pagina"]))
conv = rnd.sample(conv, 10)

def prof(t): return (t or "(sem profissão)")[:60]

linhas = []
for grupo, itens in (("A", alea), ("B", prop)):
    for r, motivo in itens:
        es = sorted(porED.get((r["comarca"], r["data_dje"], r["edicao"], r["ano"], r["tipo"]), []), key=lambda x: int(x["seq"]))
        pdf = pdf_de(r["data_dje"], r["edicao"])
        if es:
            a, b, c = es[0], es[len(es) // 2], es[-1]
            pos = [(a["seq"], prof(a["profissao"])), (b["seq"], prof(b["profissao"])), (c["seq"], prof(c["profissao"]))]
            primeiro = es[0]["seq"]
        else:
            pos = [("", "")] * 3; primeiro = ""
        linhas.append([grupo, motivo, ent.get(r["comarca"], "?"), r["comarca"], r["data_dje"], r["edicao"],
                       os.path.basename(pdf) if pdf else "não encontrado", acha_pagina(pdf, r["comarca"], GATILHO),
                       r["tipo"], r["ano"], r["validas"], primeiro, r["ultimo_numero"], r["lacunas_publicacao"],
                       pos[0][0], pos[0][1], pos[1][0], pos[1][1], pos[2][0], pos[2][1]])
for r in conv:
    pdf = pdf_de(r["data_dje"], r["edicao"])
    linhas.append(["C", "convocação", ent.get(r["comarca"], "?"), r["comarca"], r["data_dje"], r["edicao"],
                   os.path.basename(pdf) if pdf else "não encontrado", r["pagina"], "convocação", "", r["sorteados"],
                   "", "", "", "", "", "", "", "", ""])

wb = Workbook(); ws = wb.active; ws.title = "Auditoria"
CAB = ["grupo", "motivo", "entrância", "comarca", "data DJe", "edição", "arquivo PDF", "página provável",
       "caráter lido", "ano lido", "entradas lidas", "1º nº lido", "último nº lido", "números ausentes",
       "posição A", "profissão lida em A", "posição B", "profissão lida em B", "posição C", "profissão lida em C",
       "comarca ok?", "caráter e ano ok?", "início e fim ok?", "contagem ok?", "profissões ok?", "observação (sem nomes)"]
ws.append(CAB)
for i, l in enumerate(linhas, 1): ws.append(l + [""] * 6)
cinza, verde = PatternFill("solid", fgColor="EEEEEE"), PatternFill("solid", fgColor="E2F0D9")
for j, _ in enumerate(CAB, 1):
    c = ws.cell(1, j); c.font = Font(bold=True); c.alignment = Alignment(wrap_text=True, vertical="top")
    c.fill = verde if j > 20 else cinza
dv = DataValidation(type="list", formula1='"ok,erro,dúvida,não se aplica"', allow_blank=True)
ws.add_data_validation(dv); dv.add(f"U2:Y{len(linhas) + 1}")
ws.freeze_panes = "E2"
for col, w in zip("ABCDEFGHIJKLMNOPQRSTUVWXYZ", [6, 26, 13, 24, 11, 8, 22, 16, 11, 7, 9, 8, 9, 9, 8, 30, 8, 30, 8, 30, 10, 10, 10, 10, 10, 40]):
    ws.column_dimensions[col].width = w

ins = wb.create_sheet("Como conferir")
for t in ["Abra o PDF (pasta dje/) na página provável. Se houver mais de uma, o edital está numa delas.",
          "comarca ok?: o cabeçalho do edital é da comarca indicada?",
          "caráter e ano ok?: a fórmula diz provisória/definitiva e o ano lido? ('?' = caráter não declarado no edital)",
          "início e fim ok?: a lista começa no 1º nº lido e termina no último nº lido, sem entrar no edital seguinte?",
          "contagem ok?: lista numerada = confira o último número; sem número = confira se a última entrada é a da posição C.",
          "profissões ok?: nas posições A, B e C, a profissão no PDF é a lida pelo programa?",
          "Convocações (grupo C): confira só comarca e número de sorteados; as demais colunas = 'não se aplica'.",
          "Nunca escreva nomes. Para apontar uma entrada, use o número de ordem.",
          f"Amostra gerada por scripts_auxiliares/gerar_amostra_auditoria.py, semente {SEMENTE}."]:
    ins.append([t])
ins.column_dimensions["A"].width = 120
out = D("auditoria", "auditoria_editais.xlsx")
wb.save(out)
print("linhas:", len(linhas), "| A:", len(alea), "B:", len(prop), "C:", len(conv))
print("sem pagina localizada:", sum(1 for l in linhas if not re.match(r"^\d", str(l[7]))))
