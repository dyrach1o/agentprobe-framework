import { motion } from "framer-motion";
import type { Trace } from "../data/sampleTrace";

const ease: [number, number, number, number] = [0.22, 1, 0.36, 1];

export default function TraceSummary({ trace }: { trace: Trace }) {
  const llmCalls = trace.turns.filter((t) => t.turn_type === "llm_call").length;
  const toolCalls = trace.turns.filter(
    (t) => t.turn_type === "tool_call"
  ).length;
  const totalTokens = trace.total_input_tokens + trace.total_output_tokens;
  const estimatedCost =
    (trace.total_input_tokens / 1000) * 0.005 +
    (trace.total_output_tokens / 1000) * 0.015;
  const throughput = Math.round(
    totalTokens / (trace.total_latency_ms / 1000)
  );

  const stats = [
    { label: "tokens", value: totalTokens.toLocaleString() },
    {
      label: "latency",
      value: `${(trace.total_latency_ms / 1000).toFixed(2)}s`,
    },
    { label: "llm calls", value: llmCalls.toString() },
    { label: "tool calls", value: toolCalls.toString() },
    { label: "est. cost", value: `$${estimatedCost.toFixed(4)}` },
    { label: "throughput", value: `${throughput} tok/s` },
  ];

  return (
    <motion.section
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5, ease }}
      className="mb-12"
    >
      <div className="rounded-xl border border-white/[0.06] bg-[#0e0e0e] overflow-hidden">
        {/* Identity row */}
        <div className="px-5 py-3 border-b border-white/[0.04] flex flex-wrap items-center gap-x-4 gap-y-1 font-mono text-[12px]">
          <span className="text-primary">{trace.agent_name}</span>
          <span className="text-neutral-700">│</span>
          <span className="text-neutral-400">{trace.model}</span>
          <span className="text-neutral-700">│</span>
          <span className="text-neutral-600">{trace.trace_id}</span>
        </div>

        {/* Stats strip */}
        <div className="grid grid-cols-3 sm:grid-cols-6">
          {stats.map((stat, i) => (
            <div
              key={stat.label}
              className={`px-4 py-3.5 ${
                i > 0 ? "border-l border-white/[0.04]" : ""
              }`}
            >
              <div className="font-mono text-[14px] text-white leading-none mb-1.5">
                {stat.value}
              </div>
              <div className="font-mono text-[10px] text-neutral-600 uppercase tracking-[0.15em]">
                {stat.label}
              </div>
            </div>
          ))}
        </div>
      </div>
    </motion.section>
  );
}
