import { useMemo } from "react";
import type { KlineBar } from "../api";

export function KlineChart({ bars }: { bars: KlineBar[] }) {
  const view = useMemo(() => {
    if (!bars.length) return null;
    const w = 760;
    const priceH = 240;
    const volH = 70;
    const gap = 16;
    const n = bars.length;
    const cw = Math.max(2, Math.floor(w / n) - 2);
    const step = w / n;

    const highs = bars.map((b) => b.high);
    const lows = bars.map((b) => b.low);
    const vols = bars.map((b) => b.vol);
    const max = Math.max(...highs);
    const min = Math.min(...lows);
    const span = max - min || 1;
    const maxVol = Math.max(...vols) || 1;

    const y = (v: number) => priceH - ((v - min) / span) * (priceH - 10) - 5;

    // MA20 折线
    const ma20: string[] = [];
    for (let i = 0; i < n; i++) {
      if (i < 19) continue;
      const avg = bars.slice(i - 19, i + 1).reduce((s, b) => s + b.close, 0) / 20;
      const x = i * step + step / 2;
      ma20.push(`${ma20.length === 0 ? "M" : "L"}${x.toFixed(1)},${y(avg).toFixed(1)}`);
    }

    return { w, priceH, volH, gap, n, cw, step, min, max, y, maxVol, ma20: ma20.join(" ") };
  }, [bars]);

  if (!view) return <div className="muted">暂无K线数据</div>;
  const { w, priceH, volH, gap, cw, step, y, maxVol, ma20 } = view;
  const totalH = priceH + gap + volH;

  return (
    <svg viewBox={`0 0 ${w} ${totalH}`} className="kline" preserveAspectRatio="none">
      {bars.map((b, i) => {
        const up = b.close >= b.open;
        const color = up ? "#37d39a" : "#ff6b6b";
        const x = i * step + step / 2;
        const bodyTop = y(Math.max(b.open, b.close));
        const bodyH = Math.max(1, Math.abs(y(b.open) - y(b.close)));
        const vh = (b.vol / maxVol) * (volH - 6);
        return (
          <g key={b.date}>
            <line x1={x} x2={x} y1={y(b.high)} y2={y(b.low)} stroke={color} strokeWidth="1" />
            <rect
              x={x - cw / 2}
              y={bodyTop}
              width={cw}
              height={bodyH}
              fill={up ? color : color}
              opacity={up ? 0.9 : 0.85}
            />
            <rect
              x={x - cw / 2}
              y={priceH + gap + (volH - vh)}
              width={cw}
              height={vh}
              fill={color}
              opacity="0.5"
            />
          </g>
        );
      })}
      {ma20 && <path d={ma20} fill="none" stroke="#c8f26d" strokeWidth="1.6" opacity="0.9" />}
    </svg>
  );
}