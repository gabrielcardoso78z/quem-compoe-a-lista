#!/usr/bin/env python3
"""Censo estadual do procedimento de alistamento (editais de lista no Diario, todas as comarcas exceto Curitiba e Cascavel).
Le data/comarcas_pr_editais.csv e data/comarcas_pr_entradas.csv (processar_comarcas_dje.py --todas).
Edicoes examinadas: ago/2022 a out/2026 (ago-dez de 2022 a 2025, jan-jul de 2023 a 2026 e ago-9/out/2026; listas para 2023 a 2027).
Saidas (so agregados): data/resultado_censo_editais.csv (por edital valido), data/resultado_censo_comarcas.csv (por comarca),
data/saida_analise_censo_estadual.txt (via rodar_tudo).

Prazos (art. 426 do CPP): provisoria ate 10/10 e definitiva ate 10/11 do ano anterior ao da lista. Usa-se a data de
veiculacao no Diario; como a publicacao se considera feita no 1o dia util seguinte (Lei 11.419/2006, art. 4o, par. 3o),
veiculacao ate o dia 9 (ou o ultimo dia util antes do dia 10) e o criterio estrito; aqui conta-se ate o dia 10, criterio tolerante.
"""
import csv, os
from collections import Counter, defaultdict
from datetime import date

D = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
E = list(csv.DictReader(open(os.path.join(D, "comarcas_pr_editais.csv"), encoding="utf-8")))
N = list(csv.DictReader(open(os.path.join(D, "comarcas_pr_entradas.csv"), encoding="utf-8")))

# so listas aprovadas na verificacao (verificar_comarcas.py) e de comarcas verificadas
VL = {(r["comarca"], r["edicao"], r["tipo"], r["ano"]) for r in csv.DictReader(open(os.path.join(D, "verificacao_comarcas_listas.csv"), encoding="utf-8")) if r["falhas"] == "ok"}
# listas parciais (publicadas sem o trecho inicial): entram como amostra de profissao e sexo, nao para tamanho nem permanencia
PARC = {(r["comarca"], r["edicao"], r["tipo"], r["ano"]) for r in csv.DictReader(open(os.path.join(D, "verificacao_comarcas_listas.csv"), encoding="utf-8")) if r.get("parcial") == "sim"}
def parcial(e): return (e["comarca"], e["edicao"], e["tipo"], e["ano"]) in PARC
RENOV = {r["comarca"] for r in csv.DictReader(open(os.path.join(D, "verificacao_comarcas.csv"), encoding="utf-8")) if "renovacao" in r["selo"]}
VC = {r["comarca"] for r in csv.DictReader(open(os.path.join(D, "verificacao_comarcas.csv"), encoding="utf-8")) if r["selo"].startswith("verificada")}
validos = [e for e in E if (e["comarca"], e["edicao"], e["tipo"], e["ano"]) in VL and e["comarca"] in VC]
validos = [e for e in validos if e["comarca"] != "?" and e["confianca"] != "lista_nao_extraida_conflito"
           and e["ano"].isdigit() and int(e["numeradas"] or 0) >= 20 and e["tipo"] in ("provisoria", "definitiva")]
# ano coerente: ano seguinte ao da veiculacao, ou o proprio ano se veiculada de jan a set (publicacao tardia);
# fora disso (ex.: lista "para 2023" veiculada em out/2024) = erro do edital ou leitura duvidosa: fica de fora
def coerente(e):
    y, m, a = int(e["data_dje"][:4]), int(e["data_dje"][5:7]), int(e["ano"])
    return a == y + 1 or (a == y and m <= 9)
incoerentes = [e for e in validos if not coerente(e)]
validos = [e for e in validos if e not in incoerentes]
falhos = len(E) - len(validos)
print(f"Editais localizados: {len(E)}; validos para a analise: {len(validos)} "
      f"(fora: sem comarca, conflito, ano ou carater ilegivel, ou menos de 20 nomes extraidos: {falhos - len(incoerentes)}; "
      f"ano declarado incoerente com a data: {len(incoerentes)})")

proc = [e for e in E if e["comarca"] != "?" and e["ano"].isdigit() and e["tipo"] in ("provisoria", "definitiva")
        and coerente(e)]
ult_proc = {}
for e in proc:
    k = (e["comarca"], e["tipo"], e["ano"])
    if k not in ult_proc or e["data_dje"] > ult_proc[k]["data_dje"]: ult_proc[k] = e
print(f"Analise do procedimento (edital localizado, sem exigir a lista): {len(proc)} editais, {len({e['comarca'] for e in proc})} comarcas")

def no_prazo(e):
    y = int(e["ano"]) - 1
    lim = date(y, 10, 10) if e["tipo"] == "provisoria" else date(y, 11, 10)
    d = date.fromisoformat(e["data_dje"])
    return d <= lim

# uma lista por (comarca, tipo, ano): a ultima veiculacao
ult = {}
for e in validos:
    k = (e["comarca"], e["tipo"], e["ano"])
    if k not in ult or e["data_dje"] > ult[k]["data_dje"]: ult[k] = e
L = defaultdict(set)
ids_ed = defaultdict(set)
for r in N: ids_ed[(r["comarca"], r["edicao"], r["tipo"], r["ano"])].add(r["pessoa_id"])
for k, e in ult.items(): L[k] = ids_ed[(k[0], e["edicao"], k[1], k[2])]

linhas = []
for k, e in sorted(ult.items()):
    linhas.append([k[0], k[1], k[2], e["data_dje"], "sim" if no_prazo(e) else "nao", e["numeradas"], e["validas"], e["pct_profissao"], e["pct_mulheres_prenome"], e["confianca"]])
with open(os.path.join(D, "resultado_censo_editais.csv"), "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f); w.writerow(["comarca", "tipo", "ano", "data_dje", "no_prazo_tolerante", "numeradas", "validas", "pct_profissao", "pct_mulheres_prenome", "confianca"]); w.writerows(linhas)

coms = sorted({k[0] for k in ult})
anos = ["2023", "2024", "2025", "2026"]   # anos com as duas fases dentro das janelas (2027 so tem provisoria ate 9/10)
print(f"Comarcas com ao menos uma lista valida: {len(coms)}")

# 1) fases publicadas, por comarca e ano (2023-2026)
fase = Counter()
for c in sorted({k[0] for k in ult_proc}):
    for a in anos:
        p, d = (c, "provisoria", a) in ult_proc, (c, "definitiva", a) in ult_proc
        fase["provisoria e definitiva" if p and d else "so provisoria" if p else "so definitiva" if d else "nenhuma"] += 1
print("Fases localizadas por comarca-ano (2023 a 2026):", dict(fase))

# 2) prazos
for t in ("provisoria", "definitiva"):
    # provisorias de 2027 excluidas: a coleta terminou antes de vencido o prazo (10/10/2026), so registra as publicadas a tempo
    es = [e for k, e in ult_proc.items() if k[1] == t and k[2] in anos]  # listas de 2023 a 2026 (2022: fora do periodo; 2027: coleta antes do fim do prazo)
    ok = sum(no_prazo(e) for e in es)
    print(f"Prazo ({t}): {ok} de {len(es)} veiculadas ate o dia 10 ({100*ok/max(1,len(es)):.0f}%)")

# 3) profissao
pp = [float(e["pct_profissao"]) for e in ult.values() if e["pct_profissao"]]
faixa = Counter("90% ou mais" if x >= 90 else "50% a 90%" if x >= 50 else "menos de 50%" for x in pp)
print("Listas por % de entradas com profissao:", dict(faixa), f"(n={len(pp)})")

# 4) permanencia e consistencia por comarca
def lista(c, a):
    for t in ("definitiva", "provisoria"):
        if (c, t, a) in ult and L[(c, t, a)] and not parcial(ult[(c, t, a)]): return L[(c, t, a)]
    return None
porcom = []
for c in coms:
    perms = []
    for a0, a1 in zip(["2023", "2024", "2025", "2026"], ["2024", "2025", "2026", "2027"]):
        s0, s1 = lista(c, a0), lista(c, a1)
        if s0 and s1: perms.append(round(100 * len(s0 & s1) / len(s1), 1))
    tam = [int(e["validas"]) for k, e in ult.items() if k[0] == c]
    prof = [float(e["pct_profissao"]) for k, e in ult.items() if k[0] == c and e["pct_profissao"]]
    fem = [float(e["pct_mulheres_prenome"]) for k, e in ult.items() if k[0] == c and e["pct_mulheres_prenome"]]
    temP = sum((c, "provisoria", a) in ult for a in anos)
    prazoP = [no_prazo(ult[(c, "provisoria", a)]) for a in anos if (c, "provisoria", a) in ult]  # 2027 fora: coleta antes do fim do prazo
    porcom.append([c, len([k for k in ult if k[0] == c]), temP, sum(prazoP), len(prazoP),
                   round(sum(tam) / len(tam)) if tam else "", round(min(prof)) if prof else "", round(max(prof)) if prof else "",
                   round(sum(fem) / len(fem), 1) if fem else "", ";".join(str(x) for x in perms),
                   ("" if not (perms and max(perms) < 5) else
                    "renovacao_anual_verificada" if c in RENOV else "renovacao_total_ou_atribuicao_duvidosa")])
with open(os.path.join(D, "resultado_censo_comarcas.csv"), "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f); w.writerow(["comarca", "listas", "anos_com_provisoria_2023_2026", "provisorias_no_prazo", "provisorias_total",
                                   "media_nomes", "pct_profissao_min", "pct_profissao_max", "media_pct_mulheres", "permanencias_ano_a_ano", "alerta"])
    w.writerows(porcom)
todas_perm = [float(x) for r in porcom for x in r[9].split(";") if x]
alto = sum(1 for r in porcom if r[9] and max(float(x) for x in r[9].split(";")) >= 80)
print(f"Permanencia ano a ano: {len(todas_perm)} transicoes em {sum(1 for r in porcom if r[9])} comarcas; "
      f"mediana {sorted(todas_perm)[len(todas_perm)//2]:.0f}%; comarcas com alguma transicao >= 80%: {alto}")
print("Permanencia sempre < 5%:", [(r[0], r[10]) for r in porcom if r[10]])
fem_all = [float(e["pct_mulheres_prenome"]) for e in ult.values() if e["pct_mulheres_prenome"]]
print(f"Mulheres (prenome): mediana {sorted(fem_all)[len(fem_all)//2]:.1f}% das listas; listas com mais de 55%: {sum(x>55 for x in fem_all)} de {len(fem_all)}")

# ---------------------------------------------------------------------------------------------------------------
# Por entrancia: CODJ, Anexo I de 2018 (data/codj_comarcas.csv, processar_codj.py), eleitorado TSE 2024 (18-69) e Censo 2022 (SIDRA 10264)
import io, json, re, statistics, unicodedata, zipfile
from codificar_profissoes import classificar
def nn(t): return re.sub(r"\s+", " ", unicodedata.normalize("NFKD", t).encode("ascii", "ignore").decode().upper()).strip()
CODJ = {nn(r["comarca"]): r for r in csv.DictReader(open(os.path.join(D, "codj_comarcas.csv"), encoding="utf-8"))}
mun2com = {nn(m): nn(r["comarca"]) for r in CODJ.values() for m in r["municipios"].split(";") if m}
el = Counter()
z = zipfile.ZipFile("referencias/dados_tse/perfil_eleitorado_2024.zip")
with z.open("perfil_eleitorado_2024_PR.csv") as f:
    for r in csv.DictReader(io.TextIOWrapper(f, encoding="latin-1"), delimiter=";"):
        m = re.search(r"(\d+)", r["DS_FAIXA_ETARIA"]); im = int(m.group(1)) if m else -1
        if 18 <= im <= 69 and nn(r["NM_MUNICIPIO"]) in mun2com: el[mun2com[nn(r["NM_MUNICIPIO"])]] += int(r["QT_ELEITORES"])
SIDRA = [("DIRETORES", 1), ("PROFISSIONAIS DAS CIENCIAS", 2), ("TECNICOS", 3), ("APOIO ADMINISTRATIVO", 4), ("SERVICOS, VENDEDORES", 5),
         ("AGROPECUARIA", 6), ("OPERARIOS E ARTESAOS", 7), ("OPERADORES DE INSTALACOES", 8), ("OCUPACOES ELEMENTARES", 9), ("FORCAS ARMADAS", 0)]
censo = defaultdict(Counter)
for r in json.load(open("referencias/dados_ibge/SIDRA_10264_Parana_municipios_grupos_ocupacao.json"))[1:]:
    mu = nn(re.sub(r"\s*-\s*PR\s*$", "", r["D1N"])); g = next((v for k, v in SIDRA if k in nn(r["D7N"])), None)
    if mu in mun2com and g is not None and r["MN"] == "Pessoas" and r["V"].isdigit(): censo[mun2com[mu]][g] += int(r["V"])
prof_lista = defaultdict(list)
for r in N:
    if r["profissao"]: prof_lista[(r["comarca"], r["edicao"])].append(r["profissao"])

res = []
for c in coms:
    k = nn(c)
    info = CODJ.get(k)
    ent = info["entrancia"] if info else "nao_classificada"
    ks = sorted([kk for kk in ult if kk[0] == c], key=lambda kk: (kk[2], kk[1] == "definitiva"))
    inteiras = [kk for kk in ks if not parcial(ult[kk])]
    e = ult[(inteiras or ks)[-1]]                      # lista mais recente (inteira, se houver)
    pm = round(1000 * int(e["validas"]) / el[k], 1) if el.get(k) and not parcial(e) else ""
    dis = ""
    if e["pct_profissao"] and float(e["pct_profissao"]) >= 50 and censo.get(k):
        cnt = Counter()
        for p in prof_lista[(c, e["edicao"])]:
            m = re.match(r"(\d) ", classificar(p)[0])
            if m: cnt[int(m.group(1))] += 1
        tl, tc = sum(cnt.values()), sum(censo[k].values())
        if tl >= 50: dis = round(50 * sum(abs(cnt[g] / tl - censo[k][g] / tc) for g in range(10)), 1)
    r0 = next(r for r in porcom if r[0] == c)
    res.append([c, ent, info["origem_composicao"] if info else "", el.get(k, ""), e["tipo"], e["ano"], e["validas"], pm,
                e["pct_profissao"], e["pct_mulheres_prenome"], dis, r0[3], r0[4], r0[9]])
with open(os.path.join(D, "resultado_censo_comarcas_entrancia.csv"), "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f); w.writerow(["comarca", "entrancia", "origem_composicao", "eleitores_18_69", "tipo_lista_recente", "ano", "nomes",
                                   "por_mil_eleitores", "pct_profissao", "pct_mulheres", "dissimilaridade_censo",
                                   "provisorias_no_prazo", "provisorias_total", "permanencias"]); w.writerows(res)
print("\nPor entrancia (lista mais recente de cada comarca; medianas):")
def med(xs):
    xs = [float(x) for x in xs if x not in ("", None)]
    return f"{statistics.median(xs):.1f} (n={len(xs)})" if xs else "-"
for ent in ("final", "intermediaria", "inicial", "nao_classificada"):
    g = [r for r in res if r[1] == ent]
    if not g: continue
    pz = sum(r[11] for r in g); pt = sum(r[12] for r in g)
    perms = [x for r in g for x in r[13].split(";") if x]
    print(f"  {ent}: {len(g)} comarcas | por mil eleitores {med(r[7] for r in g)} | profissao {med(r[8] for r in g)}% | "
          f"mulheres {med(r[9] for r in g)}% | dissimilaridade {med(r[10] for r in g)} | permanencia {med(perms)}% | "
          f"provisorias no prazo {pz}/{pt}")
print("  nao classificadas:", [r[0] for r in res if r[1] == "nao_classificada"])
