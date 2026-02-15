import { motion, AnimatePresence } from "framer-motion";

type Verdict = "PASS" | "PARTIAL" | "FAIL" | "ERROR";

interface VerdictBadgeProps {
  verdict: Verdict;
  percentage?: number;
}

const verdictMeta: Record<Verdict, { color: string; label: string }> = {
  PASS: { color: "#22c55e", label: "pass" },
  PARTIAL: { color: "#eab308", label: "partial" },
  FAIL: { color: "#ef4444", label: "fail" },
  ERROR: { color: "#737373", label: "error" },
};

export default function VerdictBadge({ verdict, percentage }: VerdictBadgeProps) {
  const { color, label } = verdictMeta[verdict];

  return (
    <AnimatePresence mode="wait">
      <motion.div
        key={verdict}
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        exit={{ opacity: 0, y: -10 }}
        transition={{ duration: 0.4, ease: [0.22, 1, 0.36, 1] }}
        className="flex flex-col items-start gap-1"
      >
        {/* Large percentage number */}
        {percentage !== undefined && (
          <span
            className="font-display text-5xl leading-none"
            style={{ color }}
          >
            {percentage.toFixed(0)}
            <span className="text-2xl text-neutral-600">%</span>
          </span>
        )}

        {/* Verdict label as monospace */}
        <div className="flex items-center gap-2">
          <motion.span
            animate={{
              boxShadow: [
                `0 0 4px ${color}40`,
                `0 0 12px ${color}60`,
                `0 0 4px ${color}40`,
              ],
            }}
            transition={{ duration: 2, repeat: Infinity }}
            className="h-2.5 w-2.5 rounded-full"
            style={{ backgroundColor: color }}
          />
          <span
            className="font-mono text-[13px] uppercase tracking-[0.15em]"
            style={{ color }}
          >
            {label}
          </span>
        </div>
      </motion.div>
    </AnimatePresence>
  );
}
