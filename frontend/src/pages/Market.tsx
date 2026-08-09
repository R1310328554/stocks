import { useEffect, useState } from "react";
import { api, type AlertItem, type MarketOverview, type SignalItem } from "../api";

export function Market() {
  const [market, setMarket] = useState<MarketOverview | null>(null);
  const [signals, setSignals] = useState<SignalItem[]>([]);
  const [alerts, setAlerts] = useState<AlertItem[]>([]);
  const [news, setNews] = useState<{ id: string; title: string; name: string; published_at: string }[]>([]);
  const [error, setError] = useState("");

  useEffect(() => {
    void (async () => {
      try {
        const [m, s, a, n] = await Promise.all([
          api.market(),
          api.signals(),
          api.alerts(),
          api.news(),
        ]);
        setMarket(m);
        setSignals(s.items);
        setAlerts(a.items);
        setNews(n.items);
      } catch (e) {
        setError(e instanceof Error ? e.message : "加载失败");
      }
    })();
  }, []);

  return (
    <section className="section">
      <div className="section-head">
        <div>
          <h2>数据看板</h2>
          <p>市场情绪、热点板块、择时信号与异动盯盘。</p>
        </div>
      </div>

      {error && <div className="error">{error}</div>}
      {!market && !error && <div className="loading">同步市场快照…</div>}

      {market && (
        <>
          <div className="grid-3" style={{ marginBottom: "0.9rem" }}>
            {market.index_summary.map((idx) => (
              <div className="panel" key={idx.name}>
                <div className="stat-label">{idx.name}</div>
                <div className="stat-value">{idx.close.toFixed(2)}</div>
                <div className={idx.pct_chg >= 0 ? "up" : "down"}>
                  {idx.pct_chg >= 0 ? "+" : ""}
                  {idx.pct_chg.toFixed(2)}%
                </div>
              </div>
            ))}
          </div>

          <div className="grid-2">
            <div className="panel">
              <h3 style={{ marginTop: 0 }}>情绪与资金</h3>
              <div className="stat-value" style={{ marginBottom: "0.4rem" }}>
                {market.fear_greed} · {market.fear_greed_label}
              </div>
              <p className="muted">{market.commentary}</p>
              <div className="grid-3" style={{ marginTop: "0.8rem" }}>
                <div>
                  <div className="stat-label">涨停 / 跌停</div>
                  <div>
                    {market.limit_up_count} / {market.limit_down_count}
                  </div>
                </div>
                <div>
                  <div className="stat-label">北向净流入(亿)</div>
                  <div className={market.northbound_net >= 0 ? "up" : "down"}>
                    {market.northbound_net.toFixed(1)}
                  </div>
                </div>
                <div>
                  <div className="stat-label">两融变化(亿)</div>
                  <div className={market.margin_balance_change >= 0 ? "up" : "down"}>
                    {market.margin_balance_change.toFixed(1)}
                  </div>
                </div>
              </div>
            </div>
            <div className="panel">
              <h3 style={{ marginTop: 0 }}>热点板块</h3>
              <ul className="list-plain">
                {market.hot_sectors.map((s) => (
                  <li key={s.name} style={{ display: "flex", justifyContent: "space-between" }}>
                    <span>{s.name}</span>
                    <span className={s.pct_chg >= 0 ? "up" : "down"}>
                      {s.pct_chg >= 0 ? "+" : ""}
                      {s.pct_chg.toFixed(2)}%
                    </span>
                  </li>
                ))}
              </ul>
            </div>
          </div>

          <div className="grid-2" style={{ marginTop: "0.9rem" }}>
            <div className="panel">
              <h3 style={{ marginTop: 0 }}>择时信号</h3>
              <ul className="list-plain">
                {signals.slice(0, 8).map((s, i) => (
                  <li key={`${s.ts_code}-${i}`}>
                    <strong>{s.name}</strong>{" "}
                    <span className="tag">{s.signal_type}</span>{" "}
                    <span className="tag">{s.direction}</span>
                    <div className="muted">{s.description}</div>
                  </li>
                ))}
              </ul>
            </div>
            <div className="panel">
              <h3 style={{ marginTop: 0 }}>AI 盯盘异动</h3>
              <ul className="list-plain">
                {alerts.slice(0, 8).map((a) => (
                  <li key={a.id}>
                    <strong>{a.name}</strong> <span className="tag">{a.severity}</span>
                    <div>{a.message}</div>
                  </li>
                ))}
              </ul>
            </div>
          </div>

          <div className="panel" style={{ marginTop: "0.9rem" }}>
            <h3 style={{ marginTop: 0 }}>资讯快讯</h3>
            <ul className="list-plain">
              {news.slice(0, 6).map((n) => (
                <li key={n.id}>
                  {n.title}
                  <div className="muted">
                    {n.name} · {new Date(n.published_at).toLocaleString()}
                  </div>
                </li>
              ))}
            </ul>
          </div>
        </>
      )}
    </section>
  );
}