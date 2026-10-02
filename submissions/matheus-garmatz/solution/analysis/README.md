# Análise

Tudo que a ferramenta afirma vem daqui. Cada script imprime os números e grava a saída em `results/`.

```bash
pip install -r requirements.txt
./run_all.sh
```

| Script | Pergunta | Resultado principal |
|---|---|---|
| `01_exploracao.py` | Os dados são confiáveis? As variáveis óbvias preveem quem ganha? | 4 problemas de qualidade; win rate igual (60–65%) em todo recorte; AUC 0,48–0,51 fora da amostra; 81% do Engaging tem mais de 138 dias |
| `02_sinais.py` | Existe algum sinal? Quais são falsos? | Fim de trimestre é forte (80% × 49%) mas vale para todos; "2 primeiras semanas" e "primeiro deal com a conta" eram efeito do calendário; ML com tudo: 99,7% no passado, 50,7% no futuro |
| `03_equipes.py` | O que muda a receita? Especialização? Disputa por conta? Ressuscitados? | Receita = volume (46%) + ticket (28%), conversão 1%; especialização não se repete (r = −0,01); 49% dos pares conta+produto abertos têm 2+ vendedores; 5.149 pares em que os dois ganharam; reabertos ganham igual à média |
| `04_backtest.py` | A fila proposta funciona? | Top 10 por vendedor: US$ 2,35 mi contra US$ 0,87 mi no aleatório e US$ 2,09 mi só por valor; zumbis no foco: 1% contra 14%; forecast: erro de +190% cai para +60% |
| `05_planilha.py` | Quem tem o quê? | `docs/crm_relacional_equipes.xlsx`: escritório › gerente › vendedor com todos os valores |

`results/chance_por_idade.json` é a tabela de chance usada em `app/src/scoring/config.ts`
(na faixa > 138 dias o app usa 0: foram 0 ganhos em 264 casos; o 0,03 do arquivo é só a suavização estatística).
