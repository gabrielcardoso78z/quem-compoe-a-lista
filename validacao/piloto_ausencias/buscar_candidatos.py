#!/usr/bin/env python3
"""Etapa 2 do piloto: pre-busca textual das paginas candidatas para cada obrigacao sorteada.

Para cada edicao do Diario baixada (dje/) na janela da obrigacao, extrai o texto (pdftotext -layout) e guarda
em cache (fora do repositorio, padrao ~/piloto_cache) so as paginas que contem "jurad". Uma pagina e candidata
se menciona o nome da comarca (sem acento, palavra inteira). Sinais registrados por pagina: "comarca de <nome>"
ou "foro ... de <nome>"; "lista geral"; "426"; "provisori"/"definitiv". So contagens e sinais sao gravados:
nenhum nome de pessoa sai do script. A pre-busca so orienta a leitura; quem decide e a conferencia manual no PDF.

Uso: python3 auditoria/piloto_ausencias/buscar_candidatos.py [pasta_cache]
"""
import csv, json, os, re, subprocess, sys, unicodedata
from collections import defaultdict
from datetime import date

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.abspath(os.path.join(AQUI, "..", ".."))
DJE = os.path.join(RAIZ, "dje")
CACHE = sys.argv[1] if len(sys.argv) > 1 else os.path.expanduser("~/piloto_cache")
os.makedirs(CACHE, exist_ok=True)

def norm(s):
    return unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode().lower()

def paginas(pdf):
    out = os.path.join(CACHE, os.path.basename(pdf)[:-4] + ".json")
    if not os.path.exists(out):
        t = subprocess.run(["pdftotext", "-layout", pdf, "-"], capture_output=True, text=True, errors="replace").stdout
        json.dump({i + 1: norm(p) for i, p in enumerate(t.split("\f")) if "jurad" in norm(p)}, open(out, "w"))
    return json.load(open(out))

edicoes = sorted(f for f in os.listdir(DJE) if f.endswith(".pdf"))
data_ed = {f: date.fromisoformat(f[:10]) for f in edicoes}

ob = list(csv.DictReader(open(os.path.join(AQUI, "piloto_obrigacoes.csv"), encoding="utf-8")))
linhas, resumo = [], []
for o in ob:
    nome = norm(o["comarca"])
    pat_nome = re.compile(r"\b" + re.escape(nome) + r"\b")
    pat_com = re.compile(r"(comarca|foro)[^\n]{0,80}\b" + re.escape(nome) + r"\b")
    ji, jf = date.fromisoformat(o["janela_inicio"]), date.fromisoformat(o["janela_fim"])
    na_janela = [f for f in edicoes if ji <= data_ed[f] <= jf]
    fortes = 0
    for f in na_janela:
        for pg, txt in paginas(os.path.join(DJE, f)).items():
            n = len(pat_nome.findall(txt))
            if not n:
                continue
            s = {"comarca_de": bool(pat_com.search(txt)), "lista_geral": "lista geral" in txt, "art426": "426" in txt,
                 "provisoria": "provisori" in txt, "definitiva": "definitiv" in txt}
            # sinais no trecho de 800 caracteres em torno de cada mencao (a pagina inteira gera falso positivo: "426" aparece em numeros de processo)
            tr = " ".join(txt[max(0, m.start() - 800):m.end() + 800] for m in pat_nome.finditer(txt))
            for k in ("lista geral", "alistad", "alistamento", "art. 425", "art. 426"):
                s["t_" + k] = tr.count(k)
            s["t_provisori"], s["t_definitiv"] = tr.count("provisori"), tr.count("definitiv")
            s["t_sessao"] = tr.count("sorteio") + tr.count("reuniao") + tr.count("convoca") + tr.count("suplente")
            forte = bool(s["t_lista geral"] or s["t_alistad"] or s["t_alistamento"] or s["t_art. 425"] or s["t_art. 426"])
            fortes += forte
            linhas.append([o["id"], o["comarca"], o["tipo"], o["ano_lista"], f[:-4], f[:10], pg, n,
                           *[("sim" if s[k] else "") if isinstance(s[k], bool) else s[k] for k in s], "sim" if forte else ""])
    resumo.append([o["id"], o["comarca"], o["tipo"], o["ano_lista"], o["situacao_extrator"], len(na_janela),
                   sum(1 for l in linhas if l[0] == o["id"]), fortes])

with open(os.path.join(AQUI, "piloto_candidatos.csv"), "w", newline="", encoding="utf-8") as fh:
    w = csv.writer(fh)
    w.writerow(["id", "comarca", "tipo", "ano_lista", "edicao", "data", "pagina", "mencoes_comarca",
                "comarca_de", "lista_geral_pagina", "art426_pagina", "provisoria_pagina", "definitiva_pagina",
                "trecho_lista_geral", "trecho_alistad", "trecho_alistamento", "trecho_art425", "trecho_art426",
                "trecho_provisori", "trecho_definitiv", "trecho_sinais_de_sessao", "candidata_forte"])
    w.writerows(linhas)
with open(os.path.join(AQUI, "piloto_resumo_prebusca.csv"), "w", newline="", encoding="utf-8") as fh:
    w = csv.writer(fh)
    w.writerow(["id", "comarca", "tipo", "ano_lista", "situacao_extrator", "edicoes_na_janela", "paginas_candidatas", "candidatas_fortes"])
    w.writerows(resumo)
for r in resumo:
    print(*r, sep=" | ")
