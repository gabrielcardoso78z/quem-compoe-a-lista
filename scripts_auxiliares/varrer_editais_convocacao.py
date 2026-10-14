#!/usr/bin/env python3
"""Varre o Diario (um ano por chamada: python3 scripts_auxiliares/varrer_editais_convocacao.py 2025) atras de editais de
convocacao/sorteio de jurados (ficam convocados, foram sorteados, sorteou ... jurados) e atribui a comarca pelo cabecalho
(comarca_do_edital). Grava _to_delete/conv2_<ano>.json: comarca -> [(edicao, pagina, origem, marcadores numerados)].
So contagens, sem nomes."""
import re,glob,os,sys,json,importlib.util,collections; sys.path.insert(0,".")
sys.argv=[sys.argv[0]]+sys.argv[1:]
ano=sys.argv[1]; sys.argv=["x"]
spec=importlib.util.spec_from_file_location("pc","processar_comarcas_dje.py"); pc=importlib.util.module_from_spec(spec); spec.loader.exec_module(pc)
TRIG=re.compile(r"(?i)ficam?\s+convocad|foram\s+sorteados|sorteou[^.]{0,60}jurad|jurados?\s+sorteados")
res=collections.defaultdict(list)
for f in sorted(glob.glob(os.path.expanduser(f"~/djetxt/{ano}*.txt"))):
    texto=open(f,encoding="utf-8",errors="ignore").read()
    pags=texto.split("\f")
    cand=[k for k,pg in enumerate(pags) if TRIG.search(pg) and re.search(r"(?i)j[uú]ri",pg)]
    if not cand: continue
    ini,ac=[],0
    for pg in pags: ini.append(ac); ac+=pg.count("\n")
    vistos=set()
    for k in cand:
        T=pc.segmentos(texto,ini[k]+1,max_pag=1)
        for m in TRIG.finditer(T):
            c,o=pc.comarca_do_edital(T,m.start())
            if c=="?" : continue
            key=(c,k)
            if key in vistos: continue
            vistos.add(key)
            # sorteados: marcadores numerados ate 600 chars depois
            nums=len(pc.MARC.findall(T[m.start():m.start()+3000]))
            res[c].append((os.path.basename(f)[:21],k+1,o,nums))
json.dump(res,open(f"_to_delete/conv2_{ano}.json","w"))
print(ano,len(res),"comarcas;",sum(len(v) for v in res.values()),"editais")
