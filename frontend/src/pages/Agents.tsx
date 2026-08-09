import { useEffect, useState, type FormEvent } from "react";
import { api, type TradeAdvice } from "../api";
import { AdviceCard } from "../components/AdviceCard";

type Expert = { agent: string; summary: string; stance: string; points: string[] };

export function Agents() {
  const [code, setCode] = useState("600519.SH");
  const [question, setQuestion] = useState("当前是否适合分批建仓？持有多久？");
  const [decision, setDecision] = useState("");
  const [score, setScore] = useState(0);
  const [experts, setExperts] = useState<Expert[]>([]);
  const [advice, setAdvice] = useState<TradeAdvice | undefined>();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const run = async () => {
    setLoading(true);
    setError("");
    try {
      const data = await api.agents(code, question);
      setDecision(data.decision);
      setScore(data.consensus_score);
      setExperts(data.experts);
      setAdvice(data.trade_advice);
    } catch (e) {
      setError(e instanceof Error ? e.message : "协同分析失败");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    void run();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const onSubmit = (e: FormEvent) => {
    e.preventDefault();
    void run();
  };

  return (
    <section className="section">
      <div className="section-head">
        <div>
          <h2>多专家协同</h2>
          <p>宏观 / 产业 / 财报 / 技术 / 风控 五专家会诊，主 Agent 输出共识。</p>
        </div>
      </div>

      <form className="panel input-row" onSubmit={onSubmit} style={{ marginBottom: "1rem" }}>
        <input id="agent-code" name="code" type="text" value={code} onChange={(e) => setCode(e.target.value)} />
        <input
          id="agent-q"
          name="question"
          type="text"
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
        />
        <button className="btn btn-primary" type="submit" disabled={loading}>
          {loading ? "会诊中…" : "发起会诊"}
        </button>
      </form>

      {error && <div className="error">{error}</div>}

      <div className="grid-2" style={{ marginBottom: "0.9rem" }}>
        <div className="panel">
          <div className="stat-label">共识评分</div>
          <div className="stat-value score">{score}</div>
          <p>{decision}</p>
        </div>
        <AdviceCard advice={advice} />
      </div>

      <div className="grid-3">
        {experts.map((ex) => (
          <div className="panel" key={ex.agent}>
            <h3 style={{ marginTop: 0 }}>
              {ex.agent} <span className="tag">{ex.stance}</span>
            </h3>
            <p className="muted">{ex.summary}</p>
            <ul className="list-plain">
              {ex.points.filter(Boolean).map((p) => (
                <li key={p}>{p}</li>
              ))}
            </ul>
          </div>
        ))}
      </div>
    </section>
  );
}