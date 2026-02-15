export interface ModelCost {
  model: string;
  cost: number;
  color: string;
}

export interface TokenUsagePoint {
  test: string;
  inputTokens: number;
  outputTokens: number;
}

export interface ProviderShare {
  name: string;
  value: number;
  color: string;
}

export interface SummaryCard {
  label: string;
  value: string;
  numericValue: number;
  suffix: string;
  description: string;
}

export const summaryCards: SummaryCard[] = [
  {
    label: "Total Cost",
    value: "$0.0847",
    numericValue: 0.0847,
    suffix: "",
    description: "Across all test runs",
  },
  {
    label: "Total Tokens",
    value: "45,230",
    numericValue: 45230,
    suffix: "",
    description: "Input + output tokens",
  },
  {
    label: "Budget Used",
    value: "42.4%",
    numericValue: 42.4,
    suffix: "%",
    description: "Of $0.20 budget",
  },
  {
    label: "Avg Cost/Test",
    value: "$0.0085",
    numericValue: 0.0085,
    suffix: "",
    description: "Per test execution",
  },
];

export const costByModel: ModelCost[] = [
  { model: "gpt-4o", cost: 0.042, color: "#e2a04f" },
  { model: "claude-3-5-sonnet", cost: 0.0245, color: "#8b5cf6" },
  { model: "gemini-1.5-pro", cost: 0.0112, color: "#c76a4a" },
  { model: "gpt-4o-mini", cost: 0.007, color: "#22c55e" },
];

export const tokenUsageOverTests: TokenUsagePoint[] = [
  { test: "Test 1", inputTokens: 3200, outputTokens: 1800 },
  { test: "Test 2", inputTokens: 4100, outputTokens: 2200 },
  { test: "Test 3", inputTokens: 3800, outputTokens: 1600 },
  { test: "Test 4", inputTokens: 5200, outputTokens: 2800 },
  { test: "Test 5", inputTokens: 4500, outputTokens: 2100 },
  { test: "Test 6", inputTokens: 3900, outputTokens: 1900 },
  { test: "Test 7", inputTokens: 6100, outputTokens: 3400 },
  { test: "Test 8", inputTokens: 4800, outputTokens: 2500 },
  { test: "Test 9", inputTokens: 5500, outputTokens: 2900 },
  { test: "Test 10", inputTokens: 4130, outputTokens: 2400 },
];

export const costByProvider: ProviderShare[] = [
  { name: "OpenAI", value: 45, color: "#e2a04f" },
  { name: "Anthropic", value: 30, color: "#8b5cf6" },
  { name: "Google", value: 15, color: "#c76a4a" },
  { name: "Other", value: 10, color: "#f0c078" },
];

export const budgetConfig = {
  totalBudget: 0.2,
  used: 0.0847,
  percentage: 42.4,
};
