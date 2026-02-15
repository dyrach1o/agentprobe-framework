import { motion } from "framer-motion";
import { sampleTrace } from "../data/sampleTrace";
import TraceSummary from "../components/TraceSummary";
import TraceTimeline from "../components/TraceTimeline";

const ease = [0.22, 1, 0.36, 1] as const;

export default function TraceViewer() {
  return (
    <div className="min-h-screen bg-[#0a0a0a]">
      <div className="mx-auto max-w-5xl px-6 py-32">
        {/* -------------------------------------------------------- */}
        {/* Header                                                    */}
        {/* -------------------------------------------------------- */}
        <motion.header
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, ease }}
          className="mb-16"
        >
          <p className="mb-4 text-[13px] font-medium uppercase tracking-[0.2em] text-primary">
            Trace Explorer
          </p>
          <h1 className="font-display text-4xl text-white sm:text-5xl">
            Trace Viewer
          </h1>
          <p className="mt-4 max-w-2xl text-base leading-relaxed text-neutral-400">
            Explore a complete agent execution trace &mdash; every LLM call,
            tool invocation, and decision captured.
          </p>
        </motion.header>

        {/* -------------------------------------------------------- */}
        {/* Input / Output overview                                   */}
        {/* -------------------------------------------------------- */}
        <motion.section
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.1, ease }}
          className="mb-12 grid gap-5 md:grid-cols-2"
        >
          {/* User Input card */}
          <div className="rounded-2xl border border-white/[0.06] bg-surface p-6 transition-colors duration-300 hover:border-white/[0.1] hover:bg-surface-light">
            <h3 className="mb-3 text-[13px] font-medium uppercase tracking-[0.2em] text-primary">
              User Input
            </h3>
            <p className="text-sm leading-relaxed text-neutral-300">
              {sampleTrace.input_text}
            </p>
          </div>

          {/* Agent Output card */}
          <div className="rounded-2xl border border-white/[0.06] bg-surface p-6 transition-colors duration-300 hover:border-white/[0.1] hover:bg-surface-light">
            <h3 className="mb-3 text-[13px] font-medium uppercase tracking-[0.2em] text-accent">
              Agent Output
            </h3>
            <p className="text-sm leading-relaxed text-neutral-300">
              {sampleTrace.output_text}
            </p>
          </div>
        </motion.section>

        {/* Divider */}
        <div className="divider-gradient mb-12" />

        {/* -------------------------------------------------------- */}
        {/* Summary stats                                             */}
        {/* -------------------------------------------------------- */}
        <TraceSummary trace={sampleTrace} />

        {/* Divider */}
        <div className="divider-gradient mb-12" />

        {/* -------------------------------------------------------- */}
        {/* Timeline                                                  */}
        {/* -------------------------------------------------------- */}
        <TraceTimeline turns={sampleTrace.turns} />
      </div>
    </div>
  );
}
