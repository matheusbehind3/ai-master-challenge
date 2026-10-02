"""Carregamento e junção das 4 tabelas — base de todos os scripts de análise."""
from pathlib import Path
import numpy as np
import pandas as pd

DATA = Path(__file__).resolve().parent.parent / 'app' / 'public' / 'data'
REF = pd.Timestamp('2017-12-31')  # "hoje": último dia com dados
ZOMBIE_AGE = 138                  # maior ciclo de qualquer deal fechado


def load() -> pd.DataFrame:
    p = pd.read_csv(DATA / 'sales_pipeline.csv', parse_dates=['engage_date', 'close_date'])
    p['product'] = p['product'].replace('GTXPro', 'GTX Pro')  # 1.480 linhas grafadas errado
    p = (p.merge(pd.read_csv(DATA / 'products.csv'), on='product', how='left')
          .merge(pd.read_csv(DATA / 'sales_teams.csv'), on='sales_agent', how='left')
          .merge(pd.read_csv(DATA / 'accounts.csv'), on='account', how='left'))
    p['won'] = np.where(p.deal_stage == 'Won', 1, np.where(p.deal_stage == 'Lost', 0, np.nan))
    p['cycle'] = (p.close_date - p.engage_date).dt.days
    return p


def closed_clean(p: pd.DataFrame) -> pd.DataFrame:
    """Deals fechados, sem a coorte de 2016 (perdas antes de mar/2017 não existem no dataset)."""
    return p[p.won.notna() & (p.engage_date >= '2017-01-01')].copy()


def title(t: str):
    print('\n' + '=' * 78 + '\n' + t + '\n' + '=' * 78)
