import { useEffect, useMemo, useState } from 'react';
import { buildModel, parseCsv } from './scoring/model';
import type { Model } from './scoring/types';
import { SellerView } from './components/SellerView';
import { ManagerView } from './components/ManagerView';
import { TrustView } from './components/TrustView';

type Role = 'vend' | 'ger' | 'conf';
const DEMO_SELLER = 'Rosalina Dieter'; // dona do deal nº 1 da empresa (GTK 500 na Betasoloin)
const STORAGE_KEY = 'radar-decisions-v1';

async function loadModel(): Promise<Model> {
  const files = ['accounts', 'products', 'sales_teams', 'sales_pipeline'];
  const [accounts, products, teams, pipeline] = await Promise.all(
    files.map((f) => fetch(`${import.meta.env.BASE_URL}data/${f}.csv`).then((r) => r.text()).then(parseCsv)),
  );
  return buildModel({ accounts, products, teams, pipeline });
}

/** Decisões do vendedor. No protótipo ficam no navegador; em produção iriam para o CRM. */
function useDecisions() {
  const [decisions, setDecisions] = useState<Record<string, string>>(() => {
    try { return JSON.parse(localStorage.getItem(STORAGE_KEY) ?? '{}'); } catch { return {}; }
  });
  const decide = (id: string, label: string) => {
    const next = { ...decisions, [id]: label };
    setDecisions(next);
    try { localStorage.setItem(STORAGE_KEY, JSON.stringify(next)); } catch { /* navegador sem storage */ }
  };
  const reset = () => {
    setDecisions({});
    try { localStorage.removeItem(STORAGE_KEY); } catch { /* idem */ }
  };
  return { decisions, decide, reset };
}

export default function App() {
  const [model, setModel] = useState<Model | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [role, setRole] = useState<Role>('vend');
  const [office, setOffice] = useState('');
  const [manager, setManager] = useState('');
  const [seller, setSeller] = useState(DEMO_SELLER);
  const [toast, setToast] = useState<string | null>(null);
  const { decisions, decide, reset } = useDecisions();

  useEffect(() => { loadModel().then(setModel).catch((e) => setError(String(e))); }, []);
  useEffect(() => { window.scrollTo(0, 0); }, [role, seller]);

  const scoped = useMemo(() => (model?.sellers ?? []).filter(
    (s) => (!office || s.office === office) && (!manager || s.manager === manager)), [model, office, manager]);
  const offices = [...new Set((model?.sellers ?? []).map((s) => s.office))];
  const managers = [...new Set((model?.sellers ?? []).filter((s) => !office || s.office === office).map((s) => s.manager))];
  const currentSeller = scoped.some((s) => s.name === seller) ? seller : scoped[0]?.name;

  const onDecide = (id: string, label: string) => {
    decide(id, label);
    setToast('Registrado: ' + label);
    setTimeout(() => setToast(null), 2200);
  };
  const openSeller = (name: string) => { setSeller(name); setRole('vend'); };
  const nDecisions = Object.keys(decisions).length;

  if (error) return <div className="loading">Não foi possível carregar os dados: {error}</div>;
  if (!model) return <div className="loading">Carregando 8.800 oportunidades…</div>;

  return (
    <>
      <header className="top">
        <div className="bar">
          <div className="logo"><i />Radar de Pipeline</div>
          <span className="ctx">Hoje: 31/12/2017 · último dia do 4º trimestre</span>
          <nav className="seg" aria-label="Visão">
            {([['vend', 'Vendedor'], ['ger', 'Gerente'], ['conf', 'Por que confiar']] as [Role, string][]).map(([r, label]) => (
              <button key={r} className={role === r ? 'on' : ''} onClick={() => setRole(r)}>{label}</button>
            ))}
          </nav>
        </div>
        {role !== 'conf' && (
          <div className="filters">
            <label>Escritório
              <select value={office} onChange={(e) => { setOffice(e.target.value); setManager(''); }}>
                <option value="">Todos</option>{offices.map((o) => <option key={o}>{o}</option>)}
              </select>
            </label>
            <label>Gerente
              <select value={manager} onChange={(e) => setManager(e.target.value)}>
                <option value="">Todos</option>{managers.map((m) => <option key={m}>{m}</option>)}
              </select>
            </label>
            {role === 'vend' && (
              <label>Vendedor
                <select value={currentSeller} onChange={(e) => setSeller(e.target.value)}>
                  {scoped.map((s) => <option key={s.name}>{s.name}</option>)}
                </select>
              </label>
            )}
            <span className="log">
              {nDecisions} {nDecisions === 1 ? 'decisão registrada' : 'decisões registradas'}
              {nDecisions > 0 && <> · <a href="#" onClick={(e) => { e.preventDefault(); reset(); }}>limpar</a></>}
            </span>
          </div>
        )}
      </header>

      <main>
        {role === 'vend' && currentSeller && (
          <SellerView key={currentSeller} model={model} seller={currentSeller} decisions={decisions} onDecide={onDecide} />
        )}
        {role === 'ger' && (
          <ManagerView model={model} sellers={scoped} onOpenSeller={openSeller}
            scope={manager ? 'Equipe de ' + manager : office ? 'Escritório ' + office : 'Todas as equipes'} />
        )}
        {role === 'conf' && <TrustView />}
      </main>

      <footer className="foot">
        Dados: CRM Sales Predictive Analytics (Kaggle, CC0) · 8.800 oportunidades · “hoje” = último dia do dataset.
        As decisões ficam salvas só neste navegador; em produção iriam para o CRM e virariam o dado de atividade que hoje falta.
      </footer>
      <div className={'toast' + (toast ? ' on' : '')}>{toast}</div>
    </>
  );
}
