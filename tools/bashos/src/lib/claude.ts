// Thin Claude client for the AI engine, with prompt caching on the large,
// stable instruction context (we pay full price for it once, then cache-read it
// on subsequent calls). Model abstraction kept deliberately thin to avoid
// vendor lock-in (PLAN.md principle).
import Anthropic from "@anthropic-ai/sdk";

export type Tier = "opus" | "sonnet" | "haiku";

// Model IDs per the project environment. Opus for hard drafting/reasoning,
// Sonnet/Haiku for bulk and chores (cost tiering, PLAN.md §10).
const MODELS: Record<Tier, string> = {
  opus: "claude-opus-4-8",
  sonnet: "claude-sonnet-4-6",
  haiku: "claude-haiku-4-5-20251001",
};

export interface RunArgs {
  /** Stable, cacheable context (instruction files + house style). */
  systemContext: string;
  /** The prompt/skill body (also fairly stable). */
  promptBody: string;
  /** The variable input (target file content + user ask). */
  userInput: string;
  tier?: Tier;
  maxTokens?: number;
}

export interface RunResult {
  text: string;
  model: string;
  usage: {
    inputTokens: number;
    outputTokens: number;
    cacheReadTokens: number;
    cacheCreationTokens: number;
  };
}

export function hasApiKey(): boolean {
  return Boolean(process.env.ANTHROPIC_API_KEY);
}

export async function run(args: RunArgs): Promise<RunResult> {
  if (!hasApiKey())
    throw new Error("ANTHROPIC_API_KEY is not set. Add it to your environment or .env.");

  const tier = args.tier ?? "opus";
  const model = MODELS[tier];
  const client = new Anthropic();

  // System is split so the bulk (instruction context + prompt body) is marked
  // cacheable; the variable user input is sent normally.
  const msg = await client.messages.create({
    model,
    max_tokens: args.maxTokens ?? 4096,
    system: [
      { type: "text", text: "You are the BASH OS content/automation agent. Follow the house instructions and the prompt exactly. Produce only the requested artifact." },
      { type: "text", text: args.systemContext },
      { type: "text", text: args.promptBody, cache_control: { type: "ephemeral" } },
    ],
    messages: [{ role: "user", content: args.userInput }],
  });

  const text = msg.content
    .filter((b): b is Anthropic.TextBlock => b.type === "text")
    .map((b) => b.text)
    .join("\n");

  const u = msg.usage;
  return {
    text,
    model,
    usage: {
      inputTokens: u.input_tokens,
      outputTokens: u.output_tokens,
      cacheReadTokens: u.cache_read_input_tokens ?? 0,
      cacheCreationTokens: u.cache_creation_input_tokens ?? 0,
    },
  };
}
