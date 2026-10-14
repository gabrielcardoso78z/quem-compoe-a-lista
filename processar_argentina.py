#!/usr/bin/env python3
"""Le as listas principais de jurados da Provincia de Buenos Aires (SCBA, PDF em argentina/raw_ar/),
pseudonimiza e grava data/ar_entradas.csv. Nenhum nome ou documento e gravado.

Formato do PDF: cabecalho "Departamento Judicial X" e, por linha, Tipo Doc. | Documento | Apellido y Nombres | Partido.
O sorteio anual da Provincia e feito sobre as TERMINACOES do DNI (3 ultimos digitos): seis por ano (duas titulares
e quatro complementares; INECIP, 2025). Por isso os 3 ultimos digitos assumem so seis valores em cada lista.
(Correcao de 12/10/2026: a primeira versao deste script supunha que a SCBA mascarava esses digitos.)
Chave da pessoa: DNI completo, pseudonimizado com a mesma chave secreta da pesquisa (pseudo_doc); a terminacao
sorteada e gravada a parte (e informacao publica do sorteio). O texto do PDF fica fora do projeto (~/artxt).

Uso: python3 processar_argentina.py
"""
import csv, glob, hashlib, os, re, subprocess, sys
from collections import Counter
from coletar_listas import pseudonimo, chave_secreta, DATA
import dje_comum as dc

AQUI = os.path.dirname(os.path.abspath(__file__))
RAW = os.path.join(AQUI, "argentina", "raw_ar")
TXT = os.path.expanduser("~/artxt")
LINHA = re.compile(r"^\s*(DNI|LE|LC|CI|PAS|DU|CE)\s+([\d.]+)\s+(.+?)\s{2,}(\S.*?)\s*$")
DEP = re.compile(r"^\s*Departamento Judicial\s+(.+?)\s*$")


def pseudo_doc(texto, chave):
    """Mesma chave e mesmo hash da pesquisa, mas preservando os digitos (pseudonimo() apaga numeros, pois foi feito para nomes)."""
    return hashlib.sha256((chave + "|DOC|" + texto).encode()).hexdigest()[:16]


def texto(pdf):
    os.makedirs(TXT, exist_ok=True)
    out = os.path.join(TXT, os.path.basename(pdf)[:-4] + ".txt")
    if not os.path.exists(out):
        subprocess.run(["pdftotext", "-layout", pdf, out], check=True)
    return open(out, encoding="utf-8", errors="ignore").read().split("\n")


def main():
    chave = chave_secreta()
    linhas, resumo = [], []
    for pdf in sorted(glob.glob(os.path.join(RAW, "lista_*.pdf"))):
        ano = re.search(r"(\d{4})", os.path.basename(pdf)).group(1)
        dep, n, perdidas, sufixos = None, 0, 0, Counter()
        for l in texto(pdf):
            m = DEP.match(l)
            if m: dep = m.group(1); continue
            m = LINHA.match(l)
            if not m:
                if re.search(r"\d{1,2}\.\d{3}\.\d{3}", l): perdidas += 1
                continue
            tipo, doc, nome, partido = m.groups()
            dig = re.sub(r"\D", "", doc)
            sufixos[dig[-3:]] += 1
            nome_n = re.sub(r"\s+", " ", nome).strip().upper()
            prenome = nome_n.split(",", 1)[1].split()[0] if "," in nome_n and nome_n.split(",", 1)[1].split() else ""
            linhas.append([ano, dep, partido.strip().upper(),
                           pseudo_doc(f"{tipo}{dig}", chave),                                  # pessoa (DNI completo)
                           pseudonimo(nome_n, chave),                          # so nome (teste de sensibilidade)
                           dig[-3:],                                                           # terminacao sorteada
                           dc.sexo(prenome) if prenome else "nf"])
            n += 1
        resumo.append((ano, n, perdidas, len(sufixos)))
        print(f"{ano}: {n} entradas, {perdidas} linhas com documento nao lidas, {len(sufixos)} codigos de sufixo distintos", flush=True)
    with open(os.path.join(DATA, "ar_entradas.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f); w.writerow(["ano", "departamento", "partido", "pessoa_id", "id_nome", "terminacao", "sexo_prenome"]); w.writerows(linhas)
    print(f"{len(linhas)} entradas gravadas em data/ar_entradas.csv")


if __name__ == "__main__":
    main()
