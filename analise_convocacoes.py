#!/usr/bin/env python3
"""Curitiba (1a e 2a Varas): quem e sorteado, repeticao e permanencia dos sorteados (secao 4.4).
Le data/convocacoes.csv (processar_convocacoes.py) e data/base_listas.csv. Saida: data/saida_analise_convocacoes.txt
(via rodar_tudo). So agregados.

RECONSTRUIDO em 12/10/2026: o arquivo original foi sobrescrito por engano (o script do estado, hoje
analise_convocacoes_estado.py, foi gravado com este nome). A reconstrucao reproduz a saida anterior (copia de 12/10/2026,
01:08), conferida linha a linha; ver REFERENCIAS_E_FONTES.md.
Definicoes: lista do ano = lista definitiva da Vara para o ano; "% da lista sorteada" = sorteados do ano que estao na
lista do ano / tamanho da lista; habitual = pessoa presente em 5 ou mais listas definitivas da Vara de 2014 em diante;
"sorteados que seguem" = sorteados do ano presentes na lista definitiva do ano seguinte."""
import csv, os
from collections import Counter, defaultdict
D = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
C = [r for r in csv.DictReader(open(os.path.join(D, "convocacoes.csv"), encoding="utf-8")) if r["ano"].isdigit()]
B = list(csv.DictReader(open(os.path.join(D, "base_listas.csv"), encoding="utf-8")))
for v in ("Curitiba 1a Vara", "Curitiba 2a Vara"):
    L = defaultdict(set)
    for r in B:
        if r["vara"] == v and r["tipo"] == "definitiva": L[int(r["ano"])].add(r["pessoa_id"])
    anos_lista = Counter(p for a, ps in L.items() if a >= 2014 for p in ps)
    hab = lambda p: anos_lista[p] >= 5
    S = defaultdict(list)
    for r in C:
        if r["vara"] == v: S[int(r["ano"])].append(r["pessoa_id"])
    print(f"=== {v} ===")
    todos = defaultdict(set)
    for y in range(2015, 2027):
        if not S.get(y): continue
        s = set(S[y]); l = L.get(y, set())
        for p in s: todos[p].add(y)
        rep = sum(1 for p, n in Counter(S[y]).items() if n >= 2)
        linha = (f"{y}: {len(S[y]):4d} convocacoes, {len(s):4d} pessoas | {100*len(s & l)/len(l):4.1f}% da lista foi sorteada | "
                 f"convocadas 2x+ no ano: {rep:3d} | habituais(5+ anos de lista): {100*sum(map(hab, s))/len(s):4.1f}% dos sorteados x "
                 f"{100*sum(map(hab, l))/len(l):4.1f}% da lista")
        if L.get(y + 1): linha += f" | sorteados que seguem na lista de {y+1}: {100*len(s & L[y+1])/len(s):4.1f}%"
        print(linha)
    dist = Counter(len(a) for a in todos.values())
    print(f"Total: {len(todos)} pessoas sorteadas em 2015-2026; anos com sorteio por pessoa: "
          + ", ".join(f"{k} ano(s): {dist[k]}" for k in sorted(dist)))
    # pessoa-ano: sorteados distintos de cada ano e nomes das listas dos mesmos anos, somados
    ys = [y for y in range(2015, 2027) if S.get(y)]
    hs = sum(hab(p) for y in ys for p in set(S[y])) / sum(len(set(S[y])) for y in ys)
    hl = sum(hab(p) for y in ys for p in L.get(y, ())) / sum(len(L.get(y, ())) for y in ys)
    print(f"Habituais: {100*hs:.1f}% dos sorteados x {100*hl:.1f}% das listas")
    if v == "Curitiba 1a Vara": print()
