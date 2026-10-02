export const usd = (v: number) => 'US$ ' + Math.round(v).toLocaleString('pt-BR');

export const usdShort = (v: number) =>
  v >= 1e6 ? 'US$ ' + (v / 1e6).toFixed(2).replace('.', ',') + ' mi'
  : v >= 1e3 ? 'US$ ' + Math.round(v / 1e3) + ' mil'
  : usd(v);

export const pct = (p: number) => Math.round(p * 100) + '%';

export const dateBR = (d: Date) => d.toISOString().slice(0, 10).split('-').reverse().join('/');

export const sum = <T,>(xs: T[], f: (x: T) => number) => xs.reduce((s, x) => s + f(x), 0);
