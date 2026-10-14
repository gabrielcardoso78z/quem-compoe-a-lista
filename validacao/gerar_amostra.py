#!/usr/bin/env python3
"""Amostra para o segundo codificador (validacao da classificacao COD).
Sorteia 200 ENTRADAS (nao grafias) das listas definitivas 2014-2026 com profissao informada,
semente fixa, e grava duas planilhas: uma para o colega (sem a nossa categoria) e o gabarito."""
import csv, random, sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from codificar_profissoes import classificar
AQUI = os.path.dirname(os.path.abspath(__file__)); BASE = os.path.dirname(AQUI)
ents = [r["profissao"] for r in csv.DictReader(open(os.path.join(BASE, "data/base_listas.csv"), encoding="utf-8"))
        if r["tipo"] == "definitiva" and 2014 <= int(r["ano"]) <= 2026 and classificar(r["profissao"])[0] != "Nao informada"]
random.seed(20261011); amostra = random.sample(ents, 200)
CATS = ["0 Forcas armadas, policiais e bombeiros militares", "1 Diretores e gerentes", "2 Profissionais das ciencias e intelectuais",
        "3 Tecnicos e profissionais de nivel medio", "4 Trabalhadores de apoio administrativo", "5 Trabalhadores dos servicos e vendedores",
        "6 Agropecuaria", "7 Operarios e artesaos", "8 Operadores de maquinas e montadores", "9 Ocupacoes elementares",
        "Estudante ou estagiario", "Aposentado", "Do lar", "Desempregado", "Servidor publico sem ocupacao informada",
        "Empregado sem ocupacao informada", "Outros ou nao classificado"]
with open(os.path.join(AQUI, "amostra_para_codificar.csv"), "w", newline="", encoding="utf-8-sig") as f:
    w = csv.writer(f, delimiter=";"); w.writerow(["id", "profissao (como publicada)", "categoria (escolha uma da aba de categorias)"])
    for i, p in enumerate(amostra, 1): w.writerow([i, p, ""])
with open(os.path.join(AQUI, "categorias.csv"), "w", newline="", encoding="utf-8-sig") as f:
    w = csv.writer(f, delimiter=";"); w.writerow(["categoria"]); [w.writerow([c]) for c in CATS]
with open(os.path.join(AQUI, "gabarito_NAO_ENVIAR.csv"), "w", newline="", encoding="utf-8-sig") as f:
    w = csv.writer(f, delimiter=";"); w.writerow(["id", "categoria_script"])
    for i, p in enumerate(amostra, 1): w.writerow([i, classificar(p)[0]])
print("ok: 200 entradas")
