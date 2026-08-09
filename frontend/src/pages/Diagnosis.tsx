import { useEffect, useMemo, useState, type FormEvent } from "react";
import { useSearchParams } from "react-router-dom";
import { api, type DiagnosisReport } from "../api";

function Sparkline({ series }: { series?: { dates: string[]; close: number[]; ma20: number[] } }) {
  const path = useMemo(() => {
    if (!series?.close?.length) return "";
    const w = 520;
    const h = 120;
    const min = Math.min(...series.close);
    const max = Math.max(...series.close);
    const span = max - min || 1;
    return series.close
      .map((v, i) => {
        const x = (i / (series.close.length - 1 || 1)) * w;
        const y = h - ((v - min) / span) * (h - 12) - 6;
        return `${i === 0 ? "M" : "L"}${x.toFixed(1)},${y.toFixed(1)}`;
      })
      .join(" ");
  }, [series]);

  if (!path) return <div className="muted">暂无走势</div>;
  return (
    <svg className="spark" viewBox="0 0 520 120" preserveAspectRatio="none">
      <path d={path} fill="none" stroke="#c8f26d" strokeWidth="2.5" />
    </svg>
  );
}

export function Diagnosis() {
  const [params, setParams] = useSearchParams();
  const [code, setCode] = useState(params.get("code") || "600519.SH");
  const [report, setReport] = useState<DiagnosisReport | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const run = async (tsCode: string) => {
    setLoading(true);
    setError("");
    try {
      const data = await api.diagnosis(tsCode);
      setReport(data);
      setParams({ code: tsCode });
    } catch (e) {
      setError(e instanceof Error ? e.message : "诊股失败");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    void run(code);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const onSubmit = (e: FormEvent) => {
    e.preventDefault();
    void run(code.trim());
  };

  const series = report?.indicators?.series as
    | { dates: string[]; close: number[]; ma20: number[] }
    | undefined;

  return (
    <section className="section">
      <div className="section-head">
        <div>
          <h2>智能诊股</h2>
          <p>基本面、技术面、资金面一次看清，并给出风险提示。</p>
        </div>
      </div>

      <form className="panel input-row" onSubmit={onSubmit} style={{ marginBottom: "1rem" }}>
        <input
          type="text"
          value={code}
          onChange={(e) => setCode(e.target.value)}
          placeholder="输入代码，如 600519.SH / 300750.SZ"
        />
        <button className="btn btn-primary" type="submit" disabled={loading}>
          {loading ? "诊断中…" : "开始诊股"}
        </button>
      </form>

      {error && <div className="error">{error}</div>}

      {report && (
        <>
          <div className="grid-3" style={{ marginBottom: "0.9rem" }}>
            <div className="panel">
              <div className="stat-label">综合评级</div>
              <div className="stat-value">
                {report.overall_score} · {report.overall_level}
              </div>
              <div className="muted">
                {report.name} {report.ts_code} · {report.industry}
              </div>
            </div>
            <div className="panel">
              <div className="stat-label">基本面</div>
              <div className="stat-value">
                {report.fundamental.score} · {report.fundamental.level}
              </div>
            </div>
            <div className="panel">
              <div className="stat-label">技术 / 资金</div>
              <div className="stat-value">
                {report.technical.score} / {report.capital.score}
              </div>
            </div>
          </div>

          <div className="grid-2">
            <div className="panel">
              <h3 style={{ marginTop: 0 }}>近端走势</h3>
              <Sparkline series={series} />
              <div className="muted" style={{ marginTop: "0.6rem" }}>
                {(report.signals || []).slice(0, 4).join(" · ") || "暂无即时信号"}
              </div>
            </div>
            <div className="panel">
              <h3 style={{ marginTop: 0 }}>风险提示</h3>
              <ul className="list-plain">
                {report.risks.map((r) => (
                  <li key={r}>{r}</li>
                ))}
              </ul>
            </div>
          </div>

          <div className="grid-3" style={{ marginTop: "0.9rem" }}>
            {[report.fundamental, report.technical, report.capital].map((sec, idx) => (
              <div className="panel" key={idx}>
                <h3 style={{ marginTop: 0 }}>
                  {idx === 0 ? "基本面" : idx === 1 ? "技术面" : "资金面"}
                </h3>
                <p className="muted">{sec.summary}</p>
                <ul className="list-plain">
                  {sec.details.map((d) => (
                    <li key={d}>{d}</li>
                  ))}
                </ul>
              </div>
            ))}
          </div>
        </>
      )}
    </section>
  );
}