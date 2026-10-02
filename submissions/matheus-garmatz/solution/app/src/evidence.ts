/**
 * Resultados da análise exibidos na aba "Por que confiar".
 * Todos são reproduzíveis rodando os scripts em `solution/analysis/`
 * (saídas salvas em `solution/analysis/results/`).
 */

/** 04_backtest.py — top 10 por vendedor em 4 datas (jul–out/2017), receita ganha em 90 dias. */
export const BACKTEST = [
  { name: 'Nossa lógica (valor × idade)', revenue: 2346145, zombieShare: 0.01, ours: true },
  { name: 'Só ordenar por valor', revenue: 2090131, zombieShare: 0.13 },
  { name: '"Baseline de IA" (valor × win rate vendedor/produto)', revenue: 2085209, zombieShare: 0.12 },
  { name: 'Mais novos primeiro', revenue: 1109819, zombieShare: 0 },
  { name: 'Aleatório (o "feeling")', revenue: 873779, zombieShare: 0.14 },
  { name: 'Mais antigos primeiro', revenue: 549131, zombieShare: 0.53 },
];

export const PAIRED = { better: 56, equal: 51, worse: 13, gainPerSellerMonth: 3686, ciLow: 2500, ciHigh: 4812 };

export const FORECAST_BACKTEST = { naiveError: '+83% a +190%', adjustedError: '+38% a +60%' };

export const DISCARDED: [string, string][] = [
  ['Win rate do vendedor, produto, conta, setor, região', 'Não prevê o resultado em dados futuros (AUC 0,47–0,51; 0,50 = cara ou coroa)'],
  ['Modelo de machine learning com todas as variáveis', '99,7% de acerto no passado, 50,7% no futuro — decorou, não aprendeu'],
  ['"Vendedor X é bom no produto Y"', 'Não se repete de um semestre para o outro (correlação −0,01)'],
  ['Histórico da conta, fase recente do vendedor, carga de deals, dia da semana', 'Sem sinal'],
  ['"Primeiro deal com a conta ganha mais"', 'Parecia +3,5 pontos; sumiu ao controlar pelo trimestre (efeito do calendário)'],
  ['Fim de trimestre (80% de vitória no 3º mês vs 49% no 1º)', 'Sinal forte, mas vale para todos os deals ao mesmo tempo → não muda a ordem; vira contexto'],
];

export const HUMAN_IN_LOOP: [string, string, string][] = [
  ['Marca e explica deals zumbis', 'O vendedor mantém ou encerra', 'O CRM não registra ligações e reuniões; o vendedor pode saber de algo que o sistema não vê'],
  ['Avisa conflito de conta', 'Vendedores e gerente combinam quem segue', '5.149 casos em que dois vendedores ganharam o mesmo produto na mesma conta — bloquear mataria receita'],
  ['Lista a segunda chance', 'O vendedor escolhe reabordar', 'O motivo da perda não está no CRM'],
  ['Calcula o score com regras fixas', 'O vendedor pode discordar (fica registrado)', 'Auditável e explicável; as decisões viram o dado de atividade que hoje falta'],
];
