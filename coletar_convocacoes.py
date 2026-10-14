#!/usr/bin/env python3
"""Coleta os editais de convocacao de jurados (sorteados para cada reuniao) das duas Varas
de Curitiba no site do TJPR, guarda o HTML em raw_conv/ e gera data/convocacoes.csv
com nomes pseudonimizados (mesma chave secreta das listas)."""
import csv, os, re, time, unicodedata
from coletar_listas import baixar, titulo, separar, chave_secreta, pseudonimo, BASE, PAUSA
from processar_listas import extrair

AQUI = os.path.dirname(os.path.abspath(__file__))
RAWC = os.path.join(AQUI, "raw_conv"); os.makedirs(RAWC, exist_ok=True)
DATA = os.path.join(AQUI, "data")
INSTANCIAS = {"s0CT": "Curitiba 1a Vara", "qE2i": "Curitiba 2a Vara"}
MESES = {m: i + 1 for i, m in enumerate(["JANEIRO","FEVEREIRO","MARCO","ABRIL","MAIO","JUNHO","JULHO","AGOSTO","SETEMBRO","OUTUBRO","NOVEMBRO","DEZEMBRO"])}

def sem_acento(t): return unicodedata.normalize("NFKD", t).encode("ascii", "ignore").decode().upper()

def mes_ano(tit):
    t = sem_acento(tit)
    a = re.findall(r"20\d\d", t); m = next((MESES[k] for k in MESES if k in t), None)
    return (int(max(a)) if a else None), m

def listar(inst):
    p = f"_com_liferay_asset_publisher_web_portlet_AssetPublisherPortlet_INSTANCE_{inst}_"
    vistos = {}
    for cur in range(1, 60):
        u = (f"{BASE}/editais-convocacao-jurados?p_p_id=com_liferay_asset_publisher_web_portlet_AssetPublisherPortlet_INSTANCE_{inst}"
             f"&p_p_lifecycle=0&p_p_state=normal&p_p_mode=view&{p}delta=100&p_r_p_resetCur=false&{p}cur={cur}")
        pag = baixar(u); time.sleep(PAUSA)
        if not pag: break
        i = pag.find(f'id="p_p_id{p}"'); bloco = pag[i:] if i >= 0 else pag
        j = bloco.find("portlet-boundary", 200); bloco = bloco[:j] if j > 0 else bloco
        novos = 0
        for href in re.findall(r'href="([^"]*/content/[^"]*)"', bloco):
            href = href.replace("&amp;", "&")
            cam = re.sub(r"\?.*$", "", href); ent = re.search(r"p_r_p_assetEntryId=(\d+)", href)
            if cam not in vistos or (ent and "assetEntryId" not in vistos[cam]):
                if cam not in vistos: novos += 1
                vistos[cam] = cam + (f"?p_r_p_assetEntryId={ent.group(1)}" if ent else "")
        print(f"{INSTANCIAS[inst]}: pagina {cur}, {len(vistos)} editais", flush=True)
        if novos == 0: break
    return list(vistos.values())

def main():
    chave = chave_secreta()
    docs, ents = [], []
    for inst, vara in INSTANCIAS.items():
        urls = listar(inst)
        for k, url in enumerate(urls, 1):
            url = url if url.startswith("http") else BASE + url
            did = inst + "_" + re.sub(r"[^A-Za-z0-9]+", "_", url.split("/content/")[-1].split("?")[0])[:80]
            arq = os.path.join(RAWC, did + ".html")
            if os.path.exists(arq) and os.path.getsize(arq) > 5000:
                pag = open(arq, encoding="utf-8").read()
            else:
                pag = baixar(url); time.sleep(PAUSA)
                if not pag: continue
                open(arq, "w", encoding="utf-8").write(pag)
            tit = titulo(pag); ano, mes = mes_ano(tit)
            itens, formato = extrair(pag)
            n = 0
            for seq, resto in itens:
                nome, prof = separar(resto)
                if len(nome.split()) < 2: continue
                ents.append([did, vara, ano, mes, seq, pseudonimo(nome, chave), prof]); n += 1
            erro = "conteúdo não pôde ser encontrado" in pag
            docs.append([did, vara, tit, ano, mes, n, formato, "erro" if erro else "ok"])
            print(f"[{vara} {k}/{len(urls)}] {ano}-{mes}: {n} jurados  {tit[:60]}", flush=True)
    with open(os.path.join(DATA, "convocacoes_documentos.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f); w.writerow(["doc_id","vara","titulo","ano","mes","n_jurados","formato","status"]); w.writerows(docs)
    with open(os.path.join(DATA, "convocacoes.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f); w.writerow(["doc_id","vara","ano","mes","seq","pessoa_id","profissao"]); w.writerows(ents)
    print(f"\nPronto: {len(docs)} editais, {len(ents)} convocacoes.")

if __name__ == "__main__":
    main()
