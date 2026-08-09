import { FormEvent, useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api, PickItem, PickListResponse } from "../api";

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
  const [data, setData] = useState<PickListResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [query, setQuery] = useState("市盈率小于40，ROE大于12，医药或白酒");
  const [nlLoading, setNlLoading] = useState(false);

  const load = async () => {
    setLoading(true);
    setError("");
    try {
      setData(await api.picks(20));
    } catch (e) {
      setError(e instanceof Error ? e.message : "加载失败");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    void load();
  }, []);

  const onNatural = async (e: FormEvent) => {
    e.preventDefault();
    setNlLoading(true);
    setError("");
    try {
      setData(await api.naturalPicks(query, 15));
    } catch (err) {
      setError(err instanceof Error ? err.message : "自然语言选股失败");
    } finally {
      setNlLoading(false);
    }
  };

  return (
    <section className="section">
      <div className="section-head">
        <div>
          <h2>每日选股榜单</h2>
          <p>六大因子加权评分，给新手一张可执行的关注清单。</p>
        </div>
        <button className="btn btn-ghost" onClick={() => void load()} type="button">
          刷新
        </button>
      </div>

      <form className="panel input-row" onSubmit={onNatural} style={{ marginBottom: "1rem" }}>
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="试试：市盈率小于30，净利润增长大于20，半导体"
        />
        <button className="btn btn-primary" type="submit" disabled={nlLoading}>
          {nlLoading ? "解析中…" : "自然语言选股"}
        </button>
      </form>

      {loading && <div className="loading">正在计算多因子得分…</div>}
      {error && <div className="error">{error}</div>}

      {data && (
        <>
          <p className="muted" style={{ marginBottom: "0.8rem" }}>
            {data.trade_date} · 策略 {data.strategy} · 数据源 {data.data_source} · 共 {data.total} 只
          </p>
          <div className="panel" style={{ overflowX: "auto" }}>
            <table className="table">
              <thead>
                <tr>
                  <th>排名</th>
                  <th>标的</th>
                  <th>综合分</th>
                  <th>因子拆解</th>
                  <th>理由</th>
                  <th></th>
                </tr>
              </thead>
              <tbody>
                {data.items.map((item) => (
                  <tr key={item.ts_code}>
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
                    <td style={{ minWidth: 220 }}>
                      <FactorBars factors={item.factors} />
                    </td>
                    <td style={{ maxWidth: 280 }}>{item.reason}</td>
                    <td>
                      <Link className="btn btn-ghost" to={`/diagnosis?code=${item.ts_code}`}>
                        诊股
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </>
      )}
    </section>
  );
}