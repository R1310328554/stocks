import type { TradeAdvice } from "../api";

export function AdviceCard({ advice, compact = false }: { advice?: TradeAdvice; compact?: boolean }) {
  if (!advice) return <span className="muted">暂无建议</span>;
  if (compact) {
    return (
      <div className="advice-compact">
        <div>
          <strong>{advice.action}</strong>
          <span className="tag">{advice.confidence}</span>
        </div>
        <div className="muted">
          持有 {advice.hold_days_min}-{advice.hold_days_max} 日 · 止损 {advice.stop_loss_price} · 止盈{" "}
          {advice.take_profit_price}
        </div>
      </div>
    );
  }
  return (
    <div className="panel advice-card">
      <div className="advice-head">
        <h3>交易建议</h3>
        <span className="tag">{advice.confidence}信心</span>
      </div>
      <div className="stat-value" style={{ fontSize: "1.25rem" }}>
        {advice.action}
      </div>
      <p className="muted">
        {advice.hold_horizon}（{advice.hold_days_min}-{advice.hold_days_max} 交易日） · {advice.position_advice}
      </p>
      <div className="grid-3" style={{ marginTop: "0.8rem" }}>
        <div>
          <div className="stat-label">参考买入</div>
          <div>{advice.entry_price}</div>
        </div>
        <div>
          <div className="stat-label">止损价 / 幅度</div>
          <div className="down">
            {advice.stop_loss_price} / -{advice.stop_loss_pct}%
          </div>
        </div>
        <div>
          <div className="stat-label">止盈价 / 幅度</div>
          <div className="up">
            {advice.take_profit_price} / +{advice.take_profit_pct}%
          </div>
        </div>
      </div>
      <ul className="list-plain" style={{ marginTop: "0.9rem" }}>
        {advice.checklist.map((c) => (
          <li key={c}>{c}</li>
        ))}
      </ul>
      <p className="muted" style={{ marginBottom: 0 }}>
        {advice.risk_note}
      </p>
    </div>
  );
}