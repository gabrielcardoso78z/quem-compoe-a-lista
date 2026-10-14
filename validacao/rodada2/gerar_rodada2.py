#!/usr/bin/env python3
"""Segunda rodada de validacao da classificacao COD (14/10/2026), pedida pelos pareceres externos.
Regras CONGELADAS: o hash de codificar_profissoes.py e gravado em REGRAS_CONGELADAS.txt e conferido por calcular_kappa_r2.py.
Amostra NOVA: 200 entradas das listas definitivas 2014-2026 com profissao informada, semente 20261014 (a 1a rodada usou 20261011).
So a profissao vai para a planilha; nenhum nome."""
import csv, hashlib, os, random, sys
AQUI = os.path.dirname(os.path.abspath(__file__)); BASE = os.path.dirname(os.path.dirname(AQUI))
sys.path.insert(0, BASE); sys.path.insert(0, os.path.dirname(AQUI))
from codificar_profissoes import classificar
h = hashlib.sha256(open(os.path.join(BASE, "codificar_profissoes.py"), "rb").read()).hexdigest()
ents = [r["profissao"] for r in csv.DictReader(open(os.path.join(BASE, "data/base_listas.csv"), encoding="utf-8"))
        if r["tipo"] == "definitiva" and 2014 <= int(r["ano"]) <= 2026 and classificar(r["profissao"])[0] != "Nao informada"]
random.seed(20261014); amostra = random.sample(ents, 200)
r1 = {r["profissao (como publicada)"].strip().upper() for r in csv.DictReader(open(os.path.join(os.path.dirname(AQUI), "amostra_para_codificar.csv"), encoding="utf-8-sig"), delimiter=";")}
with open(os.path.join(AQUI, "amostra_r2.csv"), "w", newline="", encoding="utf-8-sig") as f:
    w = csv.writer(f, delimiter=";"); w.writerow(["id", "profissao (como publicada)"])
    for i, p in enumerate(amostra, 1): w.writerow([i, p])
with open(os.path.join(AQUI, "gabarito_r2_NAO_ENVIAR.csv"), "w", newline="", encoding="utf-8-sig") as f:
    w = csv.writer(f, delimiter=";"); w.writerow(["id", "categoria_script", "grafia_ja_na_rodada1"])
    for i, p in enumerate(amostra, 1): w.writerow([i, classificar(p)[0], "sim" if p.strip().upper() in r1 else "nao"])
with open(os.path.join(AQUI, "REGRAS_CONGELADAS.txt"), "w") as f:
    f.write(f"codificar_profissoes.py sha256 {h}\nsemente 20261014; universo {len(ents)} entradas; gerado em 14/10/2026\n")
print("ok:", len(amostra), "entradas;", sum(p.strip().upper() in r1 for p in amostra), "grafias ja vistas na rodada 1; hash", h[:12])
