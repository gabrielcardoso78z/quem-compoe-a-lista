#!/usr/bin/env python3
"""Le os anexos do CODJ (Lei 14.277/2003) em referencias/normas e grava data/codj_comarcas.csv:
comarca, entrancia (Anexo I, versao de 08/01/2018; a de 24/03/2010 fica como conferencia) e municipios que a compoem (Anexo III, Tabela 2, versao de 08/01/2015).
Os nomes de municipio sao validados contra os 399 municipios do PR (TSE 2024); o que nao casa e descartado.
A Comarca da Regiao Metropolitana de Curitiba (Anexo III, Tabela 1) nao esta nesta tabela: seus foros entram so pela entrancia."""
import csv, io, os, re, subprocess, unicodedata, zipfile
AQUI = os.path.dirname(os.path.abspath(__file__))
NORM = os.path.join(AQUI, "referencias/normas")
def n(t): return re.sub(r"\s+", " ", unicodedata.normalize("NFKD", t).encode("ascii", "ignore").decode().upper()).strip()
def texto(pdf): return subprocess.run(["pdftotext", "-layout", pdf, "-"], capture_output=True, text=True).stdout

z = zipfile.ZipFile(os.path.join(AQUI, "referencias/dados_tse/perfil_eleitorado_2024.zip"))
with z.open("perfil_eleitorado_2024_PR.csv") as f:
    MUN = {n(r["NM_MUNICIPIO"]): r["NM_MUNICIPIO"].strip().title() for r in csv.DictReader(io.TextIOWrapper(f, encoding="latin-1"), delimiter=";")}
def prefixo_municipio(s):
    pal = n(s).split()
    for k in range(min(6, len(pal)), 0, -1):
        if " ".join(pal[:k]) in MUN: return MUN[" ".join(pal[:k])]
    return None

# Anexo I: entrancia
ent = {}
for l in texto(os.path.join(NORM, "CODJ_Anexo_I_entrancias_2010.pdf")).split("\n"):
    for m in re.finditer(r"(?<![\w])(\d{1,2})\s+([A-ZÀ-Ú][^\d]*?)(?=\s{2,}\d|\s{3,}|\s*$)", l):
        nome, x = m.group(2).strip(), m.start()
        if "Comarca da Regi" in nome: continue
        ent[n(nome)] = ("final" if x < 40 else "intermediaria" if x < 110 else "inicial", nome)
    for m in re.finditer(r"Foro (?:Central|Regional) de ([A-ZÀ-Ú][\w\sà-ú]+?)(?=\s{2,}|$)", l):
        ent[n(m.group(1))] = ("final", m.group(1).strip() + " (foro da RM de Curitiba)")

# Anexo I, versao de 08/01/2018 (transcrita de PDF do TJPR em referencias/normas/CODJ_Anexo_I_entrancias_2018.csv):
# prevalece sobre a de 2010 (Leis 17.210/2012 e 17.249/2012: Regioes Metropolitanas de Londrina e Maringa,
# elevacoes de entrancia, comarcas novas como Ampere, Marmeleiro, Sao Joao, Nova Aurora e Pontal do Parana)
ent2010 = dict(ent)
for r in csv.DictReader(open(os.path.join(NORM, "CODJ_Anexo_I_entrancias_2018.csv"), encoding="utf-8")):
    rm = r["organizacao"]
    ent[n(r["unidade"])] = (r["entrancia"], r["unidade"] + (" (foro da RM de " + rm.split("Metropolitana de ")[1] + ")" if rm else ""))
ent.pop(n("Santa Izabel do Ivaí"), None)   # grafia de 2010; em 2018, "Santa Isabel do Ivaí"
for k in [k for k in ent if k in ent2010 and ent2010[k][0] != ent[k][0]]:
    print("entrancia mudou de 2010 para 2018:", ent[k][1], ent2010[k][0], "->", ent[k][0])
print("so em 2010 (fora da lista de 2018):", sorted(v[1] for k, v in ent2010.items() if k not in {n(r["unidade"]) for r in csv.DictReader(open(os.path.join(NORM, "CODJ_Anexo_I_entrancias_2018.csv"), encoding="utf-8"))}))

# Anexo III, Tabela 2: composicao
comp, atual = {}, None
for l in texto(os.path.join(NORM, "CODJ_Anexo_III_Tabela_2_composicao_2015.pdf")).split("\n"):
    m = re.match(r"^\s{20,60}(\d{1,3})\s+(\S.*?)\s{2,}(\S.*)$", l)
    if m:
        c = prefixo_municipio(m.group(2))
        if c: atual = c; comp.setdefault(atual, []); resto = m.group(3)
        else: resto = None
    else:
        resto = l.strip() if atual and re.match(r"^\s{60,}\S", l) else None
    if atual and resto:
        mu = prefixo_municipio(resto)
        if mu and mu not in comp[atual]: comp[atual].append(mu)

linhas = []
for k, (e, nome) in sorted(ent.items()):
    c = prefixo_municipio(nome.split(" (foro")[0]) or nome
    if "(foro" in nome: mun, origem = c, "foro"
    elif comp.get(c): mun, origem = ";".join(comp[c]), "anexo_iii_tab2"
    else: mun, origem = c, "so_sede"   # transferidas para a Tabela 1 (regioes metropolitanas) ou nao lidas
    linhas.append([c, e, mun, origem])
with open(os.path.join(AQUI, "data", "codj_comarcas.csv"), "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f); w.writerow(["comarca", "entrancia", "municipios", "origem_composicao"]); w.writerows(linhas)
from collections import Counter
print("entrancias:", Counter(e for e, _ in ent.values()))
print("comarcas com composicao lida:", len(comp), "| municipios cobertos:", len({m for v in comp.values() for m in v}))
sem = [l[0] for l in linhas if l[3] == "so_sede"]
print("comarcas classificadas sem composicao:", len(sem), sem[:15])
