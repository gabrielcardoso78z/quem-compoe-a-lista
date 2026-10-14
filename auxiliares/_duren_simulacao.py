"""Teste de Duren/Castaneda e simulação do sorteio argentino para Curitiba (13/10/2026).
Entradas: data/aprof_serie_anual.csv (percentuais por Vara-ano, já agregados), data/resultado_perfil.csv
(grupos COD agregados), data/resultado_tse.csv (eleitorado 18-69). Nenhum dado pessoal.
n_classificado ~ n * pct_com_profissao * (1 - estudantes - aposentados - do lar): aproximação conservadora."""
import csv, math
P2, P789 = 24.0, 9.6+6.2+9.8   # Censo 2022, Curitiba (SIDRA 10264): grupo 2; grupos 7+8+9
print("== Disparidades (listas agregadas, resultado_perfil.csv) ==")
perf = {}
for r in csv.DictReader(open("data/resultado_perfil.csv", encoding="utf-8")):
    perf.setdefault(r["vara"], {})[r["grupo_COD"][0]] = (float(r["pct_lista"]), float(r["pct_censo2022"]))
for v, g in perf.items():
    for nome, ks in [("grupo 9 (elementares)", "9"), ("grupo 7 (operarios)", "7"), ("grupos 7-9", "789"), ("grupo 2 (sup.)", "2")]:
        l = sum(g[k][0] for k in ks); p = sum(g[k][1] for k in ks)
        print(f"{v} | {nome}: lista {l:.1f} pop {p:.1f} | abs {p-l:+.1f} pp | comp {(p-l)/p*100:+.1f}%")
print("== Desvios-padrão por Vara-ano (Castaneda) ==")
for r in csv.DictReader(open("data/aprof_serie_anual.csv", encoding="utf-8")):
    if not r["pct_grupo2"] or not r["pct_com_profissao"]: continue
    n = int(r["n"]); f = float(r["pct_com_profissao"])/100
    out = sum(float(r[k] or 0) for k in ["pct_estudantes","pct_aposentados","pct_do_lar"])/100
    nc = n*f*(1-out)
    if nc < 100: continue
    z2 = (float(r["pct_grupo2"])-P2)/100/math.sqrt(P2/100*(1-P2/100)/nc)
    z7 = (float(r["pct_grupos789"])-P789)/100/math.sqrt(P789/100*(1-P789/100)/nc)
    print(f"{r['vara']} {r['ano']}: n_class~{nc:.0f} g2 {r['pct_grupo2']} z={z2:+.1f} | g789 {r['pct_grupos789']} z={z7:+.1f}")
print("== Simulação do sorteio argentino (1 por mil eleitores 18-69) ==")
tse = {(r["municipio"],r["universo"],r["categoria"]):(int(r["eleitores"]),float(r["pct"])) for r in csv.DictReader(open("data/resultado_tse.csv",encoding="utf-8"))}
tot = sum(v[0] for k,v in tse.items() if k[0]=="Curitiba" and k[1]=="18-69" and k[2] in ("FEMININO","MASCULINO"))
n = round(tot/1000); print("eleitores 18-69:", tot, "-> lista", n)
for cat in ["SUPERIOR COMPLETO","SUPERIOR INCOMPLETO","ENSINO MEDIO COMPLETO","ENSINO FUNDAMENTAL INCOMPLETO"]:
    p = tse[("Curitiba","18-69",cat)][1]/100; se = math.sqrt(p*(1-p)/n)
    print(f"  {cat}: esperado {p*100:.1f}% (IC95 {100*(p-1.96*se):.1f}-{100*(p+1.96*se):.1f})")
