export type Stage = 'Prospecting' | 'Engaging' | 'Won' | 'Lost';
export type Clock = 'healthy' | 'cooling' | 'lastChance' | 'zombie';

/** Linhas cruas dos CSVs. */
export interface RawTables {
  accounts: Record<string, string>[];
  products: Record<string, string>[];
  teams: Record<string, string>[];
  pipeline: Record<string, string>[];
}

export interface Account {
  name: string;
  sector: string;
  revenue: number;
  employees: number;
  country: string;
  parent: string | null;
}

export interface Seller {
  name: string;
  manager: string;
  office: string;
}

export interface Opportunity {
  id: string;
  seller: string;
  manager: string;
  office: string;
  product: string;
  price: number;
  account: string | null;
  stage: Stage;
  engageDate: Date | null;
  closeDate: Date | null;
  closeValue: number | null;
}

export interface ScoreParts {
  /** 1–100, ou 0 para zumbi. Ordem idêntica ao valor esperado. */
  score: number;
  /** Pontos que vêm do valor do deal. */
  valuePts: number;
  /** Pontos que vêm do momento (idade → chance). */
  momentPts: number;
  /** Valor esperado em 90 dias = preço × chance. */
  expectedValue: number;
}

/** Deal aberto, pronto para a interface. */
export interface OpenDeal extends Opportunity {
  sector: string | null;
  /** Só Engaging tem idade. */
  age: number | null;
  clock: Clock | null;
  bandLabel: string | null;
  winChance90d: number | null;
  scoring: ScoreParts | null;
  /** Outros vendedores com deal aberto na mesma conta + produto. */
  conflicts: string[];
}

export interface SecondChance {
  id: string;
  seller: string;
  account: string;
  product: string;
  price: number;
  lostOn: Date;
  daysAgo: number;
}

export type ProfileLabel = 'Volume + ticket alto' | 'Máquina de volume' | 'Caçador de ticket alto' | 'Em desenvolvimento';

export interface SellerProfile {
  closedPerMonth: number;
  avgTicket: number;
  wonRevenue: number;
  label: ProfileLabel;
}

export interface Model {
  sellers: Seller[];
  openDeals: OpenDeal[];
  secondChance: SecondChance[];
  profiles: Record<string, SellerProfile>;
  quality: DataQuality;
}

export interface DataQuality {
  productNameFixed: number;
  openWithoutAccount: number;
  prospectingWithoutDate: number;
  sellersWithoutDeals: string[];
}
