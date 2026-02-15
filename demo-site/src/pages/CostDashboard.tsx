import { motion } from "framer-motion";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  AreaChart,
  Area,
  PieChart,
  Pie,
  Cell,
} from "recharts";
import { CostIcon, TokenIcon, TrendIcon, GaugeIcon } from "../components/Icons.tsx";
import GlowCard from "../components/GlowCard.tsx";
import BudgetGauge from "../components/BudgetGauge.tsx";
import {
  summaryCards,
  costByModel,
  tokenUsageOverTests,
  costByProvider,
  budgetConfig,
} from "../data/costData.ts";

/* ------------------------------------------------------------------ */
/*  Constants                                                          */
/* ------------------------------------------------------------------ */

const EASE: [number, number, number, number] = [0.22, 1, 0.36, 1];
const STAGGER = 0.08;

/* ------------------------------------------------------------------ */
/*  Animated number display                                            */
/* ------------------------------------------------------------------ */

function AnimatedValue({
  value,
  className = "",
}: {
  value: string;
  className?: string;
}) {
  return (
    <motion.span
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5, delay: 0.2, ease: EASE }}
      className={className}
    >
      {value}
    </motion.span>
  );
}

/* ------------------------------------------------------------------ */
/*  Custom tooltip — Obsidian theme                                    */
/* ------------------------------------------------------------------ */

interface TooltipPayloadItem {
  name: string;
  value: number;
  color: string;
  dataKey: string;
}

interface CustomTooltipProps {
  active?: boolean;
  payload?: TooltipPayloadItem[];
  label?: string;
}

function ObsidianTooltip({ active, payload, label }: CustomTooltipProps) {
  if (!active || !payload?.length) return null;
  return (
    <div className="rounded-lg border border-white/[0.06] bg-[#141414] px-3 py-2 shadow-xl">
      {label && (
        <p className="mb-1 text-xs font-medium text-neutral-500">{label}</p>
      )}
      {payload.map((entry) => (
        <p key={entry.dataKey} className="text-xs" style={{ color: entry.color }}>
          {entry.name}:{" "}
          {typeof entry.value === "number" &&
          entry.dataKey !== "inputTokens" &&
          entry.dataKey !== "outputTokens"
            ? `$${entry.value.toFixed(4)}`
            : entry.value.toLocaleString()}
        </p>
      ))}
    </div>
  );
}

/* ------------------------------------------------------------------ */
/*  Summary card icons & colors                                        */
/* ------------------------------------------------------------------ */

const cardIcons = [CostIcon, TokenIcon, GaugeIcon, TrendIcon];

/* ------------------------------------------------------------------ */
/*  Page component                                                     */
/* ------------------------------------------------------------------ */

export default function CostDashboard() {
  return (
    <div className="min-h-screen pb-16 px-4 sm:px-6 lg:px-8">
      <div className="mx-auto max-w-7xl">
        {/* ========================================================== */}
        {/*  Header — section label + serif title, left-aligned         */}
        {/* ========================================================== */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, ease: EASE }}
          className="mb-10 pt-8"
        >
          <p className="text-[13px] uppercase tracking-[0.2em] text-primary mb-4">
            Analytics
          </p>
          <h1 className="font-display text-3xl sm:text-4xl text-white mb-3">
            Cost Dashboard
          </h1>
          <p className="text-neutral-500 text-base sm:text-lg max-w-2xl">
            Track token usage and costs across providers with built-in budget
            enforcement.
          </p>
        </motion.div>

        {/* ========================================================== */}
        {/*  Summary Cards                                              */}
        {/* ========================================================== */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-10">
          {summaryCards.map((card, i) => {
            const Icon = cardIcons[i];

            return (
              <GlowCard key={card.label} delay={i * STAGGER}>
                <div className="flex items-start justify-between">
                  <div>
                    <p className="text-[11px] font-medium text-neutral-500 uppercase tracking-[0.15em] mb-1">
                      {card.label}
                    </p>
                    <AnimatedValue
                      value={card.value}
                      className="text-2xl font-bold text-white font-mono"
                    />
                    <p className="text-xs text-neutral-600 mt-1">
                      {card.description}
                    </p>
                  </div>
                  <div
                    className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl border border-white/[0.06] bg-white/[0.03]"
                  >
                    <Icon size={20} />
                  </div>
                </div>
              </GlowCard>
            );
          })}
        </div>

        {/* ========================================================== */}
        {/*  Charts Row 1: Cost by Model + Token Usage                  */}
        {/* ========================================================== */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
          {/* Cost by Model (Horizontal Bar Chart) */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.6, delay: 0.1, ease: EASE }}
            className="rounded-2xl border border-white/[0.06] bg-surface p-6"
          >
            <h3 className="text-[13px] font-medium text-neutral-500 uppercase tracking-wider mb-4">
              Cost by Model
            </h3>
            <ResponsiveContainer width="100%" height={240}>
              <BarChart
                data={costByModel}
                layout="vertical"
                margin={{ top: 0, right: 30, left: 10, bottom: 0 }}
              >
                <CartesianGrid
                  strokeDasharray="3 3"
                  stroke="#1e1e1e"
                  horizontal={false}
                />
                <XAxis
                  type="number"
                  tick={{ fill: "#737373", fontSize: 11 }}
                  tickFormatter={(v: number) => `$${v.toFixed(3)}`}
                  axisLine={{ stroke: "#262626" }}
                />
                <YAxis
                  type="category"
                  dataKey="model"
                  tick={{ fill: "#737373", fontSize: 11 }}
                  width={130}
                  axisLine={{ stroke: "#262626" }}
                />
                <Tooltip content={<ObsidianTooltip />} />
                <Bar
                  dataKey="cost"
                  name="Cost"
                  radius={[0, 6, 6, 0]}
                  animationDuration={1200}
                >
                  {costByModel.map((entry) => (
                    <Cell key={entry.model} fill={entry.color} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </motion.div>

          {/* Token Usage Over Tests (Area Chart) */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.6, delay: 0.2, ease: EASE }}
            className="rounded-2xl border border-white/[0.06] bg-surface p-6"
          >
            <h3 className="text-[13px] font-medium text-neutral-500 uppercase tracking-wider mb-4">
              Token Usage Over Tests
            </h3>
            <ResponsiveContainer width="100%" height={240}>
              <AreaChart
                data={tokenUsageOverTests}
                margin={{ top: 0, right: 10, left: 0, bottom: 0 }}
              >
                <defs>
                  <linearGradient
                    id="inputGradient"
                    x1="0"
                    y1="0"
                    x2="0"
                    y2="1"
                  >
                    <stop offset="0%" stopColor="#e2a04f" stopOpacity={0.3} />
                    <stop offset="100%" stopColor="#e2a04f" stopOpacity={0.02} />
                  </linearGradient>
                  <linearGradient
                    id="outputGradient"
                    x1="0"
                    y1="0"
                    x2="0"
                    y2="1"
                  >
                    <stop offset="0%" stopColor="#8b5cf6" stopOpacity={0.3} />
                    <stop offset="100%" stopColor="#8b5cf6" stopOpacity={0.02} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#1e1e1e" />
                <XAxis
                  dataKey="test"
                  tick={{ fill: "#737373", fontSize: 11 }}
                  axisLine={{ stroke: "#262626" }}
                />
                <YAxis
                  tick={{ fill: "#737373", fontSize: 11 }}
                  axisLine={{ stroke: "#262626" }}
                  tickFormatter={(v: number) =>
                    v >= 1000 ? `${(v / 1000).toFixed(1)}k` : String(v)
                  }
                />
                <Tooltip content={<ObsidianTooltip />} />
                <Area
                  type="monotone"
                  dataKey="inputTokens"
                  name="Input Tokens"
                  stroke="#e2a04f"
                  strokeWidth={2}
                  fill="url(#inputGradient)"
                  animationDuration={1400}
                />
                <Area
                  type="monotone"
                  dataKey="outputTokens"
                  name="Output Tokens"
                  stroke="#8b5cf6"
                  strokeWidth={2}
                  fill="url(#outputGradient)"
                  animationDuration={1400}
                />
              </AreaChart>
            </ResponsiveContainer>

            {/* Legend */}
            <div className="mt-3 flex items-center gap-6">
              <div className="flex items-center gap-2">
                <div className="h-2.5 w-2.5 rounded-full bg-primary" />
                <span className="text-xs text-neutral-500">Input Tokens</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="h-2.5 w-2.5 rounded-full bg-accent" />
                <span className="text-xs text-neutral-500">Output Tokens</span>
              </div>
            </div>
          </motion.div>
        </div>

        {/* ========================================================== */}
        {/*  Charts Row 2: Cost Distribution + Budget Gauge             */}
        {/* ========================================================== */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Cost Distribution (Donut Chart) */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.6, delay: 0.1, ease: EASE }}
            className="rounded-2xl border border-white/[0.06] bg-surface p-6"
          >
            <h3 className="text-[13px] font-medium text-neutral-500 uppercase tracking-wider mb-4">
              Cost Distribution by Provider
            </h3>
            <div className="flex flex-col sm:flex-row items-center gap-6">
              <ResponsiveContainer width="100%" height={220}>
                <PieChart>
                  <Pie
                    data={costByProvider}
                    cx="50%"
                    cy="50%"
                    innerRadius={55}
                    outerRadius={85}
                    paddingAngle={3}
                    dataKey="value"
                    animationDuration={1200}
                    stroke="none"
                  >
                    {costByProvider.map((entry) => (
                      <Cell key={entry.name} fill={entry.color} />
                    ))}
                  </Pie>
                  <Tooltip
                    content={({ active, payload }) => {
                      if (!active || !payload?.length) return null;
                      const data = payload[0].payload as {
                        name: string;
                        value: number;
                        color: string;
                      };
                      return (
                        <div className="rounded-lg border border-white/[0.06] bg-[#141414] px-3 py-2 shadow-xl">
                          <p
                            className="text-xs font-medium"
                            style={{ color: data.color }}
                          >
                            {data.name}: {data.value}%
                          </p>
                        </div>
                      );
                    }}
                  />
                </PieChart>
              </ResponsiveContainer>

              {/* Legend */}
              <div className="flex flex-col gap-2.5 sm:min-w-[120px]">
                {costByProvider.map((entry) => (
                  <div key={entry.name} className="flex items-center gap-2.5">
                    <div
                      className="h-3 w-3 rounded-sm shrink-0"
                      style={{ backgroundColor: entry.color }}
                    />
                    <span className="text-xs text-neutral-500">
                      {entry.name}
                    </span>
                    <span className="ml-auto text-xs font-mono text-neutral-300">
                      {entry.value}%
                    </span>
                  </div>
                ))}
              </div>
            </div>
          </motion.div>

          {/* Budget Gauge */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.6, delay: 0.2, ease: EASE }}
            className="rounded-2xl border border-white/[0.06] bg-surface p-6 flex flex-col"
          >
            <h3 className="text-[13px] font-medium text-neutral-500 uppercase tracking-wider mb-4">
              Budget Utilization
            </h3>

            <div className="flex-1 flex flex-col items-center justify-center gap-6">
              <BudgetGauge
                percentage={budgetConfig.percentage}
                used={budgetConfig.used}
                total={budgetConfig.totalBudget}
              />

              {/* Zone legend */}
              <div className="flex items-center gap-5">
                <div className="flex items-center gap-1.5">
                  <div className="h-2 w-6 rounded-full" style={{ backgroundColor: "#22c55e" }} />
                  <span className="text-[10px] text-neutral-600">0-60%</span>
                </div>
                <div className="flex items-center gap-1.5">
                  <div className="h-2 w-6 rounded-full" style={{ backgroundColor: "#eab308" }} />
                  <span className="text-[10px] text-neutral-600">60-80%</span>
                </div>
                <div className="flex items-center gap-1.5">
                  <div className="h-2 w-6 rounded-full" style={{ backgroundColor: "#ef4444" }} />
                  <span className="text-[10px] text-neutral-600">80-100%</span>
                </div>
              </div>

              {/* Summary row */}
              <div className="w-full grid grid-cols-3 gap-3 text-center">
                <div className="rounded-lg border border-white/[0.06] bg-white/[0.03] p-3">
                  <p className="text-[10px] text-neutral-600 uppercase tracking-[0.15em] mb-0.5">
                    Spent
                  </p>
                  <p className="text-sm font-mono font-semibold text-neutral-300">
                    ${budgetConfig.used.toFixed(4)}
                  </p>
                </div>
                <div className="rounded-lg border border-white/[0.06] bg-white/[0.03] p-3">
                  <p className="text-[10px] text-neutral-600 uppercase tracking-[0.15em] mb-0.5">
                    Remaining
                  </p>
                  <p className="text-sm font-mono font-semibold text-success">
                    ${(budgetConfig.totalBudget - budgetConfig.used).toFixed(4)}
                  </p>
                </div>
                <div className="rounded-lg border border-white/[0.06] bg-white/[0.03] p-3">
                  <p className="text-[10px] text-neutral-600 uppercase tracking-[0.15em] mb-0.5">
                    Budget
                  </p>
                  <p className="text-sm font-mono font-semibold text-neutral-300">
                    ${budgetConfig.totalBudget.toFixed(2)}
                  </p>
                </div>
              </div>
            </div>
          </motion.div>
        </div>
      </div>
    </div>
  );
}
