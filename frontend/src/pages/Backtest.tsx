import { useMemo, useState } from "react";
import { api, BacktestReport } from "../api";

export function Backtest() {
  const [report, setReport] = useState<BacktestReport | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const path = useMemo(() => {
    if (!report?.equity_curve?.length) return "";
    const vals = report.equity_curve.map((p) => p.equity);
    const w = 640;
    const h = 160;
    const min = Math.min(...vals);
    const max = Math.max(...vals);
    const span = max - min || 1;
    return vals
      .map((v, i) => {
        const x = (i / (vals.length - 1 || 1)) * w;
        const y = h - ((v - min) / span) * (h - 16) - 8;
        return `${i === 0 ? "M" : "L"}${x.toFixed(1)},${y.toFixed(1)}`;
      })
      .join(" ");
  }, [report]);

  const run = async () => {
    setLoading(true);
    setError("");
    try {
      setReport(await api.backtest());
    } catch (e) {
      setError(e instanceof Error ? e.message : "回测失败");
    } finally {
      setLoading(false);
    }
  };

  return (
    <section className="section">
      <div className="section-head">
        <div>
          <h2>策略回测</h2>
          <p>用当前多因子榜单成分做近端收益近似，帮助理解策略波动。</p>
        </div>
        <button className="btn btn-primary" type="button" onClick={() => void run()} disabled={loading}>
          {loading ? "回测中…" : "运行回测"}
        </button>
      </div>

      {error && <div className="error">{error}</div>}

      {report && (
        <>
          <div className="grid-3" style={{ marginBottom: "0.9rem" }}>
            <div className="panel">
              <div className="stat-label">累计收益</div>
              <div className={`stat-value ${report.total_return >= 0 ? "up" : "down"}`}>
                {report.total_return.toFixed(2)}%
              </div>
            </div>
            <div className="panel">
              <div className="stat-label">最大回撤</div>
              <div className="stat-value down">{report.max_drawdown.toFixed(2)}%</div>
            </div>
            <div className="panel">
              <div className="stat-label">胜率 / 夏普</div>
              <div className="stat-value">
                {report.win_rate.toFixed(1)}% / {report.sharpe.toFixed(2)}
              </div>
            </div>
          </div>
          <div className="panel">
            <svg className="spark" viewBox="0 0 640 160" preserveAspectRatio="none" style={{ height: 160 }}>
              <path d={path} fill="none" stroke="#37d39a" strokeWidth="2.5" />
            </svg>
            <p className="muted">{report.commentary}</p>
          </div>
        </>
      )}

      {!report && !loading && <div className="empty">点击右上角运行一次回测。</div>}
    </section>
  );
}