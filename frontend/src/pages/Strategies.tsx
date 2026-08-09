import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api, type StrategyHit, type StrategyMeta } from "../api";
import { AdviceCard } from "../components/AdviceCard";

export function Strategies() {
  const [list, setList] = useState<StrategyMeta[]>([]);
  const [active, setActive] = useState<string>("");
  const [hits, setHits] = useState<StrategyHit[]>([]);
  const [selected, setSelected] = useState<StrategyHit | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    void (async () => {
      try {
        const res = await api.strategies();
        setList(res.items);
        if (res.items[0]) {
          setActive(res.items[0].id);
          await run(res.items[0].id);
        }
      } catch (e) {
        setError(e instanceof Error ? e.message : "加载失败");
      }
    })();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const run = async (id: string) => {
    setLoading(true);
    setError("");
    try {
      const res = await api.runStrategy(id, 10);
      setHits(res.items);
      setSelected(res.items[0] || null);
    } catch (e) {
      setError(e instanceof Error ? e.message : "策略运行失败");
    } finally {
      setLoading(false);
    }
  };

  const activeMeta = list.find((s) => s.id === active);

  return (
    <section className="section">
      <div className="section-head">
        <div>
          <h2>策略中心</h2>
          <p>神奇九转、均线、MACD、北向、融资追击等命名策略一键运行。</p>
        </div>
      </div>

      {error && <div className="error">{error}</div>}

      <div className="grid-3" style={{ marginBottom: "0.9rem" }}>
        {list.map((s) => (
          <button
            key={s.id}
            type="button"
            className={`panel strategy-card ${active === s.id ? "strategy-active" : ""}`}
            onClick={() => {
              setActive(s.id);
              void run(s.id);
            }}
          >
            <div style={{ display: "flex", justifyContent: "space-between" }}>
              <strong>{s.name}</strong>
              <span className="tag">{s.category}</span>
            </div>
            <p className="muted" style={{ margin: "0.35rem 0" }}>
              {s.desc}
            </p>
            {s.stats && (
              <div className="muted">
                胜率 {s.stats.win_rate}% · 均益 {s.stats.avg_return}% · 今日信号{" "}
                {s.stats.signals_today}
              </div>
            )}
          </button>
        ))}
      </div>

      {loading && <div className="loading">运行策略中…</div>}

      {hits.length > 0 && (
        <div className="grid-2">
          <div className="panel" style={{ overflowX: "auto" }}>
            <h3 style={{ marginTop: 0 }}>
              {activeMeta?.name} · 命中 {hits.length}
            </h3>
            <table className="table">
              <thead>
                <tr>
                  <th>#</th>
                  <th>标的</th>
                  <th>方向</th>
                  <th>触发原因</th>
                </tr>
              </thead>
              <tbody>
                {hits.map((h) => (
                  <tr
                    key={h.ts_code}
                    className={selected?.ts_code === h.ts_code ? "row-active" : ""}
                    onClick={() => setSelected(h)}
                    style={{ cursor: "pointer" }}
                  >
                    <td>{h.rank}</td>
                    <td>
                      <Link to={`/stock/${h.ts_code}`}>
                        <strong>{h.name}</strong>
                      </Link>
                      <div className="muted">
                        {h.close}{" "}
                        <span className={h.pct_chg >= 0 ? "up" : "down"}>
                          {h.pct_chg >= 0 ? "+" : ""}
                          {h.pct_chg}%
                        </span>
                      </div>
                    </td>
                    <td>
                      <span className={`tag ${h.direction === "buy" ? "tag-live" : ""}`}>
                        {h.direction}
                      </span>
                    </td>
                    <td className="muted">{h.why}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <AdviceCard advice={selected?.advice} />
        </div>
      )}
      {!hits.length && !loading && <div className="empty">该策略今日暂无命中标的。</div>}
    </section>
  );
}