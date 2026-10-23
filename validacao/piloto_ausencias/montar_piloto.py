#!/usr/bin/env python3
"""Piloto de ausencias: o extrator deixa de achar editais que existem?

Etapa 1 (este script): monta a populacao de obrigacoes (comarca, tipo de lista, ano da lista),
classifica cada uma pelo resultado do extrator atual, sorteia uma amostra estratificada e
prepara a planilha de conferencia manual. Etapa 2 (buscar_candidatos.py) faz a pre-busca textual.

Populacao: comarcas do CODJ (data/codj_comarcas.csv) menos Curitiba e Cascavel, mais Paicandu
(comarca com edital localizado que nao consta no CODJ); listas para 2023 a 2026, provisoria e definitiva.
Situacao no extrator (mesma regra de analise_censo_estadual.py: editais com comarca, tipo e ano legiveis
e ano coerente com a data; ultima veiculacao de cada lista; prazo tolerante, ate o dia 10):
  no_prazo | fora_do_prazo | nao_localizada
Amostra: 10 nao_localizada, 5 fora_do_prazo, 5 no_prazo; semente fixa. Nenhum nome de pessoa e lido ou impresso.
"""
import csv, os, random, unicodedata
from datetime import date

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.abspath(os.path.join(AQUI, "..", ".."))
D = os.path.join(RAIZ, "data")
SEMENTE = 20261022
COTAS = {"nao_localizada": 10, "fora_do_prazo": 5, "no_prazo": 5}
ANOS = ("2023", "2024", "2025", "2026")

def norm(s):
    return unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode().lower().strip()

comarcas = sorted({r["comarca"] for r in csv.DictReader(open(os.path.join(D, "codj_comarcas.csv"), encoding="utf-8"))
                   if norm(r["comarca"]) not in ("curitiba", "cascavel")} | {"Paiçandu"})

def coerente(e):
    y, m, a = int(e["data_dje"][:4]), int(e["data_dje"][5:7]), int(e["ano"])
    return a == y + 1 or (a == y and m <= 9)

E = list(csv.DictReader(open(os.path.join(D, "comarcas_pr_editais.csv"), encoding="utf-8")))
proc = [e for e in E if e["comarca"] != "?" and e["ano"].isdigit() and e["tipo"] in ("provisoria", "definitiva") and coerente(e)]
ult = {}
for e in proc:
    k = (norm(e["comarca"]), e["tipo"], e["ano"])
    if k not in ult or e["data_dje"] > ult[k]["data_dje"]:
        ult[k] = e

def limite(tipo, ano):
    y = int(ano) - 1
    return date(y, 10, 10) if tipo == "provisoria" else date(y, 11, 10)

pop = []
for c in comarcas:
    for a in ANOS:
        for t in ("provisoria", "definitiva"):
            e = ult.get((norm(c), t, a))
            if e is None:
                sit, data, ed = "nao_localizada", "", ""
            else:
                sit = "no_prazo" if date.fromisoformat(e["data_dje"]) <= limite(t, a) else "fora_do_prazo"
                data, ed = e["data_dje"], e["edicao"]
            pop.append({"comarca": c, "tipo": t, "ano_lista": a, "situacao_extrator": sit,
                        "data_dje_extrator": data, "edicao_extrator": ed})

rng = random.Random(SEMENTE)
amostra = []
for sit, n in COTAS.items():
    estrato = [p for p in pop if p["situacao_extrator"] == sit]
    amostra += rng.sample(estrato, n)

def janela(a):
    # da abertura da janela de agosto do ano anterior ate setembro do ano da lista (mesma regra de coerencia)
    return date(int(a) - 1, 8, 1), date(int(a), 9, 30)

MANUAIS = ["edital_existe_no_dje", "edicao_encontrada", "data_disponibilizacao", "pagina", "tipo_correto",
           "comarca_correta", "edicoes_examinadas", "classificacao_final", "observacao", "conferido_por", "data_conferencia"]
os.makedirs(AQUI, exist_ok=True)
with open(os.path.join(AQUI, "piloto_obrigacoes.csv"), "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["id", "comarca", "tipo", "ano_lista", "situacao_extrator", "data_dje_extrator", "edicao_extrator",
                "janela_inicio", "janela_fim", "prazo_legal"] + MANUAIS)
    for i, p in enumerate(amostra, 1):
        ji, jf = janela(p["ano_lista"])
        w.writerow([f"P{i:02d}", p["comarca"], p["tipo"], p["ano_lista"], p["situacao_extrator"], p["data_dje_extrator"],
                    p["edicao_extrator"], ji, jf, limite(p["tipo"], p["ano_lista"])] + [""] * len(MANUAIS))

from collections import Counter
print("comarcas:", len(comarcas), "| obrigacoes:", len(pop), "|", dict(Counter(p["situacao_extrator"] for p in pop)))
print("amostra:", len(amostra), dict(Counter(p["situacao_extrator"] for p in amostra)))
