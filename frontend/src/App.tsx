import { Navigate, Route, Routes } from "react-router-dom";
import { Layout } from "./components/Layout";
import { Backtest } from "./pages/Backtest";
import { Diagnosis } from "./pages/Diagnosis";
import { Home } from "./pages/Home";
import { Market } from "./pages/Market";
import { Picks } from "./pages/Picks";
import { Watchlist } from "./pages/Watchlist";

export default function App() {
  return (
    <Routes>
      <Route element={<Layout />}>
        <Route index element={<Home />} />
        <Route path="picks" element={<Picks />} />
        <Route path="diagnosis" element={<Diagnosis />} />
        <Route path="market" element={<Market />} />
        <Route path="watchlist" element={<Watchlist />} />
        <Route path="backtest" element={<Backtest />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Route>
    </Routes>
  );
}