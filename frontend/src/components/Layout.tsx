import { NavLink, Outlet } from "react-router-dom";

export function Layout() {
  return (
    <div className="app-shell">
      <header className="nav">
        <NavLink to="/" className="brand">
          智选<span>投</span>
        </NavLink>
        <nav className="nav-links">
          <NavLink to="/" end>
            首页
          </NavLink>
          <NavLink to="/picks">选股</NavLink>
          <NavLink to="/diagnosis">诊股</NavLink>
          <NavLink to="/market">看板</NavLink>
          <NavLink to="/watchlist">自选</NavLink>
          <NavLink to="/backtest">回测</NavLink>
        </nav>
      </header>
      <Outlet />
    </div>
  );
}