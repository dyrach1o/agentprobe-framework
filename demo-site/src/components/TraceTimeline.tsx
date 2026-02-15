import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { BrainIcon, WrenchIcon, ChevronDownIcon, SuccessCircleIcon, FailCircleIcon } from "../components/Icons";
import { Prism as SyntaxHighlighter } from "react-syntax-highlighter";
import { vscDarkPlus } from "react-syntax-highlighter/dist/esm/styles/prism";
import type { Turn } from "../data/sampleTrace";

const ease: [number, number, number, number] = [0.22, 1, 0.36, 1];

/* ------------------------------------------------------------------ */
/* Single turn card                                                    */
/* ------------------------------------------------------------------ */

function TurnCard({ turn, index }: { turn: Turn; index: number }) {
  const [open, setOpen] = useState(false);
  const isLlm = turn.turn_type === "llm_call";

  const dotColor = isLlm ? "bg-primary/20" : "bg-accent/20";
  const borderColor = isLlm ? "border-l-primary" : "border-l-accent";
  const Icon = isLlm ? BrainIcon : WrenchIcon;

  const latency = isLlm
    ? turn.llm_call?.latency_ms
    : turn.tool_call?.latency_ms;

  return (
    <motion.div
      initial={{ opacity: 0, x: -24 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ duration: 0.5, delay: index * 0.08, ease }}
      className="relative pl-10"
    >
      {/* Timeline dot */}
      <div
        className={`absolute left-0 top-5 flex h-7 w-7 items-center justify-center rounded-full ${dotColor}`}
      >
        <Icon size={16} />
      </div>

      {/* Vertical connector line */}
      <div className="absolute left-[13px] top-12 bottom-0 w-px bg-white/[0.06]" />

      {/* Card */}
      <button
        type="button"
        onClick={() => setOpen((prev) => !prev)}
        className={`w-full cursor-pointer rounded-2xl border border-white/[0.06] border-l-[3px] ${borderColor}
                    bg-surface p-5 text-left transition-colors duration-300
                    hover:border-white/[0.1] hover:bg-surface-light`}
      >
        {/* Header row */}
        <div className="flex items-center justify-between gap-3">
          <div className="flex min-w-0 flex-1 items-center gap-3">
            {/* Step number */}
            <span className="flex h-6 w-6 shrink-0 items-center justify-center rounded-lg border border-white/[0.06] font-mono text-xs font-semibold text-neutral-500">
              {index + 1}
            </span>

            {/* Type badge — border style, no bg fill */}
            <span
              className={`shrink-0 rounded-md border px-2.5 py-0.5 text-xs font-medium ${
                isLlm
                  ? "border-primary/30 text-primary"
                  : "border-accent/30 text-accent"
              }`}
            >
              {isLlm ? "LLM Call" : "Tool Call"}
            </span>

            {/* Name */}
            <span className="truncate text-sm text-white">
              {isLlm
                ? turn.llm_call?.model ?? "unknown"
                : turn.tool_call?.tool_name ?? "unknown"}
            </span>

            {/* Success / failure badge (tool calls only) */}
            {!isLlm && turn.tool_call && (
              <span
                className={`flex shrink-0 items-center gap-1 rounded-md border px-2 py-0.5 text-xs font-medium ${
                  turn.tool_call.success
                    ? "border-success/30 text-success"
                    : "border-danger/30 text-danger"
                }`}
              >
                {turn.tool_call.success ? (
                  <SuccessCircleIcon size={14} />
                ) : (
                  <FailCircleIcon size={14} />
                )}
                {turn.tool_call.success ? "success" : "failed"}
              </span>
            )}
          </div>

          {/* Right side: tokens / latency / chevron */}
          <div className="flex shrink-0 items-center gap-3">
            {isLlm && turn.llm_call && (
              <span className="hidden font-mono text-xs text-neutral-500 sm:inline">
                {turn.llm_call.input_tokens} in / {turn.llm_call.output_tokens}{" "}
                out
              </span>
            )}
            {latency !== undefined && (
              <span className="font-mono text-xs text-neutral-600">
                {latency >= 1000
                  ? `${(latency / 1000).toFixed(2)}s`
                  : `${latency}ms`}
              </span>
            )}
            <motion.span
              animate={{ rotate: open ? 180 : 0 }}
              transition={{ duration: 0.25, ease }}
            >
              <ChevronDownIcon size={16} />
            </motion.span>
          </div>
        </div>

        {/* Collapsed summary */}
        <p className="mt-2.5 text-xs leading-relaxed text-neutral-400">
          {turn.content}
        </p>
      </button>

      {/* Expanded detail */}
      <AnimatePresence>
        {open && (
          <motion.div
            key={turn.turn_id + "-detail"}
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: "auto", opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.35, ease }}
            className="overflow-hidden"
          >
            <div className="mt-2 space-y-4 rounded-2xl border border-white/[0.06] bg-surface-light p-5">
              {isLlm && turn.llm_call && <LlmDetail call={turn.llm_call} />}
              {!isLlm && turn.tool_call && (
                <ToolDetail call={turn.tool_call} />
              )}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  );
}

/* ------------------------------------------------------------------ */
/* LLM call detail                                                     */
/* ------------------------------------------------------------------ */

function LlmDetail({
  call,
}: {
  call: NonNullable<Turn["llm_call"]>;
}) {
  return (
    <>
      {/* Token badges — border style */}
      <div className="flex flex-wrap gap-2">
        <span className="rounded-md border border-primary/30 px-2.5 py-1 font-mono text-xs font-medium text-primary">
          {call.input_tokens} input tokens
        </span>
        <span className="rounded-md border border-primary/30 px-2.5 py-1 font-mono text-xs font-medium text-primary">
          {call.output_tokens} output tokens
        </span>
        <span className="rounded-md border border-white/[0.06] px-2.5 py-1 font-mono text-xs text-neutral-500">
          {call.latency_ms}ms latency
        </span>
        <span className="rounded-md border border-white/[0.06] px-2.5 py-1 font-mono text-xs text-neutral-500">
          {call.model}
        </span>
      </div>

      {/* Input */}
      <div>
        <h4 className="mb-2 text-[13px] font-medium uppercase tracking-[0.2em] text-neutral-500">
          Input
        </h4>
        <div className="rounded-xl border border-white/[0.06] bg-surface p-4 text-sm leading-relaxed text-neutral-300">
          {call.input_text}
        </div>
      </div>

      {/* Output */}
      <div>
        <h4 className="mb-2 text-[13px] font-medium uppercase tracking-[0.2em] text-neutral-500">
          Output
        </h4>
        <div className="rounded-xl border border-white/[0.06] bg-surface p-4 text-sm leading-relaxed text-neutral-300">
          {call.output_text}
        </div>
      </div>
    </>
  );
}

/* ------------------------------------------------------------------ */
/* Tool call detail                                                    */
/* ------------------------------------------------------------------ */

function ToolDetail({
  call,
}: {
  call: NonNullable<Turn["tool_call"]>;
}) {
  const codeStyle: React.CSSProperties = {
    margin: 0,
    borderRadius: "0.75rem",
    fontSize: "0.8125rem",
    lineHeight: 1.6,
    border: "1px solid rgba(255,255,255,0.06)",
  };

  return (
    <>
      {/* Status badges — border style */}
      <div className="flex flex-wrap gap-2">
        <span className="rounded-md border border-accent/30 px-2.5 py-1 text-xs font-medium text-accent">
          {call.tool_name}
        </span>
        <span
          className={`rounded-md border px-2.5 py-1 text-xs font-medium ${
            call.success
              ? "border-success/30 text-success"
              : "border-danger/30 text-danger"
          }`}
        >
          {call.success ? "Success" : "Failed"}
        </span>
        <span className="rounded-md border border-white/[0.06] px-2.5 py-1 font-mono text-xs text-neutral-500">
          {call.latency_ms}ms
        </span>
      </div>

      {/* Input JSON */}
      <div>
        <h4 className="mb-2 text-[13px] font-medium uppercase tracking-[0.2em] text-neutral-500">
          Tool Input
        </h4>
        <SyntaxHighlighter
          language="json"
          style={vscDarkPlus}
          customStyle={codeStyle}
        >
          {JSON.stringify(call.tool_input, null, 2)}
        </SyntaxHighlighter>
      </div>

      {/* Output or Error */}
      <div>
        <h4 className="mb-2 text-[13px] font-medium uppercase tracking-[0.2em] text-neutral-500">
          {call.success ? "Tool Output" : "Error"}
        </h4>
        {call.success && call.tool_output ? (
          <div className="rounded-xl border border-white/[0.06] bg-surface p-4 text-sm leading-relaxed text-success">
            {call.tool_output}
          </div>
        ) : (
          <div className="rounded-xl border border-danger/20 bg-surface p-4 text-sm leading-relaxed text-danger">
            {call.error ?? "Unknown error"}
          </div>
        )}
      </div>
    </>
  );
}

/* ------------------------------------------------------------------ */
/* TraceTimeline                                                       */
/* ------------------------------------------------------------------ */

export default function TraceTimeline({ turns }: { turns: Turn[] }) {
  return (
    <section>
      <motion.div
        initial={{ opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5, delay: 0.2, ease }}
        className="mb-8"
      >
        <p className="mb-4 text-[13px] font-medium uppercase tracking-[0.2em] text-primary">
          Timeline
        </p>
        <h2 className="font-display text-3xl text-white">
          Execution Timeline
        </h2>
      </motion.div>

      <div className="relative space-y-6">
        {turns.map((turn, i) => (
          <TurnCard key={turn.turn_id} turn={turn} index={i} />
        ))}

        {/* Tail cap */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: turns.length * 0.08 + 0.3, ease }}
          className="pl-10"
        >
          <div className="absolute left-[9px] flex h-4 w-4 items-center justify-center rounded-full border border-white/[0.06] bg-surface">
            <div className="h-1.5 w-1.5 rounded-full bg-neutral-600" />
          </div>
          <p className="pt-0.5 text-xs text-neutral-600">
            Trace complete &mdash; {turns.length} turns
          </p>
        </motion.div>
      </div>
    </section>
  );
}
