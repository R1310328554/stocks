import { useEffect, useState, type FormEvent } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { api, type PaperAccount } from "../api";

export function Paper() {
  const [params] = useSearchParams();
  const [account, setAccount] = useState<PaperAccount | null>(null);
  const [code, setCode] = useState(params.get("code") || "600519.SH");
  const [shares, setShares] = useState("100");
  const [side, setSide] = useState<"buy" | "sell">("buy");
  const [msg, setMsg] = useState("");
  const [error, setError] = useState("");

  const load = async () => {
    try {
      setAccount(await api.paperAccount());
    } catch (e) {
      setError(e instanceof Error ? e.message : "加载失败");
    }
  };

  useEffect(() => {
    void load();
  }, []);

  const onSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setMsg("");
    setError("");
    try {
      const res = await api.paperOrder({ ts_code: code.trim(), side, shares: Number(shares) });
      setMsg(`${side === "buy" ? "买入" : "卖出"}成功：${res.price} × ${shares} 股，金额 ${res.amount}`);
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "下单失败");
    }
  };

  const onReset = async () => {
    await api.paperReset();
    setMsg("账户已重置为 10 万初始资金");
    await load();
  };

  return (
    <section className="section">
      <div className="section-head">
        <div>
          <h2>模拟交易</h2>
          <p>10 万虚拟资金实盘价格演练，先验证纪律再上真金。</p>
        </div>
        <button className="btn btn-ghost" type="button" onClick={() => void onReset()}>
          重置账户
        </button>
      </div>

      <div className="grid-3" style={{ marginBottom: "0.9rem" }}>
        <div className="panel">
          <div className="stat-label">总资产</div>
          <div className="stat-value">{account?.total_assets?.toLocaleString() ?? "-"}</div>
          <div className={(account?.total_pnl ?? 0) >= 0 ? "up" : "down"}>
            {(account?.total_pnl ?? 0) >= 0 ? "+" : ""}
            {account?.total_pnl} （{account?.total_pnl_pct}%）
          </div>
        </div>
        <div className="panel">
          <div className="stat-label">可用现金</div>
          <div className="stat-value">{account?.cash?.toLocaleString() ?? "-"}</div>
        </div>
        <div className="panel">
          <div className="stat-label">持仓市值</div>
          <div className="stat-value">{account?.market_value?.toLocaleString() ?? "-"}</div>
        </div>
      </div>

      <form className="panel input-row" onSubmit={onSubmit} style={{ marginBottom: "0.9rem" }}>
        <input
          id="paper-code"
          name="code"
          type="text"
          value={code}
          onChange={(e) => setCode(e.target.value)}
          placeholder="代码，如 600519.SH"
        />
        <select value={side} onChange={(e) => setSide(e.target.value as "buy" | "sell")} aria-label="方向">
          <option value="buy">买入</option>
          <option value="sell">卖出</option>
        </select>
        <input
          id="paper-shares"
          name="shares"
          type="text"
          value={shares}
          onChange={(e) => setShares(e.target.value)}
          placeholder="股数（100 的倍数）"
        />
        <button className="btn btn-primary" type="submit">
          下单
        </button>
      </form>

      {msg && <div className="loading">{msg}</div>}
      {error && <div className="error">{error}</div>}

      <div className="grid-2">
        <div className="panel" style={{ overflowX: "auto" }}>
          <h3 style={{ marginTop: 0 }}>当前持仓</h3>
          <table className="table">
            <thead>
              <tr>
                <th>标的</th>
                <th>持仓</th>
                <th>成本 / 现价</th>
                <th>盈亏</th>
              </tr>
            </thead>
            <tbody>
              {(account?.positions || []).map((p) => (
                <tr key={p.ts_code}>
                  <td>
                    <Link to={`/stock/${p.ts_code}`}>
                      <strong>{p.name}</strong>
                    </Link>
                    <div className="muted">{p.ts_code}</div>
                  </td>
                  <td>{p.shares} 股</td>
                  <td>
                    {p.avg_cost} / {p.price}
                  </td>
                  <td className={p.pnl >= 0 ? "up" : "down"}>
                    {p.pnl >= 0 ? "+" : ""}
                    {p.pnl}（{p.pnl_pct}%）
                  </td>
                </tr>
              ))}
              {!account?.positions?.length && (
                <tr>
                  <td colSpan={4} className="muted">
                    暂无持仓，先从选股榜单挑一只试试。
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
        <div className="panel" style={{ overflowX: "auto" }}>
          <h3 style={{ marginTop: 0 }}>成交记录</h3>
          <table className="table">
            <thead>
              <tr>
                <th>时间</th>
                <th>标的</th>
                <th>方向</th>
                <th>价格×数量</th>
              </tr>
            </thead>
            <tbody>
              {(account?.orders || []).slice(0, 12).map((o) => (
                <tr key={o.id}>
                  <td className="muted">{new Date(o.created_at).toLocaleString()}</td>
                  <td>{o.name}</td>
                  <td>
                    <span className={`tag ${o.side === "buy" ? "tag-live" : ""}`}>
                      {o.side === "buy" ? "买入" : "卖出"}
                    </span>
                  </td>
                  <td>
                    {o.price} × {o.shares}
                  </td>
                </tr>
              ))}
              {!account?.orders?.length && (
                <tr>
                  <td colSpan={4} className="muted">
                    暂无成交记录
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </section>
  );
}