const API_BASE = import.meta.env.VITE_API_BASE || "http://127.0.0.1:8000/api/v1";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { "Content-Type": "application/json", ...(init?.headers || {}) },
    ...init,
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(text || res.statusText);
  }
  return res.json() as Promise<T>;
}

export type FactorBreakdown = {
  value: number;
  growth: number;
  quality: number;
  momentum: number;
  capital: number;
  sentiment: number;
};

export type TradeAdvice = {
  action: string;
  confidence: string;
  hold_horizon: string;
  hold_days_min: number;
  hold_days_max: number;
  position_advice: string;
  entry_price: number;
  stop_loss_pct: number;
  take_profit_pct: number;
  stop_loss_price: number;
  take_profit_price: number;
  trailing_stop_pct: number;
  checklist: string[];
  risk_note: string;
};

export type PickItem = {
  rank: number;
  ts_code: string;
  name: string;
  industry: string;
  asset_type?: string;
  total_score: number;
  factors: FactorBreakdown;
  reason: string;
  close?: number;
  pct_chg?: number;
  pe?: number;
  pb?: number;
  roe?: number;
  manager?: string;
  metrics?: Record<string, string | number>;
  themes?: string[];
  patterns?: string[];
  advice?: TradeAdvice;
};

export type PickListResponse = {
  trade_date: string;
  strategy: string;
  data_source: string;
  total: number;
  items: PickItem[];
  asset_type?: string;
  methodology?: string;
};

export type MarketOverview = {
  trade_date: string;
  data_source: string;
  index_summary: { name: string; close: number; pct_chg: number }[];
  hot_sectors: { name: string; pct_chg: number }[];
  limit_up_count: number;
  limit_down_count: number;
  northbound_net: number;
  margin_balance_change: number;
  fear_greed: number;
  fear_greed_label: string;
  commentary: string;
};

export type DiagnosisReport = {
  ts_code: string;
  name: string;
  industry: string;
  trade_date: string;
  overall_score: number;
  overall_level: string;
  fundamental: { score: number; level: string; summary: string; details: string[] };
  technical: { score: number; level: string; summary: string; details: string[] };
  capital: { score: number; level: string; summary: string; details: string[] };
  sentiment?: { score: number; level: string; summary: string; details: string[] };
  layers?: Record<string, string>;
  risks: string[];
  signals: string[];
  advice?: TradeAdvice;
  indicators: Record<string, unknown>;
};

export type WatchItem = {
  id: number;
  ts_code: string;
  name: string;
  group_name: string;
  note: string;
  created_at: string;
};

export type SignalItem = {
  ts_code: string;
  name: string;
  signal_type: string;
  direction: string;
  strength: number;
  description: string;
  generated_at: string;
};

export type AlertItem = {
  id: string;
  ts_code: string;
  name: string;
  alert_type: string;
  message: string;
  severity: string;
  created_at: string;
};

export type BacktestReport = {
  strategy: string;
  start_date: string;
  end_date: string;
  total_return: number;
  max_drawdown: number;
  win_rate: number;
  sharpe: number;
  equity_curve: { date: string; equity: number }[];
  commentary: string;
};

export type QuoteItem = {
  ts_code: string;
  name: string;
  price: number;
  pct_chg: number;
  volume: number;
  updated_at: string;
};

export type SourceHealth = {
  total: number;
  live: number;
  configured: number;
  demo_fallback: number;
  reliability_score: number;
  guidance: string;
  items: {
    id: string;
    name: string;
    tier: string;
    authority: string;
    coverage: string[];
    status: string;
    notes: string;
  }[];
};

export const api = {
  health: () => request<{ status: string; data_source: string; features: string[] }>("/health"),
  sources: () => request<SourceHealth>("/meta/sources"),
  market: () => request<MarketOverview>("/market/overview"),
  picks: (topN = 20) => request<PickListResponse>(`/picks/daily?top_n=${topN}`),
  hotPicks: (topN = 15) => request<PickListResponse>(`/picks/hot?top_n=${topN}`),
  patternPicks: (topN = 15) => request<PickListResponse>(`/picks/pattern?top_n=${topN}`),
  naturalPicks: (query: string, topN = 15) =>
    request<PickListResponse>("/picks/natural", {
      method: "POST",
      body: JSON.stringify({ query, top_n: topN }),
    }),
  recommend: (assetType: "etf" | "lof" | "fund" | "bond", topN = 10) =>
    request<PickListResponse>(`/recommend/${assetType}?top_n=${topN}`),
  diagnosis: (code: string) => request<DiagnosisReport>(`/diagnosis/${encodeURIComponent(code)}`),
  capitalFlow: (code: string) => request(`/capital-flow/${encodeURIComponent(code)}`),
  signals: () => request<{ trade_date: string; items: SignalItem[] }>("/signals/timing"),
  alerts: () => request<{ items: AlertItem[] }>("/alerts"),
  news: () =>
    request<{ items: { id: string; title: string; source: string; name: string; published_at: string }[] }>(
      "/news",
    ),
  quotes: () => request<{ server_time: string; items: QuoteItem[] }>("/quotes"),
  watchlist: () => request<WatchItem[]>("/watchlist"),
  addWatch: (body: { ts_code: string; name?: string; group_name?: string; note?: string }) =>
    request<WatchItem>("/watchlist", { method: "POST", body: JSON.stringify(body) }),
  removeWatch: (id: number) => request<{ ok: boolean }>(`/watchlist/${id}`, { method: "DELETE" }),
  backtest: () =>
    request<BacktestReport>("/backtest", {
      method: "POST",
      body: JSON.stringify({ strategy: "multi_factor", top_n: 10 }),
    }),
  portfolio: (holdings: { ts_code: string; weight?: number; cost?: number }[] = []) =>
    request<{
      portfolio_score: number;
      concentration_top: number;
      holdings: Array<{
        ts_code: string;
        name: string;
        asset_type: string;
        weight: number;
        score: number;
        level: string;
        advice?: TradeAdvice;
      }>;
      suggestions: string[];
      allocation_hint: Record<string, string>;
    }>("/portfolio/analyze", {
      method: "POST",
      body: JSON.stringify({ holdings }),
    }),
  agents: (ts_code?: string, question?: string) =>
    request<{
      question: string;
      target: { ts_code: string; name: string };
      consensus_score: number;
      decision: string;
      experts: { agent: string; summary: string; stance: string; points: string[] }[];
      trade_advice?: TradeAdvice;
    }>("/agents/research", {
      method: "POST",
      body: JSON.stringify({ ts_code, question }),
    }),
  dailyReport: () => request("/reports/daily"),
};

export function wsQuotesUrl() {
  const base = API_BASE.replace(/^http/, "ws");
  return `${base}/ws/quotes`;
}