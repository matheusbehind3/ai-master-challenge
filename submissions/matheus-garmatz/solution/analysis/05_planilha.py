"""05 — Planilha relacional: as 4 tabelas ligadas por escritório › gerente › vendedor.
Saída: docs/crm_relacional_equipes.xlsx (fórmulas; Excel recalcula ao abrir).
"""
import pandas as pd, numpy as np
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.table import Table, TableStyleInfo
from openpyxl.formatting.rule import CellIsRule

from pathlib import Path
D = str(Path(__file__).resolve().parent.parent / 'app' / 'public' / 'data') + '/'
OUT = str(Path(__file__).resolve().parents[2] / 'docs' / 'crm_relacional_equipes.xlsx')

raw_p = pd.read_csv(D + 'sales_pipeline.csv')
acc = pd.read_csv(D + 'accounts.csv')
prod = pd.read_csv(D + 'products.csv')
team = pd.read_csv(D + 'sales_teams.csv')

p = raw_p.copy()
p['produto_corrigido'] = np.where(p['product'] == 'GTXPro', 'Sim (GTXPro → GTX Pro)', '')
p['product'] = p['product'].replace('GTXPro', 'GTX Pro')
p = p.merge(team, on='sales_agent', how='left').merge(prod, on='product', how='left').merge(acc, on='account', how='left')
p['engage_date'] = pd.to_datetime(p.engage_date)
p['close_date'] = pd.to_datetime(p.close_date)
order = {'Central': 0, 'East': 1, 'West': 2}
p = p.sort_values(['regional_office', 'manager', 'sales_agent', 'engage_date'], key=lambda s: s.map(order) if s.name == 'regional_office' else s)

# ---------- estilos ----------
F = 'Arial'
H_FILL = PatternFill('solid', fgColor='1F3864'); H_FONT = Font(name=F, bold=True, color='FFFFFF')
SUB_FILL = PatternFill('solid', fgColor='D9E1F2'); TOT_FILL = PatternFill('solid', fgColor='BDD7EE')
INPUT_FONT = Font(name=F, color='0000FF', bold=True); YELLOW = PatternFill('solid', fgColor='FFFF00')
BASE = Font(name=F, size=10); BOLD = Font(name=F, size=10, bold=True)
thin = Side(style='thin', color='BFBFBF')
USD = '$#,##0;($#,##0);-'; PCT = '0.0%'; INT = '#,##0;-#,##0;-'; DATE = 'yyyy-mm-dd'

def header(ws, row, cols, widths=None):
    for i, c in enumerate(cols, 1):
        cell = ws.cell(row=row, column=i, value=c)
        cell.font = H_FONT; cell.fill = H_FILL
        cell.alignment = Alignment(horizontal='center', vertical='center', wrap_text=True)
    ws.row_dimensions[row].height = 32
    if widths:
        for i, w in enumerate(widths, 1):
            ws.column_dimensions[get_column_letter(i)].width = w

def font_all(ws):
    for row in ws.iter_rows():
        for c in row:
            if c.font is None or c.font.name != F:
                c.font = Font(name=F, size=c.font.size if c.font and c.font.size else 10, bold=c.font.bold if c.font else False,
                              color=c.font.color if c.font else None)

wb = Workbook()

# ================= Premissas / Leia-me =================
ws = wb.active; ws.title = 'Leia-me'
ws.column_dimensions['A'].width = 34; ws.column_dimensions['B'].width = 18; ws.column_dimensions['C'].width = 90
ws['A1'] = 'CRM relacional — Escritório › Gerente › Vendedor › Deal › Conta › Produto'; ws['A1'].font = Font(name=F, size=14, bold=True)
ws['A2'] = 'Todas as 4 tabelas do dataset ligadas com exatidão. Os números das abas de resumo são fórmulas sobre a aba Pipeline_Completo.'; ws['A2'].font = BASE

ws['A4'] = 'PREMISSAS (editáveis)'; ws['A4'].font = BOLD
prem = [
    ('Data de referência ("hoje")', pd.Timestamp('2017-12-31'), 'Último dia com dados no dataset. Usada para calcular a idade dos deals abertos.'),
    ('Limite "Saudável" (dias)', 88, 'Até aqui = dentro do tempo em que ~75% dos deals ganhos fecham (p75 do ciclo dos ganhos = 85 dias).'),
    ('Limite "Esfriando" (dias)', 120, '~95% dos deals ganhos fecharam até 114 dias.'),
    ('Limite "Zumbi" (dias)', 138, 'Maior ciclo de qualquer deal fechado no histórico. Acima disso nenhum deal jamais fechou.'),
]
for i, (k, v, note) in enumerate(prem, 5):
    ws.cell(row=i, column=1, value=k).font = BASE
    c = ws.cell(row=i, column=2, value=v); c.font = INPUT_FONT; c.fill = YELLOW
    if i == 5: c.number_format = DATE
    ws.cell(row=i, column=3, value=note).font = BASE
REF, L1, L2, L3 = "'Leia-me'!$B$5", "'Leia-me'!$B$6", "'Leia-me'!$B$7", "'Leia-me'!$B$8"

ws['A11'] = 'COMO AS TABELAS SE LIGAM'; ws['A11'].font = BOLD
rel = [
    ('sales_pipeline.sales_agent', '→ sales_teams', 'Cada deal tem 1 vendedor; cada vendedor tem 1 gerente e 1 escritório regional.'),
    ('sales_pipeline.product', '→ products', 'Preço de tabela e série. Corrigido: "GTXPro" (1.480 linhas) não existia em products → tratado como "GTX Pro".'),
    ('sales_pipeline.account', '→ accounts', 'Setor, receita, funcionários, país, empresa-mãe. 1.425 deals abertos NÃO têm conta preenchida.'),
    ('Hierarquia', '3 › 6 › 35', '3 escritórios › 6 gerentes (2 por escritório) › 35 vendedores. 5 vendedores não têm nenhum deal.'),
]
for i, r in enumerate(rel, 12):
    for j, v in enumerate(r, 1):
        ws.cell(row=i, column=j, value=v).font = BASE

ws['A17'] = 'DEFINIÇÕES'; ws['A17'].font = BOLD
defs = [
    ('Receita ganha', '', 'Soma de close_value dos deals Won (valor real fechado).'),
    ('Pipeline aberto (estimado)', '', 'Deals Engaging + Prospecting não têm close_value. Usamos o preço de tabela do produto (nos ganhos, close_value ≈ preço de tabela, desvio médio < 1%).'),
    ('Win rate', '', 'Won ÷ (Won + Lost). Atenção: deals iniciados em 2016 têm win rate inflado (82%) porque perdas antes de mar/2017 não estão no dataset.'),
    ('Relógio do deal', '', 'Só para Engaging: Saudável / Esfriando / Última chance / Zumbi, pela idade na data de referência e pelos limites acima.'),
    ('Ciclo (dias)', '', 'close_date − engage_date (deals fechados).'),
]
for i, r in enumerate(defs, 18):
    for j, v in enumerate(r, 1):
        c = ws.cell(row=i, column=j, value=v); c.font = BASE; c.alignment = Alignment(wrap_text=True, vertical='top')

ws['A24'] = 'ABAS'; ws['A24'].font = BOLD
tabs = [
    ('Hierarquia', 'Escritório › Gerente › Vendedor com todos os números de cada um, subtotais por gerente e escritório.'),
    ('Resumo_Escritorio / Resumo_Gerente', 'Visão consolidada por nível.'),
    ('Produto_x_Gerente', 'Receita ganha e pipeline aberto de cada produto, por equipe.'),
    ('Contas', 'Cada conta com seus números e quantos vendedores/gerentes/escritórios mexem nela.'),
    ('Pipeline_Completo', 'As 8.800 oportunidades com TODAS as colunas das 4 tabelas lado a lado (filtrável).'),
    ('Qualidade_Dados', 'Problemas encontrados nos dados, com contagem.'),
    ('raw_*', 'Os 4 CSVs originais, sem alteração, para auditoria.'),
]
for i, (a, b) in enumerate(tabs, 25):
    ws.cell(row=i, column=1, value=a).font = BOLD; ws.cell(row=i, column=3, value=b).font = BASE
ws['A33'] = 'Legenda: texto azul com fundo amarelo = premissa editável. Demais números = fórmulas.'; ws['A33'].font = Font(name=F, size=9, italic=True)

# ================= Pipeline_Completo =================
pc = wb.create_sheet('Pipeline_Completo')
cols = ['opportunity_id', 'Escritório', 'Gerente', 'Vendedor', 'Conta', 'Setor', 'Receita conta (US$ mi)', 'Funcionários',
        'País sede', 'Empresa-mãe', 'Ano fundação', 'Produto', 'Série', 'Preço tabela (US$)', 'Estágio', 'engage_date',
        'close_date', 'close_value (US$)', 'Valor considerado (US$)', 'Ciclo (dias)', 'Idade aberto (dias)', 'Relógio',
        'Ganho (1/0)', 'Produto corrigido?', 'Conta faltando?']
header(pc, 1, cols, [12, 10, 16, 18, 20, 14, 12, 11, 12, 16, 9, 14, 7, 11, 11, 11, 11, 11, 12, 8, 9, 13, 7, 14, 9])
n = len(p)
for i, r in enumerate(p.itertuples(index=False), 2):
    vals = [r.opportunity_id, r.regional_office, r.manager, r.sales_agent, r.account if pd.notna(r.account) else None,
            r.sector if pd.notna(r.sector) else None, r.revenue if pd.notna(r.revenue) else None,
            int(r.employees) if pd.notna(r.employees) else None, r.office_location if pd.notna(r.office_location) else None,
            r.subsidiary_of if pd.notna(r.subsidiary_of) else None, int(r.year_established) if pd.notna(r.year_established) else None,
            r.product, r.series, int(r.sales_price), r.deal_stage,
            r.engage_date.to_pydatetime() if pd.notna(r.engage_date) else None,
            r.close_date.to_pydatetime() if pd.notna(r.close_date) else None,
            r.close_value if pd.notna(r.close_value) else None]
    for j, v in enumerate(vals, 1):
        pc.cell(row=i, column=j, value=v)
    # S: valor considerado — Won=close_value, Lost=0, aberto=preço tabela
    pc.cell(row=i, column=19, value=f'=IF(O{i}="Won",R{i},IF(O{i}="Lost",0,N{i}))')
    pc.cell(row=i, column=20, value=f'=IF(AND(P{i}<>"",Q{i}<>""),Q{i}-P{i},"")')
    pc.cell(row=i, column=21, value=f'=IF(AND(O{i}="Engaging",P{i}<>""),{REF}-P{i},"")')
    pc.cell(row=i, column=22, value=f'=IF(O{i}<>"Engaging","",IF(U{i}<={L1},"Saudável",IF(U{i}<={L2},"Esfriando",IF(U{i}<={L3},"Última chance","Zumbi"))))')
    pc.cell(row=i, column=23, value=f'=IF(O{i}="Won",1,IF(O{i}="Lost",0,""))')
    pc.cell(row=i, column=24, value=r.produto_corrigido or None)
    pc.cell(row=i, column=25, value=f'=IF(E{i}="","Sim","")')
last = n + 1
for col, fmt in [('N', USD), ('R', USD), ('S', USD), ('G', '#,##0.00'), ('H', '#,##0'), ('P', DATE), ('Q', DATE), ('T', INT), ('U', INT)]:
    for c in pc[f'{col}2:{col}{last}']:
        c[0].number_format = fmt
tab = Table(displayName='Pipeline', ref=f'A1:Y{last}')
tab.tableStyleInfo = TableStyleInfo(name='TableStyleLight9', showRowStripes=True)
pc.add_table(tab); pc.freeze_panes = 'E2'

# helper ranges
R = lambda col: f"Pipeline_Completo!${col}$2:${col}${last}"
OFF, MGR, AG, ACC, PRD, STG, VAL, REL, CV = R('B'), R('C'), R('D'), R('E'), R('L'), R('O'), R('S'), R('V'), R('R')

def metric_formulas(crit):  # crit: list of (range, ref) pairs → returns dict col->formula
    c = ','.join(f'{rg},{rf}' for rg, rf in crit)
    return [
        f'=COUNTIFS({c})',
        f'=COUNTIFS({c},{STG},"Won")',
        f'=COUNTIFS({c},{STG},"Lost")',
        f'=COUNTIFS({c},{STG},"Engaging")',
        f'=COUNTIFS({c},{STG},"Prospecting")',
        None,  # win rate (computed from row)
        f'=SUMIFS({CV},{c},{STG},"Won")',
        None,  # ticket médio
        f'=SUMIFS({VAL},{c},{STG},"Engaging")+SUMIFS({VAL},{c},{STG},"Prospecting")',
        f'=COUNTIFS({c},{REL},"Saudável")+COUNTIFS({c},{REL},"Esfriando")+COUNTIFS({c},{REL},"Última chance")',
        f'=SUMIFS({VAL},{c},{REL},"Saudável")+SUMIFS({VAL},{c},{REL},"Esfriando")+SUMIFS({VAL},{c},{REL},"Última chance")',
        f'=COUNTIFS({c},{REL},"Zumbi")',
        f'=SUMIFS({VAL},{c},{REL},"Zumbi")',
        None,  # % pipeline zumbi
        f'=COUNTIFS({c},{STG},"Engaging",{ACC},"")+COUNTIFS({c},{STG},"Prospecting",{ACC},"")',
    ]
MET = ['Deals total', 'Won', 'Lost', 'Engaging', 'Prospecting', 'Win rate', 'Receita ganha (US$)', 'Ticket médio ganho (US$)',
       'Pipeline aberto (US$)', 'Engaging vivos (≤ limite zumbi)', 'Valor vivos (US$)', 'Zumbis', 'Valor zumbi (US$)',
       '% pipeline Engaging zumbi', 'Abertos sem conta']
MFMT = [INT, INT, INT, INT, INT, PCT, USD, USD, USD, INT, USD, INT, USD, PCT, INT]

def write_metrics(ws, row, first_col, formulas, sum_rows=None):
    """formulas list or, if sum_rows given, SUM of those rows."""
    for k in range(len(MET)):
        col = first_col + k; L = get_column_letter(col)
        if MET[k] == 'Win rate':
            f = f'=IFERROR({get_column_letter(first_col+1)}{row}/({get_column_letter(first_col+1)}{row}+{get_column_letter(first_col+2)}{row}),"")'
        elif MET[k].startswith('Ticket'):
            f = f'=IFERROR({get_column_letter(first_col+6)}{row}/{get_column_letter(first_col+1)}{row},"")'
        elif MET[k].startswith('% pipeline'):
            f = f'=IFERROR({get_column_letter(first_col+12)}{row}/({get_column_letter(first_col+10)}{row}+{get_column_letter(first_col+12)}{row}),"")'
        elif sum_rows is not None:
            f = '=' + '+'.join(f'{L}{r}' for r in sum_rows) if len(sum_rows) < 12 else f'=SUM({L}{sum_rows[0]}:{L}{sum_rows[-1]})'
        else:
            f = formulas[k]
        c = ws.cell(row=row, column=col, value=f); c.number_format = MFMT[k]; c.font = BASE

# ================= Hierarquia =================
h = wb.create_sheet('Hierarquia', 1)
hcols = ['Escritório', 'Gerente', 'Vendedor'] + MET
header(h, 1, hcols, [11, 17, 19] + [10, 8, 8, 9, 10, 8, 13, 11, 13, 11, 13, 8, 13, 11, 9])
row = 2; office_rows = []; total_rows = []
for off in ['Central', 'East', 'West']:
    mgr_tot_rows = []
    for mgr in team[team.regional_office == off].manager.unique():
        agent_rows = []
        for ag in team[team.manager == mgr].sales_agent:
            h.cell(row=row, column=1, value=off).font = BASE
            h.cell(row=row, column=2, value=mgr).font = BASE
            h.cell(row=row, column=3, value=ag).font = BASE
            write_metrics(h, row, 4, metric_formulas([(AG, f'$C{row}')]))
            agent_rows.append(row); row += 1
        # subtotal gerente (fórmula direta por gerente — independe da lista)
        for cc in range(1, 4 + len(MET)):
            h.cell(row=row, column=cc).fill = SUB_FILL
        h.cell(row=row, column=1, value=off).font = BOLD
        h.cell(row=row, column=2, value=mgr).font = BOLD
        h.cell(row=row, column=3, value=f'Subtotal {mgr}').font = BOLD
        write_metrics(h, row, 4, metric_formulas([(MGR, f'$B{row}')]))
        for cc in range(4, 4 + len(MET)): h.cell(row=row, column=cc).font = BOLD
        mgr_tot_rows.append(row); row += 1
    for cc in range(1, 4 + len(MET)):
        h.cell(row=row, column=cc).fill = TOT_FILL
    h.cell(row=row, column=1, value=off).font = BOLD
    h.cell(row=row, column=3, value=f'TOTAL escritório {off}').font = BOLD
    write_metrics(h, row, 4, metric_formulas([(OFF, f'$A{row}')]))
    for cc in range(4, 4 + len(MET)): h.cell(row=row, column=cc).font = BOLD
    office_rows.append(row); row += 2
h.cell(row=row, column=3, value='TOTAL GERAL').font = BOLD
write_metrics(h, row, 4, None, sum_rows=office_rows)
for cc in range(1, 4 + len(MET)):
    h.cell(row=row, column=cc).fill = H_FILL; h.cell(row=row, column=cc).font = H_FONT
h.freeze_panes = 'D2'
# destaque: vendedores sem deals
h.conditional_formatting.add(f'D2:D{row}', CellIsRule(operator='equal', formula=['0'], fill=PatternFill('solid', fgColor='F8CBAD')))
h.cell(row=row + 2, column=1, value='Linhas em laranja (Deals total = 0): vendedores cadastrados em sales_teams sem nenhuma oportunidade no pipeline.').font = Font(name=F, size=9, italic=True)
h.cell(row=row + 3, column=1, value='Check: TOTAL GERAL de "Deals total" deve ser 8.800 →').font = Font(name=F, size=9, italic=True)
h.cell(row=row + 3, column=4, value=f'=IF(D{row}=COUNTA(Pipeline_Completo!$A$2:$A${last}),"OK","ERRO")').font = BOLD

# ================= Resumo_Escritorio / Resumo_Gerente =================
def summary(name, key_label, keys, rng, extra=None):
    s = wb.create_sheet(name)
    cols = [key_label] + (['Escritório'] if extra else []) + ['Vendedores (cadastrados)', 'Vendedores ativos'] + MET
    header(s, 1, cols, [18] + ([11] if extra else []) + [11, 10] + [10, 8, 8, 9, 10, 8, 13, 11, 13, 11, 13, 8, 13, 11, 9])
    off = 1 + (1 if extra else 0)
    for i, k in enumerate(keys, 2):
        s.cell(row=i, column=1, value=k).font = BOLD
        if extra: s.cell(row=i, column=2, value=extra[k]).font = BASE
        keycol = 'regional_office' if key_label == 'Escritório' else 'manager'
        s.cell(row=i, column=off + 1, value=int((team[keycol] == k).sum())).font = BASE
        s.cell(row=i, column=off + 1).number_format = INT
        act = int(p[p[keycol] == k].sales_agent.nunique())
        c = s.cell(row=i, column=off + 2, value=act); c.font = BASE
        write_metrics(s, i, off + 3, metric_formulas([(rng, f'$A{i}')]))
    t = len(keys) + 2
    s.cell(row=t, column=1, value='TOTAL').font = BOLD
    for cc in range(off + 1, off + 3 + len(MET) + 1):
        L = get_column_letter(cc)
        s.cell(row=t, column=cc, value=f'=SUM({L}2:{L}{t-1})')
    write_metrics(s, t, off + 3, None, sum_rows=list(range(2, t)))
    for cc in range(1, off + 3 + len(MET)):
        s.cell(row=t, column=cc).fill = TOT_FILL; s.cell(row=t, column=cc).font = BOLD
    s.cell(row=t + 2, column=1, value='"Vendedores cadastrados"/"ativos" são contagens fixas (sales_teams.csv e vendedores com ≥1 deal).').font = Font(name=F, size=9, italic=True)
    s.freeze_panes = 'B2'
summary('Resumo_Escritorio', 'Escritório', ['Central', 'East', 'West'], OFF)
mgr_off = dict(zip(team.manager, team.regional_office))
summary('Resumo_Gerente', 'Gerente', list(dict.fromkeys(team.manager)), MGR, extra=mgr_off)

# ================= Produto_x_Gerente =================
px = wb.create_sheet('Produto_x_Gerente')
mgrs = list(dict.fromkeys(team.manager)); prods = prod.sort_values('sales_price')['product'].tolist()
px['A1'] = 'Receita ganha (US$) — produto × gerente'; px['A1'].font = Font(name=F, size=12, bold=True)
def matrix(top, metric):
    px.cell(row=top, column=1, value='Produto').font = H_FONT; px.cell(row=top, column=1).fill = H_FILL
    px.cell(row=top, column=2, value='Preço tabela').font = H_FONT; px.cell(row=top, column=2).fill = H_FILL
    for j, m in enumerate(mgrs, 3):
        c = px.cell(row=top, column=j, value=m); c.font = H_FONT; c.fill = H_FILL; c.alignment = Alignment(wrap_text=True, horizontal='center')
        px.cell(row=top - 1, column=j, value=mgr_off[m]).font = Font(name=F, size=9, italic=True)
    tc = 3 + len(mgrs); c = px.cell(row=top, column=tc, value='Total'); c.font = H_FONT; c.fill = H_FILL
    for i, pr in enumerate(prods, top + 1):
        px.cell(row=i, column=1, value=pr).font = BOLD
        px.cell(row=i, column=2, value=int(prod.set_index('product').sales_price[pr])).number_format = USD
        for j in range(3, tc):
            Lh = get_column_letter(j)
            if metric == 'won':
                f = f'=SUMIFS({CV},{PRD},$A{i},{MGR},{Lh}${top},{STG},"Won")'
            elif metric == 'open':
                f = f'=SUMIFS({VAL},{PRD},$A{i},{MGR},{Lh}${top},{STG},"Engaging")+SUMIFS({VAL},{PRD},$A{i},{MGR},{Lh}${top},{STG},"Prospecting")'
            else:
                f = f'=IFERROR(COUNTIFS({PRD},$A{i},{MGR},{Lh}${top},{STG},"Won")/(COUNTIFS({PRD},$A{i},{MGR},{Lh}${top},{STG},"Won")+COUNTIFS({PRD},$A{i},{MGR},{Lh}${top},{STG},"Lost")),"")'
            c = px.cell(row=i, column=j, value=f); c.number_format = PCT if metric == 'wr' else USD; c.font = BASE
        Lf, Ll = get_column_letter(3), get_column_letter(tc - 1)
        if metric == 'wr':
            f = f'=IFERROR(COUNTIFS({PRD},$A{i},{STG},"Won")/(COUNTIFS({PRD},$A{i},{STG},"Won")+COUNTIFS({PRD},$A{i},{STG},"Lost")),"")'
        else:
            f = f'=SUM({Lf}{i}:{Ll}{i})'
        c = px.cell(row=i, column=tc, value=f); c.number_format = PCT if metric == 'wr' else USD; c.font = BOLD
    b = top + 1 + len(prods)
    px.cell(row=b, column=1, value='Total').font = BOLD
    if metric != 'wr':
        for j in range(3, tc + 1):
            L = get_column_letter(j); c = px.cell(row=b, column=j, value=f'=SUM({L}{top+1}:{L}{b-1})'); c.number_format = USD; c.font = BOLD; c.fill = TOT_FILL
    return b
b = matrix(4, 'won')
px.cell(row=b + 2, column=1, value='Pipeline aberto (US$, preço de tabela) — produto × gerente').font = Font(name=F, size=12, bold=True)
b = matrix(b + 5, 'open')
px.cell(row=b + 2, column=1, value='Win rate — produto × gerente (Won ÷ fechados)').font = Font(name=F, size=12, bold=True)
matrix(b + 5, 'wr')
px.column_dimensions['A'].width = 16; px.column_dimensions['B'].width = 11
for j in range(3, 4 + len(mgrs)): px.column_dimensions[get_column_letter(j)].width = 15

# ================= Contas =================
ct = wb.create_sheet('Contas')
ccols = ['Conta', 'Setor', 'País sede', 'Empresa-mãe', 'Receita (US$ mi)', 'Funcionários', 'Deals total', 'Won', 'Lost', 'Abertos',
         'Win rate', 'Receita ganha (US$)', 'Pipeline aberto (US$)', 'Nº vendedores que atuam', 'Nº gerentes', 'Nº escritórios', 'Vendedor com mais deals']
header(ct, 1, ccols, [24, 14, 13, 18, 11, 11, 9, 7, 7, 8, 9, 13, 13, 11, 9, 9, 22])
pa = p.dropna(subset=['account'])
for i, a in enumerate(acc.sort_values('account').itertuples(index=False), 2):
    s = pa[pa.account == a.account]
    vals = [a.account, a.sector, a.office_location, a.subsidiary_of if pd.notna(a.subsidiary_of) else None, a.revenue, a.employees]
    for j, v in enumerate(vals, 1): ct.cell(row=i, column=j, value=v).font = BASE
    ct.cell(row=i, column=7, value=f'=COUNTIFS({ACC},$A{i})')
    ct.cell(row=i, column=8, value=f'=COUNTIFS({ACC},$A{i},{STG},"Won")')
    ct.cell(row=i, column=9, value=f'=COUNTIFS({ACC},$A{i},{STG},"Lost")')
    ct.cell(row=i, column=10, value=f'=G{i}-H{i}-I{i}')
    ct.cell(row=i, column=11, value=f'=IFERROR(H{i}/(H{i}+I{i}),"")').number_format = PCT
    ct.cell(row=i, column=12, value=f'=SUMIFS({CV},{ACC},$A{i},{STG},"Won")').number_format = USD
    ct.cell(row=i, column=13, value=f'=SUMIFS({VAL},{ACC},$A{i},{STG},"Engaging")+SUMIFS({VAL},{ACC},$A{i},{STG},"Prospecting")').number_format = USD
    ct.cell(row=i, column=14, value=int(s.sales_agent.nunique()))
    ct.cell(row=i, column=15, value=int(s.manager.nunique()))
    ct.cell(row=i, column=16, value=int(s.regional_office.nunique()))
    ct.cell(row=i, column=17, value=s.sales_agent.value_counts().index[0] if len(s) else None)
    ct.cell(row=i, column=5).number_format = '#,##0.00'; ct.cell(row=i, column=6).number_format = '#,##0'
lr = len(acc) + 1
ct.cell(row=lr + 2, column=1, value='Nº vendedores/gerentes/escritórios: contagem distinta calculada a partir do pipeline (valor fixo).').font = Font(name=F, size=9, italic=True)
ct.cell(row=lr + 3, column=1, value='Achado: nenhuma conta tem "dono" — em média ~15 vendedores de ~3 escritórios mexem na mesma conta.').font = Font(name=F, size=9, italic=True, bold=True)
ct.cell(row=lr + 4, column=1, value='Deals SEM conta (todos abertos):').font = BOLD
ct.cell(row=lr + 4, column=7, value=f'=COUNTIFS({ACC},"")-COUNTBLANK(Pipeline_Completo!$A$2:$A${last})')
ct.auto_filter.ref = f'A1:Q{lr}'; ct.freeze_panes = 'B2'

# ================= Qualidade_Dados =================
q = wb.create_sheet('Qualidade_Dados')
header(q, 1, ['Problema', 'Qtde', 'Impacto / tratamento'], [52, 10, 90])
issues = [
    ('Produto "GTXPro" grafado sem espaço (não existe em products)', f'=COUNTIFS(Pipeline_Completo!$X$2:$X${last},"Sim*")', 'Sem correção, 1.480 deals ficam sem preço/série. Tratado como "GTX Pro".'),
    ('Deals abertos sem conta preenchida', f'=COUNTIFS({ACC},"")-COUNTBLANK(Pipeline_Completo!$A$2:$A${last})', 'Não dá pra saber setor/porte. Ação no CRM: vincular conta.'),
    ('Deals em Prospecting sem engage_date', f'=COUNTIFS({STG},"Prospecting")', 'Sem data nenhuma: impossível medir idade. Ordenar só por valor.'),
    ('Deals Engaging acima do limite zumbi', f'=COUNTIFS({REL},"Zumbi")', 'Mais velhos que qualquer deal já fechado. Inflam o pipeline.'),
    ('Vendedores cadastrados sem nenhum deal', '=COUNTIFS(Hierarquia!$D:$D,0)', 'Carl Lin, Natalya Ivanova, Carol Thompson, Mei-Mei Johns, Elizabeth Anderson.'),
    ('Setor "technolgy" (erro de digitação na origem)', '=COUNTIFS(raw_accounts!$B:$B,"technolgy")', 'Mantido como está (nº de contas), não afeta cruzamentos.'),
    ('Deals iniciados em 2016 (win rate inflado)', f'=COUNTIFS(Pipeline_Completo!$P$2:$P${last},"<"&DATE(2017,1,1),{STG},"Won")+COUNTIFS(Pipeline_Completo!$P$2:$P${last},"<"&DATE(2017,1,1),{STG},"Lost")', 'close_date só existe a partir de 01/03/2017 → perdas antigas sumiram. Excluir de análises de win rate.'),
]
for i, (a, b_, c_) in enumerate(issues, 2):
    q.cell(row=i, column=1, value=a).font = BASE
    q.cell(row=i, column=2, value=b_).font = BOLD; q.cell(row=i, column=2).number_format = INT
    cc = q.cell(row=i, column=3, value=c_); cc.font = BASE; cc.alignment = Alignment(wrap_text=True)

# ================= raw =================
for nm, df in [('raw_sales_pipeline', raw_p), ('raw_accounts', acc), ('raw_products', prod), ('raw_sales_teams', team)]:
    w = wb.create_sheet(nm)
    header(w, 1, list(df.columns), [16] * len(df.columns))
    for r in df.itertuples(index=False):
        w.append([None if (isinstance(v, float) and np.isnan(v)) else v for v in r])
    w.freeze_panes = 'A2'

# fonte global
for w in wb.worksheets:
    for rw in w.iter_rows():
        for c in rw:
            if c.value is not None and (c.font.name != F):
                c.font = Font(name=F, size=10, bold=c.font.bold, color=c.font.color, italic=c.font.italic)

wb.save(OUT)
print('saved', OUT)
