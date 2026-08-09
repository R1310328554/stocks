import { useEffect, useState } from "react";
import { api, type TradeAdvice } from "../api";
import { AdviceCard } from "../components/AdviceCard";

type Holding = {
  ts_code: string;
  name: string;
  asset_type: string;
  weight: number;
  score: number;
  level: string;
  advice?: TradeAdvice;
};

export function Portfolio() {
  const [score, setScore] = useState(0);
  const [holdings, setHoldings] = useState<Holding[]>([]);
  const [suggestions, setSuggestions] = useState<string[]>([]);
  const [hint, setHint] = useState<Record<string, string>>({});
  const [selected, setSelected] = useState<Holding | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    void (async () => {
      try {
        const data = await api.portfolio([
          { ts_code: "510300.SH", weight: 0.4 },
          { ts_code: "600519.SH", weight: 0.25 },
          { ts_code: "300750.SZ", weight: 0.15 },
          { ts_code: "019740.SH", weight: 0.2 },
        ]);
        setScore(data.portfolio_score);
        setHoldings(data.holdings);
        setSuggestions(data.suggestions);
        setHint(data.allocation_hint);
        setSelected(data.holdings[0] || null);
      } catch (e) {
        setError(e instanceof Error ? e.message : "分析失败");
      }
    })();
  }, []);

  return (
    <section className="section">
      <div className="section-head">
        <div>
          <h2>持仓诊断</h2>
          <p>组合评分、集中度与单标的止损止盈建议。</p>
        </div>
      </div>

      {error && <div className="error">{error}</div>}

      <div className="grid-3" style={{ marginBottom: "0.9rem" }}>
        <div className="panel">
          <div className="stat-label">组合评分</div>
          <div className="stat-value score">{score}</div>
        </div>
        <div className="panel">
          <div className="stat-label">建议配置</div>
          <div className="muted">
            股票 {hint.stock || "-"} · ETF {hint.etf || "-"} · 债/现金 {hint.bond_or_cash || "-"}
          </div>
        </div>
        <div className="panel">
          <div className="stat-label">组合建议</div>
          <div>{suggestions[0] || "加载中…"}</div>
        </div>
      </div>

      <div className="grid-2">
        <div className="panel">
          <table className="table">
            <thead>
              <tr>
                <th>标的</th>
                <th>类型</th>
                <th>权重</th>
                <th>评分</th>
              </tr>
            </thead>
            <tbody>
              {holdings.map((h) => (
                <tr
                  key={h.ts_code}
                  className={selected?.ts_code === h.ts_code ? "row-active" : ""}
                  onClick={() => setSelected(h)}
                  style={{ cursor: "pointer" }}
                >
                  <td>
                    <strong>{h.name}</strong>
                    <div className="muted">{h.ts_code}</div>
                  </td>
                  <td>{h.asset_type}</td>
                  <td>{h.weight}%</td>
                  <td className="score">
                    {h.score} · {h.level}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          <ul className="list-plain" style={{ marginTop: "1rem" }}>
            {suggestions.map((s) => (
              <li key={s}>{s}</li>
            ))}
          </ul>
        </div>
        <AdviceCard advice={selected?.advice} />
      </div>
    </section>
  );
}