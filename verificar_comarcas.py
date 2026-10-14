#!/usr/bin/env python3
"""Verificacao comarca a comarca das listas extraidas do Diario (o "trabalho de formiguinha" feito para
Laranjeiras do Sul e Cantagalo, aplicado a todas). Le data/comarcas_pr_editais.csv e comarcas_pr_entradas.csv.

Para cada edital (lista) com 20+ nomes:
  V1 numeracao (descontados os numeros ausentes do texto da edicao): numeros distintos extraidos / ultimo numero >= 0,95
  V2 duplicatas: pessoas repetidas na mesma lista <= 5% (repeticoes do proprio edital ficam registradas)
  V3 identidade: parte da lista presente em listas de OUTRAS comarcas <= 10% (homonimos comuns dao ~1-3%)
  V4 profissao: <= 5% das profissoes mal separadas (numero de ordem colado, CEP, telefone, paragrafo/artigo ou mais de 120 caracteres; titulos longos da CBO passam)
  V5 data: ano da lista = ano da veiculacao + 1, ou o proprio ano se veiculada de jan a set (publicacao tardia)
Por comarca:
  V6 coerencia temporal: com 2+ anos de listas, alguma transicao com 20%+ de permanencia
     (0% em todas = renovacao integral real OU listas de comarcas diferentes; fica pendente para exame)
Selo: "verificada" (a comarca passa em V6 ou tem um so ano, com ao menos uma lista aprovada), "pendente" (motivos listados). Listas reprovadas em V1-V5/V7 saem uma a uma.
Saidas: data/verificacao_comarcas_listas.csv (por lista) e data/verificacao_comarcas.csv (por comarca). So agregados.
"""
import csv, re, os
from collections import Counter, defaultdict

D = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
E = list(csv.DictReader(open(os.path.join(D, "comarcas_pr_editais.csv"), encoding="utf-8")))
N = list(csv.DictReader(open(os.path.join(D, "comarcas_pr_entradas.csv"), encoding="utf-8")))

lista = defaultdict(list)                     # (comarca, edicao, tipo, ano) -> entradas
for r in N: lista[(r["comarca"], r["edicao"], r["tipo"], r["ano"])].append(r)
pid_com = defaultdict(set)                    # pessoa -> comarcas em que aparece
for (c, ed, t, a), rs in lista.items():
    if c == "?": continue                     # lista sem comarca nao conta como "outra comarca" em V3
    for r in rs: pid_com[r["pessoa_id"]].add(c)
ed_info = {(e["comarca"], e["edicao"], e["tipo"], e["ano"]): e for e in E}

linhas, por_com = [], defaultdict(list)
for k, rs in lista.items():
    c, ed, t, a = k
    if c == "?" or len(rs) < 20: continue
    e = ed_info.get(k, {})
    seqs = {int(r["seq"]) for r in rs}; ult = max(int(e.get("ultimo_numero") or 0), max(seqs))
    ids = [r["pessoa_id"] for r in rs]; u = set(ids)
    # numeros ausentes do proprio texto da edicao (lacuna da publicacao, medida na extracao) nao contam contra a leitura
    lac = int(e.get("lacunas_publicacao") or 0)
    v1 = len(seqs) / (ult - lac) if ult - lac > 0 else 0
    v2 = 1 - len(u) / len(ids)
    v3 = sum(1 for p in u if len(pid_com[p] - {c}) > 0) / len(u)
    profs = [r["profissao"] for r in rs if r["profissao"]]
    # profissao mal separada = texto que carrega outra entrada ou o corpo do edital: numero de ordem colado ("51. fulano"),
    # CEP, telefone, paragrafo/artigo, ou mais de 120 caracteres. Titulos longos da CBO, sem esses sinais, passam
    # (ex.: "professores de nivel superior do ensino fundamental (5a a 8a series)", 78 caracteres)
    def mal_separada(p):
        return (len(p) > 120 or re.search(r"\d{1,4}\s*[.)]\s*[a-z\u00e0-\u00fa]", p) is not None
                or re.search(r"\d{5}-?\d{3}|\(\d{2}\)\s*\d{4}|\u00a7\s*\d|\bart\.", p) is not None)
    v4 = sum(mal_separada(p) for p in profs) / len(profs) if len(profs) >= 20 else 0   # com menos de 20 profissoes, nao se mede
    # ano da lista = ano seguinte ao da veiculacao, ou o proprio ano quando veiculada de janeiro a setembro (publicacao tardia)
    _y, _m = int(e.get("data_dje", "0000-00")[:4] or 0), int(e.get("data_dje", "0000-00")[5:7] or 0)
    v5 = a.isdigit() and (int(a) == _y + 1 or (int(a) == _y and _m <= 9))
    # lista parcial: a publicacao comeca depois do 1 (o trecho inicial nao foi impresso; ex.: Telemaco Borba 2026, do
    # 1.070; Araucaria 2026, do 430) mas a parte publicada e continua. Usada so como amostra (profissao, sexo), nunca
    # para tamanho da lista ou permanencia (Gabriel, 12/10/2026)
    v1_rel = len(seqs) / (ult - min(seqs) + 1) if seqs else 0
    parcial = v1 < 0.95 and min(seqs) > 1 and v1_rel >= 0.95
    if parcial: v1 = v1_rel
    falhas = [n for n, ok in (("V1 numeracao", v1 >= 0.95), ("V2 duplicatas", v2 <= 0.05),
                              ("V3 identidade", v3 <= 0.10), ("V4 profissao", v4 <= 0.05), ("V5 data", v5)) if not ok]
    linhas.append([c, ed, e.get("data_dje", ""), t, a, len(u), round(100 * v1, 1), round(100 * v2, 1), round(100 * v3, 1),
                   round(100 * v4, 1), "sim" if v5 else "nao", round(100 * len(profs) / len(rs), 1), ";".join(falhas) or "ok",
                   "sim" if parcial else ""])
    por_com[c].append((t, a, e.get("data_dje", ""), u, falhas))


FORTE = ("mesma_coluna", "concorda", "so_fecho", "reatribuida_por_identidade")
for c, ls in por_com.items():
    fortes = [u for (t, a, d, u, fal), k in zip(ls, range(len(ls)))]
for c in list(por_com):
    ls = por_com[c]
    conf = {}
    for (cc, ed, t, a), rs in lista.items():
        if cc == c: conf[(t, a, ed_info.get((cc, ed, t, a), {}).get("data_dje", ""))] = ed_info.get((cc, ed, t, a), {}).get("confianca", "")
    uf = set().union(*[u for (t, a, d, u, fal) in ls if conf.get((t, a, d)) in FORTE] or [set()])
    novos = []
    for (t, a, d, u, fal) in ls:
        if conf.get((t, a, d)) not in FORTE and uf and len(u & uf) / len(u) < 0.2:
            fal = fal + ["V7 atribuicao fraca nao confirmada"]
            for l in linhas:
                if l[0] == c and l[2] == d and l[3] == t and l[4] == a: l[12] = (l[12] + ";" if l[12] != "ok" else "") + "V7 atribuicao fraca nao confirmada"
        novos.append((t, a, d, u, fal))
    por_com[c] = novos

# gravado so depois da V7 (antes era gravado antes, e a reprovacao em V7 nunca chegava ao censo: auditoria 12/10/2026, B1)
with open(os.path.join(D, "verificacao_comarcas_listas.csv"), "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["comarca", "edicao", "data_dje", "tipo", "ano", "pessoas", "v1_numeracao_pct", "v2_duplicatas_pct",
                "v3_em_outras_comarcas_pct", "v4_profissao_longa_pct", "v5_data_coerente", "pct_profissao", "falhas", "parcial"])
    w.writerows(sorted(linhas))

res = []
for c, ls in sorted(por_com.items()):
    # uma lista por ano: a definitiva mais recente, senao a provisoria
    ano = {}
    for t, a, d, u, fal in sorted(ls, key=lambda x: (x[1], x[0] == "definitiva", x[2])):
        if fal and all(f.split()[0] in ("V1", "V2", "V3", "V4", "V5", "V7") for f in fal): continue
        ano[a] = (t, u)
    anos = sorted(a for a in ano if a.isdigit())
    perms = [round(100 * len(ano[a1][1] & ano[a0][1]) / len(ano[a1][1]), 1)
             for a0, a1 in zip(anos, anos[1:]) if int(a1) == int(a0) + 1]
    # listas com falha em V1-V5 ou V7 sao excluidas uma a uma; a comarca segue com as demais (so V6 reprova a comarca)
    graves = sorted({f for *_, fal in ls for f in fal if f.split()[0] == "V3"
                     and not any(g.split()[0] == "V7" for g in fal)})
    excl = sum(1 for *_, fal in ls if fal and all(f.split()[0] in ("V1", "V2", "V3", "V4", "V5", "V7") for f in fal))
    falhas = graves[:]
    if len(anos) >= 2 and perms and max(perms) < 20: falhas.append("V6 coerencia temporal")
    if excl == len(ls): falhas.append("todas as listas excluidas (V1-V5/V7)")
    # renovacao integral real: listas do MESMO ano coincidem (90%+), embora mudem de um ano para o outro
    mesmo_ano = defaultdict(list)
    for t, a, d, u, fal in ls:
        if not (fal and all(f.split()[0] in ("V1", "V2", "V3", "V4", "V5", "V7") for f in fal)): mesmo_ano[a].append(u)
    coerente = [max(len(x & y) / min(len(x), len(y)) for i, x in enumerate(us) for y in us[i + 1:])
                for us in mesmo_ano.values() if len(us) >= 2]
    renov = "V6 coerencia temporal" in falhas and coerente and min(coerente) >= 0.9
    if renov: falhas.remove("V6 coerencia temporal")
    selo = ("verificada (renovacao anual)" if renov and not falhas else "verificada" if not falhas else "pendente")
    res.append([c, len(ls), len(anos), ";".join(map(str, perms)), selo, ";".join(falhas), excl])
with open(os.path.join(D, "verificacao_comarcas.csv"), "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f); w.writerow(["comarca", "listas", "anos", "permanencias", "selo", "falhas", "listas_excluidas_v4_v5"]); w.writerows(res)

sel = Counter(r[4] for r in res)
print(f"Listas verificadas: {len(linhas)} | ok: {sum(l[12] == 'ok' for l in linhas)}")
print("Falhas por criterio (listas):", Counter(f for l in linhas for f in l[12].split(";") if f != "ok"))
print(f"Comarcas: {len(res)} | {dict(sel)}")
print("Pendentes:")
for r in res:
    if r[4] == "pendente": print(f"   {r[0]:28s} listas={r[1]:2d} anos={r[2]} perm={r[3]:22s} -> {r[5]}")
