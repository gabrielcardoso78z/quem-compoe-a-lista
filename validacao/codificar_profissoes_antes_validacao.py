#!/usr/bin/env python3
"""Classificacao automatica das profissoes (texto livre) em grandes grupos da CBO 2002,
com marcacoes a parte (estudante, aposentado, do lar, servidor publico).
Gera codificacao_profissoes.csv para revisao humana (abre no Excel)."""
import csv, re, unicodedata
from collections import Counter

def norm(t):
    t = unicodedata.normalize("NFKD", t).encode("ascii", "ignore").decode().upper()
    t = re.sub(r"\(A\)|\(O\)|/A\b|/O\b", "", t)
    return re.sub(r"\s+", " ", re.sub(r"[^A-Z0-9 ]", " ", t)).strip()

# (categoria, regex) na ordem de prioridade; a primeira que casar vence
REGRAS = [  # alinhadas aos grandes grupos da COD (Censo 2022); a primeira que casar vence
    ("Nao informada", r"^(NAO INFORMAD|PROFISSAO NAO INFORMAD|NAO CONSTA|SEM PROFISSAO|N I$)|^$"),
    ("Estudante ou estagiario", r"\bJOVEM APRENDIZ|\bMENOR APRENDIZ|\bAPRENDIZ$|\bESTUDANTE|\bESTUDANDE|\bESTAGIARI|\bBOLSISTA|\bACADEMIC|\bUNIVERSITARI"),
    ("Aposentado", r"\bAPOSENTAD|\bINATIV|\bPENSIONIST|\bRESERVA REMUNERADA|\bDA RESERVA\b|\bREFORMAD"),
    ("Do lar", r"\bDO LAR\b|\bDONA DE CASA|\bPRENDAS DOMESTICAS"),
    ("Desempregado", r"\bDESEMPREGAD|\bSEM OCUPACAO"),
    ("0 Forcas armadas, policiais e bombeiros militares", r"\bMILITAR\b|\bPOLICIAL MILITAR|\bBOMBEIRO MILITAR|\bSARGENTO|\bTENENTE|\bCAPITAO|\bSOLDADO\b|\bCABO\b|\bMARINHA|\bAERONAUTICA|\bEXERCITO"),
    ("1 Diretores e gerentes", r"EMPRESARI|\bINDUSTRIAL$|\bCAPITALISTA|\bINVESTIDOR|\bGERENTE|\bDIRETOR|\bDIRIGENTE|\bSUPERINTENDENTE|\bPROPRIETARI|\bSOCIO|\bEMPREENDEDOR|\bCOORDENADOR|\bSUPERVISOR|\bENCARREGADO"),
    ("2 Profissionais das ciencias e intelectuais", r"\bADVOGAD|\bBACHAREL|\bASSESSOR|\bLOCUTOR|\bRADIALISTA|\bCONSULTOR TRIBUTARI|\bWEB DESIGN|\bENGENHEIR|\bENG\b|\bMEDIC[OA]\b|\bDENTISTA|\bODONTOLOG|\bPROFESSOR|\bDOCENTE|\bPEDAGOG|\bPSICO|\bECONOMISTA|\bCONTADOR|\bCONTABILISTA|\bARQUITET|\bANALISTA|\bADMINISTRADOR|\bADMISTRADOR|\bFARMACEUTIC|\bNUTRICIONIST|\bFISIOTERAPEUT|\bTERAPEUTA|\bENFERMEIR[OA]\b|\bASSISTENTE SOCIAL|\bJORNALISTA|\bBIOLOG|\bQUIMIC|\bFISIC[OA]\b|\bVETERINARI|\bBIBLIOTECARI|\bPUBLICITARI|\bDESIGNER|\bPROGRAMADOR|\bSOCIOLOG|\bHISTORIADOR|\bGEOGRAF|\bFONOAUDIOLOG|\bAUDITOR|\bPROCURADOR|\bDELEGADO|\bJUIZ|\bPROMOTOR\b(?! DE VENDAS)|\bDEFENSOR|\bTEOLOG|\bPASTOR|\bSACERDOTE|\bMUSIC|\bARTISTA|\bATOR\b|\bATRIZ|\bCANTOR|\bBAILARIN|\bCOREOGRAF|\bESCRITOR|\bREDATOR|\bRELACOES PUBLICAS|\bESTATISTIC|\bMATEMATIC|\bBIOMEDIC|\bGEOLOG|\bAGRONOM|\bZOOTECNIST|\bCIENTISTA|\bPESQUISADOR|\bTRADUTOR|\bTURISMOLOG|\bSECRETARIO EXECUTIVO|\bOFICIAL DE JUSTICA|\bESCRIVAO"),
    ("3 Tecnicos e profissionais de nivel medio", r"\bTECNIC|\bTEC\b|\bTECNOLOG|\bAUXILIAR DE ENFERMAGEM|\bAUX DE ENFERMAGEM|\bAUXILIAR DE LABORATORIO|\bAUXILIAR DE FARMACIA|\bINSTRUMENTADOR|\bMASSAGISTA|\bPODOLOG|\bDESENHISTA|\bINSPETOR|\bAGENTE DE SAUDE|\bCORRETOR|\bREPRESENTANTE COMERCIAL|\bFOTOGRAF|\bPARAMEDIC|\bSOCORRISTA|\bINSTRUTOR|\bEDUCADOR|\bTRANSACOES IMOBILIARIAS|\bAGENTE DE VIAGEM|\bCOMPRADOR|\bPROTETICO|\bDECORADOR|\bPRODUTOR CULTURAL|\bORCAMENTISTA|\bVISTORIADOR|\bDESPACHANTE|\bPOLICIAL CIVIL|\bINVESTIGADOR|\bDETETIVE"),
    ("4 Trabalhadores de apoio administrativo", r"\bASSISTENTE ADMINISTRATIV|\bAUXILIAR ADM|\bAUX ADM|\bADMINISTRATIV[OA]$|\bAUXILIAR JURIDIC|\bASSI?S?TENTE JURIDIC|\bAUXILIAR DE CARTORIO|\bESCREVENTE|\bCARTEIRO|\bDIGITADOR|\bSECURITARI|\bTELEATENDENTE|\bCUSTOMER SERVICE|\bOFICIAL JUDICIARI|\bAGENTE ADMINISTRATIV|\bAUXILIAR DE ESCRITORIO|\bESCRITURARI|\bSECRETARI|\bRECEPCIONIST|\bTELEFONIST|\bBANCARI|\bCAIXA\b|\bDATILOGRAF|\bAUXILIAR CONTABIL|\bAUXILIAR DE CONTABILIDADE|\bOPERADOR DE TELEMARKETING|\bATENDENTE|\bTECNICO JUDICIARI|\bAUXILIAR JUDICIARI|\bASSISTENTE\b|\bARQUIVISTA|\bALMOXARIF|\bFINANCEIRO$|\bFATURAMENTO|\bRECUPERADOR DE CREDITO|\bNEGOCIADOR DE COBRANCA|\bAUXILIAR DE INFORMATICA"),
    ("9 Ocupacoes elementares", r"\bDOMESTIC|\bDIARISTA|\bFAXINEIR|\bLIMPEZA|\bSERVICOS GERAIS|\bAUXILIAR DE SERVICOS|\bGARI\b|\bLIXEIRO|\bAUXILIAR DE COZINHA|\bAJUDANTE|\bCARREGADOR|\bSERVENTE|\bEMBALADOR|\bREPOSITOR|\bJORNALEIRO|\bLAVADOR|\bAUXILIAR DE PRODUCAO|\bAUX DE PRODUCAO|\bOFFICE BOY|\bCONTINUO|\bENTREGADOR|\bMERENDEIR|\bCOPEIR|\bTRABALHADOR BRACAL"),
    ("5 Trabalhadores dos servicos e vendedores", r"\bCOMERCIANTE|\bGUIA DE TURISMO|\bCOMISSARI|\bCONSULTOR[A]? DE VENDAS|\bFRENTISTA|\bFISCAL DE LOJA|\bAGENTE EDUCACIONAL|\bVENDEDOR|\bCOMERCIARI|\bBALCONISTA|\bVIGILANTE|\bVIGIA\b|\bSEGURANCA|\bPORTEIR|\bZELADOR|\bGARAGISTA|\bASCENSORISTA|\bCABELE|\bBARBEIR|\bMANICURE|\bESTETICIST|\bCOZINHEIR|\bSALGADEIR|\bGARCO|\bGARCON|\bGARCONETE|\bBABA\b|\bCUIDADOR|\bAGENTE COMUNITARI|\bAUTONOM|\bAMBULANTE|\bFEIRANTE|\bPROMOTOR DE VENDAS|\bAGENTE PENITENCIARI|\bGUARDA\b|\bAGENTE DE TRANSITO|\bINSPETOR DE ALUNOS|\bMANOBRISTA|\bCOBRADOR|\bBOMBEIRO CIVIL|\bLAVANDEIR|\bTINTUREIR"),
    ("6 Agropecuaria", r"\bAGRICULTOR|\bLAVRADOR|\bPRODUTOR RURAL|\bJARDINEIR|\bAGROPECUARI|\bPECUARIST|\bTRABALHADOR RURAL|\bAVICULTOR|\bAPICULTOR"),
    ("7 Operarios e artesaos", r"\bARTESA|\bMETALURGIC|\bPEDREIR|\bPINTOR|\bCARPINTEIR|\bMARCENEIR|\bSERRALHEIR|\bSOLDADOR|\bTORNEIR|\bELETRICISTA|\bENCANADOR|\bCONSTRUCAO CIVIL|\bPADEIR|\bCONFEITEIR|\bACOUGUEIR|\bGRAFIC|\bIMPRESSOR|\bFUNILEIR|\bVIDRACEIR|\bAZULEJIST|\bGESSEIR|\bSAPATEIR|\bOURIVES|\bCOSTUREIR|\bMECANIC|\bMANUTENCAO|\bREPARADOR|\bLANTERNEIR"),
    ("8 Operadores de maquinas e montadores", r"\bOPERADOR\b|\bOPERARI|\bMOTORISTA|\bCONDUTOR|\bCAMINHONEIR|\bTAXISTA|\bMOTOBOY|\bMONTADOR|\bMAQUINIST|\bAPARELHOS DE PRODUCAO|\bESTOQUISTA|\bCONFERENTE"),
    ("Servidor publico sem ocupacao informada", r"\bSERVIDOR|\bFUNCIONARI[OA] PUBLIC|\bFUNCIONALISMO|\bFUNC PUBLIC"),
    ("Empregado sem ocupacao informada", r"\bFUNCIONARI|\bEMPREGAD|\bCOLABORADOR|\bTRABALHADOR\b|\bCLT\b|\bPRIVAD|\bAUXILIAR$|\bCONSULTOR"),
]
PUBLICO = re.compile(r"\bSERVIDOR|\bPUBLIC|\bMUNICIPAL|\bESTADUAL|\bFEDERAL|\bPREFEITURA|\bSECRETARIA DE|\bTRIBUNAL|\bJUDICIARI|\bMINISTERIO|\bASSEMBLEIA|\bCAMARA|\bCOPEL|\bSANEPAR|\bCAIXA ECONOMICA|\bBANCO DO BRASIL|\bUFPR|\bUTFPR|\bINSS|\bRECEITA FEDERAL|\bPOLICIA|\bMILITAR|\bGUARDA MUNICIPAL|\bDETRAN|\bCORREIOS|\bAGENTE PENITENCIARI")

def classificar(p):
    n = norm(p)
    for cat, rx in REGRAS:
        if re.search(rx, n): return cat, n
    return "Outros ou nao classificado", n

def main():
    freq = Counter()
    for r in csv.DictReader(open("data/base_listas.csv", encoding="utf-8")):
        if int(r["ano"]) >= 2014: freq[norm(r["profissao"])] += 1
    tot = sum(freq.values()); por_cat = Counter(); linhas = []
    for g, n in freq.most_common():
        cat, _ = classificar(g); pub = "sim" if PUBLICO.search(g) else ""
        por_cat[cat] += n; linhas.append([g or "(vazio)", n, cat, pub, ""])
    with open("codificacao_profissoes.csv", "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f, delimiter=";"); w.writerow(["grafia (normalizada)", "frequencia 2014-2027", "categoria sugerida", "vinculo publico", "revisao (preencher so se discordar)"]); w.writerows(linhas)
    print(f"{len(freq)} grafias distintas, {tot} entradas (2014-2027)")
    acum = 0
    for i, (g, n) in enumerate(freq.most_common(), 1):
        acum += n
        if i in (50, 100, 200, 400): print(f"  as {i} grafias mais frequentes cobrem {100*acum/tot:.1f}% das entradas")
    inf = tot - por_cat["Nao informada"]
    for c, n in por_cat.most_common(): print(f"  {c:58} {n:6} ({100*n/tot:.1f}% do total; {100*n/inf:.1f}% das informadas)" if c != "Nao informada" else f"  {c:58} {n:6} ({100*n/tot:.1f}% do total)")
    nc = [l for l in linhas if l[2] == "Outros ou nao classificado"][:40]
    print("\nnao classificadas mais frequentes:", "; ".join(f"{l[0]} ({l[1]})" for l in nc))

if __name__ == "__main__": main()
