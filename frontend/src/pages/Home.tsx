import { Link } from "react-router-dom";

export function Home() {
  return (
    <section className="hero">
      <div className="hero-visual" aria-hidden />
      <p className="hero-brand">
        智选<em>投</em>
      </p>
      <h1>把复杂选股，收成一张清晰榜单。</h1>
      <p>面向经验不足、资金有限的你：多因子打分、择时信号与诊股解读，一步看懂该关注什么。</p>
      <div className="cta-row">
        <Link className="btn btn-primary" to="/picks">
          查看今日选股
        </Link>
        <Link className="btn btn-ghost" to="/diagnosis">
          先诊一只股
        </Link>
      </div>
    </section>
  );
}