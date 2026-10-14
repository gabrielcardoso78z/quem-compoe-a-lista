#!/usr/bin/env python3
"""Extrai listas de jurados de Curitiba do texto do Diario (pdftotext -layout), pseudonimiza e grava data/dje_*.csv.

Versao consolidada (12/10/2026): inclui o antigo auxiliares/_proc2013.py (mesmo codigo, outros candidatos e
outros arquivos de saida). Versoes antigas em auxiliares/historico/.

Uso:  python3 processar_dje.py [pasta_txt] [principal|2013|todos]
      pasta_txt padrao: ~/djetxt (texto gerado por "python3 buscar_dje.py converter")
      principal -> data/dje_documentos.csv e data/dje_entradas.csv (usados por montar_base.py)
      2013      -> data/dje_documentos_2013.csv e data/dje_entradas_2013.csv (busca da 1a Vara 2013; nao entra na base)
"""
import csv, glob, os, re, sys, collections
from coletar_listas import separar, chave_secreta, pseudonimo, DATA
ENT = re.compile(r"^\s*(\d{1,4})\s*[.\-–)]\s*(.+?)\s*$")
CANDIDATOS = [  # (arquivo, linha do cabecalho, tipo, ano_da_lista)
    ("2009-10-13_ed247", 186412, "provisoria", "2010"),
    ("2009-10-15_ed249", 269190, "provisoria", "2010"),
    ("2009-11-10_ed266", 473038, "definitiva", "2010"),
    ("2009-11-10_ed266", 474061, "definitiva", "2010"),
    ("2010-10-15_ed491", 417381, "provisoria", "2011"),
    ("2011-10-10_ed732", 256817, "provisoria", "2012"),
    ("2011-10-10_ed732", 259366, "provisoria", "2012"),
    ("2011-10-13_ed734", 339717, "provisoria", "2012"),
    ("2012-10-02_ed961", 275298, "provisoria", "2013"),
    ("2012-10-10_ed967", 283333, "provisoria", "2013"),
    ("2026-10-08_ed4231", 293248, "provisoria", "2027"),
    ("2026-10-09_ed4232", 18469, "provisoria", "2027"),
]
CANDIDATOS_2013 = [  # busca da lista de 2013 da 1a Vara (ex-_proc2013.py)
    ("2012-10-22_ed974", 237280, "provisoria", "2013"),
    ("2012-10-22_ed974", 252946, "provisoria", "2013"),
    ("2012-10-23_ed975", 355674, "provisoria", "2013"),
    ("2012-11-12_ed988", 277124, "definitiva", "2013"),
    ("2012-11-13_ed989", 266483, "definitiva", "2013"),
    ("2012-11-14_ed990", 218157, "provisoria", "2013"),
    ("2012-10-03_ed962", 317232, "provisoria", "2013"),
]
CONJUNTOS = {"principal": (CANDIDATOS, ""), "2013": (CANDIDATOS_2013, "_2013")}


def extrair(L, i0):
    """Segue a numeracao 1, 2, 3... a partir do cabecalho, tolerando quebras de linha."""
    out, esperado, i, perdidas = [], 1, i0, 0
    while i < min(len(L), i0 + 40000):
        m = ENT.match(L[i])
        if m and int(m.group(1)) in (esperado, esperado + 1, esperado + 2):
            texto = m.group(2)
            # continua na linha seguinte se o nome terminou sem profissao e a proxima nao e entrada
            if i + 1 < len(L) and L[i + 1].strip() and not ENT.match(L[i + 1]) and texto.rstrip().endswith(("-", "–")):
                texto += " " + L[i + 1].strip()
            out.append((m.group(1), texto)); esperado = int(m.group(1)) + 1; perdidas = 0
        elif out:
            perdidas += 1
            if perdidas > 400:
                # a lista pode continuar mais adiante (quebra de pagina/coluna): procura "esperado" seguido de "esperado+1"
                salto = next((j for j in range(i, min(len(L), i + 20000))
                              if (m1 := ENT.match(L[j])) and int(m1.group(1)) == esperado
                              and any((m2 := ENT.match(L[k])) and int(m2.group(1)) == esperado + 1 for k in range(j + 1, min(len(L), j + 6)))), None)
                if salto is None: break
                i, perdidas = salto, 0
                continue
        i += 1
    return out


def processar(TXT, candidatos, sufixo):
    chave = chave_secreta()
    # conjuntos das listas do site, para identificar a vara pela sobreposicao
    site = collections.defaultdict(set)
    for r in csv.DictReader(open(os.path.join(DATA, "entradas.csv"), encoding="utf-8")):
        if r["vara"].startswith("Curitiba"): site[(r["vara"], r["tipo"], r["ano"])].add(r["pessoa_id"])
    docs, ents = [], []
    for arq, ln, tipo, ano in candidatos:
        L = open(os.path.join(TXT, arq + ".txt"), encoding="utf-8", errors="ignore").read().split("\n")
        itens = extrair(L, ln)
        ids = []
        for seq, t in itens:
            nome, prof = separar(t)
            if len(nome.split()) >= 2: ids.append((seq, pseudonimo(nome, chave), prof))
        s = {p for _, p, _ in ids}
        sobre = sorted(((len(s & v) / max(len(s), 1), k) for k, v in site.items() if k[2] in (ano, str(int(ano) - 1), str(int(ano) + 1))), reverse=True)[:2]
        prof = sum(1 for _, _, p in ids if p.strip())
        docs.append([arq, ln, tipo, ano, len(ids), prof, sobre[0][1][0] if sobre else "", f"{sobre[0][0]:.2f}" if sobre else "", str(sobre[0][1][1:]) if sobre else ""])
        print(arq, ln, tipo, ano, "entradas", len(ids), "com_prof", prof, "melhor_sobreposicao", [(f"{a:.2f}", k) for a, k in sobre], flush=True)
        for seq, p, pr in ids: ents.append([f"dje_{arq}_{ln}", tipo, ano, seq, p, pr])
    with open(os.path.join(DATA, f"dje_documentos{sufixo}.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f); w.writerow(["edicao","linha","tipo","ano","n_entradas","com_profissao","vara_por_sobreposicao","sobreposicao","lista_comparada"]); w.writerows(docs)
    with open(os.path.join(DATA, f"dje_entradas{sufixo}.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f); w.writerow(["doc_id","tipo","ano","seq","pessoa_id","profissao"]); w.writerows(ents)


def main(argv):
    TXT = next((a for a in argv if a not in CONJUNTOS and a != "todos"), os.path.expanduser("~/djetxt"))
    qual = next((a for a in argv if a in CONJUNTOS or a == "todos"), "principal")
    if not glob.glob(os.path.join(TXT, "*.txt")):
        sys.exit(f"Sem texto do Diario em {TXT}. Rode antes: python3 buscar_dje.py converter")
    for nome in (CONJUNTOS if qual == "todos" else [qual]):
        print(f"== conjunto {nome}", flush=True)
        processar(TXT, *CONJUNTOS[nome])


if __name__ == "__main__":
    main(sys.argv[1:])
