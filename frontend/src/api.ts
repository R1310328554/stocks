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

export type PickItem = {
  rank: number;
  ts_code: string;
  name: string;
  industry: string;
  total_score: number;
  factors: FactorBreakdown;
  reason: string;
  close?: number;
  pct_chg?: number;
  pe?: number;
  pb?: number;
  roe?: number;
};

export type PickListResponse = {
  trade_date: string;
  strategy: string;
  data_source: string;
  total: number;
  items: PickItem[];
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
  risks: string[];
  signals: string[];
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

export const api = {
  health: () => request<{ status: string; data_source: string }>("/health"),
  market: () => request<MarketOverview>("/market/overview"),
  picks: (topN = 20) => request<PickListResponse>(`/picks/daily?top_n=${topN}`),
  naturalPicks: (query: string, topN = 15) =>
    request<PickListResponse>("/picks/natural", {
      method: "POST",
      body: JSON.stringify({ query, top_n: topN }),
    }),
  diagnosis: (code: string) => request<DiagnosisReport>(`/diagnosis/${encodeURIComponent(code)}`),
  capitalFlow: (code: string) => request(`/capital-flow/${encodeURIComponent(code)}`),
  signals: () => request<{ trade_date: string; items: SignalItem[] }>("/signals/timing"),
  alerts: () => request<{ items: AlertItem[] }>("/alerts"),
  news: () => request<{ items: { id: string; title: string; source: string; name: string; published_at: string }[] }>("/news"),
  watchlist: () => request<WatchItem[]>("/watchlist"),
  addWatch: (body: { ts_code: string; name?: string; group_name?: string; note?: string }) =>
    request<WatchItem>("/watchlist", { method: "POST", body: JSON.stringify(body) }),
  removeWatch: (id: number) => request<{ ok: boolean }>(`/watchlist/${id}`, { method: "DELETE" }),
  backtest: () =>
    request<BacktestReport>("/backtest", {
      method: "POST",
      body: JSON.stringify({ strategy: "multi_factor", top_n: 10 }),
    }),
  dailyReport: () => request("/reports/daily"),
};