#!/usr/bin/env python3
"""Extrai dos textos do Diario (-layout, ~/djetxt) as listas gerais de jurados de outras comarcas
(alem de Curitiba e Cascavel), pseudonimiza com a chave da pesquisa e grava:
  data/comarcas_extra_* (ou comarcas_pr_* com --todas): editais.csv  censo por edital (comarca, data, tipo, ano, contagens; sem nomes)
  data/comarcas_extra_entradas.csv  entradas pseudonimizadas (pessoa_id, profissao, sexo; sem nomes)

Uso:
  python3 processar_comarcas_dje.py                     -> Laranjeiras do Sul e Cantagalo
  python3 processar_comarcas_dje.py "Nome da Comarca"...-> comarcas indicadas
  python3 processar_comarcas_dje.py --todas             -> censo estadual (todas as comarcas achadas)
  ... --padrao=2023*                                    -> so as edicoes que casam com o padrao (roda em blocos)
"""
import csv, os, re, sys, unicodedata
from collections import Counter
from coletar_listas import separar, pseudonimo, chave_secreta, DATA
import dje_comum as dc
import leitores_listas as LL
DJE_PDF = os.path.join(os.path.dirname(os.path.abspath(__file__)), "dje")

ALVO_PADRAO = ["Laranjeiras do Sul", "Cantagalo"]
CAB = re.compile(r"(?i)j[uú]ri\s+(?:da\s+comarca\s+)?(?:do\s+foro\s+\w+\s+)?de\s+"
                 r"([A-ZÀ-Ú][\wÀ-ú']+(?:\s+(?:do|da|de|dos|das|d')?\s*[A-ZÀ-Ú][\wÀ-ú]+){0,3})")
FIM = re.compile(r"(?i)para que (n[aã]o )?se possa alegar|art\.\s*43[67]|EDITAL|forma da lei")

def reparar(t):
    """Acento corrompido na propria publicacao (UTF-8 lido como Latin-1: "MÃ¡rcio" por "Márcio"; F10). So mexe
    no par "Ã/Â + caractere de 0x80 a 0xBF", que nao ocorre em grafia correta ("JOÃO" fica como esta).
    Repete ate estabilizar (no maximo 3 vezes), para a codificacao dupla ("ConceiÃÂ§Ã£o": a 1a passada deixa "Ã§",
    a 2a chega a "ç"); a nova passada so acha par se a anterior o formou. "Ã-" entre minusculas e o "í" cujo
    segundo byte (0xAD, hifen suave) a extracao de texto converteu em "-" ("LucÃ-lia") ou perdeu ("LucÃlia"):
    nas edicoes de lista de 2022 a 2026, das 76 ocorrencias de "Ã" entre minusculas, 75 viram palavra existente no
    proprio corpus com "í" (conferencia de 12/10/2026). Em caixa alta "Ã-" pode ser grafia correta ("IRMÃ-"), entao
    so e trocado por "Í" quando a mesma entrada tem outro par corrompido."""
    def um(m):
        try: return m.group(0).encode("latin-1").decode("utf-8")
        except UnicodeError: return m.group(0)
    corrompido = bool(re.search(r"[\u00c2\u00c3][\u0080-\u00bf]", t))
    for _ in range(3):
        novo = re.sub(r"(?<=[a-z\u00e0-\u00ff])\u00c3-?(?=[a-z\u00e0-\u00ff])", "\u00ed", re.sub(r"[\u00c2\u00c3][\u0080-\u00bf]", um, t))
        if corrompido:   # em caixa alta "Ã-" so vira "Í" se a mesma entrada tem outro par corrompido ("NOMÃ-XX - ...Ã¡...", exemplo ficticio)
            novo = re.sub(r"(?<=[A-Z])\u00c3-(?=[A-Z])", "\u00cd", novo)
        if novo == t: break
        t = novo
    return t

def nrm(t):
    return re.sub(r"\s+", " ", unicodedata.normalize("NFKD", t).encode("ascii", "ignore").decode().upper()).strip()


_MUN = None
def municipios():
    """Nomes oficiais dos 399 municipios do PR (TSE 2024), normalizados; as comarcas e foros tem nome de municipio."""
    global _MUN
    if _MUN is None:
        import zipfile, io
        z = zipfile.ZipFile(os.path.join(os.path.dirname(os.path.abspath(__file__)), "referencias/dados_tse/perfil_eleitorado_2024.zip"))
        with z.open("perfil_eleitorado_2024_PR.csv") as f:
            _MUN = {nrm(r["NM_MUNICIPIO"]): r["NM_MUNICIPIO"].strip().title()
                    for r in csv.DictReader(io.TextIOWrapper(f, encoding="latin-1"), delimiter=";")}
    return _MUN

def oficial(nome):
    """Maior prefixo do nome capturado que e um municipio do PR ('Dois Vizinhos E...' -> 'Dois Vizinhos')."""
    pal = nrm(nome).split()
    for k in range(min(len(pal), 5), 0, -1):
        cand = " ".join(pal[:k])
        if cand in municipios(): return municipios()[cand]
    return None

REF_COM = re.compile(r"(?i)(?:j[u\u00fa]ri|comarca|foro(?:\s+regional)?)\s+(?:da\s+comarca\s+)?(?:de|do|da)\s*(?=[A-ZÀ-Ú])"
                     r"([A-Z\u00c0-\u00da][\w\u00c0-\u00fa']+(?:\s+(?:do|da|de|dos|das|d')?\s*[A-Z\u00c0-\u00da][\w\u00c0-\u00fa']+){0,4})")

SECAO = re.compile(r"([A-Z\u00c0-\u00da][A-Z\u00c0-\u00da' ]{2,40}?)\s+(?:JU\S{1,2}ZO\s+\S{1,2}NICO|\d+\S{0,2}\s+VARA|VARA\s+(?:CRIMINAL|\S{1,2}NICA|DO\s+J\S{1,2}RI)|SECRETARIA)\b")

def comarca_no_trecho(trecho, ultima=True):
    ms = [oficial(m.group(1)) for m in REF_COM.finditer(trecho)]
    ms = [x for x in ms if x and nrm(x) != "PARANA"]
    if not ms: return None
    return ms[-1] if ultima else ms[0]

def comarca_do_edital(T, i0):
    """Comarca pelo corpo do edital: primeiro na mesma coluna, antes de 'foram alistados';
    se nao houver, na coluna anterior. Devolve (nome, origem)."""
    ini = T.rfind(SEP, 0, i0) + 1
    c = comarca_no_trecho(T[max(ini, i0 - 1500):i0])
    if c: return c, "mesma_coluna"
    # cabecalho de secao do Diario na mesma coluna, logo antes do edital: "<MUNICIPIO> JUIZO UNICO|VARA ...|SECRETARIA ...
    # Edital" (auditoria 12/10/2026, F5: a lista de Arapoti foi atribuida a Arapongas, da coluna vizinha)
    secoes = [oficial(m.group(1)) for m in SECAO.finditer(T, max(ini, i0 - 1500), i0)]
    secoes = [x for x in secoes if x]
    if secoes: return secoes[-1], "mesma_coluna_secao"
    ant = T.rfind(SEP, 0, max(0, ini - 1)) + 1
    c = comarca_no_trecho(T[ant:ini])
    return (c, "coluna_anterior") if c else ("?", "nenhuma")

def comarca_do_fecho(T, fim):
    trecho = " ".join(T[fim:fim + 2500].split(SEP)[:2])
    trecho = re.sub(r"(?i)curitiba,\s*\d{1,2}\s+de\s+\w+\s+de\s+20\d\d\s*-\s*edi\w+", " ", trecho)  # cabecalho do Diario
    return comarca_no_trecho(trecho, ultima=False)


CAB_ED = ["comarca", "data_dje", "edicao", "tipo", "ano", "numeradas", "ultimo_numero", "validas", "com_profissao",
          "pct_profissao", "pct_mulheres_prenome", "comarca_cabecalho", "comarca_fecho", "confianca", "lacunas_publicacao"]
CAB_EN = ["comarca", "ano", "tipo", "data_dje", "edicao", "seq", "pessoa_id", "profissao", "sexo_prenome"]
SEP = "\x00"
# redacoes de edital de lista: "foram alistados" (a mais comum), "foi procedido o alistamento dos jurados para comporem
# a lista geral" (Rolandia, Rio Negro) e "torna publica a lista" (2026)
GATILHO = r"(?i)foram\s+alistad|procedido\s+o\s+alistamento\s+dos\s+jurados|torna\s+p[u\u00fa]blica\s+a\s+(?:lista|rela)"
MARC = re.compile(r"(?<![\d/,])(\d{1,4})\s*[.\u2013)]\s*(?=[A-Z\u00c0-\u00da])")

def segmentos(texto, linha0, max_pag=40, lo=60, hi=140):
    """Texto a partir da pagina de linha0, em ordem de leitura (coluna esq., depois dir., pagina a pagina),
    com as linhas de cada coluna unidas por espaco e as colunas/paginas separadas por SEP.
    Assim uma entrada que quebra de linha (lista em paragrafo corrido) e lida inteira, e o texto de
    uma coluna nunca se mistura ao da coluna vizinha."""
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
        L = LL.limpar_pagina(L)       # cabecalho e rodape do Diario fora do texto (auditoria 12/10/2026, F1 e F7)
        for col in ([l[:c] for l in L], [l[c:] for l in L]):
            partes.append(" ".join(x.strip() for x in col if x.strip()))
    return SEP.join(partes)

# fim de entrada: formulas de fecho do edital e a transcricao dos arts. 436 a 446 que vem depois da lista
# (auditoria 12/10/2026, F3: "soldador 'Art. 436. O servico do juri...", "... edital n 2024 - provisoria")
CORTE = re.compile(r"(?i)\s(?:e,?\s*para que|dado e passado|na forma do artigo|['\"\u201c\u2018]?\s*art\.?\s*\d|edital\b)"
                   r"|['\"\u201c\u2018]\s*art\.?\s*43\d")   # aspas coladas na palavra anterior ("empresario'Art. 436")

def texto_entrada(T, ini, fim, ultimo=False):
    """Texto de uma entrada, do fim do seu marcador ao inicio do seguinte. Fica na coluna do marcador; se ali nao ha
    nome (o numero de ordem fechou a coluna e o nome comeca na coluna seguinte: auditoria 12/10/2026, F1/F6),
    usa o trecho da coluna seguinte ate o proximo marcador. Na ultima entrada da lista nao ha esse recurso."""
    partes = T[ini:fim].split(SEP)
    txt = partes[0]
    if not ultimo and len(partes) > 1 and len(re.findall(r"[^\W\d_]{2,}", txt)) < 2:
        txt = (txt + " " + partes[1]).strip()     # nome que comeca no pe de uma coluna e termina na seguinte
    txt = CORTE.split(txt)[0]
    return txt.strip(" .;,")

def lacuna_por_digito(n, m):
    """m e n com um digito a menos (numero de ordem impresso errado, ex.: '11.' no lugar de '111.'; F8)."""
    a, b = str(n), str(m)
    return len(b) == len(a) - 1 and any(a[:i] + a[i + 1:] == b for i in range(len(a)))

def preencher_lacunas(T, marcas):
    """Numeros que faltam entre dois marcadores da cadeia: procura, so dentro do trecho entre eles, o numero esperado
    com marcador frouxo (seguido de minuscula, "?", "]", fim de coluna...). Cobre nomes em minusculas ou com acento
    corrompido (F2), caractere solto antes do nome (F4), numero no fim da linha ou da coluna (F1/F6) e numero impresso
    com um digito a menos quando so falta um (F8). Listas sem lacuna nao mudam."""
    out = [marcas[0]]
    for (a_ini, a_fim, a_num), b in zip(marcas, marcas[1:]):
        b_ini, b_fim, b_num = b
        pos = a_fim
        for n in range(a_num + 1, b_num):
            m = re.compile(r"(?<![\d/,.])%d\s*[.\u2013)]\s*(?=[^\d\s.,;:)\-])" % n).search(T, pos, b_ini)
            if m is None and b_num - a_num == 2:
                for m2 in re.finditer(r"(?:^|(?<=[;\x00 ]))(\d{1,4})\s*[.)]\s*(?=[A-Z\u00c0-\u00da])", T[pos:b_ini]):
                    if lacuna_por_digito(n, int(m2.group(1))):
                        m = re.compile(re.escape(m2.group(0))).search(T, pos + m2.start(), b_ini); break
            if m is None: continue
            out.append((m.start(), m.end(), n)); pos = m.end()
        out.append(b)
    return out

def extrair_lista(T, i0, limite=None, relax=False, corta_no_limite=False):
    """Melhor cadeia de marcadores 1, 2, 3... a partir de i0 (buracos de ate 3 numeros;
    ate 6.000 caracteres entre marcadores). Cada entrada vai do seu marcador ao seguinte da cadeia,
    sem atravessar troca de coluna ou de pagina.
    relax=True (so quando a leitura normal da menos de 20 nomes): aceita cadeia que comeca em numero ate 60
    logo depois do edital (ate 1.500 caracteres) e saltos de ate 60 numeros entre linhas vizinhas (ate 250
    caracteres), para editais publicados com trechos da numeracao ausentes do texto (ex.: Maringa, ed. 3816)."""
    marc = [(m.start(), m.end(), int(m.group(1))) for m in MARC.finditer(T, i0)]
    abertos = []
    for k, (ini, fim, num) in enumerate(marc):
        colocado = False
        for ch in abertos:
            _, ufim, unum = marc[ch[-1]]
            salto = 60 if relax and ini - ufim < 250 else 3
            if unum < num <= unum + salto and ini - ufim < 6000:
                ch.append(k); colocado = True; break
        if not colocado and (num == 1 or (num <= 3 and ini - i0 < 600) or (relax and not abertos and ini - i0 < 1500)):
            abertos.append([k])
        if len(abertos) > 8:
            abertos = sorted(abertos, key=len, reverse=True)[:8]
    if limite is not None:   # a lista de um edital comeca antes do edital seguinte
        abertos = [ch for ch in abertos if marc[ch[0]][0] < limite]
    if not abertos: return [], i0
    perto = [ch for ch in abertos if marc[ch[0]][0] - i0 < 4000 and len(ch) >= 10]
    melhor = min(perto, key=lambda ch: marc[ch[0]][0]) if perto else max(abertos, key=lambda ch: (len(ch), -ch[0]))
    if corta_no_limite and limite is not None:     # convocacoes: a cadeia termina antes do gatilho seguinte
        melhor = [k for k in melhor if marc[k][0] < limite]
        if not melhor: return [], i0
    marcas = preencher_lacunas(T, [marc[k] for k in melhor])
    out = []
    for a, (_, ini, num) in enumerate(marcas):
        ultimo = a + 1 == len(marcas)
        fim = min(len(T), ini + 160) if ultimo else marcas[a + 1][0]
        out.append((num, texto_entrada(T, ini, fim, ultimo)))
    return out, marc[melhor[-1]][1]


def extrair_lista_uns(T, i0, limite=None):
    """Lista em que todas as entradas vem numeradas "1." (numeracao automatica perdida na diagramacao; ex.: Cambe,
    2025 e 2026): a sequencia de marcadores "1." que comeca logo depois do edital, renumerada 1, 2, 3..."""
    marc = [(m.start(), m.end(), int(m.group(1))) for m in MARC.finditer(T, i0)]
    if limite is not None: marc = [x for x in marc if x[0] < limite]
    run = []
    for x in marc:
        if not run:
            if x[2] == 1 and x[0] - i0 < 1500: run = [x]
            continue
        if x[2] != 1 or x[0] - run[-1][1] >= 6000: break
        run.append(x)
    out = []
    for a, (ini, fim, _) in enumerate(run):
        nxt = run[a + 1][0] if a + 1 < len(run) else min(len(T), fim + 160)
        out.append((a + 1, texto_entrada(T, fim, nxt, a + 1 == len(run))))
    return out, (run[-1][1] if run else i0)


def main():
    args = sys.argv[1:]
    todas = "--todas" in args or "--juntar" in args
    bruto = "--bruto" in args          # extrai e grava sem as passadas globais (para rodar ano a ano)
    juntar = "--juntar" in args        # junta os brutos e faz as passadas globais (conflitos, identidade, duplicatas)
    padrao = next((a.split("=",1)[1] for a in args if a.startswith("--padrao=")), "202*")
    alvos = [a for a in args if not a.startswith("--")] or ALVO_PADRAO
    alvos_n = {nrm(a) for a in alvos}
    chave = chave_secreta()
    pref = ("pr" if todas else "extra") + ("" if padrao == "202*" else "_" + padrao.strip("*").replace("-", ""))
    editais, entradas, vistos = [], [], set()
    for f in ([] if juntar else dc.arquivos(padrao, dc.TXT_LAYOUT)):
        texto = open(f, encoding="utf-8", errors="ignore").read()
        linhas = texto.split("\n")
        # paginas que contem editais de lista; cada pagina e lida uma vez, e todos os editais dela sao extraidos
        inicio_pag, acum = [], 0
        for pg in texto.split("\f"):
            inicio_pag.append(acum); acum += pg.count("\n")
        # paginas candidatas: pre-filtro barato no texto bruto; o gatilho e confirmado no texto por colunas,
        # porque a frase pode quebrar de linha com a coluna vizinha intercalada
        paginas_com = [k for k, pg in enumerate(texto.split("\f"))
                       if re.search(r"(?i)foram\s+alistad|procedido\s+o|torna\s+p[u\u00fa]blica", pg)
                       and re.search(GATILHO, segmentos(texto, inicio_pag[k] + 1, max_pag=1))]
        for p in paginas_com:
            T = segmentos(texto, inicio_pag[p] + 1)
            Tp = T   # texto da pagina; cada edital recomeca dele (a leitura alternativa de um edital nao contamina o seguinte)
            fim_pag = [k for k, ch in enumerate(T) if ch == SEP]
            fim_pag = fim_pag[1] if len(fim_pag) > 1 else len(T)
            for j in re.finditer(GATILHO, Tp[:fim_pag]):
              T = Tp
              i0 = j.start()
              com, origem = comarca_do_edital(T, i0)
              ctx = T[i0:i0 + 600].replace(SEP, " ")
              # remove o cabecalho/rodape de pagina do DJE, que pode cair no meio da frase ("para o ano - 306 - Curitiba, 15 de Outubro de 2025 - ... de 2026")
              ctx = re.sub(r"(?is)(-\s*\d*\s*-?\s*)?Curitiba,\s*\d+\s+de\s+\w+\s+de\s+20\d\d\s*-\s*Edi..o\s+n\S*\s*\d+(\s*Di.rio\s+Eletr.nico\s+do\s+Tribun\w*(\s+de\s+Justi.a\s+do\s+Paran.)?)?", " ", ctx)
              if re.match(r"(?i)torna", T[i0:i0 + 6]) and not re.search(r"(?i)jurad|j[u\u00fa]ri", T[max(0, i0 - 600):i0 + 600]):
                  continue     # "torna publica a relacao" de outra materia (ex.: Paranavai 3814, Antonina 3865)
              car = re.search(r"(?i)(?:(?:car\S{1,3}ter|lista\s+geral)\s+|alistad[oa]s?,?\s+)(DEFINITIV|PROVIS[O\u00d3]RI)", ctx[:400])
              tipo = ("definitiva" if car.group(1).upper().startswith("D") else "provisoria") if car else "?"
              ano = re.search(r"(?i)ano\s+de\s*(20\d\d)", ctx[:400]) or re.search(r"(?i)ano\s+de\s*(20\d\d)", ctx) or re.search(r"(20\d\d)", ctx[:400])
              prox = re.search(GATILHO, T[i0 + 20:])
              limite = i0 + 20 + prox.start() if prox else None
              T0 = T
              de_tabela = False
              lista, fim_lista = extrair_lista(T, i0, limite)
              # tabela NOME | PROFISSAO logo depois da formula: le a tabela, mesmo que haja uma cadeia numerada
              # mais adiante (que seria a lista de outra comarca; ex.: Rolandia x Sarandi, ed. 3786)
              P = LL.colunas_linhas(texto, inicio_pag[p] + 1)
              pos = LL.posicao(P, i0)
              pdf = os.path.join(DJE_PDF, os.path.basename(f)[:-4] + ".pdf")
              if pos and os.path.exists(pdf) and re.search(r"NOME\s{2,}PROFISS", "\n".join(P[pos[0]][pos[1]:pos[1] + 40])):
                  lt = LL.ler_tabela_bbox(pdf, p + 1 + pos[0] // 2, pos[0] % 2)
                  if len(lt) >= 20:
                      lista, fim_lista, de_tabela = [(n + 1, t) for n, t in enumerate(lt)], i0 + 400, True
                      print(f"  (lista sem numeracao, tabela NOME/PROFISSAO: {len(lt)} entradas)", flush=True)
              if len(lista) < 20:
                  T2 = segmentos(texto, inicio_pag[p] + 1, lo=40, hi=220)
                  j2 = list(re.finditer(GATILHO, T2))
                  k = [m.start() for m in re.finditer(GATILHO, Tp[:fim_pag])].index(i0)
                  if k < len(j2):
                      p2 = re.search(GATILHO, T2[j2[k].start() + 20:])
                      l2, f2 = extrair_lista(T2, j2[k].start(), j2[k].start() + 20 + p2.start() if p2 else None)
                      if len(l2) > len(lista): lista, fim_lista, T = l2, f2, T2
              if 20 <= len(lista) and not de_tabela:
                  # cadeia interrompida por um salto de numeracao (ex.: Londrina 4232, de 1339 para 1379): a leitura
                  # tolerante, se comeca no mesmo numero e rende 20% mais, continua a mesma lista
                  l3, f3 = extrair_lista(T0, i0, limite, relax=True)
                  if l3 and l3[0][0] == lista[0][0] and len(l3) > 1.2 * len(lista):
                      print(f"  (lista continuada apos salto: {len(lista)} -> {len(l3)} numeradas, ate {l3[-1][0]})", flush=True)
                      lista, fim_lista, T = l3, f3, T0
              # cadeia numerada que comeca longe do edital (mais de 1.500 caracteres) e lista sem numero logo depois
              # da formula: a cadeia e de outra comarca (ex.: Campina Grande do Sul 4022, Carlopolis 4021)
              if lista and not de_tabela and pos and not re.search(r"(?<![\d/,])0*%d\s*[.\u2013)]" % lista[0][0], T0[i0:i0 + 1500]):
                  l5 = LL.ler_sem_numero(P, pos[0], pos[1])
                  if len(l5) >= 20:
                      lista, fim_lista, T, de_tabela = [(n + 1, t) for n, t in enumerate(l5)], i0 + 400, T0, True
                      print(f"  (lista sem numeracao logo apos o edital, cadeia numerada distante descartada: {len(l5)} entradas)", flush=True)
              if lista and not de_tabela:
                  l6 = LL.ler_paragrafo(T0, i0)
                  if len(l6) >= max(50, 2 * len(lista)):
                      lista, fim_lista, T, de_tabela = [(n + 1, t) for n, t in enumerate(l6)], i0 + 400, T0, True
                      print(f"  (lista em paragrafo corrido, no lugar de cadeia curta: {len(l6)} entradas)", flush=True)
              if len(lista) < 20:
                  l3, f3 = extrair_lista(T0, i0, limite, relax=True)
                  if len(l3) >= 20 and len(l3) > len(lista) and (l3[0][0] <= 60 or len(l3) >= 50):
                      lista, fim_lista, T = l3, f3, T0
                      print(f"  (leitura tolerante: comeca em {l3[0][0]}, {len(l3)} numeradas ate {l3[-1][0]})", flush=True)
              if len(lista) < 20:
                  l4, f4 = extrair_lista_uns(T0, i0, limite)
                  if len(l4) >= 20:
                      lista, fim_lista, T = l4, f4, T0
                      print(f"  (entradas todas numeradas 1: {len(l4)} lidas em sequencia)", flush=True)
              if len(lista) < 20:
                  # lista sem numeracao, uma entrada por linha ("NOME - Profissao")
                  if pos:
                      l5 = LL.ler_sem_numero(P, pos[0], pos[1])
                      if len(l5) >= 20:
                          lista, fim_lista, T = [(n + 1, t) for n, t in enumerate(l5)], i0 + 400, T0
                          print(f"  (lista sem numeracao, uma entrada por linha: {len(l5)} entradas)", flush=True)
              if len(lista) < 20:
                  # lista em paragrafo corrido, separada por ";" ou ","
                  l6 = LL.ler_paragrafo(T0, i0)
                  if len(l6) >= 20:
                      lista, fim_lista, T = [(n + 1, t) for n, t in enumerate(l6)], i0 + 400, T0
                      print(f"  (lista em paragrafo corrido: {len(l6)} entradas)", flush=True)
              # numeros que faltam na cadeia e nao aparecem em lugar nenhum do trecho da lista, nem com padrao frouxo:
              # lacuna da propria publicacao (ex.: Maringa, ed. 3816, sem os numeros 1 a 29 e 350 a 389), nao da leitura
              lacunas = 0
              if lista:
                  lidos = {n for n, _ in lista}
                  presentes = {int(m.group(1)) for m in re.finditer(r"(?<![\d/,])(\d{1,4})\s*[.\u2013)-]", T[i0:fim_lista + 200])}
                  lacunas = sum(1 for n in range(1, lista[-1][0] + 1) if n not in lidos and n not in presentes)
                  # lacuna da publicacao so ate 10% da numeracao; acima disso e falha de leitura (ex.: Araucaria 4019)
                  if lacunas > 0.10 * lista[-1][0]: lacunas = 0
              com_cab = com
              com_fecho = comarca_do_fecho(T, fim_lista) or ""
              if com == "?" and com_fecho: com = com_fecho
              conf = ("concorda" if com_fecho and nrm(com_fecho) == nrm(com_cab) else
                      "diverge" if com_fecho and com_cab != "?" else origem)
              if nrm(com) in ("CURITIBA", "CASCAVEL"): continue
              if not todas and nrm(com) not in alvos_n: continue
              assinatura = (os.path.basename(f), nrm(com), tipo, tuple(t for _, t in lista[:5]), len(lista))
              if assinatura in vistos: continue          # mesmo edital achado duas vezes na pagina
              vistos.add(assinatura)
              ok, sexos, profs, embutidas = 0, Counter(), 0, 0
              data_dje, ed = dc.edicao(f), os.path.basename(f)[:-4].split("_ed")[-1]
              for seq, t in lista:
                  nome, prof = separar(reparar(t))
                  if re.fullmatch(r"[\d\s.\-\u2013]*", prof): prof = ""     # numero de pagina lido como profissao (F7)
                  # numeracao repetida ou fora de ordem no DJe ("12.FULANO - x 12.BELTRANO - y"): a 2a entrada fica dentro
                  # da profissao da 1a; corta ali, para nao guardar nome no campo profissao (a 2a pessoa nao e contada)
                  emb = re.search(r"(?<![\d/])\d{1,4}\s*[.\u2013)]\s*[A-Za-z\u00c0-\u00ff]{3,}\s+[A-Za-z\u00c0-\u00ff]{2,}", prof)
                  if emb:
                      prof = prof[:emb.start()].strip(" -\u2013,;.")
                      embutidas += 1
                  if len(nome.split()) < 2: continue
                  ok += 1
                  if prof.strip(): profs += 1
                  sx = dc.sexo(nome); sexos[sx] += 1
                  entradas.append([com, ano.group(1) if ano else "?", tipo, data_dje, ed, seq,
                                   pseudonimo(nome, chave), prof.strip().lower(), sx])
              cl = sexos["F"] + sexos["M"]
              editais.append([com, data_dje, ed, tipo, ano.group(1) if ano else "?",
                              len(lista), lista[-1][0] if lista else 0, ok, profs,
                              round(100 * profs / ok, 1) if ok else "",
                              round(100 * sexos["F"] / cl, 1) if cl else "", com_cab, com_fecho, conf, lacunas])
              print(f"{com} | {data_dje} ed{ed} | {tipo} {ano.group(1) if ano else '?'} | "
                    f"{len(lista)} numeradas, {ok} validas, {profs} com profissao"
                    + (f", {embutidas} entrada(s) embutida(s) cortada(s) da profissao" if embutidas else ""), flush=True)
    if bruto:
        tag = padrao.strip("*").replace("-", "") or "tudo"
        for nome, linhas_, cab in (("editais", editais, CAB_ED), ("entradas", entradas, CAB_EN)):
            with open(os.path.join(DATA, f"comarcas_bruto_{tag}_{nome}.csv"), "w", newline="", encoding="utf-8") as fo:
                w = csv.writer(fo); w.writerow(cab); w.writerows(linhas_)
        print(f"bruto {tag}: {len(editais)} editais, {len(entradas)} entradas")
        return
    if juntar:
        import glob as _g
        editais, entradas = [], []
        for arq in sorted(_g.glob(os.path.join(DATA, "comarcas_bruto_*_editais.csv"))):
            editais += [list(r) for r in list(csv.reader(open(arq, encoding="utf-8")))[1:]]
        for arq in sorted(_g.glob(os.path.join(DATA, "comarcas_bruto_*_entradas.csv"))):
            entradas += [list(r) for r in list(csv.reader(open(arq, encoding="utf-8")))[1:]]
        # a mesma edicao pode estar em dois brutos (padroes sobrepostos): fica uma copia
        vist_e = set(); editais = [e for e in editais if not (tuple(e) in vist_e or vist_e.add(tuple(e)))]
        print(f"juntando: {len(editais)} editais, {len(entradas)} entradas")
    # conflitos: a mesma lista (>80% das pessoas) atribuida a duas comarcas na mesma edicao.
    # Vence a comarca cujas listas de outros anos contem as mesmas pessoas; a outra fica como lista nao extraida.
    from collections import defaultdict
    L = defaultdict(set)
    for r in entradas: L[(r[0], r[4])].add(r[6])
    perdedores = set()
    por_ed = defaultdict(list)
    for (c, ed) in L: por_ed[ed].append(c)
    for ed, cs in por_ed.items():
        for x in range(len(cs)):
            for y in range(x + 1, len(cs)):
                a, b = L[(cs[x], ed)], L[(cs[y], ed)]
                if cs[x] == cs[y] or min(len(a), len(b)) <= 30 or len(a & b) / min(len(a), len(b)) <= 0.8: continue
                u = a | b
                def ident(c): return max([len(L[k] & u) / len(u) for k in L if k[0] == c and k[1] != ed] or [0])
                perde = cs[x] if ident(cs[x]) < ident(cs[y]) else cs[y]
                perdedores.add((perde, ed))
                print(f"conflito ed{ed}: {cs[x]} x {cs[y]} -> lista atribuida a {cs[y] if perde == cs[x] else cs[x]}")
    entradas = [r for r in entradas if (r[0], r[4]) not in perdedores]
    for e in editais:
        if (e[0], e[2]) in perdedores:
            e[5:10] = [0, 0, 0, 0, ""]; e[13] = "lista_nao_extraida_conflito"
    # identidade ao longo do tempo (passada geral): uma lista pertence a comarca cujas OUTRAS listas contem as mesmas pessoas.
    # Reatribui (a) listas sem comarca ("?") com 50%+ das pessoas nas listas de uma unica comarca e (b) listas cuja
    # sobreposicao com outra comarca supera em 30 pontos a sobreposicao com as listas da propria comarca.
    if todas:
        L = defaultdict(set)
        for r in entradas: L[(r[0], r[4])].add(r[6])
        conf_ed = {(e[0], e[2]): e[13] for e in editais}
        FORTE = ("mesma_coluna", "concorda", "so_fecho")
        por_c = defaultdict(set)                       # ancoras: so listas de atribuicao forte
        for (c, ed), s_ in L.items():
            if c != "?" and conf_ed.get((c, ed)) in FORTE: por_c[c].add(ed)
        mudar = {}
        for (c, ed), s_ in L.items():
            if len(s_) < 20 or conf_ed.get((c, ed)) in FORTE: continue   # listas fortes nao sao movidas
            def sob(cc): 
                u = set().union(*[L[(cc, e2)] for e2 in por_c[cc] if not (cc == c and e2 == ed)] or [set()])
                return len(s_ & u) / len(s_)
            propria = sob(c) if c != "?" and por_c.get(c) else 0.0
            cands = sorted(((sob(cc), cc) for cc in por_c if cc not in (c, "?")), reverse=True)[:1]
            if cands and cands[0][0] >= 0.5 and cands[0][0] > propria + 0.3:
                mudar[(c, ed)] = cands[0][1]
                print(f"identidade: ed{ed} {c} -> {cands[0][1]} ({100*cands[0][0]:.0f}% das pessoas; propria {100*propria:.0f}%)")
        for r in entradas:
            if (r[0], r[4]) in mudar: r[0] = mudar[(r[0], r[4])]
        for e in editais:
            if (e[0], e[2]) in mudar:
                e[0] = mudar[(e[0], e[2])]; e[13] = "reatribuida_por_identidade"
    # carater nao declarado ("?"): se a comarca ja veiculou antes, no mesmo ano de lista, um edital provisorio,
    # e ainda nao ha definitivo para esse ano, este e o definitivo (formula de Cambe: "foram alistados, provisoriamente" no 1o e "foram alistados" no 2o)
    prov = {}
    for e in editais:
        if e[3] == "provisoria" and ((e[0], e[4]) not in prov or e[1] < prov[(e[0], e[4])]): prov[(e[0], e[4])] = e[1]
    defin = {(e[0], e[4]) for e in editais if e[3] == "definitiva"}
    inferidos = set()
    for e in editais:
        if (e[3] == "?" and e[0] != "?" and (e[0], e[4]) in prov and prov[(e[0], e[4])] < e[1]
                and (e[0], e[4]) not in defin):
            e[3] = "definitiva"; inferidos.add((e[0], e[2], e[4]))
    # dois editais "?" da mesma comarca e ano de lista, em datas diferentes, sem outro edital: o 1o e a provisoria,
    # o 2o a definitiva (art. 426: publicacao provisoria e depois definitiva; formula de Cambe sem o carater)
    grupos = defaultdict(list)
    for e in editais:
        if e[0] != "?": grupos[(e[0], e[4])].append(e)
    for (c, a), es in grupos.items():
        if (len(es) == 2 and all(e[3] == "?" for e in es) and es[0][1] != es[1][1]
                and all(a.isdigit() and e[1][:4] == str(int(a) - 1) for e in es)):
            es.sort(key=lambda e: e[1]); es[0][3], es[1][3] = "provisoria", "definitiva"
            inferidos.add((c, es[0][2], a, "provisoria")); inferidos.add((c, es[1][2], a, "definitiva"))
    tipo_inf = {(c, ed, a): t for c, ed, a, *t in [x if len(x) == 4 else (*x, "definitiva") for x in inferidos]}
    for r in entradas:
        if r[2] == "?" and (r[0], r[4], r[1]) in tipo_inf: r[2] = tipo_inf[(r[0], r[4], r[1])][0]
    if inferidos: print("carater inferido:", sorted(inferidos))
    # a mesma entrada (edicao, comarca, numero, pessoa) lida duas vezes conta uma so
    vist, uni = set(), []
    for r in entradas:
        k = (r[0], r[4], r[2], r[5], r[6])   # com tipo: provisoria e definitiva na mesma edicao sao listas distintas
        if k not in vist: vist.add(k); uni.append(r)
    entradas = uni
    with open(os.path.join(DATA, f"comarcas_{pref}_editais.csv"), "w", newline="", encoding="utf-8") as fo:
        w = csv.writer(fo); w.writerow(CAB_ED)
        w.writerows(editais)
    with open(os.path.join(DATA, f"comarcas_{pref}_entradas.csv"), "w", newline="", encoding="utf-8") as fo:
        w = csv.writer(fo); w.writerow(CAB_EN)
        w.writerows(entradas)
    print(f"{len(editais)} editais, {len(entradas)} entradas gravadas em data/comarcas_{pref}_*.csv")

if __name__ == "__main__":
    main()
