import { NavLink, Outlet } from "react-router-dom";

const links = [
  ["/", "首页", true],
  ["/picks", "选股", false],
  ["/assets", "多资产", false],
  ["/diagnosis", "诊股", false],
  ["/market", "看板", false],
  ["/monitor", "盯盘", false],
  ["/portfolio", "持仓", false],
  ["/agents", "专家", false],
  ["/watchlist", "自选", false],
  ["/backtest", "回测", false],
] as const;

export function Layout() {
  return (
    <div className="app-shell">
      <header className="nav">
        <NavLink to="/" className="brand">
          智选<span>投</span>
        </NavLink>
        <nav className="nav-links">
          {links.map(([to, label, end]) => (
            <NavLink key={to} to={to} end={end}>
              {label}
            </NavLink>
          ))}
        </nav>
      </header>
      <Outlet />
    </div>
  );
}