import { useState } from 'react';
import { FOCUS_SIZE } from '../scoring/config';
import { aliveByScore } from '../scoring/model';
import type { Model } from '../scoring/types';
import { CLOCK_LABEL, daysLeft } from '../explain';
import { dateBR, sum, usd, usdShort } from '../format';
import { DealCard } from './DealCard';

type Tab = 'foco' | 'vivos' | 'zumbis' | 'second' | 'pros';
const PAGE = 20;

interface Props {
  model: Model;
  seller: string;
  decisions: Record<string, string>;
  onDecide: (id: string, label: string) => void;
}

export function SellerView({ model, seller, decisions, onDecide }: Props) {
  const [tab, setTab] = useState<Tab>('foco');
  const [shown, setShown] = useState(PAGE);
  const go = (t: Tab) => { setTab(t); setShown(PAGE); };

  const mine = model.openDeals.filter((d) => d.seller === seller);
  const profile = model.profiles[seller];
  const alive = aliveByScore(mine);
  const zombies = mine.filter((d) => d.clock === 'zombie').sort((a, b) => b.price - a.price);
  const prospects = mine.filter((d) => d.stage === 'Prospecting').sort((a, b) => b.price - a.price);
  const conflicts = mine.filter((d) => d.conflicts.length > 0 && d.clock !== 'zombie');
  const second = model.secondChance.filter((s) => s.seller === seller).sort((a, b) => b.price - a.price);
  const first = seller.split(' ')[0];

  if (!mine.length && !profile) {
    return (
      <>
        <h1>{seller}</h1>
        <p className="sub">Cadastrado na equipe, mas sem nenhuma oportunidade no CRM.</p>
        <div className="hint">É capacidade ociosa: um bom uso seria assumir a revisão de zumbis da equipe ou a lista de segunda chance.</div>
      </>
    );
  }

  // Resumo da semana — frases montadas a partir dos números do vendedor.
  const weak = !alive.length || alive[0].scoring!.expectedValue < 300;
  const items: React.ReactNode[] = [];
  if (!weak) items.push(<>Comece por <b>{alive[0].product}{alive[0].account ? ' na ' + alive[0].account : ''}</b> (score {alive[0].scoring!.score}, {usd(alive[0].price)}).</>);
  if (weak && prospects.length) items.push(<>Seu pipeline vivo está nos <b>{prospects.length} prospects</b> ({usdShort(sum(prospects, (d) => d.price))}). Comece pelo maior: <b>{prospects[0].product}{prospects[0].account ? ' na ' + prospects[0].account : ''}</b> ({usd(prospects[0].price)}).</>);
  const urgent = alive.filter((d) => d.clock !== 'healthy').sort((a, b) => b.price - a.price)[0];
  if (urgent && !weak) {
    items.push(urgent.id === alive[0].id
      ? <>Ele está na fase “{CLOCK_LABEL[urgent.clock!].toLowerCase()}”: {daysLeft(urgent)}.</>
      : <><b>{urgent.product}{urgent.account ? ' na ' + urgent.account : ''}</b> está na fase “{CLOCK_LABEL[urgent.clock!].toLowerCase()}”: {daysLeft(urgent)}.</>);
  }
  if (zombies.length) items.push(<><b>{zombies.length} zumbis</b> ({usdShort(sum(zombies, (d) => d.price))}) esperam sua decisão: manter ou encerrar.</>);
  if (conflicts.length) items.push(<><b>{conflicts.length} deal{conflicts.length > 1 ? 's' : ''}</b> com colega na mesma conta e produto — vale combinar quem segue.</>);

  const focus = alive.slice(0, FOCUS_SIZE);
  const fill = focus.length < FOCUS_SIZE ? prospects.slice(0, FOCUS_SIZE - focus.length) : [];
  const tabs: [Tab, string, number][] = ([
    ['foco', 'Foco da semana', focus.length + fill.length],
    ['vivos', 'Todos os vivos', alive.length],
    ['zumbis', 'Zumbis para revisar', zombies.length],
    ['second', 'Segunda chance', second.length],
    ['pros', 'Prospecting', prospects.length],
  ] as [Tab, string, number][]).filter(([t, , n]) => n > 0 || t === 'foco');

  const card = (d: typeof mine[number]) => <DealCard key={d.id} deal={d} decision={decisions[d.id]} onDecide={onDecide} />;
  const more = (n: number) => n > shown && <button className="more" onClick={() => setShown(shown + PAGE)}>Mostrar mais</button>;

  return (
    <>
      <h1>Bom dia, {first}.</h1>
      {profile && (
        <p className="sub">
          Seu perfil: <b>{profile.label}</b> · {profile.closedPerMonth.toFixed(1).replace('.', ',')} deals fechados/mês · ticket médio {usd(profile.avgTicket)}
        </p>
      )}
      <div className="brief"><b>Sua semana em {items.length} pontos</b><ol>{items.map((x, i) => <li key={i}>{x}</li>)}</ol></div>

      <div className="kpis">
        <div className="kpi"><span>Deals vivos</span><b>{alive.length}</b><small>{usdShort(sum(alive, (d) => d.price))} em valor</small></div>
        <div className="kpi"><span>Valor esperado (90 dias)</span><b>{usdShort(sum(alive, (d) => d.scoring!.expectedValue))}</b><small>valor × chance pela idade</small></div>
        <div className="kpi"><span>Zumbis para decidir</span><b>{zombies.length}</b><small>{usdShort(sum(zombies, (d) => d.price))} parados</small></div>
        <div className="kpi"><span>Conflitos de conta</span><b>{conflicts.length}</b><small>colega no mesmo produto</small></div>
      </div>

      <div className="tabs" role="tablist">
        {tabs.map(([t, label, n]) => (
          <button key={t} role="tab" className={t === tab ? 'on' : ''} onClick={() => go(t)}>{label}<span className="n">{n}</span></button>
        ))}
      </div>

      {tab === 'foco' && (
        <>
          <div className="hint">Os deals com maior valor esperado (valor × chance de ganhar em 90 dias pela idade). No teste histórico, focar assim trouxe 2,7× mais receita que escolher no feeling.</div>
          {weak && fill.length > 0 ? (
            // Pipeline em Engaging fraco: os prospects valem mais, então vêm primeiro.
            <>
              {fill.map(card)}
              {focus.length > 0 && <><h2>Deals em andamento</h2>{focus.map(card)}</>}
            </>
          ) : (
            <>
              {focus.map(card)}
              {fill.length > 0 && <><h2>Para completar sua semana: prospects de maior valor</h2>{fill.map(card)}</>}
            </>
          )}
          {!focus.length && !fill.length && <div className="empty">Sem deals vivos no momento.</div>}
        </>
      )}
      {tab === 'vivos' && <>{alive.slice(0, shown).map(card)}{more(alive.length)}</>}
      {tab === 'zumbis' && (
        <>
          <div className="hint">Deals com mais de 138 dias. A ferramenta não encerra nada sozinha: o CRM não registra suas ligações e reuniões, então quem sabe se o deal está vivo é você.</div>
          {zombies.slice(0, shown).map(card)}{more(zombies.length)}
        </>
      )}
      {tab === 'pros' && (
        <>
          <div className="hint">Prospects não têm data no CRM, então não têm relógio. Ordenados por valor.</div>
          {prospects.slice(0, shown).map(card)}{more(prospects.length)}
        </>
      )}
      {tab === 'second' && (
        <>
          <div className="hint">Deals que você perdeu há mais de 30 dias, em contas onde ninguém tem deal aberto hoje no mesmo produto. No histórico, oportunidades reabertas após uma perda ganharam 61,7% — igual à média (61,5%). Perder não queima a conta.</div>
          <table>
            <thead><tr><th>Conta</th><th>Produto</th><th className="r">Valor</th><th>Perdido em</th><th /></tr></thead>
            <tbody>
              {second.slice(0, shown).map((s) => (
                <tr key={s.id}>
                  <td>{s.account}</td><td>{s.product}</td><td className="r">{usd(s.price)}</td>
                  <td>{dateBR(s.lostOn)} ({s.daysAgo} dias)</td>
                  <td>{decisions[s.id] ? <span className="decided">✓ {decisions[s.id]}</span>
                    : <button className="btn" onClick={() => onDecide(s.id, 'Reabordagem planejada')}>Reabordar</button>}</td>
                </tr>
              ))}
            </tbody>
          </table>
          {more(second.length)}
        </>
      )}
    </>
  );
}
