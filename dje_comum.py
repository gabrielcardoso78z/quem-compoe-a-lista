"""Funcoes comuns as buscas no texto do Diario da Justica (DJe) do TJPR.

Reune o que estava repetido nos scripts de auxiliares/ (versoes antigas em auxiliares/historico/).
Nenhuma funcao grava nomes: as buscas imprimem so datas, linhas, contagens e pseudonimos agregados.

Pastas de texto (fora do projeto, porque o texto do Diario traz nomes e e grande):
  ~/djetxt  pdftotext -layout   (colunas preservadas; usado nas buscas)
  ~/djeraw  pdftotext padrao    (fluxo de leitura; usado por processar_dje.py, cujas linhas de cabecalho
                                 foram anotadas nesse formato)
"""
import glob, gzip, os, re, subprocess, unicodedata
from collections import Counter

AQUI = os.path.dirname(os.path.abspath(__file__))
PDF_DIR = os.path.join(AQUI, "dje")
TXT_LAYOUT = os.path.expanduser("~/djetxt")
TXT_RAW = os.path.expanduser("~/djeraw")

# entrada numerada de lista ("123. NOME - PROFISSAO", "123 - NOME", "123) NOME")
ENT = re.compile(r"^\s*(\d{1,4})\s*[.\-–)]\s*(.+?)\s*$")


def converter(pdf_dir=PDF_DIR, layout_dir=TXT_LAYOUT, raw_dir=TXT_RAW, raw=True):
    """Converte com pdftotext as edicoes de dje/ que ainda nao tem texto. Retorna (novos_layout, novos_raw)."""
    os.makedirs(layout_dir, exist_ok=True)
    if raw: os.makedirs(raw_dir, exist_ok=True)
    n1 = n2 = 0
    for pdf in sorted(glob.glob(os.path.join(pdf_dir, "*.pdf"))):
        base = os.path.basename(pdf)[:-4] + ".txt"
        out = os.path.join(layout_dir, base)
        if not os.path.exists(out):
            subprocess.run(["pdftotext", "-layout", pdf, out]); n1 += 1
        if raw:
            out = os.path.join(raw_dir, base)
            if not os.path.exists(out):
                subprocess.run(["pdftotext", pdf, out]); n2 += 1
    return n1, n2


def arquivos(padrao="202*", pasta=TXT_LAYOUT):
    return sorted(glob.glob(os.path.join(pasta, padrao + ".txt")))


def ler_linhas(f):
    return open(f, encoding="utf-8", errors="ignore").read().split("\n")


def ler_achatado(f):
    """Texto com todas as quebras de linha e espacos reduzidos a um espaco (segunda passada: acha cabecalhos partidos)."""
    return re.sub(r"\s+", " ", open(f, encoding="utf-8", errors="ignore").read())


def edicao(f, n=10):
    return os.path.basename(f)[:n]


# --- reordenacao de colunas (texto -layout) ---------------------------------------------------------------

def fluxo(texto, linha0, max_pag=40):
    """Reordena o texto em fluxo de colunas (esq. depois dir.) a partir da pagina da linha0."""
    paginas = texto.split("\f"); acum = 0; p0 = 0
    for k, pg in enumerate(paginas):
        n = pg.count("\n")
        if acum + n >= linha0: p0 = k; break
        acum += n
    linhas = []
    for k in range(p0, min(len(paginas), p0 + max_pag)):
        L = paginas[k].split("\n")
        # ponto de corte: posicao mais comum de inicio da 2a coluna
        pos = [m.end() for l in L for m in re.finditer(r"\s{3,}(?=\S)", l) if 60 < m.end() < 140]
        c = Counter(pos).most_common(1)[0][0] if pos else 10**6
        esq = [l[:c].rstrip() for l in L]; dire = [l[c:].strip() for l in L]
        linhas += [("E", x) for x in esq] + [("D", x) for x in dire]
    return [x for _, x in linhas]


ENTR = re.compile(r"^\s*(\d{1,4})\s*[.\-–)]\s*(\S.*)$")


def lista_cascavel(texto, linha0):
    """Extrai a lista de Cascavel seguindo a numeracao 1, 2, 3... a partir do cabecalho "Juri de Cascavel"."""
    fl = fluxo(texto, linha0)
    h = next(j for j, x in enumerate(fl) if re.search(r"(?i)j[úu]ri de cascavel", x))
    out, esp = [], 1
    for x in fl[h:]:
        m = ENTR.match(x)
        if m and int(m.group(1)) == esp:
            out.append((m.group(1), m.group(2))); esp += 1
        elif out and re.search(r"(?i)para que (n[aã]o )?se possa alegar|art\.\s*436", x): break
    return out


# --- sexo provavel pelo prenome (mesma tabela e limiar de analise_sexo.py) ----------------------------------

def _nrm(t):
    return re.sub(r"[^A-Z]", "", unicodedata.normalize("NFKD", t).encode("ascii", "ignore").decode().upper())


_TAB = None


def sexo(nome, limiar=0.9):
    global _TAB
    if _TAB is None:
        import csv
        _TAB = {}
        for r in csv.DictReader(gzip.open(os.path.join(AQUI, "referencias/dados_nomes/nomes.csv.gz"), "rt", encoding="utf-8")):
            f, m = float(r["frequency_female"] or 0), float(r["frequency_male"] or 0)
            for n in [r["first_name"]] + [x for x in (r.get("alternative_names") or "").split("|") if x]:
                _TAB.setdefault(_nrm(n), (f, m))
    k = _nrm(nome.split()[0]) if nome.split() else ""
    if k not in _TAB: return "nf"
    f, m = _TAB[k]; t = f + m
    return "F" if t and f / t >= limiar else "M" if t and m / t >= limiar else "ind"
