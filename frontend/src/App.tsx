import { Navigate, Route, Routes } from "react-router-dom";
import { Layout } from "./components/Layout";
import { Agents } from "./pages/Agents";
import { Assets } from "./pages/Assets";
import { Backtest } from "./pages/Backtest";
import { DataCenter } from "./pages/DataCenter";
import { Diagnosis } from "./pages/Diagnosis";
import { Home } from "./pages/Home";
import { Market } from "./pages/Market";
import { Monitor } from "./pages/Monitor";
import { Paper } from "./pages/Paper";
import { Picks } from "./pages/Picks";
import { Portfolio } from "./pages/Portfolio";
import { Screener } from "./pages/Screener";
import { StockDetail } from "./pages/StockDetail";
import { Strategies } from "./pages/Strategies";
import { Watchlist } from "./pages/Watchlist";

export default function App() {
  return (
    <Routes>
      <Route element={<Layout />}>
        <Route index element={<Home />} />
        <Route path="picks" element={<Picks />} />
        <Route path="screener" element={<Screener />} />
        <Route path="strategies" element={<Strategies />} />
        <Route path="assets" element={<Assets />} />
        <Route path="stock/:code" element={<StockDetail />} />
        <Route path="diagnosis" element={<Diagnosis />} />
        <Route path="datacenter" element={<DataCenter />} />
        <Route path="market" element={<Market />} />
        <Route path="monitor" element={<Monitor />} />
        <Route path="paper" element={<Paper />} />
        <Route path="portfolio" element={<Portfolio />} />
        <Route path="agents" element={<Agents />} />
        <Route path="watchlist" element={<Watchlist />} />
        <Route path="backtest" element={<Backtest />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Route>
    </Routes>
  );
}