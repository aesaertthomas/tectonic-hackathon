type Bar = { label: string; value: number; highlight?: boolean };

const WIDTH = 320;
const HEIGHT = 140;
const AXIS = 18;
const TOP = 8;
const GAP = 6;

/** Minimal bar chart. `band` shades the usual range. Values are cents; negatives are drawn as zero. */
export function BarChart({ bars, band }: { bars: Bar[]; band?: { low: number; high: number } }) {
  const max = Math.max(1, ...bars.map((b) => b.value), band?.high ?? 0);
  const barWidth = (WIDTH - GAP * (bars.length - 1)) / bars.length;
  const y = (v: number) => HEIGHT - AXIS - (Math.max(0, v) / max) * (HEIGHT - AXIS - TOP);

  return (
    <svg viewBox={`0 0 ${WIDTH} ${HEIGHT}`} className="chart" role="img" aria-label="Monthly amounts">
      {band && <rect x={0} y={y(band.high)} width={WIDTH} height={Math.max(1, y(band.low) - y(band.high))} className="chart-band" />}
      {bars.map((b, i) => {
        const x = i * (barWidth + GAP);
        const top = y(b.value);
        return (
          <g key={`${b.label}-${i}`}>
            <rect x={x} y={top} width={barWidth} height={HEIGHT - AXIS - top} rx={3} className={b.highlight ? "bar-rect bar-hi" : "bar-rect"} />
            <text x={x + barWidth / 2} y={HEIGHT - 5} textAnchor="middle" className="chart-label">
              {b.label}
            </text>
          </g>
        );
      })}
    </svg>
  );
}
