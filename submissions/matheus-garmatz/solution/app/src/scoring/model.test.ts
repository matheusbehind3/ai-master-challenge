/**
 * Testes com os DADOS REAIS. Os números esperados vêm da análise em Python
 * (`solution/analysis/`), então este arquivo garante que o app e a análise
 * contam a mesma história.
 */
import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';
import { describe, expect, it } from 'vitest';
import { aliveByScore, buildModel, forecast, parseCsv } from './model';
import { boundsFrom, clockOf, scoreDeal } from './score';

const dir = resolve(__dirname, '../../public/data');
const read = (f: string) => parseCsv(readFileSync(resolve(dir, f), 'utf8'));
const model = buildModel({
  accounts: read('accounts.csv'), products: read('products.csv'),
  teams: read('sales_teams.csv'), pipeline: read('sales_pipeline.csv'),
});
const open = model.openDeals;

describe('limpeza e junção das 4 tabelas', () => {
  it('corrige o produto "GTXPro" (1.480 linhas) e todo deal tem preço', () => {
    expect(model.quality.productNameFixed).toBe(1480);
    expect(open.every((d) => d.price > 0)).toBe(true);
  });
  it('encontra os problemas de qualidade conhecidos', () => {
    expect(open.length).toBe(2089);
    expect(model.quality.openWithoutAccount).toBe(1425);
    expect(model.quality.prospectingWithoutDate).toBe(500);
    expect(model.quality.sellersWithoutDeals.sort()).toEqual(
      ['Carl Lin', 'Carol Thompson', 'Elizabeth Anderson', 'Mei-Mei Johns', 'Natalya Ivanova']);
  });
});

describe('relógio do deal', () => {
  it('usa os cortes 90 / 120 / 138 dias', () => {
    expect(clockOf(90)).toBe('healthy');
    expect(clockOf(91)).toBe('cooling');
    expect(clockOf(121)).toBe('lastChance');
    expect(clockOf(138)).toBe('lastChance');
    expect(clockOf(139)).toBe('zombie');
  });
  it('1.291 zumbis (US$ 3,2 mi) e 298 Engaging vivos', () => {
    const z = open.filter((d) => d.clock === 'zombie');
    expect(z.length).toBe(1291);
    expect(z.reduce((s, d) => s + d.price, 0)).toBe(3198664);
    expect(aliveByScore(open).length).toBe(298);
  });
});

describe('score', () => {
  const b = boundsFrom([55, 550, 1096, 3393, 4821, 5482, 26768]);
  it('zumbi tem score 0', () => {
    expect(scoreDeal(26768, 0, b).score).toBe(0);
  });
  it('score = pontos de valor + pontos de momento', () => {
    const s = scoreDeal(4821, 0.47, b);
    expect(s.valuePts + s.momentPts).toBe(s.score);
  });
  it('a ordem do score é a ordem do valor esperado', () => {
    const alive = aliveByScore(open);
    for (let i = 1; i < alive.length; i++) {
      if (alive[i - 1].scoring!.score > alive[i].scoring!.score) {
        expect(alive[i - 1].scoring!.expectedValue).toBeGreaterThan(alive[i].scoring!.expectedValue);
      }
    }
  });
  it('deal nº 1 da empresa: GTK 500 na Betasoloin, score 96 = +85 valor +11 momento', () => {
    const top = aliveByScore(open)[0];
    expect([top.product, top.account, top.seller]).toEqual(['GTK 500', 'Betasoloin', 'Rosalina Dieter']);
    expect(top.age).toBe(95);
    expect(top.scoring).toMatchObject({ score: 96, valuePts: 85, momentPts: 11 });
  });
});

describe('conflitos, segunda chance, perfis e forecast', () => {
  it('467 deals abertos têm outro vendedor na mesma conta + produto', () => {
    expect(open.filter((d) => d.conflicts.length > 0).length).toBe(467);
  });
  // A análise em Python dizia 1.702: um bug (pandas `row.product` é um método, não a coluna)
  // fazia o filtro "já existe deal aberto nesta conta + produto" nunca aplicar.
  // Este teste cruzado pegou o erro; o número correto é 489.
  it('489 oportunidades de segunda chance (sem deal aberto na mesma conta + produto)', () => {
    expect(model.secondChance.length).toBe(489);
    const openPairs = new Set(open.filter((d) => d.account).map((d) => d.account + '|' + d.product));
    expect(model.secondChance.some((s) => openPairs.has(s.account + '|' + s.product))).toBe(false);
    expect(model.secondChance.every((s) => s.daysAgo >= 30)).toBe(true);
  });
  it('perfis usam volume e ticket', () => {
    expect(model.profiles['Rosalina Dieter'].label).toBe('Caçador de ticket alto');
    expect(model.profiles['Anna Snelling'].label).toBe('Máquina de volume');
    expect(Math.round(model.profiles['Darcel Schlecht'].wonRevenue)).toBe(1153214);
  });
  it('forecast ajustado é bem menor que o ingênuo (zumbis valem 0)', () => {
    const f = forecast(open);
    expect(Math.round(f.naive)).toBe(Math.round(open.filter((d) => d.stage === 'Engaging')
      .reduce((s, d) => s + d.price, 0) * 0.62));
    expect(f.adjusted).toBeLessThan(f.naive / 5);
  });
});
