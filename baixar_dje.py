#!/usr/bin/env python3
"""Baixa edicoes do Diario da Justica do TJPR (e-DJ) para a pasta dje/. Usa so a biblioteca padrao.

Versao consolidada (12/10/2026): substitui baixar_dje.py, baixar_dje_cascavel.py, baixar_dje_cascavel2.py
e baixar_dje_2013.py, que so diferiam no periodo baixado (versoes antigas em auxiliares/historico/).
A logica de download e a mesma; edicoes ja baixadas sao puladas.

Uso:
  python3 baixar_dje.py curitiba            janelas das listas de Curitiba que faltam no site (busca original)
  python3 baixar_dje.py cascavel            15/09 a 30/11 de 2022 a 2025 e 15/09 a 30/09/2026
  python3 baixar_dje.py cascavel2           01/08 a 14/09 de 2022 a 2026
  python3 baixar_dje.py 2013                01/08 a 09/09/2012 e 17/11/2012 a 31/03/2013
  python3 baixar_dje.py ano 2027            janelas do art. 426 para a lista do ano indicado:
                                            01 a 15/10 e 03 a 14/11 do ano anterior
  python3 baixar_dje.py periodo 2026-10-01 2026-10-15     qualquer periodo
"""
import datetime as dt, http.cookiejar, os, re, sys, time, urllib.parse, urllib.request

BASE = "https://portal.tjpr.jus.br"
PESQ = BASE + "/e-dj/publico/diario/pesquisar.do"
AQUI = os.path.dirname(os.path.abspath(__file__))
DESTINO = os.path.join(AQUI, "dje")
D = dt.date


def janelas_curitiba():
    # (inicio, fim) de cada janela: provisorias ate 10/10, definitivas ate 10/11
    J = []
    for ano in (2009, 2010, 2011, 2012, 2022, 2024, 2025, 2026):
        J.append((D(ano, 10, 1), D(ano, 10, 15)))
    for ano in (2009, 2022, 2024, 2025):
        J.append((D(ano, 11, 3), D(ano, 11, 14)))
    # busca ampliada das provisorias de 2013 (publicadas em 2012 fora da janela padrao)
    J.append((D(2012, 9, 10), D(2012, 9, 30)))
    J.append((D(2012, 10, 16), D(2012, 11, 16)))
    return J


PRESETS = {
    "curitiba": janelas_curitiba,
    # busca ampliada para Cascavel (11/10/2026)
    "cascavel": lambda: [(D(a, 9, 15), D(a, 11, 30)) for a in (2022, 2023, 2024, 2025)] + [(D(2026, 9, 15), D(2026, 9, 30))],
    # busca ampliada 2 (12/10/2026): provisorias publicadas antes da janela
    "cascavel2": lambda: [(D(a, 8, 1), D(a, 9, 14)) for a in (2022, 2023, 2024, 2025, 2026)],
    # lista de 2013 da 1a Vara (12/10/2026)
    "2013": lambda: [(D(2012, 8, 1), D(2012, 9, 9)), (D(2012, 11, 17), D(2013, 3, 31))],
}


def janelas_de_argumentos(args):
    if not args:
        sys.exit(__doc__)
    if args[0] in PRESETS:
        return PRESETS[args[0]]()
    if args[0] == "ano" and len(args) == 2:
        a = int(args[1]) - 1
        return [(D(a, 10, 1), D(a, 10, 15)), (D(a, 11, 3), D(a, 11, 14))]
    if args[0] == "periodo" and len(args) == 3:
        return [(D.fromisoformat(args[1]), D.fromisoformat(args[2]))]
    sys.exit(__doc__)


def baixar(janelas):
    os.makedirs(DESTINO, exist_ok=True)
    jar = http.cookiejar.CookieJar()
    op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))
    op.addheaders = [("User-Agent", "Mozilla/5.0 (Macintosh) pesquisa-academica-IC-listas-jurados")]

    def abrir(url, dados=None):
        for tent in range(3):
            try:
                with op.open(url, data=dados, timeout=120) as r:
                    return r.read()
            except Exception as e:
                print(f"  ! tentativa {tent+1} falhou: {e}", flush=True); time.sleep(5)
        return None

    abrir(PESQ)  # inicia a sessao
    hoje = dt.date.today()
    for ini, fim in janelas:
        d = ini
        while d <= min(fim, hoje):
            if d.weekday() < 5:
                form = urllib.parse.urlencode({"pageSize": "10", "pageNumber": "1", "sortColumn": "dataVeiculacao",
                                               "sortOrder": "desc", "numero": "", "dataVeiculacao": d.strftime("%d/%m/%Y")}).encode()
                html = (abrir(PESQ, form) or b"").decode("latin-1")
                for tr in re.findall(r"<tr[^>]*>(.*?)</tr>", html, re.S):
                    m = re.search(r"downloadWindow\('([^']+)'", tr)
                    num = re.search(r">\s*(\d{3,5})\s*<", tr)
                    if not m: continue
                    n = num.group(1) if num else "x"
                    arq = os.path.join(DESTINO, f"{d.isoformat()}_ed{n}.pdf")
                    if os.path.exists(arq) and os.path.getsize(arq) > 10000:
                        print(f"{d} ed. {n}: ja baixada", flush=True); continue
                    pdf = abrir(BASE + m.group(1).replace("&amp;", "&"))
                    time.sleep(1)
                    if pdf and pdf[:4] == b"%PDF":
                        open(arq, "wb").write(pdf)
                        print(f"{d} ed. {n}: {len(pdf)//1024} KB", flush=True)
                    else:
                        print(f"{d} ed. {n}: falhou", flush=True)
                time.sleep(1)
            d += dt.timedelta(days=1)
    print("Download do Diario encerrado.")


if __name__ == "__main__":
    baixar(janelas_de_argumentos(sys.argv[1:]))
