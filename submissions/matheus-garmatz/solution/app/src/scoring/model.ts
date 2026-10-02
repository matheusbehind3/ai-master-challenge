import Papa from 'papaparse';
import { NAIVE_WIN_RATE, PRODUCT_FIXES, REF_DATE, SECOND_CHANCE_MIN_DAYS } from './config';
import { ageBand, boundsFrom, clockOf, daysBetween, scoreDeal } from './score';
import type {
  Account, DataQuality, Model, OpenDeal, Opportunity, ProfileLabel, RawTables,
  SecondChance, Seller, SellerProfile, Stage,
} from './types';

export function parseCsv(text: string): Record<string, string>[] {
  return Papa.parse<Record<string, string>>(text.trim(), { header: true, skipEmptyLines: true }).data;
}

const date = (s: string) => (s ? new Date(s + 'T00:00:00Z') : null);
const num = (s: string) => (s === '' || s == null ? null : Number(s));
const median = (xs: number[]) => {
  const s = [...xs].sort((a, b) => a - b);
  const m = Math.floor(s.length / 2);
  return s.length % 2 ? s[m] : (s[m - 1] + s[m]) / 2;
};

/** Liga as 4 tabelas: pipeline → vendedor (gerente, escritório), produto (preço), conta. */
export function buildModel(raw: RawTables): Model {
  const sellers: Seller[] = raw.teams.map((t) => ({
    name: t.sales_agent, manager: t.manager, office: t.regional_office,
  }));
  const sellerBy = new Map(sellers.map((s) => [s.name, s]));
  const priceBy = new Map(raw.products.map((p) => [p.product, Number(p.sales_price)]));
  const accountBy = new Map<string, Account>(raw.accounts.map((a) => [a.account, {
    name: a.account, sector: a.sector, revenue: Number(a.revenue), employees: Number(a.employees),
    country: a.office_location, parent: a.subsidiary_of || null,
  }]));

  let productNameFixed = 0;
  const opps: Opportunity[] = raw.pipeline.map((r) => {
    const fixed = PRODUCT_FIXES[r.product];
    if (fixed) productNameFixed++;
    const product = fixed ?? r.product;
    const seller = sellerBy.get(r.sales_agent)!;
    return {
      id: r.opportunity_id, seller: r.sales_agent, manager: seller.manager, office: seller.office,
      product, price: priceBy.get(product)!, account: r.account || null, stage: r.deal_stage as Stage,
      engageDate: date(r.engage_date), closeDate: date(r.close_date), closeValue: num(r.close_value),
    };
  });

  const bounds = boundsFrom([...priceBy.values()]);
  const isOpen = (o: Opportunity) => o.stage === 'Engaging' || o.stage === 'Prospecting';

  // Quem está com deal aberto em cada conta + produto (para o alerta de conflito).
  const openByPair = new Map<string, Set<string>>();
  for (const o of opps) {
    if (!isOpen(o) || !o.account) continue;
    const k = o.account + '|' + o.product;
    if (!openByPair.has(k)) openByPair.set(k, new Set());
    openByPair.get(k)!.add(o.seller);
  }

  const openDeals: OpenDeal[] = opps.filter(isOpen).map((o) => {
    const conflicts = o.account
      ? [...(openByPair.get(o.account + '|' + o.product) ?? [])].filter((s) => s !== o.seller).sort()
      : [];
    const base = { ...o, sector: o.account ? accountBy.get(o.account)?.sector ?? null : null, conflicts };
    if (o.stage !== 'Engaging' || !o.engageDate) {
      return { ...base, age: null, clock: null, bandLabel: null, winChance90d: null, scoring: null };
    }
    const age = daysBetween(o.engageDate, REF_DATE);
    const band = ageBand(age);
    return {
      ...base, age, clock: clockOf(age), bandLabel: band.label, winChance90d: band.p,
      scoring: scoreDeal(o.price, band.p, bounds),
    };
  });

  return {
    sellers,
    openDeals,
    secondChance: secondChanceList(opps, openByPair),
    profiles: sellerProfiles(opps),
    quality: dataQuality(opps, openDeals, sellers, productNameFixed),
  };
}

/**
 * Perdas há 30+ dias em conta + produto onde ninguém tem deal aberto hoje.
 * Uma linha por vendedor + conta + produto (a perda mais recente).
 */
function secondChanceList(opps: Opportunity[], openByPair: Map<string, Set<string>>): SecondChance[] {
  const latest = new Map<string, Opportunity>();
  for (const o of opps) {
    if (o.stage !== 'Lost' || !o.account || !o.closeDate) continue;
    if (openByPair.has(o.account + '|' + o.product)) continue;
    if (daysBetween(o.closeDate, REF_DATE) < SECOND_CHANCE_MIN_DAYS) continue;
    const k = [o.account, o.product, o.seller].join('|');
    const prev = latest.get(k);
    if (!prev || prev.closeDate! < o.closeDate) latest.set(k, o);
  }
  return [...latest.values()].map((o) => ({
    id: o.id, seller: o.seller, account: o.account!, product: o.product, price: o.price,
    lostOn: o.closeDate!, daysAgo: daysBetween(o.closeDate!, REF_DATE),
  }));
}

/**
 * Perfil = o que se repete de um semestre para o outro (análise 03):
 * volume (correlação 0,95) e ticket (0,71). Win rate NÃO entra (0,35).
 */
function sellerProfiles(opps: Opportunity[]): Record<string, SellerProfile> {
  const closed = opps.filter((o) => o.stage === 'Won' || o.stage === 'Lost');
  const months = new Set(closed.map((o) => o.closeDate!.toISOString().slice(0, 7))).size;
  const stats = new Map<string, { closed: number; won: number; revenue: number }>();
  for (const o of closed) {
    const s = stats.get(o.seller) ?? { closed: 0, won: 0, revenue: 0 };
    s.closed++;
    if (o.stage === 'Won') { s.won++; s.revenue += o.closeValue ?? 0; }
    stats.set(o.seller, s);
  }
  const rows = [...stats.entries()].map(([name, s]) => ({
    name, perMonth: s.closed / months, ticket: s.revenue / s.won, revenue: s.revenue,
  }));
  const medVol = median(rows.map((r) => r.perMonth));
  const medTicket = median(rows.map((r) => r.ticket));
  const out: Record<string, SellerProfile> = {};
  for (const r of rows) {
    const hv = r.perMonth >= medVol, ht = r.ticket >= medTicket;
    const label: ProfileLabel = hv && ht ? 'Volume + ticket alto' : hv ? 'Máquina de volume'
      : ht ? 'Caçador de ticket alto' : 'Em desenvolvimento';
    out[r.name] = { closedPerMonth: r.perMonth, avgTicket: r.ticket, wonRevenue: r.revenue, label };
  }
  return out;
}

function dataQuality(opps: Opportunity[], open: OpenDeal[], sellers: Seller[], fixed: number): DataQuality {
  const active = new Set(opps.map((o) => o.seller));
  return {
    productNameFixed: fixed,
    openWithoutAccount: open.filter((d) => !d.account).length,
    prospectingWithoutDate: open.filter((d) => d.stage === 'Prospecting' && !d.engageDate).length,
    sellersWithoutDeals: sellers.filter((s) => !active.has(s.name)).map((s) => s.name),
  };
}

/** Forecast dos próximos 90 dias para deals em Engaging: ingênuo × ajustado pela idade. */
export function forecast(deals: OpenDeal[]) {
  const engaging = deals.filter((d) => d.stage === 'Engaging');
  return {
    naive: engaging.reduce((s, d) => s + d.price, 0) * NAIVE_WIN_RATE,
    adjusted: engaging.reduce((s, d) => s + (d.scoring?.expectedValue ?? 0), 0),
  };
}

/** Deals vivos (Engaging fora da zona zumbi), ordenados pelo score. */
export function aliveByScore(deals: OpenDeal[]): OpenDeal[] {
  return deals
    .filter((d) => d.stage === 'Engaging' && d.clock !== 'zombie')
    .sort((a, b) => b.scoring!.score - a.scoring!.score || b.price - a.price);
}
