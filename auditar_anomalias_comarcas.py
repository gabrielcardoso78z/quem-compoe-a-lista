#!/usr/bin/env python3
"""Lista os editais com sinal de problema por comarca (tamanho atipico, comeco fora do 1, numeracao incompleta,
entradas invalidas, falha na verificacao, carater ?, atribuicao fraca). So contagens, sem nomes."""
import csv,collections,statistics
E=list(csv.DictReader(open("data/comarcas_pr_editais.csv",encoding="utf-8")))
N=list(csv.DictReader(open("data/comarcas_pr_entradas.csv",encoding="utf-8")))
V={(v["comarca"],v["edicao"],v["tipo"],v["ano"]):v for v in csv.DictReader(open("data/verificacao_comarcas_listas.csv",encoding="utf-8"))}
mn=collections.defaultdict(lambda:10**9)
for r in N: k=(r["comarca"],r["edicao"],r["tipo"],r["ano"]); mn[k]=min(mn[k],int(r["seq"]))
por=collections.defaultdict(list)
for e in E:
    if e["comarca"]!="?": por[e["comarca"]].append(e)
out=[]
for c,es in sorted(por.items()):
    tam=[int(e["validas"]) for e in es if int(e["validas"] or 0)>=20]
    med=statistics.median(tam) if tam else 0
    for e in sorted(es,key=lambda e:e["data_dje"]):
        k=(c,e["edicao"],e["tipo"],e["ano"]); v=V.get(k)
        num=int(e["numeradas"] or 0); ult=int(e["ultimo_numero"] or 0); val=int(e["validas"] or 0)
        prob=[]
        if num<20: prob.append("sem_lista(%d)"%num)
        else:
            if med and (val<0.6*med or val>1.6*med): prob.append("tamanho %d vs med %d"%(val,med))
            if mn[k]>1: prob.append("comeca %d"%mn[k])
            if ult and num<0.95*ult: prob.append("num %d/%d"%(num,ult))
            if num-val>max(3,0.03*num): prob.append("invalidas %d"%(num-val))
            if v and v["falhas"]!="ok": prob.append(v["falhas"])
        if e["tipo"]=="?": prob.append("tipo?")
        if e["confianca"] in ("diverge","coluna_anterior","nenhuma","lista_nao_extraida_conflito"): prob.append(e["confianca"])
        if prob: out.append((c,e["data_dje"],e["edicao"],e["tipo"],e["ano"],val,"; ".join(prob)))
print(len(out),"editais com sinal, em",len({o[0] for o in out}),"comarcas")
for o in out: print(" | ".join(map(str,o)))
