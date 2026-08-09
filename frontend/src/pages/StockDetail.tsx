import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import {
  api,
  type CompanyProfile,
  type DiagnosisReport,
  type KlineData,
  type ReportItem,
} from "../api";
import { AdviceCard } from "../components/AdviceCard";
import { KlineChart } from "../components/KlineChart";

export function StockDetail() {
  const { code = "600519.SH" } = useParams();
  const [kline, setKline] = useState<KlineData | null>(null);
  const [profile, setProfile] = useState<CompanyProfile | null>(null);
  const [reports, setReports] = useState<ReportItem[]>([]);
  const [diag, setDiag] = useState<DiagnosisReport | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    void (async () => {
      setError("");
      try {
        const [k, p, r, d] = await Promise.all([
          api.kline(code, 120),
          api.profile(code),
          api.reports(code),
          api.diagnosis(code),
        ]);
        setKline(k);
        setProfile(p);
        setReports(r.items);
        setDiag(d);
      } catch (e) {
        setError(e instanceof Error ? e.message : "加载失败");
      }
    })();
  }, [code]);

  const last = kline?.bars[kline.bars.length - 1];

  return (
    <section className="section">
      <div className="section-head">
        <div>
          <h2>
            {kline?.name || code}{" "}
            <span className="tag">{kline?.industry || profile?.industry || ""}</span>
          </h2>
          <p>
            {code} · 最新 {last?.close?.toFixed(2)}{" "}
            <span className={(last?.pct_chg || 0) >= 0 ? "up" : "down"}>
              {(last?.pct_chg || 0) >= 0 ? "+" : ""}
              {last?.pct_chg?.toFixed(2)}%
            </span>
          </p>
        </div>
        <div style={{ display: "flex", gap: "0.5rem" }}>
          <Link className="btn btn-ghost" to={`/diagnosis?code=${code}`}>
            深度诊股
          </Link>
          <Link className="btn btn-ghost" to={`/paper?code=${code}`}>
            模拟买入
          </Link>
        </div>
      </div>

      {error && <div className="error">{error}</div>}

      <div className="panel" style={{ marginBottom: "0.9rem" }}>
        <h3 style={{ marginTop: 0 }}>日K线（近120交易日，金线为MA20）</h3>
        {kline && <KlineChart bars={kline.bars} />}
        <div className="muted">
          {(kline?.indicators?.signals as string[] | undefined)?.slice(0, 4).join(" · ") ||
            "暂无即时信号"}
        </div>
      </div>

      <div className="grid-2" style={{ marginBottom: "0.9rem" }}>
        <div className="stack">
          {profile && (
            <div className="panel">
              <h3 style={{ marginTop: 0 }}>F10 概览</h3>
              <p className="muted">{String(profile.profile.main_business)}</p>
              <div className="grid-3">
                <div>
                  <div className="stat-label">PE / PB</div>
                  <div>
                    {profile.valuation.pe} / {profile.valuation.pb}
                  </div>
                </div>
                <div>
                  <div className="stat-label">ROE / 毛利率</div>
                  <div>
                    {profile.finance.roe}% / {profile.finance.gross_margin}%
                  </div>
                </div>
                <div>
                  <div className="stat-label">质押率</div>
                  <div>{profile.pledge_ratio}%</div>
                </div>
                <div>
                  <div className="stat-label">净利增长</div>
                  <div>{profile.finance.profit_growth}%</div>
                </div>
                <div>
                  <div className="stat-label">负债率</div>
                  <div>{profile.finance.debt_ratio}%</div>
                </div>
                <div>
                  <div className="stat-label">下次解禁</div>
                  <div>
                    {profile.unlock_next.date}（{profile.unlock_next.ratio}%）
                  </div>
                </div>
              </div>
              <h4>前五大股东</h4>
              <ul className="list-plain">
                {profile.top_holders.map((h) => (
                  <li key={h.name} style={{ display: "flex", justifyContent: "space-between" }}>
                    <span>{h.name}</span>
                    <span className="muted">
                      {h.ratio}% · {h.change}
                    </span>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
        <div className="stack">
          <AdviceCard advice={diag?.advice} />
          <div className="panel">
            <h3 style={{ marginTop: 0 }}>机构研报</h3>
            <ul className="list-plain">
              {reports.slice(0, 5).map((r) => (
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
      </div>
    </section>
  );
}