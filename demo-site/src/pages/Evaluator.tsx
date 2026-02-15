import { useState, useMemo, useCallback } from "react";
import { motion } from "framer-motion";
import type { EvaluationRule, RuleResult } from "../data/evaluatorData.ts";
import {
  defaultRules,
  defaultSampleOutput,
  evaluateOutput,
} from "../data/evaluatorData.ts";
import RuleToggle from "../components/RuleToggle.tsx";
import VerdictBadge from "../components/VerdictBadge.tsx";
import ScoreBar from "../components/ScoreBar.tsx";

export default function Evaluator() {
  const [text, setText] = useState(defaultSampleOutput);
  const [rules, setRules] = useState<EvaluationRule[]>(defaultRules);

  const result = useMemo(() => evaluateOutput(text, rules), [text, rules]);

  const handleToggle = useCallback((id: string) => {
    setRules((prev) =>
      prev.map((r) => (r.id === id ? { ...r, enabled: !r.enabled } : r))
    );
  }, []);

  const resultMap = useMemo(() => {
    const map = new Map<string, RuleResult>();
    for (const rr of result.ruleResults) {
      map.set(rr.ruleId, rr);
    }
    return map;
  }, [result]);

  const enabledCount = rules.filter((r) => r.enabled).length;
  const passedCount = result.ruleResults.filter((r) => r.passed).length;

  return (
    <div className="min-h-screen pb-16 px-6">
      <div className="mx-auto max-w-5xl">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, ease: [0.22, 1, 0.36, 1] }}
          className="mb-16 pt-12"
        >
          <p className="text-[13px] uppercase tracking-[0.2em] text-accent mb-4">
            Playground
          </p>
          <h1 className="font-display text-4xl sm:text-5xl text-white mb-4">
            Evaluator
          </h1>
          <p className="text-neutral-500 max-w-lg leading-relaxed">
            Edit the agent output and toggle rules to see evaluation scores update in real time.
          </p>
        </motion.div>

        {/* Two-column: Editor + Rules */}
        <div className="grid grid-cols-1 lg:grid-cols-5 gap-8 mb-16">
          {/* Left — Agent output editor (3 cols) */}
          <motion.div
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.1, ease: [0.22, 1, 0.36, 1] }}
            className="lg:col-span-3 flex flex-col"
          >
            <div className="flex items-baseline justify-between mb-3">
              <span className="font-mono text-[13px] text-neutral-500">
                agent_output.txt
              </span>
              <span className="font-mono text-[11px] text-neutral-600">
                {text.length} chars
              </span>
            </div>

            {/* Editor with line numbers feel */}
            <div className="relative flex-1 rounded-xl border border-white/[0.06] bg-[#0e0e0e] overflow-hidden">
              {/* Top bar mimicking editor tab */}
              <div className="flex items-center gap-2 px-4 py-2.5 border-b border-white/[0.04] bg-white/[0.01]">
                <div className="h-2.5 w-2.5 rounded-full bg-[#ff5f57]/60" />
                <div className="h-2.5 w-2.5 rounded-full bg-[#febc2e]/60" />
                <div className="h-2.5 w-2.5 rounded-full bg-[#28c840]/60" />
              </div>
              <textarea
                value={text}
                onChange={(e) => setText(e.target.value)}
                rows={18}
                spellCheck={false}
                className="w-full bg-transparent p-5 text-[13px] leading-[1.8] text-neutral-300 font-mono placeholder-neutral-700 outline-none resize-y min-h-[350px]"
                placeholder="Paste agent output here..."
              />
            </div>
          </motion.div>

          {/* Right — Rules (2 cols) */}
          <motion.div
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.2, ease: [0.22, 1, 0.36, 1] }}
            className="lg:col-span-2 flex flex-col"
          >
            <div className="flex items-baseline justify-between mb-3">
              <span className="font-mono text-[13px] text-neutral-500">
                rules.config
              </span>
              <span className="font-mono text-[11px] text-neutral-600">
                {enabledCount}/{rules.length} active
              </span>
            </div>

            {/* Rules list — terminal style */}
            <div className="rounded-xl border border-white/[0.06] bg-[#0e0e0e] overflow-hidden">
              <div className="flex items-center gap-2 px-4 py-2.5 border-b border-white/[0.04] bg-white/[0.01]">
                <div className="h-2.5 w-2.5 rounded-full bg-[#ff5f57]/60" />
                <div className="h-2.5 w-2.5 rounded-full bg-[#febc2e]/60" />
                <div className="h-2.5 w-2.5 rounded-full bg-[#28c840]/60" />
              </div>
              <div className="py-2">
                {rules.map((rule) => (
                  <RuleToggle
                    key={rule.id}
                    rule={rule}
                    result={rule.enabled ? resultMap.get(rule.id) : undefined}
                    onToggle={handleToggle}
                  />
                ))}
              </div>
            </div>

            <p className="mt-3 text-[11px] text-neutral-600 font-mono">
              click a rule to toggle · # = disabled
            </p>
          </motion.div>
        </div>

        {/* Divider */}
        <div className="divider-gradient mb-12" />

        {/* Results */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.3, ease: [0.22, 1, 0.36, 1] }}
          className="mb-16"
        >
          <p className="text-[13px] uppercase tracking-[0.2em] text-primary mb-8">
            Results
          </p>

          <div className="grid grid-cols-1 md:grid-cols-[200px_1fr] gap-12 items-start">
            {/* Verdict */}
            <div>
              <VerdictBadge verdict={result.verdict} percentage={result.percentage} />
              <p className="mt-4 font-mono text-[12px] text-neutral-600">
                {passedCount}/{enabledCount} rules passed
              </p>
            </div>

            {/* Score + breakdown */}
            <div className="space-y-8">
              <ScoreBar
                percentage={result.percentage}
                score={result.score}
                maxScore={result.maxScore}
              />

              {/* Per-rule breakdown as monospace log */}
              <div className="rounded-xl border border-white/[0.06] bg-[#0e0e0e] p-5">
                <p className="font-mono text-[11px] text-neutral-600 mb-3">
                  evaluation log
                </p>
                <div className="space-y-1">
                  {result.ruleResults.map((rr) => {
                    const rule = rules.find((r) => r.id === rr.ruleId);
                    if (!rule) return null;
                    return (
                      <motion.div
                        key={rr.ruleId}
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        className="font-mono text-[12px] leading-[1.8] flex items-center gap-3"
                      >
                        <span
                          className="shrink-0 h-1.5 w-1.5 rounded-full"
                          style={{
                            backgroundColor: rr.passed ? "#22c55e" : "#ef4444",
                          }}
                        />
                        <span className={rr.passed ? "text-neutral-400" : "text-neutral-500"}>
                          {rule.type}
                        </span>
                        <span className="text-neutral-600 truncate flex-1">
                          {rr.detail}
                        </span>
                        <span
                          className="shrink-0"
                          style={{ color: rr.passed ? "#22c55e" : "#ef4444" }}
                        >
                          {rr.passed ? "ok" : "fail"}
                        </span>
                      </motion.div>
                    );
                  })}
                </div>
              </div>
            </div>
          </div>
        </motion.div>
      </div>
    </div>
  );
}
