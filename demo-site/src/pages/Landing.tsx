import { Link } from "react-router-dom";
import { motion, useScroll, useTransform } from "framer-motion";
import { useRef } from "react";
import {
  TraceIcon,
  EvalIcon,
  CostIcon,
  SafetyIcon,
  ArrowRightIcon,
  TerminalIcon,
  ProbeEyeIcon,
  FlaskIcon,
  ChartIcon,
} from "../components/Icons";
import AnimatedCounter from "../components/AnimatedCounter";
import Logo from "../components/Logo";

/* ------------------------------------------------------------------ */
/*  Data                                                               */
/* ------------------------------------------------------------------ */

const features = [
  {
    icon: TraceIcon,
    title: "Trace Recording",
    description:
      "Every LLM call, tool invocation, and agent decision captured as a structured, replayable trace.",
  },
  {
    icon: EvalIcon,
    title: "Behavioral Evaluation",
    description:
      "Rule-based, embedding, and LLM-judge evaluators that score agent outputs on multiple dimensions.",
  },
  {
    icon: CostIcon,
    title: "Cost Tracking",
    description:
      "Built-in pricing for 6 providers with per-trace cost roll-ups and budget enforcement.",
  },
  {
    icon: SafetyIcon,
    title: "Safety Scanning",
    description:
      "6 built-in suites: prompt injection, data leakage, jailbreak, PII detection, and more.",
  },
];

const stats = [
  { target: 6, label: "Adapters" },
  { target: 6, label: "Providers" },
  { target: 1100, suffix: "+", label: "Tests" },
  { target: 6, label: "Safety Suites" },
];

const demoCards = [
  {
    to: "/trace-viewer",
    icon: ProbeEyeIcon,
    title: "Trace Viewer",
    description: "Explore a complete agent execution trace with timing and token breakdowns.",
  },
  {
    to: "/evaluator",
    icon: FlaskIcon,
    title: "Evaluator",
    description: "Run behavioral evaluators against agent outputs in real time.",
  },
  {
    to: "/cost",
    icon: ChartIcon,
    title: "Cost Dashboard",
    description: "Visualize spend across providers with drill-down by model.",
  },
];

/* ------------------------------------------------------------------ */
/*  Component                                                          */
/* ------------------------------------------------------------------ */

export default function Landing() {
  const heroRef = useRef<HTMLDivElement>(null);
  const { scrollYProgress } = useScroll({
    target: heroRef,
    offset: ["start start", "end start"],
  });
  const heroOpacity = useTransform(scrollYProgress, [0, 0.8], [1, 0]);
  const heroY = useTransform(scrollYProgress, [0, 0.8], [0, -60]);

  return (
    <div className="relative overflow-hidden">
      {/* ====== Hero ====== */}
      <section
        ref={heroRef}
        className="relative flex min-h-[92vh] flex-col items-center justify-center px-6"
      >
        {/* Background elements */}
        <div className="pointer-events-none absolute inset-0 dot-grid opacity-60" />
        <GradientOrbs />

        <motion.div
          style={{ opacity: heroOpacity, y: heroY }}
          className="relative z-10 max-w-4xl text-center"
        >
          {/* Pill badge */}
          <motion.div
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.1 }}
            className="mb-8 inline-flex items-center gap-2.5 rounded-full border border-white/[0.06] bg-white/[0.03] px-4 py-2 backdrop-blur-sm"
          >
            <TerminalIcon size={16} />
            <span className="text-[13px] text-neutral-400">
              pytest-native agent testing framework
            </span>
          </motion.div>

          {/* Headline — editorial serif */}
          <motion.h1
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8, delay: 0.2, ease: [0.22, 1, 0.36, 1] }}
            className="font-display text-[clamp(2.5rem,7vw,5.5rem)] leading-[1.05] tracking-tight text-white"
          >
            Test your agents{" "}
            <span className="text-gradient italic">
              like production software
            </span>
          </motion.h1>

          {/* Sub-copy */}
          <motion.p
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.7, delay: 0.5 }}
            className="mx-auto mt-8 max-w-xl text-lg leading-relaxed text-neutral-400"
          >
            Record traces, evaluate behavior, track costs, and scan for
            vulnerabilities — all from pytest.
          </motion.p>

          {/* CTAs */}
          <motion.div
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.7 }}
            className="mt-12 flex flex-wrap items-center justify-center gap-4"
          >
            <a
              href="#demos"
              className="group inline-flex items-center gap-2 rounded-full bg-white px-7 py-3 text-[14px] font-semibold text-black transition-all duration-300 hover:bg-neutral-200 hover:shadow-[0_0_40px_rgba(255,255,255,0.1)]"
            >
              Explore demos
              <ArrowRightIcon size={15} />
            </a>
            <a
              href="https://github.com/dyrach1o/agentprobe-framework"
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-2 rounded-full border border-white/[0.08] px-7 py-3 text-[14px] font-medium text-neutral-400 transition-all duration-300 hover:border-white/[0.15] hover:text-white"
            >
              View source
            </a>
          </motion.div>

          {/* Code snippet */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.7, delay: 0.9 }}
            className="mx-auto mt-16 max-w-lg rounded-xl border border-white/[0.06] bg-[#111]/80 p-5 backdrop-blur-sm text-left"
          >
            <div className="flex items-center gap-2 mb-4">
              <div className="h-3 w-3 rounded-full bg-[#ff5f57]" />
              <div className="h-3 w-3 rounded-full bg-[#febc2e]" />
              <div className="h-3 w-3 rounded-full bg-[#28c840]" />
              <span className="ml-3 text-[11px] text-neutral-600 font-mono">test_my_agent.py</span>
            </div>
            <pre className="font-mono text-[13px] leading-[1.7] overflow-x-auto">
              <code>
                <span className="text-neutral-500">{"# pip install agentprobe-framework"}</span>
                {"\n"}
                <span className="text-primary">async def</span>
                <span className="text-neutral-300">{" test_greeting"}</span>
                <span className="text-neutral-500">{"(agentprobe):"}</span>
                {"\n"}
                <span className="text-neutral-500">{"    trace = "}</span>
                <span className="text-primary">await</span>
                <span className="text-neutral-400">{" agentprobe.invoke("}</span>
                <span className="text-accent-light">{"\"Say hello\""}</span>
                <span className="text-neutral-500">{")"}</span>
                {"\n\n"}
                <span className="text-neutral-500">{"    "}</span>
                <span className="text-neutral-300">{"assert_trace"}</span>
                <span className="text-neutral-500">{"(trace)."}</span>
                <span className="text-primary">{"has_output"}</span>
                <span className="text-neutral-500">{"()."}</span>
                <span className="text-primary">{"contains"}</span>
                <span className="text-neutral-500">{"("}</span>
                <span className="text-accent-light">{"\"hello\""}</span>
                <span className="text-neutral-500">{")"}</span>
                {"\n"}
                <span className="text-neutral-500">{"    "}</span>
                <span className="text-neutral-300">{"assert_cost"}</span>
                <span className="text-neutral-500">{"(trace, "}</span>
                <span className="text-warm">{"max_usd"}</span>
                <span className="text-neutral-500">{"="}</span>
                <span className="text-accent-light">{"0.01"}</span>
                <span className="text-neutral-500">{")"}</span>
              </code>
            </pre>
          </motion.div>
        </motion.div>

        {/* Scroll hint */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 1.5 }}
          className="absolute bottom-10 left-1/2 -translate-x-1/2"
        >
          <motion.div
            animate={{ y: [0, 6, 0] }}
            transition={{ repeat: Infinity, duration: 2, ease: "easeInOut" }}
            className="flex flex-col items-center gap-2"
          >
            <span className="text-[11px] uppercase tracking-[0.2em] text-neutral-600">Scroll</span>
            <div className="h-8 w-px bg-gradient-to-b from-neutral-600 to-transparent" />
          </motion.div>
        </motion.div>
      </section>

      {/* ====== Divider ====== */}
      <div className="divider-gradient" />

      {/* ====== Features ====== */}
      <section className="relative mx-auto max-w-5xl px-6 py-32">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.7 }}
          className="mb-20"
        >
          <p className="text-[13px] uppercase tracking-[0.2em] text-primary mb-4">
            Capabilities
          </p>
          <h2 className="font-display text-4xl text-white sm:text-5xl max-w-lg leading-[1.15]">
            Everything you need to test agents
          </h2>
        </motion.div>

        <div className="grid gap-px sm:grid-cols-2 rounded-2xl border border-white/[0.06] overflow-hidden bg-white/[0.03]">
          {features.map((f, i) => (
            <motion.div
              key={f.title}
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true, margin: "-40px" }}
              transition={{ duration: 0.5, delay: i * 0.08 }}
              className="group p-8 bg-[#0a0a0a] transition-colors duration-500 hover:bg-surface"
            >
              <div className="mb-5 inline-flex h-10 w-10 items-center justify-center rounded-xl border border-white/[0.06] bg-white/[0.03] text-primary transition-colors duration-300 group-hover:border-primary/20 group-hover:bg-primary/[0.06]">
                <f.icon size={20} />
              </div>
              <h3 className="mb-2.5 text-[17px] font-semibold text-white">
                {f.title}
              </h3>
              <p className="text-[14px] leading-relaxed text-neutral-500">
                {f.description}
              </p>
            </motion.div>
          ))}
        </div>
      </section>

      {/* ====== Divider ====== */}
      <div className="divider-gradient" />

      {/* ====== Stats ====== */}
      <section className="mx-auto max-w-4xl px-6 py-28">
        <div className="grid grid-cols-2 gap-16 md:grid-cols-4">
          {stats.map((s) => (
            <AnimatedCounter
              key={s.label}
              target={s.target}
              suffix={s.suffix}
              label={s.label}
            />
          ))}
        </div>
      </section>

      {/* ====== Divider ====== */}
      <div className="divider-gradient" />

      {/* ====== Interactive Demos ====== */}
      <section id="demos" className="mx-auto max-w-5xl px-6 py-32">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.7 }}
          className="mb-16"
        >
          <p className="text-[13px] uppercase tracking-[0.2em] text-accent mb-4">
            Interactive
          </p>
          <h2 className="font-display text-4xl text-white sm:text-5xl max-w-lg leading-[1.15]">
            See it in action
          </h2>
          <p className="mt-5 max-w-lg text-neutral-500 leading-relaxed">
            Explore the core capabilities through live demos built with real AgentProbe data.
          </p>
        </motion.div>

        <div className="grid gap-5 md:grid-cols-3">
          {demoCards.map((card, i) => (
            <motion.div
              key={card.to}
              initial={{ opacity: 0, y: 24 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true, margin: "-40px" }}
              transition={{ duration: 0.5, delay: i * 0.1 }}
            >
              <Link
                to={card.to}
                className="group flex flex-col rounded-2xl border border-white/[0.06] bg-surface p-6 transition-all duration-500 hover:border-white/[0.1] hover:bg-surface-light"
              >
                {/* Icon area */}
                <div className="mb-6 flex h-12 w-12 items-center justify-center rounded-xl border border-white/[0.06] bg-white/[0.03] text-neutral-500 transition-all duration-500 group-hover:text-primary group-hover:border-primary/20">
                  <card.icon size={22} />
                </div>
                <h3 className="mb-2 text-[16px] font-semibold text-white">
                  {card.title}
                </h3>
                <p className="mb-5 text-[14px] leading-relaxed text-neutral-500 flex-1">
                  {card.description}
                </p>
                <div className="flex items-center gap-1.5 text-[13px] font-medium text-primary opacity-0 transition-all duration-300 group-hover:opacity-100 group-hover:translate-x-1">
                  <span>Explore</span>
                  <ArrowRightIcon size={13} />
                </div>
              </Link>
            </motion.div>
          ))}
        </div>
      </section>

      {/* ====== Divider ====== */}
      <div className="divider-gradient" />

      {/* ====== Footer ====== */}
      <footer className="mx-auto max-w-5xl px-6 py-16">
        <div className="flex flex-col items-center gap-8 sm:flex-row sm:justify-between">
          <div className="flex items-center gap-3">
            <Logo size={26} />
            <span className="text-[13px] text-neutral-600">
              AgentProbe &middot; Apache 2.0
            </span>
          </div>

          <div className="flex items-center gap-8">
            <FooterLink href="https://github.com/dyrach1o/agentprobe-framework" label="GitHub" />
            <FooterLink href="https://pypi.org/project/agentprobe-framework/" label="PyPI" />
            <FooterLink href="https://dyrach1o.github.io/agentprobe-framework/" label="Docs" />
          </div>
        </div>
      </footer>
    </div>
  );
}

/* ------------------------------------------------------------------ */
/*  Sub-components                                                     */
/* ------------------------------------------------------------------ */

function FooterLink({ href, label }: { href: string; label: string }) {
  return (
    <a
      href={href}
      target="_blank"
      rel="noopener noreferrer"
      className="text-[13px] text-neutral-600 transition-colors duration-300 hover:text-neutral-400"
    >
      {label}
    </a>
  );
}

function GradientOrbs() {
  return (
    <div className="pointer-events-none absolute inset-0 overflow-hidden">
      <motion.div
        animate={{
          x: [0, 30, -20, 0],
          y: [0, -20, 15, 0],
          scale: [1, 1.05, 0.97, 1],
        }}
        transition={{ repeat: Infinity, duration: 25, ease: "easeInOut" }}
        className="absolute -top-40 left-1/4 h-[500px] w-[500px] rounded-full opacity-[0.04]"
        style={{
          background: "radial-gradient(circle, #e2a04f, transparent 70%)",
        }}
      />
      <motion.div
        animate={{
          x: [0, -25, 15, 0],
          y: [0, 30, -15, 0],
          scale: [1, 0.97, 1.05, 1],
        }}
        transition={{ repeat: Infinity, duration: 30, ease: "easeInOut" }}
        className="absolute -bottom-32 right-1/4 h-[600px] w-[600px] rounded-full opacity-[0.04]"
        style={{
          background: "radial-gradient(circle, #8b5cf6, transparent 70%)",
        }}
      />
      <motion.div
        animate={{
          x: [0, 15, -25, 0],
          y: [0, -15, 25, 0],
        }}
        transition={{ repeat: Infinity, duration: 22, ease: "easeInOut" }}
        className="absolute top-1/3 right-1/3 h-[400px] w-[400px] rounded-full opacity-[0.03]"
        style={{
          background: "radial-gradient(circle, #c76a4a, transparent 70%)",
        }}
      />
    </div>
  );
}
