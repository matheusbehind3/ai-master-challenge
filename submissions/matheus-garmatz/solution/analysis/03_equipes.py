"""03 — Equipes, contas e vendedores: o que muda a receita, especialização,
disputa por contas, negócios "ressuscitados" e o que cada vendedor faz bem.
"""
import numpy as np
import pandas as pd
from scipy.stats import pearsonr
from common import REF, ZOMBIE_AGE, closed_clean, load, title

p = load()
c_all = p[p.won.notna()]
c = closed_clean(p)

title('1. O que explica a diferença de receita entre vendedores')
a = c_all.groupby('sales_agent').agg(closed=('won', 'size'), wr=('won', 'mean'), rev=('close_value', 'sum'))
a['ticket'] = a.rev / (a.wr * a.closed)
la = np.log(a)
for k, nome in [('closed', 'volume (deals fechados)'), ('ticket', 'ticket/mix'), ('wr', 'conversão')]:
    print(f'{nome:24s} explica {np.corrcoef(la[k], la.rev)[0, 1] ** 2:.0%} da variação de receita')
top = a.rev.idxmax()
print(f'concentração: {top} = US$ {a.rev.max():,.0f} ({a.rev.max() / a.rev.sum():.1%} da receita), {a.closed.max()} deals fechados')

title('2. O que se repete de um semestre para o outro (traço estável vs sorte)')
h1, h2 = c[c.close_date < '2017-07-01'], c[c.close_date >= '2017-07-01']
def corr(f):
    x, y = f(h1), f(h2)
    j = pd.concat([x, y], axis=1, join='inner').dropna()
    return pearsonr(j.iloc[:, 0], j.iloc[:, 1])
for nome, f in [('volume', lambda d: d.groupby('sales_agent').size()),
                ('ticket', lambda d: d[d.won == 1].groupby('sales_agent').close_value.mean()),
                ('win rate', lambda d: d.groupby('sales_agent').won.mean())]:
    r, pv = corr(f)
    print(f'{nome:9s} r={r:.2f} (p={pv:.3f})')
def ap(d):
    g = d.groupby(['sales_agent', 'product']).won.agg(['mean', 'count'])
    return g[g['count'] >= 15]['mean']
r, pv = corr(ap)
print(f'"vendedor X é bom no produto Y": r={r:.3f} (p={pv:.2f})')
mix = pd.crosstab(c.sales_agent, c['product'], normalize='index')
print('participação de cada produto nos deals de cada vendedor (mín–máx):')
print(mix.agg(['min', 'max']).round(2).to_string())
sh = mix.stack().rename('share')
wr = c.groupby(['sales_agent', 'product']).won.agg(['mean', 'count']).join(sh)
wr = wr[wr['count'] >= 15]
print(f'vender mais um produto → converter melhor nele? r={pearsonr(wr.share, wr["mean"])[0]:.2f}')

title('3. Contas: dono, disputa e deals duplicados')
pa = p.dropna(subset=['account'])
g = pa.groupby('account').agg(vend=('sales_agent', 'nunique'), ger=('manager', 'nunique'), esc=('regional_office', 'nunique'))
print(f'vendedores por conta: média {g.vend.mean():.1f}; gerentes {g.ger.mean():.1f}; escritórios {g.esc.mean():.1f}')
won = pa[pa.won == 1].groupby(['account', 'sales_agent']).close_value.sum()
share = won.groupby('account').max() / won.groupby('account').sum()
print(f'vendedor que mais fatura numa conta fica com {share.median():.0%} dela (mediana)')
pa = pa.assign(end=pa.close_date.fillna(REF)).sort_values('engage_date')
pairs = []
for _, grp in pa.groupby(['account', 'product']):
    rows = grp.to_dict('records')
    for i in range(len(rows)):
        for k in range(i + 1, len(rows)):
            x, y = rows[i], rows[k]
            if y['engage_date'] < x['end'] and x['sales_agent'] != y['sales_agent']:
                pairs.append((x['regional_office'] != y['regional_office'], x['manager'] != y['manager'],
                              x['deal_stage'], y['deal_stage']))
P = pd.DataFrame(pairs, columns=['outro_escr', 'outro_ger', 's1', 's2'])
print(f'pares de deals simultâneos (mesma conta + produto, vendedores diferentes): {len(P)}')
print(f'  entre escritórios: {P.outro_escr.sum()} | mesmo escritório, outro gerente: {(P.outro_ger & ~P.outro_escr).sum()} '
      f'| mesma equipe: {(~P.outro_ger).sum()}')
print(f'  pares em que OS DOIS ganharam: {((P.s1 == "Won") & (P.s2 == "Won")).sum()}  ← bloquear o 2º mataria receita')
o = p[p.deal_stage.isin(['Engaging', 'Prospecting'])].dropna(subset=['account'])
d = o.groupby(['account', 'product']).sales_agent.nunique()
print(f'pares conta+produto abertos com 2+ vendedores: {(d > 1).sum()} de {len(d)} ({(d > 1).mean():.0%})')

title('4. "Ressuscitados" (proxy): nova oportunidade na mesma conta + produto depois de uma perda')
lost = pa[pa.deal_stage == 'Lost']
res = []
for (acc, prd), grp in pa.groupby(['account', 'product']):
    lg = lost[(lost.account == acc) & (lost['product'] == prd)]
    for r in grp.itertuples():
        prev = lg[lg.close_date < r.engage_date]
        if len(prev):
            last = prev.sort_values('close_date').iloc[-1]
            res.append((r.deal_stage, (r.engage_date - last.close_date).days, r.sales_agent == last.sales_agent))
R = pd.DataFrame(res, columns=['stage', 'gap', 'mesmo_vendedor'])
cl = R[R.stage.isin(['Won', 'Lost'])]
base = pa[pa.won.notna() & (pa.engage_date >= '2017-03-01')].won.mean()
print(f'reabertos: {len(R)}; win rate {(cl.stage == "Won").mean():.3f} vs média {base:.3f}')
print(f'reaberto pelo mesmo vendedor que perdeu: {R.mesmo_vendedor.mean():.0%}; dias até reabrir (mediana): {R.gap.median():.0f}')
print('(o dataset não guarda histórico de etapas: "o mesmo deal voltou" não é observável)')

title('5. Escritório Central e o deal mais valioso')
e = p[p.deal_stage == 'Engaging'].assign(age=lambda d: (REF - d.engage_date).dt.days)
print(pd.crosstab(p.regional_office, p.deal_stage).to_string())
print('mês de engajamento dos Engaging abertos do Central:',
      e[e.regional_office == 'Central'].engage_date.dt.to_period('M').value_counts().sort_index().to_dict())
gtk = e[e['product'] == 'GTK 500'].sort_values('age')
print(f'GTK 500 abertos: {len(gtk)} (US$ {gtk.sales_price.sum():,.0f}); zumbis: {(gtk.age > ZOMBIE_AGE).sum()}')
print(gtk[['sales_agent', 'account', 'age']].head(3).to_string(index=False))
