#!/bin/bash
# Roda toda a análise e grava as saídas em results/ (≈ 40 s).
set -e
cd "$(dirname "$0")"
for s in 01_exploracao 02_sinais 03_equipes 04_backtest; do
  echo "→ $s"; python3 $s.py 2>&1 | grep -v Warning > results/$s.txt
done
python3 05_planilha.py
echo "ok — veja results/"
