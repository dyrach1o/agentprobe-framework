import { motion } from "framer-motion";

interface ScoreBarProps {
  percentage: number;
  score: number;
  maxScore: number;
}

function getColor(pct: number): string {
  if (pct >= 70) return "#22c55e";
  if (pct >= 40) return "#eab308";
  return "#ef4444";
}

const TOTAL_BLOCKS = 20;

export default function ScoreBar({ percentage, score, maxScore }: ScoreBarProps) {
  const color = getColor(percentage);
  const filled = Math.round((percentage / 100) * TOTAL_BLOCKS);

  return (
    <div className="space-y-3">
      {/* Score label */}
      <div className="flex items-baseline justify-between font-mono text-[13px]">
        <span className="text-neutral-500">
          score{" "}
          <span className="text-neutral-300">{score.toFixed(1)}</span>
          <span className="text-neutral-600">/{maxScore.toFixed(1)}</span>
        </span>
        <span style={{ color }}>{percentage.toFixed(1)}%</span>
      </div>

      {/* Block matrix */}
      <div className="flex items-center gap-1">
        {Array.from({ length: TOTAL_BLOCKS }, (_, i) => {
          const isFilled = i < filled;
          return (
            <motion.div
              key={i}
              initial={{ scaleY: 0, opacity: 0 }}
              animate={{ scaleY: 1, opacity: 1 }}
              transition={{
                delay: i * 0.025,
                duration: 0.3,
                ease: [0.22, 1, 0.36, 1],
              }}
              className="h-3 flex-1 rounded-[2px]"
              style={{
                backgroundColor: isFilled ? color : "rgba(255,255,255,0.04)",
                boxShadow: isFilled ? `0 0 6px ${color}30` : "none",
              }}
            />
          );
        })}
      </div>
    </div>
  );
}
