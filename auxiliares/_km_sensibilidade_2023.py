"""Sensibilidade do Kaplan-Meier da 1a Vara ao tratamento da lista de 2023.
Rodar da raiz do projeto: python3 auxiliares/_km_sensibilidade_2023.py
So contagens agregadas; nenhum nome."""
import csv
from collections import defaultdict
L = defaultdict(set)
for r in csv.DictReader(open("data/base_listas.csv", encoding="utf-8")):
    if r["tipo"] == "definitiva": L[(r["vara"], int(r["ano"]))].add(r["pessoa_id"])
v = "Curitiba 1a Vara"
def km(falta):
    pres = lambda p, a: (p in L[(v, a)]) if a not in falta else (p in L[(v, a - 1)] and p in L.get((v, a + 1), set()))
    dur = []
    for a0 in range(2010, 2026):
        if (v, a0) not in L or a0 in falta: continue
        for p in L[(v, a0)] - L.get((v, a0 - 1), set()):
            if (v, a0 - 1) in L and a0 - 1 in falta and p in L.get((v, a0 - 2), set()): continue
            t, a = 1, a0 + 1
            while a <= 2026 and pres(p, a): t += 1; a += 1
            dur.append((t, 0 if a > 2026 else 1))
    S, c = 1.0, {}
    for t in range(1, 17):
        risco = sum(1 for d, e in dur if d >= t); sai = sum(1 for d, e in dur if d == t and e == 1)
        if risco == 0: break
        S *= 1 - sai / risco; c[t] = S
    med = next((t for t, s in c.items() if s <= .5), ">16")
    return len(dur), *(round(100 * c.get(k, 0), 1) for k in (1, 3, 5, 10)), med
print("tratamento entradas apos1 apos3 apos5 apos10 mediana")
print("ponte_2023", *km({2023}))
print("2023_observada", *km(set()))
a, b, c = L[(v, 2022)], L[(v, 2023)], L[(v, 2024)]
print("\nlista 2022:", len(a), "| 2023:", len(b), "| 2024:", len(c))
print("2023 vinda de 2022: %.1f%%" % (100 * len(a & b) / len(b)))
print("2024 vinda de 2023: %.1f%%  | de 2022: %.1f%% | de 2022 e ausente em 2023: %d" % (100 * len(b & c) / len(c), 100 * len(a & c) / len(c), len((a & c) - b)))
