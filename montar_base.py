#!/usr/bin/env python3
"""Junta as listas do site e do Diario numa base unica de Curitiba: data/base_listas.csv"""
import csv, os
from collections import defaultdict
D = "data"
DJE_INCLUIR = {  # doc_id do Diario -> (vara, tipo, ano, observacao)
    "dje_2009-10-13_ed247_186412": ("Curitiba 2a Vara", "provisoria", "2010", "DJe ed. 247; vara por sobreposicao (93%)"),
    "dje_2009-11-10_ed266_474061": ("Curitiba 1a Vara", "definitiva", "2010", "DJe ed. 266; vara por sobreposicao (100% com a provisoria)"),
    "dje_2010-10-15_ed491_417381": ("Curitiba 2a Vara", "provisoria", "2011", "DJe ed. 491; vara por sobreposicao (95%)"),
    "dje_2011-10-10_ed732_256817": ("Curitiba 2a Vara", "provisoria", "2012", "DJe ed. 732; identificacao provavel (71% da definitiva)"),
    "dje_2012-10-10_ed967_283333": ("Curitiba 2a Vara", "provisoria", "2013", "DJe ed. 967; cabecalho 2a Vara/2013; nomes so coincidem com listas da 2a Vara (26% da definitiva 2013)"),
    "dje_2026-10-09_ed4232_18469": ("Curitiba 1a Vara", "provisoria", "2027", "DJe ed. 4232; Edital 10/2026 (cabecalho confere)"),
}
docs = {r["doc_id"]: r for r in csv.DictReader(open(os.path.join(D, "documentos.csv"), encoding="utf-8"))}
vistos = set(); linhas = []; resumo = defaultdict(int)
for r in csv.DictReader(open(os.path.join(D, "entradas.csv"), encoding="utf-8")):
    if not r["vara"].startswith("Curitiba") or r["tipo"] not in ("provisoria", "definitiva"): continue
    k = (r["vara"], r["tipo"], r["ano"])
    # 2023 da 1a Vara foi publicado em dois editais identicos: fica so o primeiro doc encontrado
    chave_doc = (k, r["doc_id"])
    if k not in vistos and any(x[0] == k for x in resumo): pass
    linhas.append([r["vara"], r["tipo"], r["ano"], r["seq"], r["pessoa_id"], r["profissao"], "site", r["doc_id"], ""])
for r in csv.DictReader(open(os.path.join(D, "dje_entradas.csv"), encoding="utf-8")):
    if r["doc_id"] in DJE_INCLUIR:
        v, t, a, obs = DJE_INCLUIR[r["doc_id"]]
        linhas.append([v, t, a, r["seq"], r["pessoa_id"], r["profissao"], "dje", r["doc_id"], obs])
# um documento por (vara, tipo, ano): o com mais entradas
por_doc = defaultdict(int)
for l in linhas: por_doc[((l[0], l[1], l[2]), l[7])] += 1
melhor = {}
for (k, doc), n in por_doc.items():
    if k not in melhor or n > por_doc[(k, melhor[k])]: melhor[k] = doc
final = [l for l in linhas if melhor[(l[0], l[1], l[2])] == l[7]]
with open(os.path.join(D, "base_listas.csv"), "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f); w.writerow(["vara","tipo","ano","seq","pessoa_id","profissao","fonte","doc_id","observacao"]); w.writerows(final)
cont = defaultdict(lambda: [0, 0, ""])
for l in final:
    c = cont[(l[0], l[1], l[2])]; c[0] += 1; c[1] += bool(l[5].strip()); c[2] = l[6]
print(f"{len(final)} entradas em {len(cont)} listas")
for k in sorted(cont): print(f"  {k[0][9:]} {k[1][:4]} {k[2]}: {cont[k][0]:5} nomes, {100*cont[k][1]/cont[k][0]:3.0f}% com profissao, fonte {cont[k][2]}")
