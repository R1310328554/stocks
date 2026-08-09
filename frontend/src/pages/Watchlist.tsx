import { useEffect, useState, type FormEvent } from "react";
import { Link } from "react-router-dom";
import { api, type WatchItem } from "../api";

export function Watchlist() {
  const [items, setItems] = useState<WatchItem[]>([]);
  const [tsCode, setTsCode] = useState("300750.SZ");
  const [note, setNote] = useState("关注放量突破");
  const [error, setError] = useState("");

  const load = async () => {
    setError("");
    try {
      setItems(await api.watchlist());
    } catch (e) {
      setError(e instanceof Error ? e.message : "加载失败");
    }
  };

  useEffect(() => {
    void load();
  }, []);

  const onAdd = async (e: FormEvent) => {
    e.preventDefault();
    try {
      await api.addWatch({ ts_code: tsCode.trim(), note, group_name: "默认" });
      setNote("");
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "添加失败");
    }
  };

  const onRemove = async (id: number) => {
    await api.removeWatch(id);
    await load();
  };

  return (
    <section className="section">
      <div className="section-head">
        <div>
          <h2>自选管理</h2>
          <p>把榜单里看上的票收进自选，后续盯盘与诊股更省事。</p>
        </div>
      </div>

      <form className="panel input-row" onSubmit={onAdd} style={{ marginBottom: "1rem" }}>
        <input type="text" value={tsCode} onChange={(e) => setTsCode(e.target.value)} placeholder="股票代码" />
        <input type="text" value={note} onChange={(e) => setNote(e.target.value)} placeholder="备注" />
        <button className="btn btn-primary" type="submit">
          加入自选
        </button>
      </form>

      {error && <div className="error">{error}</div>}

      <div className="panel">
        {!items.length && <div className="empty">还没有自选，去选股页挑几只吧。</div>}
        {!!items.length && (
          <table className="table">
            <thead>
              <tr>
                <th>标的</th>
                <th>分组</th>
                <th>备注</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {items.map((item) => (
                <tr key={item.id}>
                  <td>
                    <strong>{item.name}</strong>
                    <div className="muted">{item.ts_code}</div>
                  </td>
                  <td>{item.group_name}</td>
                  <td>{item.note || "—"}</td>
                  <td style={{ display: "flex", gap: "0.4rem" }}>
                    <Link className="btn btn-ghost" to={`/diagnosis?code=${item.ts_code}`}>
                      诊股
                    </Link>
                    <button className="btn btn-ghost" type="button" onClick={() => void onRemove(item.id)}>
                      移除
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </section>
  );
}