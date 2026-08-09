import { useEffect, useState, type FormEvent } from "react";
import { Link } from "react-router-dom";
import { api, type PickItem, type PickListResponse } from "../api";
import { AdviceCard } from "../components/AdviceCard";

type Mode = "multi" | "hot" | "pattern" | "nl";

function FactorBars({ factors }: { factors: PickItem["factors"] }) {
  const entries: [string, number][] = [
    ["价值", factors.value],
    ["成长", factors.growth],
    ["质量", factors.quality],
    ["动量", factors.momentum],
    ["资金", factors.capital],
    ["情绪", factors.sentiment],
  ];
  return (
    <div className="bars">
      {entries.map(([label, value]) => (
        <div className="bar-row" key={label}>
          <span>{label}</span>
          <div className="bar-track">
            <div className="bar-fill" style={{ width: `${Math.max(8, Math.min(100, value))}%` }} />
          </div>
          <span>{value.toFixed(0)}</span>
        </div>
      ))}
    </div>
  );
}

export function Picks() {
  const [mode, setMode] = useState<Mode>("multi");
  const [data, setData] = useState<PickListResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [query, setQuery] = useState("市盈率小于40，ROE大于12，医药或白酒");
  const [selected, setSelected] = useState<PickItem | null>(null);

  const load = async (next: Mode = mode) => {
    setLoading(true);
    setError("");
    try {
      let res: PickListResponse;
      if (next === "hot") res = await api.hotPicks(15);
      else if (next === "pattern") res = await api.patternPicks(15);
      else if (next === "nl") res = await api.naturalPicks(query, 15);
      else res = await api.picks(20);
      setData(res);
      setSelected(res.items[0] || null);
    } catch (e) {
      setError(e instanceof Error ? e.message : "加载失败");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    void load("multi");
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const switchMode = (m: Mode) => {
    setMode(m);
    if (m !== "nl") void load(m);
  };

  const onNatural = async (e: FormEvent) => {
    e.preventDefault();
    setMode("nl");
    await load("nl");
  };

  return (
    <section className="section">
      <div className="section-head">
        <div>
          <h2>智能选股</h2>
          <p>多因子 / 热点 / 形态 / 自然语言，附带持有期与止损止盈建议。</p>
        </div>
        <button className="btn btn-ghost" onClick={() => void load()} type="button">
          刷新
        </button>
      </div>

      <div className="tabs">
        {(
          [
            ["multi", "多因子"],
            ["hot", "热点主题"],
            ["pattern", "形态扫描"],
            ["nl", "自然语言"],
          ] as const
        ).map(([k, label]) => (
          <button
            key={k}
            type="button"
            className={`tab ${mode === k ? "active" : ""}`}
            onClick={() => switchMode(k)}
          >
            {label}
          </button>
        ))}
      </div>

      <form className="panel input-row" onSubmit={onNatural} style={{ marginBottom: "1rem" }}>
        <input
          id="nl-query"
          name="query"
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="试试：市盈率小于30，净利润增长大于20，半导体"
        />
        <button className="btn btn-primary" type="submit" disabled={loading}>
          {loading && mode === "nl" ? "解析中…" : "自然语言选股"}
        </button>
      </form>

      {loading && <div className="loading">正在计算选股结果…</div>}
      {error && <div className="error">{error}</div>}

      {data && (
        <div className="grid-2">
          <div className="panel" style={{ overflowX: "auto" }}>
            <p className="muted" style={{ marginTop: 0 }}>
              {data.trade_date} · {data.strategy} · 源 {data.data_source} · {data.total} 只
            </p>
            <table className="table">
              <thead>
                <tr>
                  <th>排名</th>
                  <th>标的</th>
                  <th>评分</th>
                  <th>建议摘要</th>
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
                    <td>#{item.rank}</td>
                    <td>
                      <strong>{item.name}</strong>
                      <div className="muted">
                        {item.ts_code} · {item.industry}
                      </div>
                      <div className="muted">
                        {item.close?.toFixed(2)}{" "}
                        <span className={(item.pct_chg || 0) >= 0 ? "up" : "down"}>
                          {(item.pct_chg || 0) >= 0 ? "+" : ""}
                          {item.pct_chg?.toFixed(2)}%
                        </span>
                      </div>
                    </td>
                    <td className="score">{item.total_score.toFixed(1)}</td>
                    <td>
                      <AdviceCard advice={item.advice} compact />
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
                  <div className="section-head" style={{ marginBottom: "0.6rem" }}>
                    <div>
                      <h3 style={{ margin: 0 }}>
                        {selected.name} · {selected.total_score.toFixed(1)}
                      </h3>
                      <p className="muted">{selected.reason}</p>
                    </div>
                    <Link className="btn btn-ghost" to={`/diagnosis?code=${selected.ts_code}`}>
                      深度诊股
                    </Link>
                  </div>
                  <FactorBars factors={selected.factors} />
                </div>
                <AdviceCard advice={selected.advice} />
              </>
            )}
          </div>
        </div>
      )}
    </section>
  );
}