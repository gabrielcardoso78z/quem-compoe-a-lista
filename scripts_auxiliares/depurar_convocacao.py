"""Compara, para uma edicao e uma comarca, a leitura das convocacoes pelo codigo congelado e pelo atual.
Imprime papel e nome MASCARADO (letras viram A/a) de cada sorteado, marcando quem so aparece em uma versao.
Uso: python3 scripts_auxiliares/depurar_convocacao.py <edicao> <trecho da comarca>"""
import sys, os, re, csv, json, subprocess, tempfile
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if len(sys.argv) > 1 and sys.argv[1] == "--rodar":          # processo filho: roda uma versao do codigo
    cod, padrao, saida = sys.argv[2], sys.argv[3], sys.argv[4]
    sys.path.insert(0, BASE); os.chdir(BASE)
    import coletar_listas            # sempre o da raiz: a chave secreta e a da raiz (o codigo congelado criaria outra)
    sys.path.insert(0, cod)
    import processar_convocacoes_dje as cv, importlib.util
    sp = importlib.util.spec_from_file_location("pc_atual", os.path.join(BASE, "processar_comarcas_dje.py"))
    pa = importlib.util.module_from_spec(sp); sp.loader.exec_module(pa); cv.pc._MUN = pa.municipios()
    mk = lambda s: re.sub(r"[A-ZÀ-Ý]", "A", re.sub(r"[a-zß-ÿ]", "a", s))
    vis = {}; o = cv.pseudonimo
    def ps(n, c): h = o(n, c); vis[h] = mk(n); return h
    cv.pseudonimo = ps; tmp = tempfile.mkdtemp(dir=os.path.expanduser("~")); cv.DATA = tmp
    sys.argv = ["x", "--padrao=" + padrao]
    import io, contextlib
    with contextlib.redirect_stdout(io.StringIO()): cv.main()
    rows = [r for f in os.listdir(tmp) if f.endswith("entradas.csv") for r in csv.DictReader(open(os.path.join(tmp, f)))]
    json.dump([[r["comarca"], r["pagina"], r["papel"], r["pessoa_id"], vis.get(r["pessoa_id"], "?")] for r in rows], open(saida, "w"))
    sys.exit()
ed, com = sys.argv[1], sys.argv[2].lower()
arq = [f for f in os.listdir(os.path.expanduser("~/djetxt")) if f.endswith(f"_ed{ed}.txt")][0][:-4]
res = {}
for rot, cod in (("velho", os.path.join(BASE, "auditoria/baseline_2026-10-12/codigo")), ("novo", BASE)):
    out = os.path.join(tempfile.mkdtemp(dir=os.path.expanduser("~")), "r.json")
    subprocess.run([sys.executable, os.path.abspath(__file__), "--rodar", cod, arq, out], check=True)
    res[rot] = [r for r in json.load(open(out)) if com in r[0].lower()]
hv = {r[3]: r for r in res["velho"]}; hn = {r[3]: r for r in res["novo"]}
for rot, outro in (("velho", hn), ("novo", hv)):
    print(f"== {rot}: {len(res[rot])} sorteados")
    for c, p, papel, h, m in res[rot]:
        marca = "" if h in outro and outro[h][2] == papel else ("  <- papel diferente" if h in outro else "  <- so nesta versao")
        print(f"   {c[:14]:14} p{p:>4} {papel:8} {m[:60]}{marca}")
