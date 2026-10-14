#!/usr/bin/env python3
"""Menu para rodar a pesquisa inteira ou etapas soltas, na ordem certa.

Uso:
  python3 rodar_tudo.py              abre o menu
  python3 rodar_tudo.py tudo         roda a cadeia sem internet: etapas 1, 2, 5, 6 e 7
  python3 rodar_tudo.py 5 6 7        roda so as etapas indicadas, nessa ordem
  python3 rodar_tudo.py analises     so as analises

As etapas 3 e 4 (texto do Diario) ficam fora do "tudo": as linhas de cabecalho anotadas em
processar_dje.py valem para o texto gerado pelo pdftotext 22.02 (poppler); outra versao pode deslocar as
linhas. Os data/dje_*.csv ja gerados ficam valendo. Rode 3 e 4 so de proposito e confira data/dje_documentos.csv.

Cada etapa chama o script de sempre (nada e reescrito aqui). A saida aparece na tela e fica
em rodar_tudo_log.txt; a de cada analise tambem em data/saida_<analise>.txt.
"""
import datetime as dt, os, shutil, subprocess, sys

AQUI = os.path.dirname(os.path.abspath(__file__))
os.chdir(AQUI)
PY = sys.executable
LOG = os.path.join(AQUI, "rodar_tudo_log.txt")
RAW_DJE = os.path.expanduser("~/djeraw")

ANALISES = [  # (script, arquivo de saida em data/)
    ("analise_renovacao.py", "saida_analise_renovacao.txt"),
    ("analise_perfil.py", "saida_analise_perfil.txt"),
    ("analise_vinculo_publico.py", "saida_analise_vinculo.txt"),
    ("analise_convocacoes.py", "saida_analise_convocacoes.txt"),
    ("analise_isentos.py", "saida_analise_isentos.txt"),
    ("analise_sexo.py", "saida_analise_sexo.txt"),
    ("analise_tse.py", "saida_analise_tse.txt"),
    ("analise_aprofundada.py", "saida_analise_aprofundada.txt"),
    ("analise_comarcas.py", "saida_analise_comarcas.txt"),
    ("verificar_comarcas.py", "saida_verificar_comarcas.txt"),
    ("analise_censo_estadual.py", "saida_analise_censo_estadual.txt"),
    ("analise_convocacoes_estado.py", "saida_analise_convocacoes_estado.txt"),   # sorteados no estado (secao 4.11)
    ("analise_argentina.py", "saida_analise_argentina.txt"),   # le data/ar_entradas.csv (processar_argentina.py)
]


def log(msg):
    print(msg, flush=True)
    with open(LOG, "a", encoding="utf-8") as f: f.write(msg + "\n")


def rodar(args, saida=None):
    """Roda um script, mostra e registra a saida. Retorna True se terminou sem erro."""
    log(f"\n>>> {' '.join(args)}   ({dt.datetime.now():%d/%m/%Y %H:%M})")
    p = subprocess.Popen([PY, "-u"] + args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, cwd=AQUI)
    linhas = []
    with open(LOG, "a", encoding="utf-8") as f:
        for l in p.stdout:
            print(l, end="", flush=True); f.write(l); linhas.append(l)
    p.wait()
    if p.returncode == 0 and saida:
        open(os.path.join(AQUI, "data", saida), "w", encoding="utf-8").writelines(linhas)
    if p.returncode != 0:
        log(f"!!! {args[0]} terminou com erro (codigo {p.returncode})")
    return p.returncode == 0


def tem_texto_dje():
    return os.path.isdir(RAW_DJE) and any(n.endswith(".txt") for n in os.listdir(RAW_DJE))


def etapa_converter():
    if not shutil.which("pdftotext"):
        log("pdftotext nao encontrado: etapa pulada. No Mac, instale com:  brew install poppler")
        return True
    return rodar(["buscar_dje.py", "converter"])


def etapa_dje():
    if not tem_texto_dje():
        log(f"Sem texto do Diario em {RAW_DJE}: etapa pulada; ficam os data/dje_*.csv atuais.")
        return True
    return rodar(["processar_dje.py", RAW_DJE, "todos"])


def etapa_analises():
    return all([rodar([s], saida) for s, saida in ANALISES])


# (codigo, descricao, funcao, precisa de internet)
ETAPAS = [
    ("1", "Processar as listas do site ja baixadas (raw/ -> data/entradas.csv)", lambda: rodar(["processar_listas.py"]), False),
    ("2", "Processar os editais de convocacao ja baixados (raw_conv/ -> data/convocacoes.csv)", lambda: rodar(["processar_convocacoes.py"]), False),
    ("3", "Converter em texto as edicoes do Diario de dje/ (pdftotext; demora)", etapa_converter, False),
    ("4", "Extrair de novo as listas de Curitiba do Diario (ver aviso no topo do script)", etapa_dje, False),
    ("5", "Montar a base unica de Curitiba (data/base_listas.csv)", lambda: rodar(["montar_base.py"]), False),
    ("6", "Codificar as profissoes (codificacao_profissoes.csv)", lambda: rodar(["codificar_profissoes.py"]), False),
    ("7", "Rodar todas as analises (data/resultado_*, aprof_*, saida_*)", etapa_analises, False),
]
ONLINE = [
    ("C", "Coletar de novo as listas do site do TJPR (internet)", lambda: rodar(["coletar_listas.py"])),
    ("V", "Coletar de novo os editais de convocacao (internet)", lambda: rodar(["coletar_convocacoes.py"])),
    ("D", "Baixar edicoes do Diario (internet)", None),
    ("B", "Buscas no texto do Diario", None),
]


def menu_baixar():
    print("\n  Baixar o Diario:\n   1 janelas do art. 426 para a lista de um ano (pede o ano)\n   2 periodo qualquer (pede as datas)"
          "\n   3 busca original de Curitiba\n   4 busca de Cascavel (15/09 a 30/11)\n   5 busca de Cascavel 2 (01/08 a 14/09)\n   6 busca da 1a Vara 2013")
    op = input("  Opcao: ").strip()
    if op == "1": return rodar(["baixar_dje.py", "ano", input("  Ano da lista (ex.: 2027): ").strip()])
    if op == "2": return rodar(["baixar_dje.py", "periodo", input("  De (AAAA-MM-DD): ").strip(), input("  Ate (AAAA-MM-DD): ").strip()])
    pres = {"3": "curitiba", "4": "cascavel", "5": "cascavel2", "6": "2013"}
    if op in pres: return rodar(["baixar_dje.py", pres[op]])
    return True


def menu_buscas():
    modos = ["converter", "identificar", "localizar", "editais", "cascavel", "profissao", "varrer"]
    print("\n  Buscas no Diario (so imprimem datas e contagens, nenhum nome):")
    for i, m in enumerate(modos, 1): print(f"   {i} {m}")
    op = input("  Opcao: ").strip()
    if not op.isdigit() or not 1 <= int(op) <= len(modos): return True
    extra = input("  Opcoes extras (Enter para nenhuma; ex.: --padrao 2012-* --limiar 0.3): ").split()
    return rodar(["buscar_dje.py", modos[int(op) - 1]] + extra)


CADEIA = ["1", "2", "5", "6", "7"]


def rodar_codigos(codigos):
    mapa = {c: f for c, _, f, _ in ETAPAS}
    for c in codigos:
        if c not in mapa:
            log(f"Etapa desconhecida: {c}"); return False
        if not mapa[c]():
            log("Cadeia interrompida."); return False
    return True


def menu():
    while True:
        print("\n=== Listas de jurados de Curitiba: menu ===")
        for c, d, _, _ in ETAPAS: print(f" {c}  {d}")
        print(" T  Tudo sem internet (1, 2, 5, 6 e 7; o Diario ja extraido fica valendo)")
        print(" A  So as analises (7)")
        print(" --- com internet ou consultas ---")
        for c, d, _ in ONLINE: print(f" {c}  {d}")
        print(" 0  Sair")
        op = input("Opcao: ").strip().upper()
        if op == "0": break
        elif op == "T": rodar_codigos(CADEIA)
        elif op == "A": etapa_analises()
        elif op == "D": menu_baixar()
        elif op == "B": menu_buscas()
        elif op in ("C", "V"): dict((c, f) for c, _, f in ONLINE)[op]()
        elif op in [c for c, *_ in ETAPAS]: rodar_codigos([op])
        else: print("Opcao invalida.")


if __name__ == "__main__":
    a = sys.argv[1:]
    if not a: menu()
    elif a == ["tudo"]: sys.exit(0 if rodar_codigos(CADEIA) else 1)
    elif a == ["analises"]: sys.exit(0 if etapa_analises() else 1)
    else: sys.exit(0 if rodar_codigos(a) else 1)
