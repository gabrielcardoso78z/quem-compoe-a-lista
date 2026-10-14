#!/bin/bash
# Rodada completa, em etapas curtas (cada uma cabe em ~3 min). Uso: bash scripts_auxiliares/rodar_tudo.sh <etapa>
#   listas1 | listas2 | conv1 | conv2 | conv2b | conv3 | final   (rodar nesta ordem)
# Logs em auditoria/rodada_correcao/. Os brutos anuais antigos (2023, 2024, 2025 sem semestre) nao devem existir em data/.
cd "$(dirname "$0")/.." || exit 1
L=auditoria/rodada_correcao; mkdir -p $L
lista() { for p in "$@"; do python3 processar_comarcas_dje.py --todas --bruto --padrao="${p}*" > $L/listas_$p.log 2>&1; echo "listas $p rc=$? $(tail -1 $L/listas_$p.log)"; done; }
conv()  { for p in "$@"; do python3 processar_convocacoes_dje.py --bruto --padrao="${p}*" > $L/conv_$p.log 2>&1; echo "conv $p rc=$? $(tail -1 $L/conv_$p.log)"; done; }
case "$1" in
  listas1) lista 2022 2023-0 2023-1 2024-0 2024-1 ;;
  listas2) lista 2025-0 2025-1 2026; python3 processar_comarcas_dje.py --juntar > $L/juntar_listas.log 2>&1; echo "juntar rc=$? $(tail -1 $L/juntar_listas.log)" ;;
  conv1) conv 2022 2023-0 2023-1 ;;
  conv2) conv 2024-0 2024-1 ;;
  conv2b) conv 2025-0 ;;
  conv3) conv 2025-1 2026 ;;
  final) python3 processar_convocacoes_dje.py --juntar > $L/juntar_conv.log 2>&1; echo "juntar conv rc=$?"
         for f in verificar_comarcas analise_censo_estadual analise_convocacoes_estado; do python3 $f.py > $L/$f.log 2>&1; echo "$f rc=$?"; done
         python3 scripts_auxiliares/testar_regressao.py > $L/regressao.log 2>&1; echo "regressao rc=$?" ;;
  *) echo "etapa?"; exit 1 ;;
esac
