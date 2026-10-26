import { useEffect, useState } from "react";
import { Area, AreaChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

type Point = { t: number; amp: number };

export function AudioWaveform({ file }: { file: File }) {
  const [data, setData] = useState<Point[] | null>(null);
  const [error, setError] = useState(false);

  useEffect(() => {
    let cancelled = false;
    setData(null);
    setError(false);
    (async () => {
      try {
        const buf = await file.arrayBuffer();
        const Ctx = window.AudioContext || (window as unknown as { webkitAudioContext: typeof AudioContext }).webkitAudioContext;
        const ctx = new Ctx();
        const audio = await ctx.decodeAudioData(buf);
        void ctx.close();
        const ch = audio.getChannelData(0);
        const buckets = 200;
        const size = Math.max(1, Math.floor(ch.length / buckets));
        const pts: Point[] = [];
        for (let i = 0; i < buckets; i++) {
          let sum = 0;
          const start = i * size;
          for (let j = start; j < start + size && j < ch.length; j++) sum += (ch[j] ?? 0) ** 2;
          const rms = Math.sqrt(sum / size);
          pts.push({ t: Number(((start / audio.sampleRate)).toFixed(2)), amp: Number((rms * 100).toFixed(2)) });
        }
        if (!cancelled) setData(pts);
      } catch {
        if (!cancelled) setError(true);
      }
    })();
    return () => { cancelled = true; };
  }, [file]);

  if (error) return <p className="text-xs text-muted-foreground">Couldn't draw a graph for this file format.</p>;
  if (!data) return <div className="h-40 animate-pulse rounded-md bg-muted" />;

  return (
    <div className="h-40 w-full">
      <ResponsiveContainer>
        <AreaChart data={data} margin={{ top: 5, right: 5, left: -20, bottom: 0 }}>
          <defs>
            <linearGradient id="wave" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="var(--primary)" stopOpacity={0.6} />
              <stop offset="100%" stopColor="var(--primary)" stopOpacity={0.05} />
            </linearGradient>
          </defs>
          <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
          <XAxis dataKey="t" tick={{ fontSize: 10 }} unit="s" minTickGap={30} />
          <YAxis tick={{ fontSize: 10 }} />
          <Tooltip formatter={(v) => [`${v}`, "Loudness"]} labelFormatter={(l) => `${l}s`} />
          <Area type="monotone" dataKey="amp" stroke="var(--primary)" fill="url(#wave)" strokeWidth={1.5} isAnimationActive={false} />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}
