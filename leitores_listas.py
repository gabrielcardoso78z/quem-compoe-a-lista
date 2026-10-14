#!/usr/bin/env python3
"""Leitores alternativos de listas de jurados no Diario, para editais que nao numeram as entradas.
Usados por processar_comarcas_dje.py so quando as leituras por numeracao dao menos de 20 nomes.

- colunas_linhas: como segmentos(), mas mantem as linhas de cada coluna (precisa delas para tabelas e
  listas sem numero), e mapeia uma posicao do texto unido (T) para (coluna, linha).
- ler_sem_numero: uma entrada por linha, "NOME - Profissao" (Grandes Rios, 2026); linha curta sem " - "
  e sem cara de nome continua a anterior.
- ler_tabela: tabela "NOME | PROFISSAO | NOME | PROFISSAO" (Rolandia), com nomes que quebram em duas
  linhas; a entrada fecha na linha em que aparece a profissao daquela subcoluna.
"""
import re
from collections import Counter

SEP = "\x00"
INICIO = re.compile(r"(?i)penas\s+da\s+lei\.?|cidad[aã]os\s*:|relacionados\s*:|seguintes\s+cidad[aã]os[^:]{0,40}:")
FIM = re.compile(r"(?i)dado\s+e\s+passado|e,?\s+para\s+que\s+chegue|\bedital\s+n|ju[ií]z(?:a|\(a\))?\s+de\s+direito|"
                 r"poder\s+judici[aá]rio|di[aá]rio\s+eletr|^\s*-\s*\d+\s*-\s*$|cpf|cep\s*:|\bn[ºº]\s*\d")
CAPS = re.compile(r"[A-ZÀ-Ý'][A-ZÀ-Ý' .]*")


# linhas de cabecalho e rodape de pagina do Diario (linha inteira): "Curitiba, 13 de Novembro de 2023 - Edicao n 3552",
# "Diario Eletronico do Tribunal de Justica do Parana" e "- 71 -". Removidas antes de unir as linhas de cada coluna,
# para que nao grudem no nome ou na profissao (auditoria de 12/10/2026, falhas F1, F7)
LINHA_PAG = re.compile(r"(?i)^\s*(?:curitiba,\s*\d{1,2}\s+de\s+\w+\s+de\s+\d{4}\s*-\s*edi\S{1,3}o\s+n\S{0,2}\s*\d+"
                       r"|di\S{1,2}rio\s+eletr\S{1,2}nico\s+do\s+tribunal\s+de\s+justi\S{1,2}a\s+do\s+paran\S{1,2}"
                       r"|-\s*\d{1,4}\s*-)\s*$")


def limpar_pagina(L):
    return ["" if LINHA_PAG.match(l) else l for l in L]


def colunas_linhas(texto, linha0, max_pag=6, lo=60, hi=140):
    paginas = texto.split("\f"); acum = 0; p0 = 0
    for k, pg in enumerate(paginas):
        n = pg.count("\n")
        if acum + n >= linha0: p0 = k; break
        acum += n
    partes = []
    for k in range(p0, min(len(paginas), p0 + max_pag)):
        L = paginas[k].split("\n")
        pos = [m.end() for l in L for m in re.finditer(r"\s{3,}(?=\S)", l) if lo < m.end() < hi]
        c = Counter(pos).most_common(1)[0][0] if pos else 10**6
        # nao separar o numero de ordem do nome: se em varias linhas a parte esquerda termina em "79." (lista
        # numerada com espaco largo entre numero e nome), a divisao recua para o inicio do numero (ex.: ed. 4022)
        if c < 10**6:
            achados = [(m.start(1), int(m.group(2))) for l in L
                       for m in [re.search(r"(?<=\s)((\d{1,4})\s*[.)\u2013-])\s*$", l[:c])]
                       if m and c - m.start(1) <= 12 and re.match(r"\s*[A-Z\u00c0-\u00dd]", l[c:])]
            nums = sorted({n for _, n in achados})
            if len(nums) >= 5 and nums[-1] - nums[0] <= 3 * len(nums):     # sequencia de numeros de ordem
                c = Counter(p for p, _ in achados).most_common(1)[0][0]
        L = limpar_pagina(L)          # cabecalho e rodape do Diario viram linhas vazias (o corte de coluna ja foi calculado)
        for col in ([l[:c] for l in L], [l[c:] for l in L]):
            partes.append([x.rstrip() for x in col])
    return partes


def posicao(partes, i):
    """(coluna, linha) da posicao i no texto unido como em segmentos() (linhas nao vazias, strip, ' ', SEP)."""
    off = 0
    for ci, linhas in enumerate(partes):
        ne = [(li, l.strip()) for li, l in enumerate(linhas) if l.strip()]
        txt = " ".join(s for _, s in ne)
        if i < off + len(txt) + 1:
            o = off
            for li, s in ne:
                if i < o + len(s) + 1: return ci, li
                o += len(s) + 1
            return ci, ne[-1][0] if ne else 0
        off += len(txt) + 1
    return None


def inicio_lista(partes, ci, li):
    """Primeira linha depois do fim da formula do edital ("penas da lei.", "cidadaos:")."""
    for c in range(ci, min(len(partes), ci + 2)):
        L = partes[c]
        for l in range(li if c == ci else 0, min(len(L), (li if c == ci else 0) + 25)):
            if INICIO.search(L[l]): return c, l + 1
    return ci, li + 1


def _e_nome(s):
    return CAPS.fullmatch(s) is not None and len(s.split()) >= 2


def ler_sem_numero(partes, ci, li, max_entradas=5000):
    out = []
    c, l = inicio_lista(partes, ci, li)
    amostra = [x for x in partes[c][l:l + 30] if x.strip()]
    if amostra and sum(";" in x or x.count(",") >= 3 for x in amostra) >= 0.3 * len(amostra):
        return []          # paragrafo corrido (";" ou ","): fica para ler_paragrafo
    while c < len(partes):
        L = partes[c]
        while l < len(L):
            s = L[l].strip(); l += 1
            if not s or CABECALHO.search(s): continue
            if FIM.search(s): return out
            if " - " in s or _e_nome(s): out.append(s)
            elif out and len(s) <= 45: out[-1] += " " + s
            else: return out
            if len(out) >= max_entradas: return out
        c += 1; l = 0
    return out


def _colunas_tabela(linhas, cab=None):
    """Posicoes (n1, p1, n2, p2): inicio de NOME e PROFISSAO nas duas subcolunas, pelo cabecalho ou inferidas."""
    if cab:
        ns = [m.start() for m in re.finditer(r"NOME", cab)]; ps = [m.start() for m in re.finditer(r"PROFISS", cab)]
        if len(ns) >= 2 and len(ps) >= 2: return ns[0], ps[0], ns[1], ps[1]
        if ns and ps: return ns[0], ps[0], None, None
    ind = Counter(len(x) - len(x.lstrip()) for x in linhas if x.strip())
    n1 = ind.most_common(1)[0][0] if ind else 0
    c2 = Counter(m.start(1) for x in linhas for m in re.finditer(r"\s{2,}([A-Z\u00c0-\u00dd]{2,})", x) if m.start(1) > n1 + 20)
    if not c2: return n1, None, None, None
    n2 = c2.most_common(1)[0][0]
    c1 = Counter(m.start(1) for x in linhas for m in re.finditer(r"\s{2,}(\S)", x) if n1 + 5 < m.start(1) < n2 - 3)
    c3 = Counter(m.start(1) for x in linhas for m in re.finditer(r"\s{2,}(\S)", x) if m.start(1) > n2 + 5)
    return n1, (c1.most_common(1)[0][0] if c1 else None), n2, (c3.most_common(1)[0][0] if c3 else None)


def _corta(h, p):
    """Divide h em (nome, profissao) na posicao p, sem partir palavra."""
    if p is None or p >= len(h): return h.strip(), ""
    while 0 < p < len(h) and h[p - 1] != " " and h[p] != " ": p += 1
    return h[:p].strip(), h[p:].strip()


def ler_tabela(partes, ci, li):
    c, l = inicio_lista(partes, ci, li)
    cab = None
    for k in range(l, min(len(partes[c]), l + 6)):
        if re.search(r"NOME\s{2,}PROFISS", partes[c][k]): cab = partes[c][k]; l = k + 1; break
    if cab is None: return []
    out = []
    primeira = True
    while c < len(partes):
        L = partes[c][l:]
        linhas = [x for x in L if x.strip()]
        if not linhas: c += 1; l = 0; continue
        n1, p1, n2, p2 = _colunas_tabela(linhas, cab if primeira else None)
        if not primeira:   # continua so se a coluna ainda parece tabela (nomes em maiusculas no inicio da linha)
            caps = sum(1 for x in linhas if re.match(r"\s*[A-Z\u00c0-\u00dd]{2,}(\s|$)", x))
            if caps < 0.6 * len(linhas): return out
        primeira = False
        acum = [[], []]
        prosa = 0
        for x in L:
            if not x.strip(): continue
            if FIM.search(x): return out
            if not re.search(r"[A-Z\u00c0-\u00dd]{2,}", x) and len(x.strip()) > 50:
                prosa += 1
                if prosa >= 2: return out
                continue
            metades = [(x[:n2] if n2 else x, (p1 - n1) if p1 is not None else None)]
            if n2: metades.append((x[n2:], (p2 - n2) if p2 is not None else None))
            for k, (h, pr) in enumerate(metades):
                h2 = h[n1:] if k == 0 else h
                nome, prof = _corta(h2, pr)
                if nome: acum[k].append(nome)
                if prof:
                    if acum[k]:
                        out.append(" ".join(acum[k]) + " - " + prof); acum[k] = []
                    elif out:
                        out[-1] += " " + prof
        for k in (0, 1):
            if acum[k]: out.append(" ".join(acum[k]))
        c += 1; l = 0
    return out


def palavras_bbox(pdf, pag0, n=6):
    """Palavras com coordenadas (pdftotext -bbox) das paginas pag0..pag0+n-1 (1-based): lista de paginas,
    cada uma com (largura, [(x0, y0, x1, palavra)])."""
    import subprocess, html
    r = subprocess.run(["pdftotext", "-f", str(pag0), "-l", str(pag0 + n - 1), "-bbox", pdf, "-"],
                       capture_output=True, text=True)
    pags = []
    for m in re.finditer(r'<page width="([\d.]+)" height="([\d.]+)">(.*?)</page>', r.stdout, re.S):
        ws = [(float(a), float(b), float(c), html.unescape(w)) for a, b, c, w in
              re.findall(r'<word xMin="([\d.]+)" yMin="([\d.]+)" xMax="([\d.]+)" yMax="[\d.]+">([^<]*)</word>', m.group(3))]
        alt = float(m.group(2))
        ws = [w for w in ws if 50 < w[1] < alt - 30]      # sem cabecalho e numero de pagina
        pags.append((float(m.group(1)), ws))
    return pags


def _linhas(ws):
    L = {}
    for x0, y, x1, w in ws: L.setdefault(round(y), []).append((x0, w))
    return [sorted(L[y]) for y in sorted(L)]


CABECALHO = re.compile(r"(?i)curitiba,\s*\d+\s+de\s+\w+\s+de\s+20\d\d|edi\S+o\s+n\S*\s*\d+|di\S+rio\s+eletr\S+nico|^justi\S+a\s+do\s+paran\S+$|^tribunal\s+de\s+justi\S+a|^-\s*\d+\s*-$")
PARADA = []   # motivo da ultima parada (diagnostico)


def ler_tabela_bbox(pdf, pag, col, apos_texto=None):
    """Tabela NOME | PROFISSAO | NOME | PROFISSAO pelas coordenadas das palavras. pag 1-based, col 0/1 (coluna
    da pagina em que esta o edital). A entrada fecha na linha em que aparece a profissao da subcoluna
    (celulas alinhadas pela base: a profissao fica na ultima linha do nome)."""
    pags = palavras_bbox(pdf, pag)
    if not pags: return []
    out = []
    cols = None
    for k, (larg, ws) in enumerate(pags):
        meio = larg / 2
        for cc in ((col, 1 - col) if k == 0 else (0, 1)):
            if k == 0 and cc < col: continue
            reg = [w for w in ws if (w[0] < meio) == (cc == 0)]
            if not reg: continue
            linhas = _linhas(reg)
            ini = 0
            if cols is None:   # primeira regiao: acha o cabecalho
                for i, ln in enumerate(linhas):
                    ns = [x for x, w in ln if w == "NOME"]; ps = [x for x, w in ln if w.startswith("PROFISS")]
                    if len(ns) >= 2 and len(ps) >= 2:
                        cols = (ns[0], ps[0], ns[1], ps[1]); ini = i + 1; break
                if cols is None: continue
                dx = 0
            else:
                linhas = [ln for ln in linhas if not CABECALHO.search(" ".join(w for _, w in ln))]
                topo = linhas[:12]
                caps0 = [ln[0][0] for ln in topo if re.fullmatch(r"[A-Z\u00c0-\u00dd'.]{2,}", ln[0][1])]
                if len(caps0) < 0.6 * len(topo): PARADA.append(('nao_tabela', k, cc, len(caps0), len(topo))); return out
                dx = Counter(round(x) for x in caps0).most_common(1)[0][0] - cols[0]
                # cabecalho repetido no alto da regiao
                for i, ln in enumerate(linhas[:3]):
                    if any(w == "NOME" for _, w in ln) and any(w.startswith("PROFISS") for _, w in ln): ini = i + 1
            n1, p1, n2, p2 = (c + dx for c in cols)
            acum = [[], []]; prof = [[], []]
            for ln in linhas[ini:]:
                txt = " ".join(w for _, w in ln)
                if CABECALHO.search(txt): continue
                if FIM.search(txt): PARADA.append(('fim', k, cc, FIM.search(txt).group(0))); return out
                if (ln[0][0] < p1 - 2 and not re.fullmatch(r"[A-Z\u00c0-\u00dd'.]{2,}", ln[0][1])
                        and len(txt) > 40):
                    PARADA.append(('prosa', k, cc)); return out
                if ln[0][0] < n1 - 4: PARADA.append(('fora', k, cc, round(ln[0][0]), round(n1))); return out        # texto fora da tabela
                parte = [[[], []], [[], []]]           # subcoluna -> (nome, profissao)
                for x, w in ln:
                    if x < p1 - 2: parte[0][0].append(w)
                    elif x < n2 - 2: parte[0][1].append(w)
                    elif x < p2 - 2: parte[1][0].append(w)
                    else: parte[1][1].append(w)
                for sc in (0, 1):
                    nm, pf = parte[sc]
                    if nm: acum[sc] += nm
                    if pf:
                        if acum[sc]:
                            out.append(" ".join(acum[sc]) + " - " + " ".join(pf)); acum[sc] = []
                        elif out:
                            out[-1] += " " + " ".join(pf)
            for sc in (0, 1):
                if acum[sc]: out.append(" ".join(acum[sc]))
    return out


FIM_TXT = re.compile(r"(?i)dado\s+e\s+passado|\be,?\s+para\s+que\b|\bedital\s+n|ju[i\u00ed]z(?:a|\(a\))?\s+de\s+direito|"
                     r"poder\s+judici[a\u00e1]rio|\bcpf\b|\bcep\b|\bn[\u00baº]\s*\d|intima\u00e7\u00e3o|\bautos\b")
CAB_TXT = re.compile(r"(?i)-?\s*\d*\s*-?\s*curitiba,\s*\d+\s+de\s+\w+\s+de\s+20\d\d\s*-\s*edi\S+o\s+n\S*\s*\d+|"
                     r"di\S+rio\s+eletr\S+nico\s+do\s+tribunal\s+de\s+justi\S+a\s+do\s+paran\S+|-\s*\d+\s*-")


def ler_paragrafo(T, i0):
    """Lista em paragrafo corrido: "Nome - profissao; Nome - profissao; ..." (Ipiranga, 2026) ou
    "Nome, Nome, Nome, ..." (Marmeleiro). Le do fim da formula do edital ate o fecho."""
    m = INICIO.search(T, i0, i0 + 900)
    if not m: return []
    txt = T[m.end():m.end() + 60000].replace(SEP, " ")
    txt = CAB_TXT.sub(" ", txt)
    f = FIM_TXT.search(txt)
    if f: txt = txt[:f.start()]
    if len(re.findall(r"(?<![\d/,])\d{1,4}\s*[.)]\s*[A-Z\u00c0-\u00dd]", txt)) >= 20: return []   # lista numerada
    sep = ";" if txt.count(";") >= 10 else ("," if txt.count(",") >= 20 else None)
    if not sep: return []
    out = []
    for item in txt.split(sep):
        it = re.sub(r"\s+", " ", item).strip(" .")
        if not it: continue
        if len(it) > 90 or re.search(r"\d{3,}", it): break
        if len(it.split(" - ")[0].split()) >= 2: out.append(it)
    return out
