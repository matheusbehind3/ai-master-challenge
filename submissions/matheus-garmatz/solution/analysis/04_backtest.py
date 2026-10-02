"""04 — Backtest com "máquina do tempo".

Em 4 datas de 2017 (1º de jul, ago, set, out) reconstruímos o pipeline aberto
EXATAMENTE como estava. Cada vendedor escolhe 10 deals segundo cada estratégia.
Medimos quanto desse foco virou receita nos 90 dias seguintes.

Sem vazamento: tudo que uma estratégia "aprende" vem de dados anteriores à data.
Prospecting fica de fora (sem data, não dá para reconstruir o passado).
"""
import json
import numpy as np
import pandas as pd
from common import load, title

p = load()
p = p[p.deal_stage != 'Prospecting'].copy()
H, N = 90, 10
BANDS = [-1, 14, 30, 60, 90, 120, 138, 10**4]
LBL = ['0-14', '15-30', '31-60', '61-90', '91-120', '121-138', '>138']
TESTS = pd.date_range('2017-07-01', '2017-10-01', freq='MS')


def snapshot(t):
    o = p[(p.engage_date < t) & ((p.close_date >= t) | p.close_date.isna())].copy()
    o['age'] = (t - o.engage_date).dt.days
    o['band'] = pd.cut(o.age, BANDS, labels=LBL)
    o['win_h'] = ((o.won == 1) & (o.close_date <= t + pd.Timedelta(days=H))).astype(int)
    o['val_h'] = o.win_h * o.close_value.fillna(0)
    return o


def band_prob(t, k=20):
    """P(ganhar em 90 dias | faixa de idade), só com snapshots cujo resultado já era conhecido em t."""
    tr = pd.concat([snapshot(s) for s in pd.date_range('2017-03-01', t - pd.Timedelta(days=H), freq='MS')])
    g = tr.groupby('band', observed=False).win_h.agg(['sum', 'count'])
    prior = tr.win_h.mean()
    return ((g['sum'] + k * prior) / (g['count'] + k)), g


def hist_wr(t, key):
    h = p[p.won.notna() & (p.close_date < t) & (p.engage_date >= '2017-01-01')]
    g = h.groupby(key).won.agg(['sum', 'count'])
    m = h.won.mean()
    return (g['sum'] + 20 * m) / (g['count'] + 20), m


def strategies(o, t):
    bp, _ = band_prob(t)
    wa, m = hist_wr(t, 'sales_agent')
    wp, _ = hist_wr(t, 'product')
    return {
        'Nossa lógica (valor × chance pela idade)': o.sales_price * o.band.map(bp).astype(float),
        'Só ordenar por valor': o.sales_price,
        '"Baseline de IA" (valor × win rate vendedor × produto)':
            o.sales_price * o.sales_agent.map(wa).fillna(m) * o['product'].map(wp).fillna(m),
        'Mais novos primeiro': -o.age,
        'Mais antigos primeiro': o.age,
    }


rows, paired = [], []
rng = np.random.default_rng(0)
for t in TESTS:
    o = snapshot(t)
    S = strategies(o, t)
    for name, score in S.items():
        top = o.assign(s=score).sort_values('s', ascending=False).groupby('sales_agent').head(N)
        rows.append(dict(t=t.date(), estrategia=name, receita=top.val_h.sum(), ganhos=top.win_h.sum(),
                         deals=len(top), zumbis=(top.age > 138).mean()))
    acc = []
    for _ in range(200):
        top = o.assign(s=rng.random(len(o))).sort_values('s').groupby('sales_agent').head(N)
        acc.append((top.val_h.sum(), top.win_h.sum(), (top.age > 138).mean()))
    a = np.mean(acc, axis=0)
    rows.append(dict(t=t.date(), estrategia='Aleatório (o "feeling", média de 200 sorteios)', receita=a[0],
                     ganhos=a[1], deals=len(top), zumbis=a[2]))
    ours, val = S['Nossa lógica (valor × chance pela idade)'], S['Só ordenar por valor']
    for ag, d in o.assign(a=ours, b=val).groupby('sales_agent'):
        paired.append(d.nlargest(N, 'a').val_h.sum() - d.nlargest(N, 'b').val_h.sum())

R = pd.DataFrame(rows)
title('1. Receita que veio do foco (top 10 por vendedor, 4 datas, 90 dias)')
S = R.groupby('estrategia').agg(receita=('receita', 'sum'), ganhos=('ganhos', 'sum'), deals=('deals', 'sum'),
                                zumbis=('zumbis', 'mean')).sort_values('receita', ascending=False)
S['acerto'] = S.ganhos / S.deals
print(S.round(3).to_string())
print('\npor data:')
print(R.pivot(index='estrategia', columns='t', values='receita').round(0).to_string())

title('2. Comparação pareada: nossa lógica vs "só valor", vendedor a vendedor, mês a mês')
d = np.array(paired)
boot = [rng.choice(d, len(d)).mean() for _ in range(2000)]
print(f'melhor: {(d > 0).sum()}  igual: {(d == 0).sum()}  pior: {(d < 0).sum()}')
print(f'ganho médio por vendedor/mês: US$ {d.mean():,.0f}  (IC 95%: US$ {np.percentile(boot, 2.5):,.0f} a {np.percentile(boot, 97.5):,.0f})')

title('3. Chance de ganhar em 90 dias por idade (aprendida até out/2017) → usada no app')
bp, g = band_prob(pd.Timestamp('2017-10-01'))
out = pd.DataFrame({'chance_90d': bp.round(3), 'ganhos': g['sum'], 'casos': g['count']})
print(out.to_string())
json.dump({k: round(float(v), 3) for k, v in bp.items()}, open('results/chance_por_idade.json', 'w'), indent=2)

title('4. Forecast da receita dos deals abertos nos 90 dias seguintes')
for t in TESTS:
    o = snapshot(t)
    bpt, _ = band_prob(t)
    naive = o.sales_price.sum() * 0.62
    ours = (o.sales_price * o.band.map(bpt).astype(float)).sum()
    real = o.val_h.sum()
    print(f'{t.date()}  real US$ {real/1e3:,.0f} mil | ingênuo {naive/1e3:,.0f} mil ({naive/real-1:+.0%}) '
          f'| ajustado {ours/1e3:,.0f} mil ({ours/real-1:+.0%})')

title('5. Receita de deals que abrem e fecham no mesmo trimestre (a parte previsível)')
w = p[p.won == 1]
for q in ['2017Q2', '2017Q3', '2017Q4']:
    ww = w[(w.close_date.dt.to_period('Q') == q) & (w.engage_date.dt.to_period('Q') == q)]
    print(f'{q}: US$ {ww.close_value.sum()/1e6:.2f} mi')
