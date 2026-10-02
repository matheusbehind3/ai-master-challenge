import { AGE_BANDS } from '../scoring/config';
import { BACKTEST, DISCARDED, HUMAN_IN_LOOP, PAIRED } from '../evidence';
import { pct, usd, usdShort } from '../format';

const chanceColor = (p: number) => (p === 0 ? 'var(--zombie)' : p < 0.2 ? 'var(--hot)' : p < 0.4 ? 'var(--warn)' : 'var(--ok)');

export function TrustView() {
  const best = BACKTEST[0].revenue;
  return (
    <>
      <h1>Por que confiar neste score</h1>
      <p className="sub">Tudo aqui foi testado no histórico antes de entrar na ferramenta. Scripts em <code>solution/analysis/</code>.</p>

      <div className="grid2">
        <div className="panel">
          <h3>Teste com “máquina do tempo”</h3>
          <div className="note" style={{ margin: '0 0 8px' }}>
            Voltamos a 4 datas de 2017 (jul–out). Em cada uma, cada vendedor focou nos seus 10 deals mais prioritários segundo cada estratégia, usando só dados disponíveis naquela data. Quanto desse foco virou receita em 90 dias?
          </div>
          {BACKTEST.map((s) => (
            <div key={s.name} className={'hbar' + (s.ours ? ' me' : '')}>
              <span>{s.name}</span>
              <div className="t"><i style={{ width: `${(100 * s.revenue) / best}%` }} /></div>
              <span>{usdShort(s.revenue)}</span>
            </div>
          ))}
          <div className="note">
            Foco desperdiçado em zumbis: nossa lógica {pct(BACKTEST[0].zombieShare)} · aleatório {pct(BACKTEST[4].zombieShare)} · mais antigos {pct(BACKTEST[5].zombieShare)}.
            Vendedor a vendedor, mês a mês, contra “só valor”: melhor em {PAIRED.better} casos, igual em {PAIRED.equal}, pior em {PAIRED.worse}
            (+{usd(PAIRED.gainPerSellerMonth)} por vendedor/mês; IC 95%: {usd(PAIRED.ciLow)} a {usd(PAIRED.ciHigh)}).
          </div>
          <div className="note"><b>O que isso prova:</b> a fila aponta para os deals que de fato fecharam. <b>O que não prova:</b> que dar atenção aumenta a chance — o CRM não registra atividade do vendedor.</div>
        </div>

        <div className="panel">
          <h3>Chance de ganhar em 90 dias, pela idade do deal</h3>
          {AGE_BANDS.map((b) => (
            <div key={b.label} className="hbar">
              <span>{b.label}</span>
              <div className="t"><i style={{ width: `${b.p * 200}%`, background: chanceColor(b.p) }} /></div>
              <span>{pct(b.p)}</span>
            </div>
          ))}
          <div className="note">Este é o “momento” do score. O “valor” é o preço de tabela do produto (os deals ganhos fecham a ±1% dele). Score = valor × chance, numa escala de 1 a 100.</div>
        </div>
      </div>

      <h2>O que testamos e deixamos de fora</h2>
      <table>
        <thead><tr><th>Ideia</th><th>Resultado</th></tr></thead>
        <tbody>{DISCARDED.map(([a, b]) => <tr key={a}><td>{a}</td><td>{b}</td></tr>)}</tbody>
      </table>

      <h2>O que a ferramenta faz e o que fica com as pessoas</h2>
      <table>
        <thead><tr><th>A ferramenta</th><th>A pessoa decide</th><th>Por quê</th></tr></thead>
        <tbody>{HUMAN_IN_LOOP.map(([a, b, c]) => <tr key={a}><td>{a}</td><td>{b}</td><td>{c}</td></tr>)}</tbody>
      </table>
    </>
  );
}
