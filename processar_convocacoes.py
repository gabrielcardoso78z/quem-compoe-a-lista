#!/usr/bin/env python3
"""Reprocessa os editais de convocacao ja baixados (raw_conv/) sem acessar o site."""
import csv, glob, os, re
from coletar_listas import titulo, separar, chave_secreta, pseudonimo
from processar_listas import extrair
from coletar_convocacoes import mes_ano, INSTANCIAS, RAWC, DATA
def main():
    chave = chave_secreta(); docs, ents = [], []
    for arq in sorted(glob.glob(os.path.join(RAWC, "*.html"))):
        did = os.path.basename(arq)[:-5]; inst = did.split("_")[0]; vara = INSTANCIAS.get(inst, "")
        pag = open(arq, encoding="utf-8").read(); tit = titulo(pag); ano, mes = mes_ano(tit)
        itens, formato = extrair(pag)
        tem_lista = formato in ("numerada", "mista")
        n = 0
        if tem_lista:
            ult = 0
            for seq, resto in itens:
                # linha de data do edital ("... de 2025. FULANO, Juiz") nao e jurado (correcao 11/10/2026)
                if 2000 <= int(seq) <= 2035 and int(seq) > ult + 1: continue
                ult = int(seq)
                nome, prof = separar(resto.strip().rstrip(";.,"))
                if len(nome.split()) < 2: continue
                ents.append([did, vara, ano, mes, seq, pseudonimo(nome, chave), prof]); n += 1
        docs.append([did, vara, tit, ano, mes, n, formato if tem_lista else "sem_lista_no_site"])
    with open(os.path.join(DATA, "convocacoes_documentos.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f); w.writerow(["doc_id","vara","titulo","ano","mes","n_jurados","formato"]); w.writerows(docs)
    with open(os.path.join(DATA, "convocacoes.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f); w.writerow(["doc_id","vara","ano","mes","seq","pessoa_id","profissao"]); w.writerows(ents)
    print(f"{len(docs)} editais, {sum(1 for d in docs if d[5])} com lista, {len(ents)} convocacoes")
if __name__ == "__main__": main()
