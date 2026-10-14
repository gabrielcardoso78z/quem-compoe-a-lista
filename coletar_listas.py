#!/usr/bin/env python3
"""
Coleta das listas de jurados publicadas no site do TJPR
(https://www.tjpr.jus.br/lista-de-jurados).

Uso:  python3 coletar_listas.py

O que faz:
  1. Percorre a pagina de listas e todas as paginas de paginacao.
  2. Baixa cada publicacao (listas provisorias, definitivas e editais).
  3. Guarda o HTML bruto em raw/ (fica so no seu computador).
  4. Gera planilhas em data/ com o NOME PSEUDONIMIZADO (hash com chave
     secreta guardada em .chave_secreta, que nunca deve ser compartilhada).

Usa apenas a biblioteca padrao do Python (nao precisa instalar nada).
"""
import csv, hashlib, html, os, re, secrets, ssl, sys, time, unicodedata
import urllib.request, urllib.error
from urllib.parse import urljoin, urlparse

BASE = "https://www.tjpr.jus.br"
INICIO = BASE + "/lista-de-jurados"
PAUSA = 1.0          # segundos entre requisicoes, para nao sobrecarregar o site
MAX_PAGINAS = 600
UA = "Mozilla/5.0 (Macintosh) pesquisa-academica-IC-listas-jurados"

AQUI = os.path.dirname(os.path.abspath(__file__))
RAW = os.path.join(AQUI, "raw")
DATA = os.path.join(AQUI, "data")
CHAVE = os.path.join(AQUI, ".chave_secreta")
os.makedirs(RAW, exist_ok=True)
os.makedirs(DATA, exist_ok=True)

# ---------------------------------------------------------------- rede
def baixar(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    try:
        with urllib.request.urlopen(req, timeout=40) as r:
            return r.read().decode("utf-8", errors="replace")
    except urllib.error.URLError as e:
        if isinstance(getattr(e, "reason", None), ssl.SSLError):
            sys.exit("Erro de certificado SSL. Rode: /usr/bin/python3 coletar_listas.py")
        print(f"  ! falha em {url}: {e}", flush=True)
        return None

# ---------------------------------------------------------------- links
HREF = re.compile(r'href="([^"]+)"', re.I)

def normalizar(url):
    url = html.unescape(url)
    url = urljoin(BASE, url)
    p = urlparse(url)
    caminho = re.sub(r"^/en(?=/)", "", p.path)
    return p, caminho

def eh_conteudo(caminho):
    return "/lista-de-jurados/" in caminho and "/content/" in caminho

def eh_paginacao(p, caminho):
    return caminho.startswith("/lista-de-jurados") and "_cur=" in (p.query or "")

# ---------------------------------------------------------------- texto
BLOCO = re.compile(r"<\s*(br|/p|/div|/li|/tr|/h\d|p|li|tr)\b[^>]*>", re.I)
TAG = re.compile(r"<[^>]+>")

def texto_do_artigo(pagina):
    ini = None
    for marca in ("journal-content-article", "asset-full-content", "asset-content"):
        i = pagina.find(marca)
        if i != -1:
            ini = i
            break
    trecho = pagina[ini:] if ini is not None else pagina
    trecho = re.sub(r"<script.*?</script>|<style.*?</style>", " ", trecho, flags=re.S | re.I)
    trecho = BLOCO.sub("\n", trecho)
    trecho = html.unescape(TAG.sub(" ", trecho))
    linhas = [re.sub(r"[ \t ]+", " ", l).strip() for l in trecho.split("\n")]
    return [l for l in linhas if l]

def titulo(pagina):
    m = re.search(r'<meta property="og:title" content="([^"]+)"', pagina) or \
        re.search(r"<title>(.*?)</title>", pagina, re.S)
    return html.unescape(m.group(1)).strip() if m else ""

ENTRADA = re.compile(r"^(\d{1,4})\s*[.\-–)]\s*(.+?)$")
SEP = re.compile(r"\s+[-–—]\s+|\s*[-–—]\s*$")

def separar(resto):
    partes = SEP.split(resto, maxsplit=1)
    nome = partes[0].strip()
    prof = partes[1].strip() if len(partes) > 1 else ""
    return nome, prof

def chave_secreta():
    if not os.path.exists(CHAVE):
        with open(CHAVE, "w") as f:
            f.write(secrets.token_hex(32))
    return open(CHAVE).read().strip()

def pseudonimo(nome, chave):
    n = unicodedata.normalize("NFKD", nome).encode("ascii", "ignore").decode()
    n = re.sub(r"[^A-Za-z ]+", " ", n)            # ignora pontuacao e numeros (ex.: "FULANO;")
    n = re.sub(r"\s+", " ", n).strip().upper()
    return hashlib.sha256((chave + "|" + n).encode()).hexdigest()[:16]

def classificar(t):
    t2 = unicodedata.normalize("NFKD", t).encode("ascii", "ignore").decode().upper()
    if "CONVOCA" in t2: return "convocacao"
    if "PROVIS" in t2: return "provisoria"
    if "DEFINI" in t2: return "definitiva"
    if "LISTA" in t2: return "lista_outra"
    return "outro"

def ano_ref(t):
    m = re.findall(r"20\d\d", t)
    return max(m) if m else ""

def vara(texto, pub):
    t = " ".join(texto[:40]).upper()
    if "CASCAVEL" in t: return "Cascavel"
    if re.search(r"\b1[ªAºO]?\s*(VARA|SECRETARIA|TRIBUNAL)", t) or "1º TRIBUNAL" in t: return "Curitiba 1a Vara"
    if re.search(r"\b2[ªAºO]?\s*(VARA|SECRETARIA|TRIBUNAL)", t): return "Curitiba 2a Vara"
    return f"indefinida ({pub})"

# ---------------------------------------------------------------- coleta
def main():
    print("Acessando", INICIO, flush=True)
    chave = chave_secreta()
    fila, vistos, conteudos, paginas_vistas = [INICIO], set(), {}, set()
    while fila and len(vistos) < MAX_PAGINAS:
        url = fila.pop(0)
        if url in vistos: continue
        vistos.add(url)
        pag = baixar(url); time.sleep(PAUSA)
        if not pag: continue
        for href in HREF.findall(pag):
            p, cam = normalizar(href)
            if eh_conteudo(cam):
                ent = re.search(r"p_r_p_assetEntryId=(\d+)", p.query or "")
                u = BASE + cam + (f"?p_r_p_assetEntryId={ent.group(1)}" if ent else "")
                if ent or cam not in conteudos:
                    conteudos[cam] = u
            elif eh_paginacao(p, cam):
                inst = re.search(r"INSTANCE_([A-Za-z0-9]+)_cur=(\d+)", p.query or "")
                chave_pag = inst.groups() if inst else p.query
                if chave_pag in paginas_vistas: continue
                paginas_vistas.add(chave_pag)
                fila.append(BASE + cam + "?" + p.query)
        print(f"indice {len(vistos)} | publicacoes encontradas: {len(conteudos)}")

    docs, entradas, sobras = [], [], []
    for i, (cam, url) in enumerate(sorted(conteudos.items()), 1):
        pub = re.search(r"asset_publisher/([^/]+)/", cam)
        pub = pub.group(1) if pub else ""
        did = pub + "_" + re.sub(r"[^A-Za-z0-9]+", "_", cam.split("/content/")[-1])[:80]
        arq = os.path.join(RAW, did + ".html")
        if os.path.exists(arq):
            pag = open(arq, encoding="utf-8").read()
        else:
            pag = baixar(url); time.sleep(PAUSA)
            if not pag: continue
            open(arq, "w", encoding="utf-8").write(pag)
        tit = titulo(pag)
        erro = "conteúdo não pôde ser encontrado" in pag
        marcas = [m.start() for m in re.finditer("journal-content-article", pag)] or [0]
        blocos = [pag[a:b] for a, b in zip(marcas, marcas[1:] + [len(pag)])]
        linhas = max((texto_do_artigo(b) for b in blocos), key=lambda ls: sum(1 for l in ls if ENTRADA.match(l)))
        v = {"s0CT": "Curitiba 1a Vara", "M4kc": "Curitiba 2a Vara"}.get(pub, "Cascavel")
        n, seqs, vistos_seq = 0, [], set()
        for l in linhas:
            m = ENTRADA.match(l)
            if not m:
                continue
            nome, prof = separar(m.group(2))
            if len(nome.split()) < 2:      # descarta linhas que nao parecem nome (sem gravar o texto)
                sobras.append([did, m.group(1), len(l)]); continue
            if m.group(1) in vistos_seq:   # conteudo repetido na pagina
                continue
            vistos_seq.add(m.group(1))
            n += 1; seqs.append(int(m.group(1)))
            entradas.append([did, v, classificar(tit), ano_ref(tit), m.group(1),
                             pseudonimo(nome, chave), prof])
        lacunas = sum(1 for a, b in zip(seqs, seqs[1:]) if b != a + 1)
        docs.append([did, pub, v, tit, classificar(tit), ano_ref(tit), n, lacunas, "erro" if erro else "ok", url])
        print(f"[{i}/{len(conteudos)}] {classificar(tit):11} {ano_ref(tit)} {v:18} {n:5} entradas  {tit[:60]}")

    with open(os.path.join(DATA, "documentos.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f); w.writerow(["doc_id","publisher","vara","titulo","tipo","ano","n_entradas","quebras_sequencia","status","url"]); w.writerows(docs)
    with open(os.path.join(DATA, "entradas.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f); w.writerow(["doc_id","vara","tipo","ano","seq","pessoa_id","profissao"]); w.writerows(entradas)
    with open(os.path.join(DATA, "linhas_descartadas.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f); w.writerow(["doc_id","seq","tamanho_linha"]); w.writerows(sobras)
    print(f"\nPronto: {len(docs)} publicacoes, {len(entradas)} entradas. Veja a pasta data/.")

if __name__ == "__main__":
    main()
