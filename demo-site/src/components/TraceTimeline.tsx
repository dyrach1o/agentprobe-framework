import { useState, useMemo } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Prism as SyntaxHighlighter } from "react-syntax-highlighter";
import { vscDarkPlus } from "react-syntax-highlighter/dist/esm/styles/prism";
import type { Turn } from "../data/sampleTrace";

const ease: [number, number, number, number] = [0.22, 1, 0.36, 1];

/* ------------------------------------------------------------------ */
/* Timing computation                                                  */
/* ------------------------------------------------------------------ */

interface TurnTiming {
  turn: Turn;
  index: number;
  startMs: number;
  durationMs: number;
}

function computeTimings(turns: Turn[]): TurnTiming[] {
  let offset = 0;
  return turns.map((turn, index) => {
    const duration =
      turn.turn_type === "llm_call"
        ? turn.llm_call?.latency_ms ?? 0
        : turn.tool_call?.latency_ms ?? 0;
    const timing = { turn, index, startMs: offset, durationMs: duration };
    offset += duration;
    return timing;
  });
}

function getBarColor(turn: Turn): string {
  if (turn.turn_type === "llm_call") return "#e2a04f";
  if (turn.tool_call && !turn.tool_call.success) return "#ef4444";
  return "#8b5cf6";
}

function formatDuration(ms: number): string {
  return ms >= 1000 ? `${(ms / 1000).toFixed(2)}s` : `${ms}ms`;
}

/* ------------------------------------------------------------------ */
/* Waterfall row                                                       */
/* ------------------------------------------------------------------ */

function WaterfallRow({
  timing,
  totalMs,
  isSelected,
  onSelect,
}: {
  timing: TurnTiming;
  totalMs: number;
  isSelected: boolean;
  onSelect: () => void;
}) {
  const { turn, index, startMs, durationMs } = timing;
  const isLlm = turn.turn_type === "llm_call";
  const color = getBarColor(turn);
  const name = isLlm
    ? turn.llm_call?.model ?? "llm"
    : turn.tool_call?.tool_name ?? "tool";
  const leftPct = (startMs / totalMs) * 100;
  const widthPct = Math.max((durationMs / totalMs) * 100, 1.5);
  const failed = !isLlm && turn.tool_call && !turn.tool_call.success;

  return (
    <motion.button
      type="button"
      onClick={onSelect}
      initial={{ opacity: 0, x: -12 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ duration: 0.4, delay: index * 0.06, ease }}
      className={`w-full text-left group transition-colors duration-200 ${
        isSelected ? "bg-white/[0.04]" : "hover:bg-white/[0.02]"
      }`}
    >
      <div className="grid grid-cols-[32px_12px_88px_1fr_60px] items-center gap-2 px-4 py-2.5">
        {/* Step number */}
        <span className="font-mono text-[11px] text-neutral-600 text-right">
          {index + 1}
        </span>

        {/* Type dot */}
        <span
          className="h-2 w-2 rounded-full shrink-0"
          style={{
            backgroundColor: color,
            boxShadow: `0 0 6px ${color}40`,
          }}
        />

        {/* Name */}
        <span
          className="font-mono text-[12px] truncate"
          style={{ color: failed ? "#ef4444" : color }}
        >
          {name}
          {failed && " ✕"}
        </span>

        {/* Waterfall bar */}
        <div className="relative h-5 rounded-sm overflow-hidden bg-white/[0.015]">
          <motion.div
            initial={{ scaleX: 0 }}
            animate={{ scaleX: 1 }}
            transition={{
              duration: 0.6,
              delay: index * 0.06 + 0.2,
              ease,
            }}
            className="absolute top-1 bottom-1 rounded-[3px] origin-left"
            style={{
              left: `${leftPct}%`,
              width: `${widthPct}%`,
              backgroundColor: color,
              opacity: 0.65,
              boxShadow: `0 0 10px ${color}25`,
            }}
          />
        </div>

        {/* Duration */}
        <span className="font-mono text-[11px] text-neutral-500 text-right">
          {formatDuration(durationMs)}
        </span>
      </div>

      {/* Content summary */}
      <div className="px-4 pb-2.5 -mt-1">
        <p className="font-mono text-[11px] text-neutral-600 truncate pl-[46px]">
          {turn.content}
        </p>
      </div>
    </motion.button>
  );
}

/* ------------------------------------------------------------------ */
/* Turn detail — LLM call                                              */
/* ------------------------------------------------------------------ */

function LlmDetail({ call }: { call: NonNullable<Turn["llm_call"]> }) {
  return (
    <div className="px-5 py-4 space-y-4 border-t border-white/[0.04] bg-white/[0.01]">
      {/* Key-value pairs */}
      <div className="font-mono text-[12px] leading-[2] space-y-0">
        <div className="flex gap-4">
          <span className="text-neutral-600 w-16 shrink-0 text-right">
            model
          </span>
          <span className="text-neutral-300">{call.model}</span>
        </div>
        <div className="flex gap-4">
          <span className="text-neutral-600 w-16 shrink-0 text-right">
            tokens
          </span>
          <span className="text-primary">{call.input_tokens}</span>
          <span className="text-neutral-700">→</span>
          <span className="text-primary">{call.output_tokens}</span>
        </div>
        <div className="flex gap-4">
          <span className="text-neutral-600 w-16 shrink-0 text-right">
            latency
          </span>
          <span className="text-neutral-400">{formatDuration(call.latency_ms)}</span>
        </div>
      </div>

      {/* Input */}
      <div>
        <div className="font-mono text-[10px] text-neutral-700 uppercase tracking-[0.15em] mb-2">
          ─── input ───────────────────────
        </div>
        <div className="rounded-lg border border-white/[0.04] bg-[#0c0c0c] px-4 py-3 font-mono text-[12px] leading-[1.7] text-neutral-400">
          {call.input_text}
        </div>
      </div>

      {/* Output */}
      <div>
        <div className="font-mono text-[10px] text-neutral-700 uppercase tracking-[0.15em] mb-2">
          ─── output ──────────────────────
        </div>
        <div className="rounded-lg border border-white/[0.04] bg-[#0c0c0c] px-4 py-3 font-mono text-[12px] leading-[1.7] text-neutral-300">
          {call.output_text}
        </div>
      </div>
    </div>
  );
}

/* ------------------------------------------------------------------ */
/* Turn detail — Tool call                                             */
/* ------------------------------------------------------------------ */

function ToolDetail({ call }: { call: NonNullable<Turn["tool_call"]> }) {
  const codeStyle: React.CSSProperties = {
    margin: 0,
    borderRadius: "0.5rem",
    fontSize: "0.75rem",
    lineHeight: 1.6,
    border: "1px solid rgba(255,255,255,0.04)",
    background: "#0c0c0c",
  };

  return (
    <div className="px-5 py-4 space-y-4 border-t border-white/[0.04] bg-white/[0.01]">
      {/* Key-value pairs */}
      <div className="font-mono text-[12px] leading-[2] space-y-0">
        <div className="flex gap-4">
          <span className="text-neutral-600 w-16 shrink-0 text-right">
            tool
          </span>
          <span className="text-accent">{call.tool_name}</span>
        </div>
        <div className="flex gap-4">
          <span className="text-neutral-600 w-16 shrink-0 text-right">
            status
          </span>
          <span className={call.success ? "text-success" : "text-danger"}>
            {call.success ? "ok" : "failed"}
          </span>
        </div>
        <div className="flex gap-4">
          <span className="text-neutral-600 w-16 shrink-0 text-right">
            latency
          </span>
          <span className="text-neutral-400">
            {formatDuration(call.latency_ms)}
          </span>
        </div>
      </div>

      {/* Input JSON */}
      <div>
        <div className="font-mono text-[10px] text-neutral-700 uppercase tracking-[0.15em] mb-2">
          ─── input ───────────────────────
        </div>
        <SyntaxHighlighter
          language="json"
          style={vscDarkPlus}
          customStyle={codeStyle}
        >
          {JSON.stringify(call.tool_input, null, 2)}
        </SyntaxHighlighter>
      </div>

      {/* Output / Error */}
      <div>
        <div className="font-mono text-[10px] text-neutral-700 uppercase tracking-[0.15em] mb-2">
          ─── {call.success ? "output" : "error"} ──────────────────────
        </div>
        <div
          className={`rounded-lg border px-4 py-3 font-mono text-[12px] leading-[1.7] ${
            call.success
              ? "border-white/[0.04] bg-[#0c0c0c] text-success"
              : "border-danger/20 bg-[#0c0c0c] text-danger"
          }`}
        >
          {call.success ? call.tool_output : call.error ?? "Unknown error"}
        </div>
      </div>
    </div>
  );
}

/* ------------------------------------------------------------------ */
/* TurnDetail dispatcher                                               */
/* ------------------------------------------------------------------ */

function TurnDetail({ turn }: { turn: Turn }) {
  if (turn.turn_type === "llm_call" && turn.llm_call) {
    return <LlmDetail call={turn.llm_call} />;
  }
  if (turn.turn_type === "tool_call" && turn.tool_call) {
    return <ToolDetail call={turn.tool_call} />;
  }
  return null;
}

/* ------------------------------------------------------------------ */
/* TraceTimeline                                                       */
/* ------------------------------------------------------------------ */

export default function TraceTimeline({
  turns,
  totalMs,
}: {
  turns: Turn[];
  totalMs: number;
}) {
  const [selectedIndex, setSelectedIndex] = useState<number | null>(null);
  const timings = useMemo(() => computeTimings(turns), [turns]);

  // Time ruler ticks (whole seconds within the trace duration)
  const totalSec = totalMs / 1000;
  const tickCount = Math.floor(totalSec);
  const ticks = Array.from({ length: tickCount + 1 }, (_, i) => i);

  return (
    <section>
      <motion.div
        initial={{ opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5, delay: 0.2, ease }}
        className="mb-6"
      >
        <p className="text-[13px] uppercase tracking-[0.2em] text-accent mb-4">
          Execution
        </p>
        <h2 className="font-display text-3xl text-white">Waterfall</h2>
      </motion.div>

      <motion.div
        initial={{ opacity: 0, y: 16 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5, delay: 0.3, ease }}
        className="rounded-xl border border-white/[0.06] bg-[#0e0e0e] overflow-hidden"
      >
        {/* Terminal chrome */}
        <div className="flex items-center gap-2 px-4 py-2.5 border-b border-white/[0.04] bg-white/[0.01]">
          <div className="h-2.5 w-2.5 rounded-full bg-[#ff5f57]/60" />
          <div className="h-2.5 w-2.5 rounded-full bg-[#febc2e]/60" />
          <div className="h-2.5 w-2.5 rounded-full bg-[#28c840]/60" />
          <span className="ml-2 font-mono text-[11px] text-neutral-600">
            waterfall
          </span>
        </div>

        {/* Column headers + time ruler */}
        <div className="grid grid-cols-[32px_12px_88px_1fr_60px] items-end gap-2 px-4 pt-2 pb-1.5 border-b border-white/[0.04]">
          <span className="font-mono text-[10px] text-neutral-700 uppercase text-right">
            #
          </span>
          <span />
          <span className="font-mono text-[10px] text-neutral-700 uppercase">
            name
          </span>
          {/* Time ruler */}
          <div className="relative h-4">
            {ticks.map((t) => (
              <span
                key={t}
                className="absolute bottom-0 font-mono text-[9px] text-neutral-700"
                style={{
                  left: `${(t / totalSec) * 100}%`,
                  transform: t === 0 ? "none" : "translateX(-50%)",
                }}
              >
                {t}s
              </span>
            ))}
          </div>
          <span className="font-mono text-[10px] text-neutral-700 uppercase text-right">
            time
          </span>
        </div>

        {/* Waterfall rows */}
        <div className="divide-y divide-white/[0.02]">
          {timings.map((timing) => (
            <div key={timing.turn.turn_id}>
              <WaterfallRow
                timing={timing}
                totalMs={totalMs}
                isSelected={selectedIndex === timing.index}
                onSelect={() =>
                  setSelectedIndex((prev) =>
                    prev === timing.index ? null : timing.index
                  )
                }
              />
              <AnimatePresence>
                {selectedIndex === timing.index && (
                  <motion.div
                    initial={{ height: 0, opacity: 0 }}
                    animate={{ height: "auto", opacity: 1 }}
                    exit={{ height: 0, opacity: 0 }}
                    transition={{ duration: 0.3, ease }}
                    className="overflow-hidden"
                  >
                    <TurnDetail turn={timing.turn} />
                  </motion.div>
                )}
              </AnimatePresence>
            </div>
          ))}
        </div>

        {/* Footer */}
        <div className="px-4 py-2.5 border-t border-white/[0.04] flex items-center justify-between font-mono text-[11px] text-neutral-600">
          <span>{turns.length} steps · click to inspect</span>
          <span>{(totalMs / 1000).toFixed(2)}s total</span>
        </div>
      </motion.div>
    </section>
  );
}
