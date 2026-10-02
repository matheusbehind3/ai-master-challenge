/**
 * Textos que explicam cada deal ao vendedor. Mantidos fora dos componentes
 * para que a regra de negócio fique legível num lugar só.
 */
import { ZOMBIE_AGE } from './scoring/config';
import type { Clock, OpenDeal } from './scoring/types';
import { pct, usd } from './format';

export const CLOCK_LABEL: Record<Clock, string> = {
  healthy: 'Saudável', cooling: 'Esfriando', lastChance: 'Última chance', zombie: 'Zumbi',
};

export function daysLeft(d: OpenDeal): string {
  const left = ZOMBIE_AGE - (d.age ?? 0);
  return left > 0 ? `faltam ${left} dias para o limite de ${ZOMBIE_AGE} dias` : `hoje é o último dia antes do limite de ${ZOMBIE_AGE} dias`;
}

export function nextStep(d: OpenDeal): string {
  if (d.stage === 'Prospecting') return 'Próximo passo: fazer o primeiro contato e registrar a data de engajamento.';
  const p = pct(d.winChance90d ?? 0);
  switch (d.clock) {
    case 'healthy': return `Avançar: agende o próximo passo. Deals nessa idade fecham ${p} das vezes em 90 dias.`;
    case 'cooling': return `Acelerar: a chance está caindo (${p} em 90 dias) — ${daysLeft(d)}.`;
    case 'lastChance': return `Decidir agora: só ${p} de chance — ${daysLeft(d)}.`;
    default: return 'Decida: se você tem um contato ativo, mantenha (e registre o motivo). Se não, marque como perdido e libere o pipeline.';
  }
}

export function whyScore(d: OpenDeal): string {
  const s = d.scoring!;
  return `+${s.valuePts} valor (${usd(d.price)}) · +${s.momentPts} momento (${d.age} dias → ${pct(d.winChance90d!)} de chance em 90 dias)`;
}

export const dealTitle = (d: { product: string; account: string | null }) =>
  `${d.product} · ${d.account ?? 'Conta não vinculada'}`;
