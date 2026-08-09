import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import {
  api,
  type CalendarItem,
  type DragonTigerItem,
  type HeatmapItem,
  type LimitUpItem,
  type RankingItem,
  type ReportItem,
} from "../api";

const RANK_KINDS = [
  ["gainers", "涨幅榜"],
  ["losers", "跌幅榜"],
  ["turnover", "换手榜"],
  ["vol_ratio", "量比榜"],
  ["inflow", "主力净流入"],
  ["amount", "成交额"],
] as const;

function heatColor(pct: number) {
  if (pct >= 3) return "rgba(55,211,154,0.55)";
  if (pct >= 1) return "rgba(55,211,154,0.32)";
  if (pct > -1) return "rgba(255,255,255,0.08)";
  if (pct > -3) return "rgba(255,107,107,0.32)";
  return "rgba(255,107,107,0.55)";
}

export function DataCenter() {
  const [kind, setKind] = useState<(typeof RANK_KINDS)[number][0]>("gainers");
  const [ranks, setRanks] = useState<RankingItem[]>([]);
  const [limitUp, setLimitUp] = useState<{ total: number; blast_rate: number; items: LimitUpItem[] } | null>(null);
  const [dragon, setDragon] = useState<DragonTigerItem[]>([]);
  const [heat, setHeat] = useState<HeatmapItem[]>([]);
  const [calendar, setCalendar] = useState<CalendarItem[]>([]);
  const [reports, setReports] = useState<ReportItem[]>([]);
  const [error, setError] = useState("");

  useEffect(() => {
    void (async () => {
      try {
        const [lu, dt, hm, cal, rp] = await Promise.all([
          api.limitUp(),
          api.dragonTiger(),
          api.heatmap(),
          api.calendar(8),
          api.reports(),
        ]);
        setLimitUp(lu);
        setDragon(dt.items);
        setHeat(hm.items);
        setCalendar(cal.items);
        setReports(rp.items);
      } catch (e) {
        setError(e instanceof Error ? e.message : "加载失败");
      }
    })();
  }, []);

  useEffect(() => {
    void api
      .rankings(kind, 15)
      .then((r) => setRanks(r.items))
      .catch((e) => setError(e instanceof Error ? e.message : "排行加载失败"));
  }, [kind]);

  return (
    <section className="section">
      <div className="section-head">
        <div>
          <h2>数据中心</h2>
          <p>排行榜、涨停池、龙虎榜、板块热力、财经日历与研报。</p>
        </div>
      </div>

      {error && <div className="error">{error}</div>}

      <div className="panel" style={{ marginBottom: "0.9rem" }}>
        <h3 style={{ marginTop: 0 }}>板块热力图</h3>
        <div className="heatmap">
          {heat.map((h) => (
            <div
              key={h.name}
              className="heat-cell"
              style={{ background: heatColor(h.avg_pct) }}
              title={`领涨 ${h.leader?.name || "-"} ${h.leader?.pct_chg ?? ""}%`}
            >
              <strong>{h.name}</strong>
              <span>{h.avg_pct >= 0 ? "+" : ""}{h.avg_pct}%</span>
            </div>
          ))}
        </div>
      </div>

      <div className="grid-2" style={{ marginBottom: "0.9rem" }}>
        <div className="panel" style={{ overflowX: "auto" }}>
          <div className="tabs" style={{ marginBottom: "0.6rem" }}>
            {RANK_KINDS.map(([k, label]) => (
              <button
                key={k}
                type="button"
                className={`tab ${kind === k ? "active" : ""}`}
                onClick={() => setKind(k)}
              >
                {label}
              </button>
            ))}
          </div>
          <table className="table">
            <thead>
              <tr>
                <th>#</th>
                <th>标的</th>
                <th>现价</th>
                <th>涨跌</th>
                <th>换手</th>
                <th>净流入(万)</th>
              </tr>
            </thead>
            <tbody>
              {ranks.map((r) => (
                <tr key={r.ts_code}>
                  <td>{r.rank}</td>
                  <td>
                    <Link to={`/stock/${r.ts_code}`}>
                      <strong>{r.name}</strong>
                    </Link>
                    <div className="muted">{r.industry}</div>
                  </td>
                  <td>{r.close}</td>
                  <td className={r.pct_chg >= 0 ? "up" : "down"}>
                    {r.pct_chg >= 0 ? "+" : ""}
                    {r.pct_chg}%
                  </td>
                  <td>{r.turnover}%</td>
                  <td className={r.main_net_inflow >= 0 ? "up" : "down"}>{r.main_net_inflow}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        <div className="stack">
          <div className="panel">
            <h3 style={{ marginTop: 0 }}>
              涨停池{" "}
              <span className="tag">
                {limitUp?.total ?? 0} 只 · 炸板率 {limitUp?.blast_rate ?? "-"}%
              </span>
            </h3>
            <ul className="list-plain">
              {(limitUp?.items || []).slice(0, 6).map((l) => (
                <li key={l.ts_code} style={{ display: "flex", justifyContent: "space-between" }}>
                  <span>
                    <Link to={`/stock/${l.ts_code}`}>{l.name}</Link>{" "}
                    <span className="tag">{l.boards}连板</span>
                  </span>
                  <span className="muted">
                    封单 {l.seal_amount}亿 · {l.reason}
                  </span>
                </li>
              ))}
              {!limitUp?.items?.length && <li className="muted">今日暂无涨停标的</li>}
            </ul>
          </div>
          <div className="panel">
            <h3 style={{ marginTop: 0 }}>龙虎榜</h3>
            <ul className="list-plain">
              {dragon.slice(0, 6).map((d) => (
                <li key={d.ts_code}>
                  <div style={{ display: "flex", justifyContent: "space-between" }}>
                    <Link to={`/stock/${d.ts_code}`}>
                      <strong>{d.name}</strong>
                    </Link>
                    <span className={d.net >= 0 ? "up" : "down"}>净买 {d.net}亿</span>
                  </div>
                  <div className="muted">
                    买一 {d.top_buyer} · 机构净 {d.institution_net}亿
                  </div>
                </li>
              ))}
            </ul>
          </div>
        </div>
      </div>

      <div className="grid-2">
        <div className="panel">
          <h3 style={{ marginTop: 0 }}>财经日历</h3>
          <ul className="list-plain">
            {calendar.slice(0, 10).map((c, i) => (
              <li key={`${c.date}-${i}`} style={{ display: "flex", gap: "0.7rem" }}>
                <span className="tag">{c.date.slice(5)}</span>
                <span>
                  {c.title} <span className="muted">（{c.label}）</span>
                </span>
              </li>
            ))}
          </ul>
        </div>
        <div className="panel">
          <h3 style={{ marginTop: 0 }}>最新研报</h3>
          <ul className="list-plain">
            {reports.slice(0, 6).map((r) => (
              <li key={r.id}>
                <strong>{r.title}</strong>
                <div className="muted">
                  {r.org} · {r.rating} · 目标价 {r.target_price}
                </div>
              </li>
            ))}
          </ul>
        </div>
      </div>
    </section>
  );
}