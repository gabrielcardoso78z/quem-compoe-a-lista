#!/usr/bin/env python3
"""Buscas no texto do Diario da Justica (DJe) do TJPR. Imprime so metadados e agregados; nenhum nome.

Versao consolidada (12/10/2026) dos scripts de auxiliares/ (versoes antigas em auxiliares/historico/):
  converter   <- primeira parte de _buscar_cascavel_dje.py (agora gera tambem o texto padrao em ~/djeraw)
  localizar   <- localizar.py (variante 1) e loc3.py (variante 2): cabecalhos de listas das Varas de Curitiba;
                 forneceu as linhas anotadas em processar_dje.py
  editais     <- _editais_pr.py: todos os editais de lista ("foram alistados ... em carater ...") e a comarca
  cascavel    <- _buscar_cascavel_dje.py: editais de lista e de convocacao de Cascavel
  identificar <- _identificar_listas_curitiba_dje.py: listas de Curitiba por sobreposicao de nomes pseudonimizados
  profissao   <- _profissao_curitiba_dje.py: o DJe traz a profissao que falta no site?
  varrer      <- _varrer.py: sequencias numeradas de 150+ nomes comparadas com as listas de 2013

Uso: python3 buscar_dje.py <modo> [opcoes]      (python3 buscar_dje.py <modo> -h para as opcoes)
Exemplos:
  python3 buscar_dje.py converter
  python3 buscar_dje.py identificar --padrao "2012-*" --limiar 0.3     (busca da 1a Vara 2013)
  python3 buscar_dje.py localizar --padrao "2012-*" --variante 2
"""
import argparse, csv, json, os, re, sys
from collections import defaultdict
import dje_comum as dc

AQUI = dc.AQUI
os.chdir(AQUI)
sys.path.insert(0, AQUI)
BASE = os.path.join(AQUI, "data", "base_listas.csv")
# regex de nome numerado no texto achatado (identificar, profissao)
NOME_ACHATADO = r"(?:^|\s)\d{1,4}\s*[.\-–)]\s*([A-ZÀ-Úa-zà-ú][A-Za-zÀ-ú' ]{5,70}?)"


def m_converter(a):
    n1, n2 = dc.converter(raw=not a.sem_raw)
    print(f"convertidas: {n1} em {dc.TXT_LAYOUT} (-layout), {n2} em {dc.TXT_RAW} (padrao)")


def m_localizar(a):
    pasta = a.txt or dc.TXT_LAYOUT
    if a.variante == 1:
        pat_vara = re.compile(r"(1|2|primeir|segund)[ªaºo]?\s*vara\s*(privativa\s*)?(do\s*)?(plen[aá]rio\s*)?(do\s*)?(1[ºo]\s*)?tribunal\s*do\s*j[uú]ri", re.I)
        for f in dc.arquivos(a.padrao, pasta):
            L = dc.ler_linhas(f); low = [x.lower() for x in L]
            for i, l in enumerate(L):
                m = pat_vara.search(l)
                if not m: continue
                ctx = " ".join(low[max(0, i-15):i+40])
                if ("curitiba" in ctx or "capital" in ctx) and re.search(r"lista.{0,40}jurad|alistamento|alistad", ctx):
                    nums = sum(1 for x in L[i:i+3000] if re.match(r"^\s*\d{1,4}\s*[.\-–)]\s*\S", x))
                    tipo = "provis" if "provis" in ctx else ("definit" if "definit" in ctx else "?")
                    vara = "1a" if re.match(r"\s*(1|primeir)", m.group(0), re.I) else "2a"
                    print(dc.edicao(f, 21), "linha", i, "vara", vara, tipo, "numeradas_ate_3000_linhas", nums, flush=True)
    else:
        for f in dc.arquivos(a.padrao, pasta):
            L = dc.ler_linhas(f); low = [x.lower() for x in L]
            for i, l in enumerate(low):
                if "tribunal do j" in l or "júri" in l and "vara" in l:
                    ctx = " ".join(low[max(0, i-8):i+25])
                    if ("curitiba" in ctx or "capital" in ctx or "foro central" in ctx) and re.search(r"jurad", ctx) and re.search(r"lista|alistamento|alistad", ctx):
                        nums = sum(1 for x in L[i:i+4000] if re.match(r"^\s*\d{1,4}\s*[.\-–)]\s*\S", x))
                        if nums < 200: continue
                        tipo = "provis" if "provis" in ctx else ("definit" if "definit" in ctx else "?")
                        v = re.search(r"(1|2|primeir|segund)[ªaºo]?\s*(vara|tribunal|secretaria)", ctx)
                        print(dc.edicao(f, 21), "linha", i, "vara", (v.group(1) if v else "?"), tipo, "numeradas", nums, flush=True)


def m_editais(a):
    res = []
    for f in dc.arquivos(a.padrao, a.txt or dc.TXT_LAYOUT):
        T = dc.ler_achatado(f)
        for m in re.finditer(r'(?i)foram\s+alistad\w*,?\s*(?:em\s+)?car[áa]ter\s+(DEFINITIVO|PROVIS[ÓO]RIO)', T):
            tipo = 'D' if m.group(1).upper().startswith('D') else 'P'
            ante = T[max(0, m.start()-700):m.start()]; pos = T[m.end():m.end()+80]
            ano = re.search(r'ano\s+de\s+(20\d\d)', pos) or re.search(r'(20\d\d)', pos)
            cs = re.findall(r'(?i)(?:j[úu]ri|criminal|[úu]nica|judicial)\s+(?:do\s+foro\s+\w+\s+)?(?:da\s+comarca\s+)?de\s+([A-ZÀ-Ú][\wÀ-ú\']+(?:\s+(?:do|da|de|dos|das|d\')?\s*[A-ZÀ-Ú][\wÀ-ú]+){0,3})', ante)
            com = cs[-1].strip() if cs else '?'
            com = re.sub(r'\s+(em|O|A|Ao|FAZ|Estado|Edital|Paraná)\b.*$', '', com)
            res.append((dc.edicao(f), tipo, ano.group(1) if ano else '?', com))
    if a.saida:
        json.dump(res, open(a.saida, 'w'))
    else:
        for r in res: print(*r, sep=" | ")
    print(len(res))


def m_cascavel(a):
    achados = []
    for f in dc.arquivos(a.padrao, a.txt or dc.TXT_LAYOUT):
        L = dc.ler_linhas(f)
        for i, l in enumerate(L):
            tipo = None
            if re.search(r"(?i)foram\s+alistad", l): tipo = "lista"
            elif re.search(r"(?i)convoca", l) and re.search(r"(?i)jurad", " ".join(L[i:i+3])): tipo = "convocacao?"
            if not tipo: continue
            w = "\n".join(L[max(0, i-25):i+3])
            # comarca: segmentos de coluna com "Juri de X" / "Juri da Comarca de X"
            coms = set(m.group(1).strip() for seg in re.split(r"\s{3,}|\n", w)
                       for m in [re.search(r"(?i)j[uú]ri\s+(?:da\s+comarca\s+)?de\s+([A-ZÀ-Ú][\wÀ-ú]+(?:\s+(?:do|da|de|dos|das)?\s*[A-ZÀ-Ú][\wÀ-ú]+)?)\s*[.,]?\s*$", seg.strip())] if m)
            if any("Cascavel" in c for c in coms) or (tipo == "lista" and re.search(r"(?i)cascavel", w) and not coms):
                car = re.search(r"(?i)car[aá]ter\s+(DEFINITIVO|PROVIS[OÓ]RIO)", " ".join(L[i:i+3]))
                ano = re.search(r"ano de (\d{4})", " ".join(L[i:i+3]))
                achados.append((os.path.basename(f)[:-4], i, tipo, sorted(coms), car.group(1) if car else "", ano.group(1) if ano else ""))
    for x in achados: print(*x, sep=" | ")
    print(len(achados), "ocorrencias candidatas")


def m_identificar(a):
    from coletar_listas import pseudonimo, chave_secreta
    k = chave_secreta(); S = defaultdict(set)
    for r in csv.DictReader(open(BASE)): S[(r['vara'][9:], r['ano'])].add(r['pessoa_id'])
    for f in dc.arquivos(a.padrao, a.txt or dc.TXT_LAYOUT):
        T = dc.ler_achatado(f)
        ids = []
        for e in re.finditer(NOME_ACHATADO + r"(?=\s[-–]\s|\s\d{1,4}\s*[.\-–)]|\s*$)", T):
            n = e.group(1).strip()
            if len(n.split()) >= 2: ids.append(pseudonimo(n, k))
        for i in range(0, len(ids), a.bloco):
            s = set(ids[i:i+a.bloco])
            for key, v in S.items():
                if len(s & v) / len(s) > a.limiar: print(dc.edicao(f), key, round(len(s & v) / len(s), 2)); break


ALVOS_PROFISSAO = [("2022-10-06","1a Vara","provisoria","2023"),("2022-11-09","1a Vara","definitiva","2023"),("2023-10-11","1a Vara","provisoria","2024"),
                   ("2023-11-20","1a Vara","definitiva","2024"),("2024-10-02","1a Vara","provisoria","2025"),("2024-11-07","1a Vara","definitiva","2025"),
                   ("2025-10-07","1a Vara","provisoria","2026"),("2025-11-06","1a Vara","definitiva","2026"),("2026-10-09","1a Vara","provisoria","2027")]


def m_profissao(a):
    from coletar_listas import pseudonimo, chave_secreta
    k = chave_secreta(); site = defaultdict(dict)
    for r in csv.DictReader(open(BASE)): site[(r['vara'][9:], r['tipo'], r['ano'])][r['pessoa_id']] = r['profissao'].strip()
    pasta = a.txt or dc.TXT_LAYOUT
    for d, v, t, ano in ALVOS_PROFISSAO:
        T = dc.ler_achatado(dc.arquivos(d + "_*", pasta)[0])
        alvo = site[(v, t, ano)]; n = comp = rec = 0; vistos = set()
        for e in re.finditer(NOME_ACHATADO + r"(\s[-–]\s[^\d]{2,60}?)?(?=\s\d{1,4}\s*[.\-–)]|\s*$)", T):
            pid = pseudonimo(e.group(1).strip(), k)
            if pid in alvo and pid not in vistos:
                vistos.add(pid); n += 1; comp += bool(e.group(2)); rec += bool(e.group(2)) and not alvo[pid]
        print(d, v, t, ano, 'casados', n, 'de', len(alvo), '| % com profissao no DJe', round(100*comp/max(1, n), 1), '| sem profissao no site e com texto no DJe:', rec)


def m_varrer(a):
    from coletar_listas import separar, chave_secreta, pseudonimo
    chave = chave_secreta(); ENT = dc.ENT
    alvo = defaultdict(set)
    for r in csv.DictReader(open(BASE, encoding="utf-8")):
        if r["ano"] == a.ano: alvo[(r["vara"][9:], r["tipo"])].add(r["pessoa_id"])
    for f in dc.arquivos(a.padrao, a.txt or dc.TXT_RAW):
        L = dc.ler_linhas(f)
        i = 0
        while i < len(L):
            m = ENT.match(L[i])
            if m and m.group(1) == "1":
                esp, j, perd, ids = 2, i + 1, 0, [pseudonimo(separar(m.group(2))[0], chave)]
                while j < len(L) and perd < 60:
                    mm = ENT.match(L[j])
                    if mm and int(mm.group(1)) in (esp, esp + 1):
                        ids.append(pseudonimo(separar(mm.group(2))[0], chave)); esp = int(mm.group(1)) + 1; perd = 0
                    else: perd += 1
                    j += 1
                if len(ids) >= 150:
                    s = set(ids)
                    best = max(((len(s & v) / len(v), k) for k, v in alvo.items()), default=(0, None))
                    print(dc.edicao(f, 16), "linha", i, "n", len(ids), "melhor", f"{best[0]:.2f}", best[1], flush=True)
                i = j if len(ids) >= 150 else i + 1
            else:
                i += 1


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="modo", required=True)
    def novo(nome, func, padrao, ajuda):
        s = sub.add_parser(nome, help=ajuda)
        s.add_argument("--padrao", default=padrao, help=f"edicoes (prefixo do arquivo, com *); padrao {padrao}")
        s.add_argument("--txt", default=None, help="pasta do texto do Diario (padrao ~/djetxt; varrer usa ~/djeraw)")
        s.set_defaults(func=func); return s
    s = sub.add_parser("converter", help="gera o texto das edicoes novas de dje/"); s.set_defaults(func=m_converter)
    s.add_argument("--sem-raw", action="store_true", help="so o texto -layout")
    novo("localizar", m_localizar, "*", "cabecalhos de listas das Varas de Curitiba").add_argument("--variante", type=int, choices=(1, 2), default=1)
    s = novo("editais", m_editais, "202*", "editais de lista de todas as comarcas"); s.add_argument("--saida", help="grava JSON")
    novo("cascavel", m_cascavel, "202*", "editais de Cascavel")
    s = novo("identificar", m_identificar, "202*", "listas de Curitiba por sobreposicao de nomes")
    s.add_argument("--limiar", type=float, default=0.5); s.add_argument("--bloco", type=int, default=300)
    novo("profissao", m_profissao, "202*", "profissao no DJe x site (1a Vara 2023-2027)")
    novo("varrer", m_varrer, "2012-*", "sequencias numeradas x listas do ano").add_argument("--ano", default="2013")
    a = p.parse_args()
    a.func(a)


if __name__ == "__main__":
    main()
