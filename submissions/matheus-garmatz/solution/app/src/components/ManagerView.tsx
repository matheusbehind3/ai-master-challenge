import { aliveByScore, forecast } from '../scoring/model';
import type { Model, Seller } from '../scoring/types';
import { sum, usdShort } from '../format';
import { FORECAST_BACKTEST } from '../evidence';

interface Props {
  model: Model;
  sellers: Seller[];
  scope: string;
  onOpenSeller: (name: string) => void;
}

export function ManagerView({ model, sellers, scope, onOpenSeller }: Props) {
  const names = new Set(sellers.map((s) => s.name));
  const deals = model.openDeals.filter((d) => names.has(d.seller));
  const alive = aliveByScore(deals);
  const zombies = deals.filter((d) => d.clock === 'zombie');
  const prospects = deals.filter((d) => d.stage === 'Prospecting');
  const engaging = deals.filter((d) => d.stage === 'Engaging');
  const conflicts = alive.filter((d) => d.conflicts.length > 0).length + prospects.filter((d) => d.conflicts.length > 0).length;
  const noAccount = deals.filter((d) => !d.account).length;
  const fc = forecast(deals);

  const rows = sellers.map((s) => {
    const m = deals.filter((d) => d.seller === s.name);
    const a = aliveByScore(m);
    const eng = m.filter((d) => d.stage === 'Engaging').length;
    return {
      s, alive: a, eng, top: a[0],
      zombies: m.filter((d) => d.clock === 'zombie').length,
      prospects: m.filter((d) => d.stage === 'Prospecting').length,
      conflicts: m.filter((d) => d.conflicts.length > 0 && d.clock !== 'zombie').length,
      ev: sum(a, (d) => d.scoring!.expectedValue),
      profile: model.profiles[s.name],
    };
  }).sort((x, y) => y.ev - x.ev);

  return (
    <>
      <h1>{scope}</h1>
      <p className="sub">{sellers.length} vendedores · clique em um vendedor para abrir a visão dele</p>
      <div className="kpis">
        <div className="kpi"><span>Pipeline no CRM</span><b>{usdShort(sum(deals, (d) => d.price))}</b><small>{deals.length} deals abertos</small></div>
        <div className="kpi"><span>Pipeline vivo</span><b>{usdShort(sum(alive, (d) => d.price) + sum(prospects, (d) => d.price))}</b><small>{alive.length} Engaging vivos ({usdShort(sum(alive, (d) => d.price))}) + {prospects.length} prospects</small></div>
        <div className="kpi"><span>Zumbis</span><b>{usdShort(sum(zombies, (d) => d.price))}</b><small>{zombies.length} deals · {engaging.length ? Math.round((100 * zombies.length) / engaging.length) : 0}% do Engaging</small></div>
        <div className="kpi"><span>Forecast 90 dias (Engaging)</span><b>{usdShort(fc.adjusted)}</b><small>o jeito ingênuo diria {usdShort(fc.naive)}</small></div>
      </div>

      <div style={{ overflowX: 'auto' }}>
        <table>
          <thead><tr><th>Vendedor</th><th>Perfil</th><th className="r">Vivos</th><th className="r">Valor esperado</th><th className="r">Prospects</th><th>Zumbis</th><th className="r">Conflitos</th><th>Deal nº 1</th></tr></thead>
          <tbody>
            {rows.map((r) => (
              <tr key={r.s.name} className="click" onClick={() => onOpenSeller(r.s.name)}>
                <td><b>{r.s.name}</b><div className="meta">{r.s.manager} · {r.s.office}</div></td>
                <td>{r.profile ? <>{r.profile.label}<div className="meta">{r.profile.closedPerMonth.toFixed(1).replace('.', ',')}/mês · ticket {usdShort(r.profile.avgTicket)}</div></> : <span className="meta">sem deals</span>}</td>
                <td className="r">{r.alive.length}</td>
                <td className="r">{usdShort(r.ev)}</td>
                <td className="r">{r.prospects || '–'}</td>
                <td>{r.eng ? <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}><div className="mini"><i style={{ width: `${(100 * r.zombies) / r.eng}%` }} /></div>{r.zombies}</div> : '–'}</td>
                <td className="r">{r.conflicts || '–'}</td>
                <td>{r.top ? <>{r.top.product}<div className="meta">{r.top.account ?? 'sem conta'} · score {r.top.scoring!.score}</div></> : '–'}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="grid2" style={{ marginTop: 14 }}>
        <div className="panel">
          <h3>Onde agir como gerente</h3>
          <ol style={{ margin: 0, paddingLeft: 18 }}>
            <li><b>{zombies.length} zumbis</b> inflam o pipeline em {usdShort(sum(zombies, (d) => d.price))}. Peça a cada vendedor uma decisão: manter ou encerrar.</li>
            <li><b>{conflicts} deals vivos</b> têm outro vendedor na mesma conta e produto. Defina quem segue.</li>
            <li><b>{noAccount} deals</b> estão sem conta vinculada no CRM.</li>
          </ol>
          <div className="note">Perfis usam o que se repete de um semestre para o outro: volume (correlação 0,95) e ticket (0,71). Conversão não se repete (0,35) — por isso a ferramenta não ranqueia vendedor por win rate.</div>
        </div>
        <div className="panel">
          <h3>Forecast honesto (próximos 90 dias, deals em Engaging)</h3>
          <div className="hbar"><span>Ingênuo (pipeline × 62%)</span><div className="t"><i style={{ width: '100%', background: '#d6dbe3' }} /></div><span>{usdShort(fc.naive)}</span></div>
          <div className="hbar me"><span>Ajustado pela idade</span><div className="t"><i style={{ width: `${fc.naive ? (100 * fc.adjusted) / fc.naive : 0}%` }} /></div><span>{usdShort(fc.adjusted)}</span></div>
          <div className="note">No teste histórico, o ingênuo errou {FORECAST_BACKTEST.naiveError}; o ajustado errou {FORECAST_BACKTEST.adjustedError}. Ainda superestima — use como referência, não como meta. Deals novos que abrem e fecham no mesmo trimestre somam ~US$ 1,5 mi por trimestre na empresa toda, a parte mais previsível da receita.</div>
        </div>
      </div>
    </>
  );
}
