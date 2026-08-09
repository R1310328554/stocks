import { Link } from "react-router-dom";

export function Home() {
  return (
    <section className="hero">
      <div className="hero-visual" aria-hidden />
      <p className="hero-brand">
        智选<em>投</em>
      </p>
      <h1>股票、基金、ETF、债券，一张榜单看清怎么买、拿多久、何处止损。</h1>
      <p>
        多因子评分 + 热点/形态/自然语言选股 + 多专家协同诊股，给资金有限的你可执行的交易建议。
      </p>
      <div className="cta-row">
        <Link className="btn btn-primary" to="/picks">
          开始选股
        </Link>
        <Link className="btn btn-ghost" to="/assets">
          看 ETF / 基金 / 债券
        </Link>
      </div>
    </section>
  );
}