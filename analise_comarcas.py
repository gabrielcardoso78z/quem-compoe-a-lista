#!/usr/bin/env python3
"""Comarcas de entrancia intermediaria (Laranjeiras do Sul) e inicial (Cantagalo): tamanho, profissao,
permanencia entre listas, sexo pelo prenome x eleitorado (TSE 2024, 18-69 anos, municipios da comarca)
e perfil ocupacional (COD) x Censo 2022 (SIDRA 10264), este ultimo quando o JSON do Parana estiver baixado.

Le data/comarcas_extra_entradas.csv e data/comarcas_extra_editais.csv (processar_comarcas_dje.py).
Grava data/resultado_comarcas_listas.csv, resultado_comarcas_permanencia.csv, resultado_comarcas_sexo.csv,
resultado_comarcas_perfil.csv. So agregados.

Composicao das comarcas: CODJ, Anexo III, Tabela 2 (TJPR). Entrancia: CODJ, Anexo I.
"""
import csv, io, json, os, re, unicodedata, zipfile
from collections import Counter, defaultdict
from codificar_profissoes import classificar

D = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
COMARCAS = {  # sede: (entrancia, municipios da comarca segundo o CODJ, Anexo III, Tab. 2)
    "Laranjeiras do Sul": ("intermediaria", ["LARANJEIRAS DO SUL", "PORTO BARREIRO", "NOVA LARANJEIRAS", "RIO BONITO DO IGUACU", "MARQUINHO"]),
    "Cantagalo": ("inicial", ["CANTAGALO", "GOIOXIM", "VIRMOND"]),
}
def n(t): return unicodedata.normalize("NFKD", t).encode("ascii", "ignore").decode().upper().strip()

E = list(csv.DictReader(open(os.path.join(D, "comarcas_extra_entradas.csv"), encoding="utf-8")))
ED = list(csv.DictReader(open(os.path.join(D, "comarcas_extra_editais.csv"), encoding="utf-8")))
_canon = {n(c): c for c in COMARCAS}
for r in E + ED: r["comarca"] = _canon.get(n(r["comarca"]), r["comarca"])

# listas: a ultima publicacao de cada (comarca, tipo, ano) vale como a lista daquele ano e tipo
ult = {}
for e in ED:
    k = (e["comarca"], e["tipo"], e["ano"])
    if k not in ult or e["data_dje"] > ult[k]["data_dje"]: ult[k] = e
listas = defaultdict(set); prof = defaultdict(Counter); sexo = defaultdict(Counter)
for r in E:
    k = (r["comarca"], r["tipo"], r["ano"])
    if k in ult and r["edicao"] == ult[k]["edicao"]:
        listas[k].add(r["pessoa_id"]); sexo[k][r["sexo_prenome"]] += 1
        if r["profissao"]: prof[k][classificar(r["profissao"])[0]] += 1

linhas = []
for k in sorted(listas):
    e = ult[k]
    linhas.append([k[0], COMARCAS[k[0]][0], k[1], k[2], e["data_dje"], len(listas[k]), e["pct_profissao"], e["pct_mulheres_prenome"]])
with open(os.path.join(D, "resultado_comarcas_listas.csv"), "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f); w.writerow(["comarca", "entrancia", "tipo", "ano", "data_dje", "pessoas", "pct_profissao", "pct_mulheres_prenome"]); w.writerows(linhas)
print("Listas (ultima publicacao de cada tipo e ano):")
for l in linhas: print("  ", *l, sep=" | ")

# permanencia: lista de um ano contra a do ano anterior, preferindo definitiva; se faltar, provisoria
def lista_do_ano(com, ano):
    for t in ("definitiva", "provisoria"):
        if (com, t, ano) in listas: return t, listas[(com, t, ano)]
    return None, None
perm = []
for com in COMARCAS:
    anos = sorted({a for (c, t, a) in listas if c == com and a.isdigit()})
    for a0, a1 in zip(anos, anos[1:]):
        t0, s0 = lista_do_ano(com, a0); t1, s1 = lista_do_ano(com, a1)
        if s0 and s1 and int(a1) == int(a0) + 1:
            perm.append([com, a1, t1, a0, t0, len(s1), len(s1 & s0), round(100 * len(s1 & s0) / len(s1), 1)])
with open(os.path.join(D, "resultado_comarcas_permanencia.csv"), "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f); w.writerow(["comarca", "ano", "tipo", "ano_anterior", "tipo_anterior", "pessoas", "ja_na_anterior", "pct_permanencia"]); w.writerows(perm)
print("Permanencia:")
for p in perm: print("  ", *p, sep=" | ")

# sexo x eleitorado (TSE 2024, 18-69 anos, todos os municipios da comarca)
z = zipfile.ZipFile("referencias/dados_tse/perfil_eleitorado_2024.zip")
mun2com = {m: c for c, (_, ms) in COMARCAS.items() for m in ms}
g = defaultdict(Counter); esc = defaultdict(Counter)
with z.open("perfil_eleitorado_2024_PR.csv") as f:
    for r in csv.DictReader(io.TextIOWrapper(f, encoding="latin-1"), delimiter=";"):
        c = mun2com.get(n(r["NM_MUNICIPIO"]))
        if not c: continue
        m = re.search(r"(\d+)", r["DS_FAIXA_ETARIA"]); im = int(m.group(1)) if m else -1
        if not 18 <= im <= 69: continue
        q = int(r["QT_ELEITORES"]); g[c][n(r["DS_GENERO"])] += q; esc[c][n(r["DS_GRAU_ESCOLARIDADE"])] += q
sx = []
for c, cnt in g.items():
    F = sum(v for k, v in cnt.items() if k.startswith("FEM")); M = sum(v for k, v in cnt.items() if k.startswith("MASC"))
    sup = sum(v for k, v in esc[c].items() if "SUPERIOR COMPLETO" in k); tot = sum(esc[c].values())
    sx.append([c, F + M, round(100 * F / (F + M), 1), round(100 * sup / tot, 1)])
with open(os.path.join(D, "resultado_comarcas_sexo.csv"), "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f); w.writerow(["comarca", "eleitores_18_69", "pct_mulheres_eleitorado", "pct_superior_completo_eleitorado"]); w.writerows(sx)
print("Eleitorado 18-69 (TSE 2024):")
for s in sx: print("  ", *s, sep=" | ")
for c, tot_el, pf, _ in sx:
    for k in sorted(listas):
        if k[0] == c:
            cl = sexo[k]["F"] + sexo[k]["M"]
            print(f"   {c} {k[1]} {k[2]}: {len(listas[k])} alistados = {1000*len(listas[k])/tot_el:.1f} por mil eleitores; mulheres {100*sexo[k]['F']/cl:.1f}% (eleitorado {pf}%)")

# perfil ocupacional (COD) da lista mais recente de cada comarca; Censo quando houver o JSON do Parana
SIDRA_GR = [("DIRETORES", 1), ("PROFISSIONAIS DAS CIENCIAS", 2), ("TECNICOS", 3), ("APOIO ADMINISTRATIVO", 4),
            ("SERVICOS, VENDEDORES", 5), ("AGROPECUARIA", 6), ("OPERARIOS E ARTESAOS", 7), ("OPERADORES DE INSTALACOES", 8),
            ("OCUPACOES ELEMENTARES", 9), ("FORCAS ARMADAS", 0)]
def grupo(cat):
    """Categoria do classificador ('2 Profissionais...') -> numero do grande grupo; demais (estudante etc.) -> None."""
    m = re.match(r"(\d) ", cat)
    return int(m.group(1)) if m else None
def grupo_sidra(nome):
    nn = n(nome)
    return next((g for k, g in SIDRA_GR if k in nn), None)
censo = {}
js = "referencias/dados_ibge/SIDRA_10264_Parana_municipios_grupos_ocupacao.json"
if os.path.exists(js):
    dados = json.load(open(js))[1:]
    for r in dados:
        mun = n(re.sub(r"\s*(-\s*PR|\(PR\))\s*$", "", r["D1N"])); c = mun2com.get(mun)
        if not c: continue
        gr = grupo_sidra(r.get("D7N", ""))
        if gr is not None and r.get("MN") == "Pessoas" and r["V"].isdigit():
            censo.setdefault(c, Counter())[gr] += int(r["V"])
perf = []
for c in COMARCAS:
    ks = sorted([k for k in listas if k[0] == c], key=lambda k: (k[2], k[1] == "definitiva"))
    k = ks[-1]; cnt = Counter()
    for cat, v in prof[k].items():
        gr = grupo(cat)
        if gr is not None: cnt[gr] += v
    tot = sum(cnt.values())
    for gr in range(10):
        pl = round(100 * cnt[gr] / tot, 1) if tot else ""
        pc = ""
        if c in censo:
            tc = sum(v for g2, v in censo[c].items() if g2 in range(10))
            pc = round(100 * censo[c][gr] / tc, 1) if tc else ""
        perf.append([c, k[2], k[1], gr, cnt[gr], pl, pc])
    if c in censo:
        dis = 0.5 * sum(abs(float(p[5] or 0) - float(p[6] or 0)) for p in perf if p[0] == c)
        print(f"   {c}: dissimilaridade lista x Censo = {dis:.1f}")
with open(os.path.join(D, "resultado_comarcas_perfil.csv"), "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f); w.writerow(["comarca", "ano", "tipo", "grupo_cod", "alistados_classificados", "pct_lista", "pct_censo"]); w.writerows(perf)
print("Perfil (lista mais recente):")
for p in perf: print("  ", *p, sep=" | ")
if not censo: print("   (Censo: rodar baixar_sidra_parana.command e repetir)")
