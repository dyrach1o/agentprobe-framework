export interface LlmCall {
  call_id: string;
  model: string;
  input_tokens: number;
  output_tokens: number;
  latency_ms: number;
  input_text: string;
  output_text: string;
}

export interface ToolCall {
  call_id: string;
  tool_name: string;
  tool_input: Record<string, unknown>;
  tool_output: string | null;
  success: boolean;
  error?: string;
  latency_ms: number;
}

export interface Turn {
  turn_id: string;
  turn_type: "llm_call" | "tool_call";
  content: string;
  llm_call?: LlmCall;
  tool_call?: ToolCall;
}

export interface Trace {
  trace_id: string;
  agent_name: string;
  model: string;
  input_text: string;
  output_text: string;
  total_input_tokens: number;
  total_output_tokens: number;
  total_latency_ms: number;
  turns: Turn[];
}

export const sampleTrace: Trace = {
  trace_id: "tr_8f2a1b3c",
  agent_name: "research-assistant",
  model: "gpt-4o",
  input_text:
    "Find the population of Tokyo and compare it to New York City",
  output_text:
    "Tokyo has a population of approximately 13.96 million in the city proper, while New York City has about 8.34 million. Tokyo is roughly 67% larger than NYC in terms of city population.",
  total_input_tokens: 1847,
  total_output_tokens: 892,
  total_latency_ms: 4230,
  turns: [
    {
      turn_id: "t1",
      turn_type: "llm_call",
      content: "I need to search for the population data of both cities.",
      llm_call: {
        call_id: "lc1",
        model: "gpt-4o",
        input_tokens: 245,
        output_tokens: 89,
        latency_ms: 820,
        input_text:
          "Find the population of Tokyo and compare it to New York City",
        output_text:
          "I'll search for the current population data for both Tokyo and New York City to make an accurate comparison.",
      },
    },
    {
      turn_id: "t2",
      turn_type: "tool_call",
      content: "13.96 million (2023 estimate)",
      tool_call: {
        call_id: "tc1",
        tool_name: "search",
        tool_input: { query: "Tokyo population 2024 census" },
        tool_output:
          "Tokyo: 13.96 million (city proper, 2023 estimate). Greater Tokyo Area: 37.4 million.",
        success: true,
        latency_ms: 340,
      },
    },
    {
      turn_id: "t3",
      turn_type: "tool_call",
      content: "8.34 million (2023 estimate)",
      tool_call: {
        call_id: "tc2",
        tool_name: "search",
        tool_input: { query: "New York City population 2024" },
        tool_output:
          "New York City: 8.34 million (2023 estimate). NYC Metropolitan Area: 20.1 million.",
        success: true,
        latency_ms: 290,
      },
    },
    {
      turn_id: "t4",
      turn_type: "tool_call",
      content: "Error: API rate limit exceeded",
      tool_call: {
        call_id: "tc3",
        tool_name: "calculator",
        tool_input: { expression: "((13.96 - 8.34) / 8.34) * 100" },
        tool_output: null,
        success: false,
        error: "API rate limit exceeded",
        latency_ms: 120,
      },
    },
    {
      turn_id: "t5",
      turn_type: "llm_call",
      content:
        "Based on the search results, I can now provide the comparison.",
      llm_call: {
        call_id: "lc2",
        model: "gpt-4o",
        input_tokens: 1602,
        output_tokens: 803,
        latency_ms: 2660,
        input_text:
          "Based on the search results: Tokyo 13.96M, NYC 8.34M. The calculator failed. Please compute the percentage difference and write the final comparison.",
        output_text:
          "Tokyo has a population of approximately 13.96 million in the city proper, while New York City has about 8.34 million. Tokyo is roughly 67% larger than NYC in terms of city population.",
      },
    },
  ],
};
