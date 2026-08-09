import { useState, type FormEvent } from "react";
import { Link } from "react-router-dom";
import { api, type ScreenerItem } from "../api";
import { AdviceCard } from "../components/AdviceCard";

type Cond = { field: string; op: "gte" | "lte"; value: string };

const FIELDS: [string, string][] = [
  ["pe", "市盈率"],
  ["pb", "市净率"],
  ["roe", "ROE%"],
  ["profit_growth", "净利增长%"],
  ["revenue_growth", "营收增长%"],
  ["dividend_yield", "股息率%"],
  ["debt_ratio", "负债率%"],
  ["turnover", "换手率%"],
  ["ret_20", "20日涨幅%"],
  ["rsi14", "RSI"],
  ["vol_ratio", "量比"],
];

const PRESETS: { name: string; conds: Cond[] }[] = [
  {
    name: "低估值蓝筹",
    conds: [
      { field: "pe", op: "lte", value: "20" },
      { field: "roe", op: "gte", value: "12" },
      { field: "dividend_yield", op: "gte", value: "1.5" },
    ],
  },
  {
    name: "高成长",
    conds: [
      { field: "profit_growth", op: "gte", value: "25" },
      { field: "revenue_growth", op: "gte", value: "15" },
    ],
  },
  {
    name: "强势动量",
    conds: [
      { field: "ret_20", op: "gte", value: "5" },
      { field: "vol_ratio", op: "gte", value: "1.2" },
    ],
  },
  {
    name: "超跌反弹",
    conds: [
      { field: "rsi14", op: "lte", value: "35" },
      { field: "roe", op: "gte", value: "8" },
    ],
  },
];

export function Screener() {
  const [conds, setConds] = useState<Cond[]>(PRESETS[0].conds);
  const [items, setItems] = useState<ScreenerItem[]>([]);
  const [selected, setSelected] = useState<ScreenerItem | null>(null);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const run = async () => {
    setLoading(true);
    setError("");
    try {
      const res = await api.screener({
        filters: conds
          .filter((c) => c.value !== "")
          .map((c) => ({ field: c.field, op: c.op, value: Number(c.value) })),
        limit: 30,
      });
      setItems(res.items);
      setTotal(res.total);
      setSelected(res.items[0] || null);
    } catch (e) {
      setError(e instanceof Error ? e.message : "筛选失败");
    } finally {
      setLoading(false);
    }
  };

  const onSubmit = (e: FormEvent) => {
    e.preventDefault();
    void run();
  };

  const update = (i: number, patch: Partial<Cond>) =>
    setConds((cs) => cs.map((c, idx) => (idx === i ? { ...c, ...patch } : c)));

  return (
    <section className="section">
      <div className="section-head">
        <div>
          <h2>条件选股器</h2>
          <p>估值、成长、质量、技术、资金条件自由组合，支持常用预设。</p>
        </div>
      </div>

      <div className="tabs">
        {PRESETS.map((p) => (
          <button
            key={p.name}
            type="button"
            className="tab"
            onClick={() => {
              setConds(p.conds.map((c) => ({ ...c })));
            }}
          >
            {p.name}
          </button>
        ))}
      </div>

      <form className="panel" onSubmit={onSubmit} style={{ marginBottom: "1rem" }}>
        {conds.map((c, i) => (
          <div className="cond-row" key={i}>
            <select
              value={c.field}
              onChange={(e) => update(i, { field: e.target.value })}
              aria-label="字段"
            >
              {FIELDS.map(([f, label]) => (
                <option key={f} value={f}>
                  {label}
                </option>
              ))}
            </select>
            <select
              value={c.op}
              onChange={(e) => update(i, { op: e.target.value as "gte" | "lte" })}
              aria-label="比较"
            >
              <option value="gte">≥</option>
              <option value="lte">≤</option>
            </select>
            <input
              type="text"
              value={c.value}
              onChange={(e) => update(i, { value: e.target.value })}
              placeholder="数值"
              aria-label="数值"
            />
            <button
              type="button"
              className="btn btn-ghost"
              onClick={() => setConds((cs) => cs.filter((_, idx) => idx !== i))}
            >
              删除
            </button>
          </div>
        ))}
        <div className="input-row" style={{ marginTop: "0.6rem" }}>
          <button
            type="button"
            className="btn btn-ghost"
            onClick={() => setConds((cs) => [...cs, { field: "pe", op: "lte", value: "30" }])}
          >
            + 添加条件
          </button>
          <button className="btn btn-primary" type="submit" disabled={loading}>
            {loading ? "筛选中…" : "开始筛选"}
          </button>
        </div>
      </form>

      {error && <div className="error">{error}</div>}

      {items.length > 0 && (
        <div className="grid-2">
          <div className="panel" style={{ overflowX: "auto" }}>
            <p className="muted" style={{ marginTop: 0 }}>
              命中 {total} 只，展示前 {items.length}
            </p>
            <table className="table">
              <thead>
                <tr>
                  <th>标的</th>
                  <th>匹配度</th>
                  <th>命中指标</th>
                </tr>
              </thead>
              <tbody>
                {items.map((it) => (
                  <tr
                    key={it.ts_code}
                    className={selected?.ts_code === it.ts_code ? "row-active" : ""}
                    onClick={() => setSelected(it)}
                    style={{ cursor: "pointer" }}
                  >
                    <td>
                      <Link to={`/stock/${it.ts_code}`}>
                        <strong>{it.name}</strong>
                      </Link>
                      <div className="muted">
                        {it.ts_code} · {it.industry}
                      </div>
                    </td>
                    <td className="score">{it.score}</td>
                    <td className="muted">
                      {Object.entries(it.matched)
                        .map(([k, v]) => `${k} ${typeof v === "number" ? v.toFixed(1) : v}`)
                        .join(" · ")}
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
                  <h3 style={{ marginTop: 0 }}>{selected.name}</h3>
                  <div className="muted">
                    {selected.signals.slice(0, 3).join(" · ") || "暂无技术信号"}
                    {selected.patterns.length > 0 && ` · 形态：${selected.patterns.join("、")}`}
                  </div>
                </div>
                <AdviceCard advice={selected.advice} />
              </>
            )}
          </div>
        </div>
      )}
      {!items.length && !loading && <div className="empty">设置条件后点击「开始筛选」。</div>}
    </section>
  );
}