"""01 — Exploração: estrutura, qualidade dos dados e a pergunta central
"as variáveis óbvias (vendedor, produto, conta, setor...) preveem quem ganha?"
"""
import pandas as pd
from scipy.stats import chi2_contingency
from sklearn.metrics import roc_auc_score
from common import DATA, REF, ZOMBIE_AGE, load, title

raw = pd.read_csv(DATA / 'sales_pipeline.csv')
p = load()

title('1. Estrutura e qualidade')
print('oportunidades:', len(p))
print(p.deal_stage.value_counts().to_string())
print('produto "GTXPro" (não existe em products.csv):', (raw['product'] == 'GTXPro').sum())
print('deals abertos sem conta:', p[p.deal_stage.isin(['Engaging', 'Prospecting']) & p.account.isna()].shape[0])
print('Prospecting sem engage_date:', p[(p.deal_stage == 'Prospecting') & p.engage_date.isna()].shape[0])
teams = pd.read_csv(DATA / 'sales_teams.csv')
print('vendedores sem nenhum deal:', sorted(set(teams.sales_agent) - set(p.sales_agent)))
print('close_date vai de', p.close_date.min().date(), 'a', p.close_date.max().date(),
      '→ perdas antes de mar/2017 não existem; coorte de 2016 fica inflada:')
c_all = p[p.won.notna()]
print(c_all.groupby(c_all.engage_date.dt.to_period('Q')).won.agg(['mean', 'count']).round(3).to_string())

title('2. Win rate por dimensão (fechados a partir de 2017)')
c = c_all[c_all.engage_date >= '2017-01-01'].copy()
print('win rate geral: %.3f' % c.won.mean())
for col in ['sales_agent', 'product', 'account', 'sector', 'regional_office', 'manager']:
    g = c.groupby(col).won.mean()
    pv = chi2_contingency(pd.crosstab(c[col].fillna('?'), c.won))[1]
    print(f'{col:16s} faixa {g.min():.2f}–{g.max():.2f}   qui-quadrado p={pv:.3f}')

title('3. Previsão fora da amostra (treina fechados até jul/17, testa ago–dez/17)')
tr, te = c[c.close_date < '2017-08-01'], c[c.close_date >= '2017-08-01']
m = tr.won.mean()
for col in ['sales_agent', 'product', 'account', 'sector']:
    g = tr.groupby(col).won.agg(['sum', 'count'])
    rate = (g['sum'] + 20 * m) / (g['count'] + 20)
    print(f'{col:12s} AUC = {roc_auc_score(te.won, te[col].map(rate).fillna(m)):.3f}   (0,50 = cara ou coroa)')
r = te.dropna(subset=['revenue'])
print(f'{"receita conta":12s} AUC = {roc_auc_score(r.won, r.revenue):.3f}')
print(f'{"preço":12s} AUC = {roc_auc_score(te.won, te.sales_price):.3f}')

title('4. Valor: close_value vs preço de tabela (ganhos)')
w = p[p.won == 1]
print((w.close_value / w.sales_price).describe().round(3).to_string())

title('5. Tempo: ciclo dos fechados e idade dos abertos')
print('ciclo dos ganhos, percentis:', c[c.won == 1].cycle.quantile([.5, .75, .9, .95, .99]).to_dict())
print('maior ciclo de qualquer deal fechado:', int(c_all.cycle.max()))
e = p[p.deal_stage == 'Engaging'].copy()
e['age'] = (REF - e.engage_date).dt.days
e['relogio'] = pd.cut(e.age, [-1, 90, 120, ZOMBIE_AGE, 10**4], labels=['saudável', 'esfriando', 'última chance', 'zumbi'])
print(e.groupby('relogio', observed=False).agg(deals=('age', 'size'), valor=('sales_price', 'sum')).to_string())
z = e[e.age > ZOMBIE_AGE]
print(f'zumbis: {len(z)} de {len(e)} ({len(z)/len(e):.0%}) — US$ {z.sales_price.sum():,.0f} '
      f'de US$ {p[p.deal_stage.isin(["Engaging","Prospecting"])].sales_price.sum():,.0f} em aberto')

title('6. Teste anti-armadilha: o limite de 138 dias é falta de janela?')
for mth in ['2017-03', '2017-04', '2017-05', '2017-06']:
    s = p[p.engage_date.dt.to_period('M') == mth]
    cl = s[s.won.notna()]
    print(f'coorte {mth}: janela de {(REF - pd.Period(mth).start_time).days} dias, maior ciclo {int(cl.cycle.max())}, '
          f'{(s.deal_stage == "Engaging").sum()} ainda abertos')
print('→ os deals fecham em até ~4 meses ou travam: o limite não é artefato da janela.')
