import { CLOCK_LIMITS, ZOMBIE_AGE } from '../scoring/config';
import type { OpenDeal } from '../scoring/types';
import { CLOCK_LABEL, dealTitle, nextStep, whyScore } from '../explain';
import { usd } from '../format';

const CLOCK_CLASS = { healthy: 'saudavel', cooling: 'esfriando', lastChance: 'ultima', zombie: 'zumbi' } as const;
const CLOCK_COLOR = { healthy: 'var(--ok)', cooling: 'var(--warn)', lastChance: 'var(--hot)', zombie: 'var(--zombie)' } as const;
const SCALE = 150; // dias representados na barra

function ClockBar({ deal }: { deal: OpenDeal }) {
  const at = (days: number) => `${(Math.min(days, SCALE) / SCALE) * 100}%`;
  const bg = `linear-gradient(90deg,var(--ok-soft) 0 ${at(CLOCK_LIMITS.healthy)},var(--warn-soft) 0 ${at(CLOCK_LIMITS.cooling)},var(--hot-soft) 0 ${at(ZOMBIE_AGE)},var(--zombie-soft) 0 100%)`;
  return (
    <>
      <div className="clockbar" style={{ background: bg }} aria-label={`${deal.age} dias de ${ZOMBIE_AGE}`}>
        <span className="pin" style={{ left: at(deal.age!), background: CLOCK_COLOR[deal.clock!] }} />
      </div>
      <div className="clocklbl">
        <span style={{ left: 0 }}>0</span>
        <span style={{ left: at(CLOCK_LIMITS.healthy) }}>90d</span>
        <span style={{ left: at(CLOCK_LIMITS.cooling) }}>120</span>
        <span style={{ left: at(ZOMBIE_AGE) }}>138</span>
      </div>
    </>
  );
}

interface Props {
  deal: OpenDeal;
  decision?: string;
  onDecide: (id: string, label: string) => void;
}

export function DealCard({ deal: d, decision, onDecide }: Props) {
  const btn = (label: string, text: string, primary = false) => (
    <button key={label} className={'btn' + (primary ? ' pri' : '')} onClick={() => onDecide(d.id, label)}>{text}</button>
  );

  const conflict = d.conflicts.length > 0 && (
    <div className="alert">
      ⚠ {d.conflicts.length === 1 ? 'Outro vendedor também está' : `Outros ${d.conflicts.length} vendedores também estão`} oferecendo {d.product} para {d.account}: {d.conflicts.slice(0, 3).join(', ')}{d.conflicts.length > 3 ? '…' : ''}. Combinem quem segue — a ferramenta não bloqueia (há casos em que os dois ganharam).
    </div>
  );
  const noAccount = !d.account && (
    <div className="alert info">🔗 Deal sem conta vinculada no CRM — vincule para ver setor e possíveis conflitos.</div>
  );

  let badge, body, buttons;
  if (d.stage === 'Prospecting') {
    badge = <div className="score" style={{ background: '#9aa6b8' }}>—</div>;
    body = (
      <>
        <div className="meta"><span className="chip c-pros">Prospecting</span>{usd(d.price)} · sem data de engajamento</div>
        <div className="why">Sem data no CRM, não dá para medir o relógio. Ordenado só pelo valor.</div>
      </>
    );
    buttons = [btn('Contato iniciado', 'Iniciar contato', true), btn('Descartado', 'Descartar')];
  } else if (d.clock === 'zombie') {
    badge = <div className="score z">0<small>zumbi</small></div>;
    body = (
      <>
        <div className="meta"><span className="chip c-zumbi">Zumbi · {d.age} dias</span>{usd(d.price)}</div>
        <ClockBar deal={d} />
        <div className="why">Nenhum deal fechou depois de {ZOMBIE_AGE} dias — e no teste histórico, <b>0 de 264</b> deals nessa idade ganharam nos 90 dias seguintes.</div>
      </>
    );
    buttons = [btn('Mantido vivo (com motivo)', 'Está vivo — manter'), btn('Marcado como perdido', 'Marcar como perdido', true)];
  } else {
    badge = <div className="score">{d.scoring!.score}<small>score</small></div>;
    body = (
      <>
        <div className="meta">
          <span className={`chip c-${CLOCK_CLASS[d.clock!]}`}>{CLOCK_LABEL[d.clock!]} · {d.age} dias</span>
          {usd(d.price)}{d.sector ? ' · ' + d.sector : ''}
        </div>
        <ClockBar deal={d} />
        <div className="why"><b>Por que {d.scoring!.score}:</b> {whyScore(d)}</div>
      </>
    );
    buttons = [
      btn('Próximo passo agendado', 'Agendei o próximo passo', true),
      d.conflicts.length > 0 && btn('Combinado com colega', 'Combinei com o colega'),
      btn('Marcado como perdido', 'Marcar como perdido'),
    ];
  }

  return (
    <div className={'deal' + (decision ? ' done' : '')}>
      {badge}
      <div>
        <div className="ttl">{dealTitle(d)}</div>
        {body}
        <div className="act">▶ {nextStep(d)}</div>
        {conflict}
        {noAccount}
      </div>
      <div className="btns">{decision ? <span className="decided">✓ {decision}</span> : buttons}</div>
    </div>
  );
}
