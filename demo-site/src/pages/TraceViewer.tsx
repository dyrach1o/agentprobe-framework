import { motion } from "framer-motion";
import { sampleTrace } from "../data/sampleTrace";
import TraceSummary from "../components/TraceSummary";
import TraceTimeline from "../components/TraceTimeline";

const ease = [0.22, 1, 0.36, 1] as const;

export default function TraceViewer() {
  return (
    <div className="min-h-screen pb-16 px-6">
      <div className="mx-auto max-w-5xl">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, ease }}
          className="mb-16 pt-12"
        >
          <p className="text-[13px] uppercase tracking-[0.2em] text-accent mb-4">
            Playground
          </p>
          <h1 className="font-display text-4xl sm:text-5xl text-white mb-4">
            Trace Viewer
          </h1>
          <p className="text-neutral-500 max-w-lg leading-relaxed">
            Explore a complete agent execution &mdash; every decision, tool
            call, and model invocation captured and timed.
          </p>
        </motion.div>

        {/* I/O Terminal */}
        <motion.div
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.1, ease }}
          className="mb-12"
        >
          <div className="flex items-baseline justify-between mb-3">
            <span className="font-mono text-[13px] text-neutral-500">
              session
            </span>
          </div>
          <div className="rounded-xl border border-white/[0.06] bg-[#0e0e0e] overflow-hidden">
            {/* Chrome */}
            <div className="flex items-center gap-2 px-4 py-2.5 border-b border-white/[0.04] bg-white/[0.01]">
              <div className="h-2.5 w-2.5 rounded-full bg-[#ff5f57]/60" />
              <div className="h-2.5 w-2.5 rounded-full bg-[#febc2e]/60" />
              <div className="h-2.5 w-2.5 rounded-full bg-[#28c840]/60" />
            </div>
            {/* Input */}
            <div className="px-5 py-3.5 border-b border-white/[0.04] font-mono text-[13px] leading-[1.7]">
              <span className="text-primary mr-3">▸</span>
              <span className="text-neutral-300">
                {sampleTrace.input_text}
              </span>
            </div>
            {/* Output */}
            <div className="px-5 py-3.5 font-mono text-[13px] leading-[1.7]">
              <span className="text-accent mr-3">◂</span>
              <span className="text-neutral-400">
                {sampleTrace.output_text}
              </span>
            </div>
          </div>
        </motion.div>

        {/* Divider */}
        <div className="divider-gradient mb-12" />

        {/* Summary stats */}
        <TraceSummary trace={sampleTrace} />

        {/* Divider */}
        <div className="divider-gradient mb-12" />

        {/* Waterfall timeline */}
        <TraceTimeline
          turns={sampleTrace.turns}
          totalMs={sampleTrace.total_latency_ms}
        />
      </div>
    </div>
  );
}
