import { motion } from "framer-motion";
import type { EvaluationRule, RuleResult } from "../data/evaluatorData.ts";

interface RuleToggleProps {
  rule: EvaluationRule;
  result?: RuleResult;
  onToggle: (id: string) => void;
}

const typeAccent: Record<EvaluationRule["type"], string> = {
  contains: "#e2a04f",
  max_length: "#8b5cf6",
  not_contains: "#ef4444",
  valid_json: "#eab308",
  matches_pattern: "#22c55e",
};

export default function RuleToggle({ rule, result, onToggle }: RuleToggleProps) {
  const color = typeAccent[rule.type];
  const active = rule.enabled;
  const passed = result?.passed;

  return (
    <motion.button
      type="button"
      layout
      onClick={() => onToggle(rule.id)}
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      className={`group w-full text-left font-mono text-[13px] leading-[1.8] rounded-lg px-4 py-2.5 transition-all duration-200 cursor-pointer select-none ${
        active
          ? "bg-white/[0.02] hover:bg-white/[0.04]"
          : "opacity-40 hover:opacity-60"
      }`}
    >
      <div className="flex items-center gap-3">
        {/* Line prefix */}
        <span
          className="w-3 shrink-0 text-center"
          style={{ color: active ? color : "#525252" }}
        >
          {active ? "▸" : "#"}
        </span>

        {/* Rule type keyword */}
        <span style={{ color }} className="shrink-0">
          {rule.type}
        </span>

        {/* Rule name / params */}
        <span className={active ? "text-neutral-300" : "text-neutral-600 line-through"}>
          {rule.name}
        </span>

        {/* Weight */}
        <span className="ml-auto shrink-0 text-neutral-600">
          ×{rule.weight}
        </span>

        {/* Result indicator — simple glowing dot */}
        {active && result && (
          <motion.span
            initial={{ scale: 0 }}
            animate={{ scale: 1 }}
            transition={{ type: "spring", stiffness: 500, damping: 25 }}
            className="shrink-0 h-2 w-2 rounded-full"
            style={{
              backgroundColor: passed ? "#22c55e" : "#ef4444",
              boxShadow: passed
                ? "0 0 8px rgba(34,197,94,0.4)"
                : "0 0 8px rgba(239,68,68,0.4)",
            }}
          />
        )}
      </div>
    </motion.button>
  );
}
