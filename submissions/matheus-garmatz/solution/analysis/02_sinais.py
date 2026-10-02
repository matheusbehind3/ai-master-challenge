"""02 — Caça a sinais (e a falsos sinais).
Inclui os dois casos em que o calendário enganou a análise.
"""
import numpy as np
import pandas as pd
from scipy.stats import chi2_contingency
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.metrics import roc_auc_score
from common import REF, closed_clean, load, title

p = load()
c = closed_clean(p)
c['moq'] = (c.close_date.dt.month - 1) % 3 + 1  # mês do trimestre em que fechou

title('1. Calendário: mês do trimestre em que o deal fecha')
print(c.groupby('moq').won.agg(['mean', 'count']).round(3).to_string())
a = c.groupby(['sales_agent', 'moq']).won.mean().unstack()
print(f'vendedores com 3º mês > 1º mês: {(a[3] > a[1]).sum()} de {len(a)}')
print(c.groupby(['regional_office', 'moq']).won.mean().unstack().round(3).to_string())
print('→ sinal forte, mas vale para TODOS os deals ao mesmo tempo: não muda a ordem da fila.')

title('2. FALSO SINAL #1: "passou das 2 primeiras semanas, ganha mais"')
late = c[c.engage_date >= '2017-03-01']
for x in [0, 14, 60, 90]:
    print(f'ciclo > {x:3d} dias: win rate {late[late.cycle > x].won.mean():.3f}')
c['cb'] = pd.cut(c.cycle, [0, 14, 60, 140])
print('controlando pelo mês do trimestre:')
print(c.groupby(['cb', 'moq'], observed=True).won.mean().unstack().round(2).to_string())
tr, te = c[c.close_date < '2017-09-01'], c[c.close_date >= '2017-09-01']
gb = HistGradientBoostingClassifier(random_state=0).fit(tr[['cycle']], tr.won)
print(f'ciclo sozinho prevendo o futuro: AUC {roc_auc_score(te.won, gb.predict_proba(te[["cycle"]])[:, 1]):.3f}')
print('→ era o calendário: dentro de cada mês do trimestre, a diferença some.')

title('3. Outras variáveis (qui-quadrado)')
c['dow'] = c.engage_date.dt.dayofweek
for col, bins in [('dow', None), ('employees', 4), ('revenue', 4), ('year_established', 4)]:
    x = c[col] if bins is None else pd.qcut(c[col], bins, duplicates='drop')
    print(f'{col:16s} p={chi2_contingency(pd.crosstab(x, c.won))[1]:.3f}')
print(f'{"empresa-mãe":16s} p={chi2_contingency(pd.crosstab(c.subsidiary_of.notna(), c.won))[1]:.3f}')
for a_, b_ in [('product', 'sector'), ('sales_agent', 'product'), ('sales_agent', 'sector')]:
    k = c[a_].fillna('') + '|' + c[b_].fillna('')
    print(f'{a_} × {b_}: p={chi2_contingency(pd.crosstab(k, c.won))[1]:.3f}')

title('4. Histórico (só o que era conhecido na data de engajamento)')
cl = p[p.won.notna()][['account', 'sales_agent', 'close_date', 'won']]
s = c[c.engage_date >= '2017-04-01'].sort_values('engage_date').copy()


def prior(row, key, days=None):
    h = cl[(cl[key] == row[key]) & (cl.close_date < row['engage_date'])]
    if days:
        h = h[h.close_date >= row['engage_date'] - pd.Timedelta(days=days)]
    return h.won.mean() if len(h) >= (5 if days else 1) else np.nan


s['acc_wr'] = s.apply(lambda r: prior(r, 'account'), axis=1)
s['ag_wr'] = s.apply(lambda r: prior(r, 'sales_agent'), axis=1)
s['form30'] = s.apply(lambda r: prior(r, 'sales_agent', 30), axis=1)
allp = p.assign(end=p.close_date.fillna(REF))
s['load'] = s.apply(lambda r: int(((allp.sales_agent == r['sales_agent']) & (allp.engage_date < r['engage_date'])
                                   & (allp.end > r['engage_date'])).sum()), axis=1)
for col, sign in [('acc_wr', 1), ('ag_wr', 1), ('form30', 1), ('load', -1)]:
    m = s.dropna(subset=[col])
    print(f'{col:8s} AUC {roc_auc_score(m.won, sign * m[col]):.3f}  (n={len(m)})')

title('5. Machine learning com tudo que se sabe no engajamento')
s['emoq'] = (s.engage_date.dt.month - 1) % 3 + 1
cats = ['sales_agent', 'product', 'account', 'sector', 'regional_office', 'manager', 'office_location']
X = s[cats + ['sales_price', 'revenue', 'employees', 'year_established', 'acc_wr', 'ag_wr', 'form30', 'load', 'emoq']].copy()
for k in cats:
    X[k] = X[k].astype('category')
trm = s.close_date < '2017-09-01'
gbm = HistGradientBoostingClassifier(max_iter=200, learning_rate=0.05, categorical_features='from_dtype',
                                     random_state=0).fit(X[trm], s.won[trm])
print(f'acerto (AUC) no passado que ele viu: {roc_auc_score(s.won[trm], gbm.predict_proba(X[trm])[:, 1]):.3f}')
print(f'acerto (AUC) no futuro:              {roc_auc_score(s.won[~trm], gbm.predict_proba(X[~trm])[:, 1]):.3f}')
print('→ decorou o passado, não aprendeu nada que sirva para o futuro.')

title('6. FALSO SINAL #2: "primeiro deal do vendedor com a conta ganha mais"')
f = c[(c.engage_date >= '2017-03-01') & c.account.notna()].sort_values('engage_date').copy()
f['primeiro'] = ~f.duplicated(['account', 'sales_agent'])
print(f.groupby('primeiro').won.agg(['mean', 'count']).round(3).to_string())
print('controlando pelo trimestre de fechamento:')
print(f.groupby([f.close_date.dt.to_period('Q'), 'primeiro']).won.agg(['mean', 'count']).round(3).unstack().to_string())
print('→ de novo o calendário: os "primeiros deals" se concentravam nos meses de mais vitória.')
