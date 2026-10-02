/**
 * Parâmetros do score. Todos vêm da análise em `solution/analysis/` —
 * nenhum número aqui é "chute". Se um dado novo mudar a análise, muda aqui.
 */

/** "Hoje" da ferramenta: último dia com dados no dataset. */
export const REF_DATE = new Date('2017-12-31T00:00:00Z');

/**
 * Chance de um deal em Engaging ser GANHO nos próximos 90 dias, pela idade dele.
 * Fonte: `analysis/04_backtest.py` — aprendido com snapshots mensais de 2017
 * (somente dados conhecidos antes de cada data de teste, suavizado com k=20).
 * Na faixa > 138 dias: 0 ganhos em 264 casos → 0.
 */
export const AGE_BANDS: { maxAge: number; label: string; p: number }[] = [
  { maxAge: 14, label: '0–14 dias', p: 0.43 },
  { maxAge: 30, label: '15–30 dias', p: 0.459 },
  { maxAge: 60, label: '31–60 dias', p: 0.485 },
  { maxAge: 90, label: '61–90 dias', p: 0.47 },
  { maxAge: 120, label: '91–120 dias', p: 0.362 },
  { maxAge: 138, label: '121–138 dias', p: 0.165 },
  { maxAge: Infinity, label: 'mais de 138 dias', p: 0 },
];

/** Limite histórico: nenhum deal fechado levou mais que isso (maior ciclo = 138 dias). */
export const ZOMBIE_AGE = 138;

/** Fases do relógio (mesmos cortes das faixas de chance). */
export const CLOCK_LIMITS = { healthy: 90, cooling: 120, lastChance: ZOMBIE_AGE };

/** Win rate histórico usado pelo forecast "ingênuo" (Won ÷ fechados). */
export const NAIVE_WIN_RATE = 0.62;

/** Segunda chance: perdas há pelo menos N dias (mediana de reabertura no histórico = 29 dias). */
export const SECOND_CHANCE_MIN_DAYS = 30;

/** Tamanho da fila "Foco da semana". */
export const FOCUS_SIZE = 10;

/** Nome digitado errado no pipeline (1.480 linhas) → nome do catálogo. */
export const PRODUCT_FIXES: Record<string, string> = { GTXPro: 'GTX Pro' };
