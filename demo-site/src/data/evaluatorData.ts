export interface EvaluationRule {
  id: string;
  name: string;
  type: "contains" | "max_length" | "not_contains" | "valid_json" | "matches_pattern";
  weight: number;
  enabled: boolean;
  /** For 'contains' rules */
  keyword?: string;
  /** For 'max_length' rules */
  maxLength?: number;
  /** For 'not_contains' rules */
  forbidden?: string[];
  /** For 'matches_pattern' rules */
  pattern?: string;
}

export interface RuleResult {
  ruleId: string;
  passed: boolean;
  detail: string;
}

export interface EvaluationResult {
  verdict: "PASS" | "PARTIAL" | "FAIL" | "ERROR";
  score: number;
  maxScore: number;
  percentage: number;
  ruleResults: RuleResult[];
}

export const defaultRules: EvaluationRule[] = [
  {
    id: "rule-1",
    name: 'Contains "temperature"',
    type: "contains",
    weight: 2.0,
    enabled: true,
    keyword: "temperature",
  },
  {
    id: "rule-2",
    name: "Max length 500 chars",
    type: "max_length",
    weight: 1.0,
    enabled: true,
    maxLength: 500,
  },
  {
    id: "rule-3",
    name: "No profanity",
    type: "not_contains",
    weight: 1.5,
    enabled: true,
    forbidden: ["damn", "hell"],
  },
  {
    id: "rule-4",
    name: "Valid JSON",
    type: "valid_json",
    weight: 1.0,
    enabled: false,
  },
  {
    id: "rule-5",
    name: "Matches pattern /\\d+[CF]/",
    type: "matches_pattern",
    weight: 2.0,
    enabled: true,
    pattern: "\\d+\\s*[CF]",
  },
];

export const defaultSampleOutput = `Global temperatures have risen by approximately 1.1 C since the pre-industrial era. The primary driver is greenhouse gas emissions from burning fossil fuels, deforestation, and industrial processes.

Key findings from recent climate research:
- Average global temperature increase: 1.1 C above pre-industrial levels
- Arctic sea ice is declining at a rate of 13% per decade
- Sea levels have risen by approximately 20cm since 1900
- Carbon dioxide levels exceeded 420 ppm in 2024

Scientists warn that exceeding a 1.5 C temperature threshold could trigger irreversible tipping points, including permafrost collapse and coral reef die-off.`;

export function evaluateOutput(
  text: string,
  rules: EvaluationRule[]
): EvaluationResult {
  const enabledRules = rules.filter((r) => r.enabled);

  if (enabledRules.length === 0) {
    return {
      verdict: "PASS",
      score: 0,
      maxScore: 0,
      percentage: 100,
      ruleResults: [],
    };
  }

  const ruleResults: RuleResult[] = enabledRules.map((rule) => {
    let passed = false;
    let detail = "";

    switch (rule.type) {
      case "contains": {
        const keyword = rule.keyword ?? "";
        passed = text.toLowerCase().includes(keyword.toLowerCase());
        detail = passed
          ? `Found "${keyword}" in output`
          : `"${keyword}" not found in output`;
        break;
      }
      case "max_length": {
        const max = rule.maxLength ?? 500;
        passed = text.length <= max;
        detail = passed
          ? `Length ${text.length} <= ${max}`
          : `Length ${text.length} exceeds limit of ${max}`;
        break;
      }
      case "not_contains": {
        const forbidden = rule.forbidden ?? [];
        const found = forbidden.filter((word) =>
          text.toLowerCase().includes(word.toLowerCase())
        );
        passed = found.length === 0;
        detail = passed
          ? "No forbidden words found"
          : `Found forbidden words: ${found.join(", ")}`;
        break;
      }
      case "valid_json": {
        try {
          JSON.parse(text);
          passed = true;
          detail = "Output is valid JSON";
        } catch {
          passed = false;
          detail = "Output is not valid JSON";
        }
        break;
      }
      case "matches_pattern": {
        const patternStr = rule.pattern ?? "";
        try {
          const regex = new RegExp(patternStr);
          passed = regex.test(text);
          detail = passed
            ? `Pattern /${patternStr}/ matched`
            : `Pattern /${patternStr}/ did not match`;
        } catch {
          passed = false;
          detail = `Invalid pattern: /${patternStr}/`;
        }
        break;
      }
    }

    return { ruleId: rule.id, passed, detail };
  });

  const maxScore = enabledRules.reduce((sum, r) => sum + r.weight, 0);
  const score = enabledRules.reduce((sum, r, i) => {
    return sum + (ruleResults[i].passed ? r.weight : 0);
  }, 0);
  const percentage = maxScore > 0 ? (score / maxScore) * 100 : 100;

  let verdict: EvaluationResult["verdict"];
  if (percentage >= 100) {
    verdict = "PASS";
  } else if (percentage >= 50) {
    verdict = "PARTIAL";
  } else {
    verdict = "FAIL";
  }

  return { verdict, score, maxScore, percentage, ruleResults };
}
