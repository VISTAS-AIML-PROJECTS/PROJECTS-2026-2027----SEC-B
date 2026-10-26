import { createServerFn } from "@tanstack/react-start";
import { z } from "zod";

const FORMATS = ["wav", "mp3", "webm", "m4a", "ogg", "aac", "flac"] as const;

export type DetectionResult = {
  leak: boolean;
  confidence: number;
  severity: "none" | "low" | "medium" | "high" | "critical";
  explanation: string;
};

export const detectLeakFromAudio = createServerFn({ method: "POST" })
  .inputValidator((d) =>
    z
      .object({
        base64: z.string().min(10).max(14_000_000),
        format: z.enum(FORMATS),
      })
      .parse(d),
  )
  .handler(async ({ data }): Promise<DetectionResult> => {
    const key = process.env["LOVABLE_API_KEY"];
    if (!key) throw new Error("AI service is not configured.");

    const res = await fetch("https://ai.gateway.lovable.dev/v1/chat/completions", {
      method: "POST",
      headers: { Authorization: `Bearer ${key}`, "Content-Type": "application/json" },
      body: JSON.stringify({
        model: "google/gemini-3.5-flash",
        response_format: { type: "json_object" },
        messages: [
          {
            role: "system",
            content:
              "You are an acoustic water-pipe leak detection classifier. Listen to the audio and decide whether it contains signatures of a water leak (continuous hissing, broadband noise, spraying, dripping, rushing water, pipe vibration). Reply ONLY with JSON: {\"leak\": boolean, \"confidence\": number 0-100, \"severity\": \"none\"|\"low\"|\"medium\"|\"high\"|\"critical\", \"explanation\": short string under 40 words}. Use severity \"none\" when leak is false.",
          },
          {
            role: "user",
            content: [
              { type: "text", text: "Classify this recording." },
              { type: "input_audio", input_audio: { data: data.base64, format: data.format } },
            ],
          },
        ],
      }),
    });

    if (!res.ok) {
      if (res.status === 429) throw new Error("Too many requests right now. Please wait a moment and try again.");
      if (res.status === 402) throw new Error("AI credits have run out. Please add credits to continue.");
      const t = await res.text();
      throw new Error(`Analysis failed (${res.status}). ${t.slice(0, 200)}`);
    }
    const json = await res.json();
    const text: string = json?.choices?.[0]?.message?.content ?? "";
    if (!text) throw new Error("The AI could not analyse this recording.");
    const match = text.match(/\{[\s\S]*\}/);
    const parsed = JSON.parse(match ? match[0] : text);
    return {
      leak: Boolean(parsed.leak),
      confidence: Math.max(0, Math.min(100, Number(parsed.confidence) || 0)),
      severity: parsed.severity ?? (parsed.leak ? "medium" : "none"),
      explanation: String(parsed.explanation ?? ""),
    };
  });
