import { AGE_BANDS, CLOCK_LIMITS } from './config';
import type { Clock, ScoreParts } from './types';

const DAY = 86_400_000;

export function daysBetween(from: Date, to: Date): number {
  return Math.round((to.getTime() - from.getTime()) / DAY);
}

export function ageBand(age: number) {
  return AGE_BANDS.find((b) => age <= b.maxAge)!;
}

export function clockOf(age: number): Clock {
  if (age <= CLOCK_LIMITS.healthy) return 'healthy';
  if (age <= CLOCK_LIMITS.cooling) return 'cooling';
  if (age <= CLOCK_LIMITS.lastChance) return 'lastChance';
  return 'zombie';
}

export interface ScoreBounds {
  minPrice: number;
  maxPrice: number;
  minChance: number; // menor chance > 0
  maxChance: number;
}

export function boundsFrom(prices: number[]): ScoreBounds {
  const chances = AGE_BANDS.map((b) => b.p).filter((p) => p > 0);
  return {
    minPrice: Math.min(...prices),
    maxPrice: Math.max(...prices),
    minChance: Math.min(...chances),
    maxChance: Math.max(...chances),
  };
}

/**
 * Score = valor esperado (preço × chance de ganhar em 90 dias) numa escala 1–100.
 *
 * Usa escala logarítmica porque os preços vão de US$ 55 a US$ 26.768 (≈ 500×):
 * em escala linear, quase todo deal teria score 0. Como log(preço × chance) =
 * log(preço) + log(chance), o score se divide exatamente em duas partes que o
 * vendedor entende: "pontos de valor" + "pontos de momento".
 *
 * A ordem dos deals é idêntica à do valor esperado — a mesma lógica validada
 * no backtest (`analysis/04_backtest.py`).
 */
export function scoreDeal(price: number, chance: number, b: ScoreBounds): ScoreParts {
  if (chance <= 0) return { score: 0, valuePts: 0, momentPts: 0, expectedValue: 0 };
  const range = Math.log((b.maxPrice * b.maxChance) / (b.minPrice * b.minChance));
  const raw = (100 * Math.log((price * chance) / (b.minPrice * b.minChance))) / range;
  const score = Math.max(1, Math.round(raw));
  const valuePts = Math.round((100 * Math.log(price / b.minPrice)) / range);
  return {
    score,
    valuePts,
    momentPts: score - valuePts,
    expectedValue: price * chance,
  };
}
