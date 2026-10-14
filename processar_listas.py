#!/usr/bin/env python3
"""Reprocessa os HTML ja baixados em raw/ (sem acessar o site) e gera data/*.csv.
Nomes sao pseudonimizados com a mesma chave secreta da coleta."""
import csv, glob, os, re
from coletar_listas import (texto_do_artigo, titulo, separar, chave_secreta, pseudonimo,
                            classificar, ano_ref, ENTRADA, DATA, RAW)

VARAS = {"s0CT": "Curitiba 1a Vara", "M4kc": "Curitiba 2a Vara", "5WKukPZuHBx9": "Cascavel"}
COLADO = re.compile(r"\s*(?=(?<![\d])\d{1,4}\.\s*[A-ZÀ-Ú])")   # quebra "12.FULANO - X 13.BELTRANO"
CABECALHO = re.compile(r"EDITAL|LISTA|JUR[ÁA]DO|JUIZ|JU[ÍI]ZA|CURITIBA|ART\.|C[ÓO]DIGO|TRIBUNAL|PODER|ESTADO|VARA|SECRETARIA|DIGITALMENTE", re.I)

def linhas_entrada(linhas):
    out = []
    for l in linhas:
        out.extend(p for p in COLADO.split(l) if p.strip())
    return out

def extrair(pag):
    marcas = [m.start() for m in re.finditer("journal-content-article", pag)] or [0]
    blocos = [pag[a:b] for a, b in zip(marcas, marcas[1:] + [len(pag)])]
    cands = [linhas_entrada(texto_do_artigo(b)) for b in blocos]
    linhas = max(cands, key=lambda ls: sum(1 for l in ls if ENTRADA.match(l)))
    numeradas = [(m.group(1), m.group(2)) for m in map(ENTRADA.match, linhas) if m]
    if len(numeradas) >= 50:
        primeiro = min(int(a) for a, _ in numeradas)
        if primeiro > 1:   # inicio da lista sem numeracao (ex.: 1 a 90 sem numero, depois "91.")
            i0 = next(i for i, l in enumerate(linhas) if ENTRADA.match(l))
            antes = [l for l in linhas[:i0] if len(l) <= 140 and not CABECALHO.search(separar(l)[0])
                     and not re.search(r"\d", separar(l)[0]) and 2 <= len(separar(l)[0].split()) <= 9]
            if len(antes) >= primeiro - 1:
                antes = antes[-(primeiro - 1):]
                return [(str(i + 1), l) for i, l in enumerate(antes)] + numeradas, "mista"
        return numeradas, "numerada"
    # lista sem numeracao: "NOME - PROFISSAO" (ou so NOME) linha a linha, apos o cabecalho
    sem = []
    for l in max(cands, key=len):
        if CABECALHO.search(l) or re.search(r"\d", l) or len(l) > 140:
            continue
        nome, prof = separar(l)
        if 2 <= len(nome.split()) <= 9:
            sem.append((str(len(sem) + 1), l))
    return sem, "sem_numeracao"

def main():
    chave = chave_secreta()
    docs, entradas, sobras = [], [], []
    for arq in sorted(glob.glob(os.path.join(RAW, "*.html"))):
        did = os.path.basename(arq)[:-5]
        pub = next((k for k in VARAS if did.startswith(k + "_")), "")
        pag = open(arq, encoding="utf-8").read()
        tit = titulo(pag)
        erro = "conteúdo não pôde ser encontrado" in pag
        itens, formato = extrair(pag)
        vistos, n, seqs = set(), 0, []
        ult = 0
        for seq, resto in itens:
            if 2000 <= int(seq) <= 2035 and int(seq) > ult + 1:   # data do edital ("... de 2015. FULANO, Juiz"), nao entrada
                continue
            ult = int(seq)
            nome, prof = separar(resto)
            if len(nome.split()) < 2:
                sobras.append([did, seq, len(resto)]); continue
            if seq in vistos: continue
            vistos.add(seq); n += 1; seqs.append(int(seq))
            entradas.append([did, VARAS.get(pub, ""), classificar(tit), ano_ref(tit), seq,
                             pseudonimo(nome, chave), prof])
        lac = sum(1 for a, b in zip(seqs, seqs[1:]) if b != a + 1)
        docs.append([did, pub, VARAS.get(pub, ""), tit, classificar(tit), ano_ref(tit), n, lac,
                     formato, "erro" if erro else "ok"])
    with open(os.path.join(DATA, "documentos.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f); w.writerow(["doc_id","publisher","vara","titulo","tipo","ano","n_entradas","quebras_sequencia","formato","status"]); w.writerows(docs)
    with open(os.path.join(DATA, "entradas.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f); w.writerow(["doc_id","vara","tipo","ano","seq","pessoa_id","profissao"]); w.writerows(entradas)
    with open(os.path.join(DATA, "linhas_descartadas.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f); w.writerow(["doc_id","seq","tamanho_linha"]); w.writerows(sobras)
    print(f"{len(docs)} publicacoes, {len(entradas)} entradas")

if __name__ == "__main__":
    main()
