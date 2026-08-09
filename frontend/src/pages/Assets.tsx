import { useEffect, useState } from "react";
import { api, type PickItem, type PickListResponse } from "../api";
import { AdviceCard } from "../components/AdviceCard";

type AssetKey = "etf" | "lof" | "fund" | "bond";

const TABS: { key: AssetKey; label: string; desc: string }[] = [
  { key: "etf", label: "ETF", desc: "低成本、透明、适合定投与底仓" },
  { key: "lof", label: "LOF", desc: "场内主题与主动增强" },
  { key: "fund", label: "基金", desc: "主动管理与行业主题" },
  { key: "bond", label: "债券", desc: "收益率、久期与信用评级" },
];

export function Assets() {
  const [tab, setTab] = useState<AssetKey>("etf");
  const [data, setData] = useState<PickListResponse | null>(null);
  const [selected, setSelected] = useState<PickItem | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const load = async (key: AssetKey) => {
    setLoading(true);
    setError("");
    try {
      const res = await api.recommend(key, 10);
      setData(res);
      setSelected(res.items[0] || null);
    } catch (e) {
      setError(e instanceof Error ? e.message : "加载失败");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    void load(tab);
  }, [tab]);

  return (
    <section className="section">
      <div className="section-head">
        <div>
          <h2>多资产优选</h2>
          <p>ETF / LOF / 基金 / 债券统一评分，并给出持有与风控建议。</p>
        </div>
      </div>

      <div className="tabs">
        {TABS.map((t) => (
          <button
            key={t.key}
            type="button"
            className={`tab ${tab === t.key ? "active" : ""}`}
            onClick={() => setTab(t.key)}
          >
            {t.label}
          </button>
        ))}
      </div>
      <p className="muted">{TABS.find((t) => t.key === tab)?.desc}</p>

      {loading && <div className="loading">计算推荐中…</div>}
      {error && <div className="error">{error}</div>}

      {data && (
        <>
          {data.methodology && <p className="muted">{data.methodology}</p>}
          <div className="grid-2">
            <div className="panel" style={{ overflowX: "auto" }}>
              <table className="table">
                <thead>
                  <tr>
                    <th>#</th>
                    <th>名称</th>
                    <th>评分</th>
                    <th>关键指标</th>
                  </tr>
                </thead>
                <tbody>
                  {data.items.map((item) => (
                    <tr
                      key={item.ts_code}
                      className={selected?.ts_code === item.ts_code ? "row-active" : ""}
                      onClick={() => setSelected(item)}
                      style={{ cursor: "pointer" }}
                    >
                      <td>{item.rank}</td>
                      <td>
                        <strong>{item.name}</strong>
                        <div className="muted">
                          {item.ts_code} · {item.industry}
                          {item.manager ? ` · ${item.manager}` : ""}
                        </div>
                      </td>
                      <td className="score">{item.total_score.toFixed(1)}</td>
                      <td className="muted" style={{ maxWidth: 240 }}>
                        {item.reason}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <div className="stack">
              {selected && (
                <>
                  <div className="panel">
                    <h3 style={{ marginTop: 0 }}>
                      {selected.name}{" "}
                      <span className="tag">{selected.asset_type || tab.toUpperCase()}</span>
                    </h3>
                    <p>{selected.reason}</p>
                    {selected.metrics && (
                      <div className="grid-3">
                        {Object.entries(selected.metrics)
                          .slice(0, 6)
                          .map(([k, v]) => (
                            <div key={k}>
                              <div className="stat-label">{k}</div>
                              <div>{String(v)}</div>
                            </div>
                          ))}
                      </div>
                    )}
                  </div>
                  <AdviceCard advice={selected.advice} />
                </>
              )}
            </div>
          </div>
        </>
      )}
    </section>
  );
}