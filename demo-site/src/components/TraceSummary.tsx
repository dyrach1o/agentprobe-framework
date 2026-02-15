import { useEffect, useRef, useState } from "react";
import { motion } from "framer-motion";
import {
  BrainIcon,
  WrenchIcon,
  ClockIcon,
  TokenIcon,
  CostIcon,
  SpeedIcon,
} from "../components/Icons";
import type { Trace } from "../data/sampleTrace";

const ease: [number, number, number, number] = [0.22, 1, 0.36, 1];

/* ------------------------------------------------------------------ */
/* Animated counter — counts up from 0 to `target` over `duration` ms */
/* Uses requestAnimationFrame with ease-out cubic                      */
/* ------------------------------------------------------------------ */

function AnimatedCounter({
  target,
  duration = 1200,
  prefix = "",
  suffix = "",
  decimals = 0,
}: {
  target: number;
  duration?: number;
  prefix?: string;
  suffix?: string;
  decimals?: number;
}) {
  const [display, setDisplay] = useState(0);
  const frameRef = useRef<number | null>(null);

  useEffect(() => {
    const start = performance.now();

    function step(now: number) {
      const elapsed = now - start;
      const progress = Math.min(elapsed / duration, 1);
      // ease-out cubic
      const eased = 1 - Math.pow(1 - progress, 3);
      setDisplay(eased * target);
      if (progress < 1) {
        frameRef.current = requestAnimationFrame(step);
      }
    }

    frameRef.current = requestAnimationFrame(step);
    return () => {
      if (frameRef.current !== null) cancelAnimationFrame(frameRef.current);
    };
  }, [target, duration]);

  const formatted =
    decimals > 0 ? display.toFixed(decimals) : Math.round(display).toString();

  return (
    <span>
      {prefix}
      {formatted}
      {suffix}
    </span>
  );
}

/* ------------------------------------------------------------------ */
/* Single stat card                                                    */
/* ------------------------------------------------------------------ */

interface StatCardProps {
  label: string;
  value: number;
  prefix?: string;
  suffix?: string;
  decimals?: number;
  icon: React.ReactNode;
  iconColor: string;
  delay: number;
}

function StatCard({
  label,
  value,
  prefix,
  suffix,
  decimals,
  icon,
  iconColor,
  delay,
}: StatCardProps) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.6, delay, ease }}
      className="rounded-2xl border border-white/[0.06] bg-surface p-6
                 transition-colors duration-300 hover:border-white/[0.1] hover:bg-surface-light"
    >
      <div className={`mb-3 flex items-center gap-2 ${iconColor}`}>
        {icon}
      </div>

      <div className="mb-1 font-mono text-2xl font-bold tracking-tight text-white">
        <AnimatedCounter
          target={value}
          prefix={prefix}
          suffix={suffix}
          decimals={decimals}
        />
      </div>

      <span className="text-[13px] font-medium uppercase tracking-[0.2em] text-neutral-500">
        {label}
      </span>
    </motion.div>
  );
}

/* ------------------------------------------------------------------ */
/* TraceSummary                                                        */
/* ------------------------------------------------------------------ */

export default function TraceSummary({ trace }: { trace: Trace }) {
  const llmCalls = trace.turns.filter((t) => t.turn_type === "llm_call").length;
  const toolCalls = trace.turns.filter(
    (t) => t.turn_type === "tool_call"
  ).length;
  const totalTokens = trace.total_input_tokens + trace.total_output_tokens;

  // rough cost estimate: $0.005 / 1k input, $0.015 / 1k output  (gpt-4o-like)
  const estimatedCost =
    (trace.total_input_tokens / 1000) * 0.005 +
    (trace.total_output_tokens / 1000) * 0.015;

  const stats: StatCardProps[] = [
    {
      label: "Total Tokens",
      value: totalTokens,
      icon: <TokenIcon size={18} />,
      iconColor: "text-primary",
      delay: 0,
    },
    {
      label: "Latency",
      value: trace.total_latency_ms / 1000,
      suffix: "s",
      decimals: 2,
      icon: <ClockIcon size={18} />,
      iconColor: "text-accent",
      delay: 0.06,
    },
    {
      label: "LLM Calls",
      value: llmCalls,
      icon: <BrainIcon size={18} />,
      iconColor: "text-primary",
      delay: 0.12,
    },
    {
      label: "Tool Calls",
      value: toolCalls,
      icon: <WrenchIcon size={18} />,
      iconColor: "text-accent",
      delay: 0.18,
    },
    {
      label: "Est. Cost",
      value: estimatedCost,
      prefix: "$",
      decimals: 4,
      icon: <CostIcon size={18} />,
      iconColor: "text-primary",
      delay: 0.24,
    },
    {
      label: "Throughput",
      value: totalTokens / (trace.total_latency_ms / 1000),
      suffix: " tok/s",
      decimals: 0,
      icon: <SpeedIcon size={18} />,
      iconColor: "text-accent",
      delay: 0.3,
    },
  ];

  return (
    <section className="mb-12">
      {/* Agent / model / trace ID pills */}
      <motion.div
        initial={{ opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5, ease }}
        className="mb-8 flex flex-wrap items-center gap-3"
      >
        <span className="rounded-full border border-primary/30 px-4 py-1.5 text-sm font-medium text-primary">
          {trace.agent_name}
        </span>
        <span className="rounded-full border border-white/[0.06] px-4 py-1.5 text-sm text-neutral-400">
          model: <span className="text-white">{trace.model}</span>
        </span>
        <span className="rounded-full border border-white/[0.06] px-4 py-1.5 font-mono text-xs text-neutral-500">
          {trace.trace_id}
        </span>
      </motion.div>

      {/* Stat cards grid */}
      <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-6">
        {stats.map((s) => (
          <StatCard key={s.label} {...s} />
        ))}
      </div>
    </section>
  );
}
