"""Classifica, sem gravar nem imprimir nomes, as entradas cujo identificador mudou entre a versao congelada
(auditoria/baseline_2026-10-12) e a atual. Roda o codigo velho e o novo nas mesmas edicoes, guarda em memoria
o nome por tras de cada pseudonimo e imprime so categorias e formas mascaradas (letras viram A/a).
Uso: python3 scripts_auxiliares/classificar_mudancas.py [max_exemplos]"""
import sys, os, re, csv, glob, io, contextlib, importlib.util, unicodedata, tempfile
from collections import Counter, defaultdict
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); os.chdir(BASE); sys.path.insert(0, BASE)
CONG = os.path.join(BASE, "auditoria/baseline_2026-10-12")
MAXEX = int(sys.argv[1]) if len(sys.argv) > 1 else 6
def carregar(nome, caminho):
    sp = importlib.util.spec_from_file_location(nome, caminho); m = importlib.util.module_from_spec(sp); sp.loader.exec_module(m); return m
novo = carregar("novo", "processar_comarcas_dje.py")
velho_ll = carregar("leitores_listas_velho", os.path.join(CONG, "codigo/leitores_listas.py"))
velho = carregar("velho", os.path.join(CONG, "codigo/processar_comarcas_dje.py"))
velho.LL = velho_ll; velho.DJE_PDF = novo.DJE_PDF
if hasattr(novo, "municipios"): velho._MUN = novo.municipios()
mk = lambda s: re.sub(r"[A-ZÀ-Ý]", "A", re.sub(r"[a-zß-ÿ]", "a", s))
def toks(s): return re.sub(r"[^A-Z ]", "", unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode().upper()).split()
def ler(p): return list(csv.DictReader(open(p, encoding="utf-8")))
chave = lambda r: (r["edicao"], r["tipo"], r["ano"], r["seq"], r["comarca"])
B = {chave(r): r for r in ler(os.path.join(CONG, "data/comarcas_pr_entradas.csv"))}
N = {chave(r): r for r in ler(os.path.join(BASE, "data/comarcas_pr_entradas.csv"))}
mud = {k: (B[k]["pessoa_id"], N[k]["pessoa_id"], B[k]["comarca"]) for k in B.keys() & N.keys() if B[k]["pessoa_id"] != N[k]["pessoa_id"]}
eds = sorted({k[0] for k in mud})
print(f"identificadores mudados: {len(mud)} em {len(eds)} edicoes")
nomes = {"velho": {}, "novo": {}}
tmp = tempfile.mkdtemp(dir=os.path.expanduser("~"))
for rot, M in (("velho", velho), ("novo", novo)):
    orig = M.pseudonimo
    def ps(nome, ch, _o=orig, _d=nomes[rot]):
        h = _o(nome, ch); _d[h] = nome; return h
    M.pseudonimo = ps; M.DATA = tmp
    for ed in eds:
        arqs = glob.glob(os.path.join(os.path.expanduser("~/djetxt"), f"*_ed{ed}.txt"))
        if not arqs: print("sem arquivo", ed); continue
        sys.argv = ["x", "--todas", "--bruto", "--padrao=" + os.path.basename(arqs[0])[:-4]]
        with contextlib.redirect_stdout(io.StringIO()): M.main()
JUNK = set("CURITIBA EDICAO DIARIO ELETRONICO TRIBUNAL JUSTICA PARANA ART ARTIGO EDITAL PARA QUE DADO PASSADO NA FORMA DO DE DA".split())
cat = Counter(); ex = defaultdict(list)
for k, (hb, hn, com) in sorted(mud.items()):
    o, n = nomes["velho"].get(hb), nomes["novo"].get(hn)
    if o is None or n is None: c = "nao reproduzido"; cat[c] += 1; ex[c].append((com, k)); continue
    to, tn = toks(o), toks(n)
    if re.search("[ÂÃ]", o) and not re.search("[ÂÃ]", n): c = "mojibake reparado"
    elif to[:len(tn)] == tn and len(tn) < len(to):
        resto = to[len(tn):]; c = "cauda removida (texto do DJe/edital)" if set(resto) & JUNK else "cauda removida (outra)"
    elif tn[:len(to)] == to and len(to) < len(tn): c = "nome completado"
    elif [t for t in to if t not in JUNK] == [t for t in tn if t not in JUNK]: c = "texto do DJe removido do meio"
    else:
        # trecho que saiu do meio: se e cabecalho/rodape do DJe, repete-se nas paginas da edicao (nomes nao se repetem)
        i = 0
        while i < min(len(to), len(tn)) and to[i] == tn[i]: i += 1
        j = 0
        while j < min(len(to), len(tn)) - i and to[-1 - j] == tn[-1 - j]: j += 1
        tirado, posto = to[i:len(to) - j], tn[i:len(tn) - j]
        txt = " ".join(toks(open(glob.glob(os.path.join(os.path.expanduser("~/djetxt"), f"*_ed{k[0]}.txt"))[0], encoding="utf-8", errors="ignore").read()))
        rep = txt.count(" ".join(tirado)) if tirado and not posto else 0
        c = f"trecho repetido na edicao removido do meio" if rep >= 3 else "outro"
        if c == "outro": ex[c].append(("tirado/posto (palavras)", len(tirado), len(posto), "repeticoes", rep))
    cat[c] += 1
    if len(ex[c]) < MAXEX or c in ("outro", "cauda removida (outra)", "nome completado"):
        ex[c].append((com, k[0], k[3], mk(o)[:90], mk(n)[:90]))
for c, v in cat.most_common(): print(f"  {c}: {v}")
for c in ex:
    print("\n--", c)
    for e in ex[c][:40]: print("   ", e)
