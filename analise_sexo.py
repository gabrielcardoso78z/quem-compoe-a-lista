#!/usr/bin/env python3
"""Sexo provavel dos alistados pelo primeiro nome (tabela de prenomes do Censo 2010, Brasil.io genero-nomes).
Roda SO no computador do pesquisador: le os nomes em raw/ e raw_conv/, mas grava apenas contagens agregadas.
Regra: feminino se >= 90% das pessoas com aquele prenome no Censo 2010 sao mulheres; masculino se >= 90% homens;
indeterminado entre esses limites; nao encontrado se o prenome nao consta da tabela.
Saida: data/resultado_sexo.csv"""
import csv, glob, gzip, os, re, unicodedata
from collections import Counter, defaultdict
from coletar_listas import separar, titulo
from processar_listas import extrair, VARAS
import processar_convocacoes as PC
LIMIAR = 0.9
def nrm(t): return re.sub(r"[^A-Z]", "", unicodedata.normalize("NFKD", t).encode("ascii", "ignore").decode().upper())
TAB = {}
for r in csv.DictReader(gzip.open("referencias/dados_nomes/nomes.csv.gz", "rt", encoding="utf-8")):
    f, m = float(r["frequency_female"] or 0), float(r["frequency_male"] or 0)
    for n in [r["first_name"]] + [x for x in (r.get("alternative_names") or "").split("|") if x]:
        k = nrm(n)
        if k and k not in TAB: TAB[k] = (f, m)
def sexo(nome):
    toks = [t for t in re.split(r"\s+", nome.strip()) if t]
    if not toks: return "nao encontrado"
    k = nrm(toks[0])
    if k not in TAB: return "nao encontrado"
    f, m = TAB[k]; tot = f + m
    if tot == 0: return "nao encontrado"
    return "F" if f / tot >= LIMIAR else "M" if m / tot >= LIMIAR else "indeterminado"
# universo: os mesmos documentos do site usados na base (Curitiba) + Cascavel
usados = {}
for r in csv.DictReader(open("data/base_listas.csv", encoding="utf-8")):
    if r["fonte"] == "site": usados[r["doc_id"]] = (r["vara"], r["tipo"], r["ano"])
for r in csv.DictReader(open("data/documentos.csv", encoding="utf-8")):
    if r["vara"] == "Cascavel": usados[r["doc_id"]] = ("Cascavel", r["tipo"] if r["tipo"] != "lista_outra" else "definitiva", r["ano"])
out = defaultdict(Counter)
for did, chave in usados.items():
    arq = os.path.join("raw", did + ".html")
    if not os.path.exists(arq): continue
    itens, _ = extrair(open(arq, encoding="utf-8").read()); ult = 0; vistos = set()
    for seq, resto in itens:
        if 2000 <= int(seq) <= 2035 and int(seq) > ult + 1: continue
        ult = int(seq); nome, _ = separar(resto)
        if len(nome.split()) < 2 or seq in vistos: continue
        vistos.add(seq)
        out[chave][sexo(nome)] += 1
# editais de convocacao (sorteados), por vara e ano
for arq in sorted(glob.glob("raw_conv/*.html")):
    did = os.path.basename(arq)[:-5]; vara = PC.INSTANCIAS.get(did.split("_")[0], "")
    pag = open(arq, encoding="utf-8").read(); ano, mes = PC.mes_ano(titulo(pag))
    if not vara or not ano: continue
    itens, formato = PC.extrair(pag)
    if formato not in ("numerada", "mista"): continue
    ult = 0
    for seq, resto in itens:
        if 2000 <= int(seq) <= 2035 and int(seq) > ult + 1: continue
        ult = int(seq); nome, _ = separar(resto.strip().rstrip(";.,"))
        if len(nome.split()) < 2: continue
        out[(vara, "sorteados", str(ano))][sexo(nome)] += 1
with open("data/resultado_sexo.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f); w.writerow(["vara", "tipo", "ano", "n", "F", "M", "indeterminado", "nao_encontrado", "pct_F_entre_classificados", "pct_classificados"])
    for k in sorted(out):
        c = out[k]; n = sum(c.values()); cl = c["F"] + c["M"]
        w.writerow([*k, n, c["F"], c["M"], c["indeterminado"], c["nao encontrado"], round(100 * c["F"] / cl, 1) if cl else "", round(100 * cl / n, 1)])
print("ok: data/resultado_sexo.csv (so contagens)")
