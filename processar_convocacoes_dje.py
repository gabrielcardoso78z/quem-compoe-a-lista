#!/usr/bin/env python3
"""Editais de convocacao (sorteio) de jurados no Diario, todas as comarcas exceto Curitiba e Cascavel.

Uso (um bloco de edicoes por chamada, como processar_comarcas_dje.py):
  python3 processar_convocacoes_dje.py --bruto --padrao=2023*   -> data/convocacoes_bruto_2023_{editais,entradas}.csv
  python3 processar_convocacoes_dje.py --juntar                 -> data/convocacoes_{editais,entradas}.csv

Gatilhos: "ficam convocados", "foram sorteados", "sorteou ... jurados", "jurados sorteados". A comarca vem do cabecalho
do edital na mesma coluna (comarca_do_edital, origem "mesma_coluna"); atribuicoes pela coluna anterior sao descartadas
(na conferencia de 12/10/2026, eram editais de comarcas vizinhas). Os sorteados sao a cadeia numerada logo apos o
gatilho, ate o gatilho seguinte; "suplente" nos 200 caracteres anteriores marca o papel. Nomes so pseudonimizados.
Saidas sem nomes: editais (comarca, data_dje, edicao, pagina, sorteados, titulares, suplentes) e entradas
(comarca, data_dje, edicao, pagina, pessoa_id, papel, sexo_prenome)."""
import csv, glob, os, re, sys
import processar_comarcas_dje as pc
import dje_comum as dc
from coletar_listas import separar, pseudonimo, chave_secreta, DATA

TRIG = re.compile(r"(?i)ficam?\s+convocad|foram\s+sorteados|sorteou[^.]{0,60}jurad|jurados?\s+sorteados")
# fim do ultimo nome de um bloco: ponto e virgula, ou ponto seguido de nova frase do edital
FIM_FRASE = re.compile(r"\s*;|\.\s+(?=(?:ficam?|dado|intime\w*|publique\w*|cumpra\w*|nada|ainda|visando|considerando|sendo|tendo|e,|e\s+para|para|os|as|o|a|curitiba)\b|[A-Z\u00c0-\u00da][a-z\u00e0-\u00fa]+,\s*\d)|\s+(?=(?-i:Ainda|Visando|Considerando|Ficam?|Dado|Nada|Intime|Publique)\b)", re.I)
CAB_E = ["comarca", "data_dje", "edicao", "pagina", "sorteados", "titulares", "suplentes"]
CAB_N = ["comarca", "data_dje", "edicao", "pagina", "pessoa_id", "papel", "sexo_prenome"]


def main():
    args = sys.argv[1:]
    if "--juntar" in args:
        for nome, cab in (("editais", CAB_E), ("entradas", CAB_N)):
            rows = []
            for arq in sorted(glob.glob(os.path.join(DATA, f"convocacoes_bruto_*_{nome}.csv"))):
                rows += list(csv.reader(open(arq, encoding="utf-8")))[1:]
            vist = set(); rows = [r for r in rows if not (tuple(r) in vist or vist.add(tuple(r)))]
            with open(os.path.join(DATA, f"convocacoes_{nome}.csv"), "w", newline="", encoding="utf-8") as fo:
                w = csv.writer(fo); w.writerow(cab); w.writerows(rows)
            print(nome, len(rows))
        return
    padrao = next((a.split("=", 1)[1] for a in args if a.startswith("--padrao=")), "202*")
    chave = chave_secreta()
    editais, entradas = [], []
    for f in dc.arquivos(padrao, dc.TXT_LAYOUT):
        texto = open(f, encoding="utf-8", errors="ignore").read()
        pags = texto.split("\f")
        cand = [k for k, pg in enumerate(pags) if TRIG.search(pg) and re.search(r"(?i)j[uú]ri", pg)]
        if not cand: continue
        ini, ac = [], 0
        for pg in pags: ini.append(ac); ac += pg.count("\n")
        data_dje, ed = dc.edicao(f), os.path.basename(f)[:-4].split("_ed")[-1]
        for k in cand:
            T = pc.segmentos(texto, ini[k] + 1, max_pag=4)
            seps = [q for q, ch in enumerate(T) if ch == pc.SEP]
            fim_pag = seps[1] if len(seps) > 1 else len(T)
            trig = [m for m in TRIG.finditer(T) if m.start() < fim_pag]
            por_com = {}
            anterior = None        # (comarca, posicao) do ultimo gatilho aceito nesta pagina
            for n_, m in enumerate(trig):
                i0 = m.start()
                com, origem = pc.comarca_do_edital(T, i0)
                # gatilho dos suplentes no mesmo edital ("a MM. Juiza sorteou, como SUPLENTES, os Jurados: 1. ..."), cuja
                # coluna nao traz o cabecalho: herda a comarca do gatilho anterior, ate 4.000 caracteres antes (F9)
                # O mesmo vale para o "ficam convocados" logo depois do "foram sorteados" do mesmo edital (ate 1.500
                # caracteres). So herda se a comarca achada (coluna anterior) e a mesma ou se nenhuma foi achada.
                if (com == "?" or origem != "mesma_coluna") and anterior and com in ("?", anterior[0]) and (
                        i0 - anterior[1] < 1500 or (i0 - anterior[1] < 4000 and re.search(r"(?i)suplente", T[i0:i0 + 120]))):
                    com, origem = anterior[0], "mesma_coluna"
                if com == "?" or origem != "mesma_coluna": continue
                anterior = (com, i0)
                if pc.nrm(com) in ("CURITIBA", "CASCAVEL"): continue
                prox = re.search(TRIG.pattern + "|" + pc.GATILHO.replace("(?i)", ""), T[i0 + 30:], re.I)
                lim = i0 + 30 + prox.start() if prox else None
                lista, _ = pc.extrair_lista(T, i0, lim, corta_no_limite=True)
                if len(lista) < 3: lista, _ = pc.extrair_lista(T, i0, lim, relax=True, corta_no_limite=True)
                papel = "suplente" if re.search(r"(?i)suplente", T[max(0, i0 - 200):i0 + 120]) else "titular"
                # suplentes em nova cadeia "1., 2., ..." depois dos titulares, sem novo gatilho ("Ficam, ainda, como
                # suplentes: 1. ..."): lidos como suplentes (auditoria 12/10/2026, F9)
                lista = [(n, t, papel) for n, t in lista]
                if lista and papel == "titular":
                    _, fim_t = pc.extrair_lista(T, i0, lim, corta_no_limite=True)
                    lim2 = lim if lim else min(len(T), fim_t + 3000)
                    # o gatilho seguinte e o proprio "sorteou, como SUPLENTES, os Jurados: 1. ..." deste edital, as vezes
                    # na pagina seguinte, onde a comarca nao e achada (Imbituva 3277): busca os suplentes ate o gatilho depois dele
                    if lim and re.search(r"(?i)suplente", T[lim:lim + 120]):
                        p2 = re.search(TRIG.pattern + "|" + pc.GATILHO.replace("(?i)", ""), T[lim + 30:], re.I)
                        lim2 = lim + 30 + p2.start() if p2 else min(len(T), lim + 3000)
                    ms = re.search(r"(?i)suplentes?", T[fim_t:lim2])
                    if ms:
                        l2, _ = pc.extrair_lista(T, fim_t + ms.start(), lim2, corta_no_limite=True)
                        if not (l2 and l2[0][0] <= 3):   # numeracao continuada: a cadeia comeca no numero seguinte ao ultimo titular
                            l3, _ = pc.extrair_lista(T, fim_t + ms.start(), lim2, relax=True, corta_no_limite=True)
                            if l3 and l3[0][0] == lista[-1][0] + 1: l2 = l3
                        # cadeia propria (1., 2., ...) ou continuacao da numeracao dos titulares (Ipora 3457: 26 a 35)
                        if l2 and (l2[0][0] <= 3 or l2[0][0] == lista[-1][0] + 1):
                            lista += [(n, t, "suplente") for n, t in l2]
                # titular e suplente na mesma numeracao (Ipora: 26 a 35 depois do titulo SUPLENTES): a partir da entrada
                # que traz a palavra, os seguintes sao suplentes; e o nome da ultima de cada bloco e cortado no fim da frase
                # ("...MARCON. Ficam, ainda...", "...;  SUPLENTES"): auditoria 12/10/2026, F3 nas convocacoes
                saida, vira = [], False
                for kk, (n, t, pp) in enumerate(lista):
                    if vira and pp == "titular": pp = "suplente"
                    corte = re.search(r"(?i)\bsuplentes?\b", t)
                    if corte: t, vira = t[:corte.start()], True
                    ult = kk + 1 == len(lista) or lista[kk + 1][2] != pp or corte
                    if ult: t = FIM_FRASE.split(t)[0]
                    saida.append((n, t.strip(" .;,:"), pp))
                d = por_com.setdefault(com, {})
                for _, t, papel in saida:
                    nome, _p = separar(pc.reparar(t))
                    if len(nome.split()) < 2: continue
                    pid = pseudonimo(nome, chave)
                    if pid in d and d[pid][0] == "titular": continue
                    d[pid] = (papel, dc.sexo(nome))
            for com, d in por_com.items():
                if not d: continue
                tit = sum(1 for p, _ in d.values() if p == "titular")
                editais.append([com, data_dje, ed, k + 1, len(d), tit, len(d) - tit])
                for pid, (p, sx) in d.items():
                    entradas.append([com, data_dje, ed, k + 1, pid, p, sx])
    tag = padrao.strip("*").replace("-", "") or "tudo"
    for nome, linhas, cab in (("editais", editais, CAB_E), ("entradas", entradas, CAB_N)):
        with open(os.path.join(DATA, f"convocacoes_bruto_{tag}_{nome}.csv"), "w", newline="", encoding="utf-8") as fo:
            w = csv.writer(fo); w.writerow(cab); w.writerows(linhas)
    print(f"convocacoes {tag}: {len(editais)} editais, {len(entradas)} sorteados")


if __name__ == "__main__":
    main()
