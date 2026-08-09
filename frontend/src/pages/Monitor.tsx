import { useEffect, useState } from "react";
import { api, wsQuotesUrl, type AlertItem, type QuoteItem, type SignalItem } from "../api";

export function Monitor() {
  const [quotes, setQuotes] = useState<QuoteItem[]>([]);
  const [alerts, setAlerts] = useState<AlertItem[]>([]);
  const [signals, setSignals] = useState<SignalItem[]>([]);
  const [live, setLive] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    void (async () => {
      try {
        const [q, a, s] = await Promise.all([api.quotes(), api.alerts(), api.signals()]);
        setQuotes(q.items);
        setAlerts(a.items);
        setSignals(s.items);
      } catch (e) {
        setError(e instanceof Error ? e.message : "加载失败");
      }
    })();

    let ws: WebSocket | null = null;
    try {
      ws = new WebSocket(wsQuotesUrl());
      ws.onopen = () => setLive(true);
      ws.onclose = () => setLive(false);
      ws.onmessage = (ev) => {
        try {
          const data = JSON.parse(ev.data) as { items: QuoteItem[] };
          if (data.items?.length) setQuotes(data.items);
        } catch {
          /* ignore */
        }
      };
    } catch {
      setLive(false);
    }
    return () => ws?.close();
  }, []);

  return (
    <section className="section">
      <div className="section-head">
        <div>
          <h2>AI 盯盘</h2>
          <p>秒级行情刷新、异动告警与择时信号同屏。</p>
        </div>
        <span className={`tag ${live ? "tag-live" : ""}`}>{live ? "LIVE" : "POLL"}</span>
      </div>

      {error && <div className="error">{error}</div>}

      <div className="panel" style={{ overflowX: "auto", marginBottom: "0.9rem" }}>
        <table className="table">
          <thead>
            <tr>
              <th>代码</th>
              <th>名称</th>
              <th>最新价</th>
              <th>涨跌幅</th>
              <th>更新</th>
            </tr>
          </thead>
          <tbody>
            {quotes.map((q) => (
              <tr key={q.ts_code}>
                <td>{q.ts_code}</td>
                <td>{q.name}</td>
                <td>{q.price.toFixed(3)}</td>
                <td className={q.pct_chg >= 0 ? "up" : "down"}>
                  {q.pct_chg >= 0 ? "+" : ""}
                  {q.pct_chg.toFixed(2)}%
                </td>
                <td className="muted">{new Date(q.updated_at).toLocaleTimeString()}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="grid-2">
        <div className="panel">
          <h3 style={{ marginTop: 0 }}>异动告警</h3>
          <ul className="list-plain">
            {alerts.map((a) => (
              <li key={a.id}>
                <strong>{a.name}</strong> <span className="tag">{a.severity}</span>
                <div>{a.message}</div>
              </li>
            ))}
          </ul>
        </div>
        <div className="panel">
          <h3 style={{ marginTop: 0 }}>择时信号</h3>
          <ul className="list-plain">
            {signals.slice(0, 10).map((s, i) => (
              <li key={`${s.ts_code}-${i}`}>
                <strong>{s.name}</strong> <span className="tag">{s.direction}</span>
                <div className="muted">{s.description}</div>
              </li>
            ))}
          </ul>
        </div>
      </div>
    </section>
  );
}