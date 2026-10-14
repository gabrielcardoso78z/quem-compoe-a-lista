#!/usr/bin/env python3
"""Monta as planilhas da 2a rodada (uma por codificador) reaproveitando o montador da 1a rodada."""
import os, shutil
AQUI = os.path.dirname(os.path.abspath(__file__)); PAI = os.path.dirname(AQUI)
src = open(os.path.join(PAI, "montar_planilha.py"), encoding="utf-8").read()
src = src.replace('"amostra_para_codificar.csv"', '"amostra_r2.csv"').replace('"codificacao_manual.xlsx"', '"codificacao_r2.xlsx"')
src = src.replace("COMO CODIFICAR (cerca de 1 hora)", "COMO CODIFICAR, 2a RODADA (cerca de 1 hora a 1h30). Codifique sem consultar a 1a rodada.")
src = src.replace('nao abra o arquivo gabarito_NAO_ENVIAR.csv', 'nao abra os arquivos gabarito_NAO_ENVIAR.csv e gabarito_r2_NAO_ENVIAR.csv')
os.chdir(AQUI); exec(compile(src, "montar", "exec"), {"__name__": "__main__"})
for quem in ("Gabriel", "professor"):
    shutil.copy("codificacao_r2.xlsx", f"codificacao_r2_{quem}.xlsx")
os.remove("codificacao_r2.xlsx"); print("ok: codificacao_r2_Gabriel.xlsx e codificacao_r2_professor.xlsx")
