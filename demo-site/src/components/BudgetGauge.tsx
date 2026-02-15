import { useEffect, useState } from "react";
import { motion } from "framer-motion";

interface BudgetGaugeProps {
  percentage: number;
  used: number;
  total: number;
}

function getGaugeColor(pct: number): string {
  if (pct < 60) return "#22c55e";
  if (pct < 80) return "#eab308";
  return "#ef4444";
}

export default function BudgetGauge({ percentage, used, total }: BudgetGaugeProps) {
  const [animatedPct, setAnimatedPct] = useState(0);

  useEffect(() => {
    const timer = setTimeout(() => setAnimatedPct(percentage), 100);
    return () => clearTimeout(timer);
  }, [percentage]);

  const radius = 80;
  const strokeWidth = 12;
  const cx = 100;
  const cy = 100;

  // Semi-circle: from 180 degrees to 0 degrees (left to right arc)
  const startAngle = Math.PI;
  const endAngle = 0;
  const totalArc = Math.PI; // 180 degrees

  // Background arc path
  const bgStartX = cx + radius * Math.cos(startAngle);
  const bgStartY = cy - radius * Math.sin(startAngle);
  const bgEndX = cx + radius * Math.cos(endAngle);
  const bgEndY = cy - radius * Math.sin(endAngle);

  const bgPath = `M ${bgStartX} ${bgStartY} A ${radius} ${radius} 0 0 1 ${bgEndX} ${bgEndY}`;

  // Filled arc based on animated percentage
  const fillAngle = startAngle - (animatedPct / 100) * totalArc;
  const filledEndX = cx + radius * Math.cos(fillAngle);
  const filledEndY = cy - radius * Math.sin(fillAngle);
  const largeArcFlag = animatedPct > 50 ? 1 : 0;

  const fillPath =
    animatedPct > 0
      ? `M ${bgStartX} ${bgStartY} A ${radius} ${radius} 0 ${largeArcFlag} 1 ${filledEndX} ${filledEndY}`
      : "";

  const color = getGaugeColor(percentage);

  // Zone markers
  const zoneMarks = [0, 60, 80, 100];
  const zoneColors = ["#22c55e", "#eab308", "#ef4444"];

  return (
    <div className="flex flex-col items-center">
      <svg viewBox="0 0 200 120" className="w-full max-w-[220px]">
        {/* Zone color arcs (background segments) */}
        {zoneMarks.slice(0, -1).map((start, i) => {
          const end = zoneMarks[i + 1];
          const sAngle = Math.PI - (start / 100) * totalArc;
          const eAngle = Math.PI - (end / 100) * totalArc;
          const sx = cx + radius * Math.cos(sAngle);
          const sy = cy - radius * Math.sin(sAngle);
          const ex = cx + radius * Math.cos(eAngle);
          const ey = cy - radius * Math.sin(eAngle);
          const large = end - start > 50 ? 1 : 0;

          return (
            <path
              key={start}
              d={`M ${sx} ${sy} A ${radius} ${radius} 0 ${large} 1 ${ex} ${ey}`}
              fill="none"
              stroke={zoneColors[i]}
              strokeWidth={strokeWidth}
              strokeLinecap="round"
              opacity={0.12}
            />
          );
        })}

        {/* Background track */}
        <path
          d={bgPath}
          fill="none"
          stroke="#262626"
          strokeWidth={strokeWidth}
          strokeLinecap="round"
          opacity={0.6}
        />

        {/* Filled arc */}
        {fillPath && (
          <motion.path
            d={fillPath}
            fill="none"
            stroke={color}
            strokeWidth={strokeWidth}
            strokeLinecap="round"
            initial={{ pathLength: 0 }}
            animate={{ pathLength: 1 }}
            transition={{ duration: 1.2, ease: "easeOut" }}
            style={{
              filter: `drop-shadow(0 0 6px ${color}60)`,
            }}
          />
        )}

        {/* Center text — percentage in gauge color */}
        <text
          x={cx}
          y={cy - 10}
          textAnchor="middle"
          fill={color}
          fontSize="22"
          fontWeight="700"
          fontFamily="'JetBrains Mono', monospace"
        >
          {percentage.toFixed(1)}%
        </text>
        {/* Details in neutral-500 */}
        <text
          x={cx}
          y={cy + 10}
          textAnchor="middle"
          fill="#737373"
          fontSize="10"
          fontFamily="'Inter', system-ui"
        >
          ${used.toFixed(4)} / ${total.toFixed(2)}
        </text>
      </svg>
    </div>
  );
}
