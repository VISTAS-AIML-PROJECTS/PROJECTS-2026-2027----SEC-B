import { createFileRoute } from "@tanstack/react-router";
import { useServerFn } from "@tanstack/react-start";
import { useRef, useState } from "react";
import { toast } from "sonner";
import { CheckCircle2, FileAudio, Loader2, TriangleAlert, Upload } from "lucide-react";
import { PageHeader } from "@/components/page-header";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { Badge } from "@/components/ui/badge";
import { detectLeakFromAudio, type DetectionResult } from "@/lib/audio-detect.functions";
import { AudioWaveform } from "@/components/audio-waveform";

export const Route = createFileRoute("/_console/detect")({
  head: () => ({
    meta: [
      { title: "Audio Leak Detection — AquaSense" },
      { name: "description", content: "Upload a pipeline audio recording and let AI detect whether a water leak is present." },
      { property: "og:title", content: "Audio Leak Detection — AquaSense" },
      { property: "og:description", content: "AI acoustic analysis of uploaded pipe recordings." },
    ],
  }),
  component: DetectPage,
});

const MAX_BYTES = 10 * 1024 * 1024;

function formatOf(file: File) {
  const ext = file.name.split(".").pop()?.toLowerCase() ?? "";
  const map: Record<string, string> = { wav: "wav", mp3: "mp3", webm: "webm", m4a: "m4a", mp4: "m4a", ogg: "ogg", oga: "ogg", aac: "aac", flac: "flac" };
  return map[ext] ?? null;
}

function toBase64(file: File) {
  return new Promise<string>((resolve, reject) => {
    const r = new FileReader();
    r.onload = () => resolve(String(r.result).split(",")[1] ?? "");
    r.onerror = () => reject(r.error);
    r.readAsDataURL(file);
  });
}

function DetectPage() {
  const detect = useServerFn(detectLeakFromAudio);
  const inputRef = useRef<HTMLInputElement>(null);
  const [file, setFile] = useState<File | null>(null);
  const [url, setUrl] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<DetectionResult | null>(null);

  const pick = (f: File | undefined): void => {
    if (!f) return;
    if (!formatOf(f)) { toast.error("Please upload WAV, MP3, M4A, OGG, AAC, FLAC or WEBM audio."); return; }
    if (f.size > MAX_BYTES) { toast.error("File is too large (max 10 MB)."); return; }
    if (url) URL.revokeObjectURL(url);
    setFile(f);
    setUrl(URL.createObjectURL(f));
    setResult(null);
  };

  const analyse = async () => {
    if (!file) return;
    setLoading(true);
    setResult(null);
    try {
      const base64 = await toBase64(file);
      const res = await detect({ data: { base64, format: formatOf(file) as "wav" } });
      setResult(res);
    } catch (e) {
      toast.error(e instanceof Error ? e.message : "Analysis failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      <PageHeader title="Audio Leak Detection" description="Upload a pipe or sensor recording — AI will tell you whether it sounds like a leak." />
      <div className="grid gap-4 lg:grid-cols-2">
        <Card className="border-border/70">
          <CardHeader>
            <CardTitle className="font-display text-lg">Upload recording</CardTitle>
            <CardDescription>WAV, MP3, M4A, OGG, AAC, FLAC or WEBM · up to 10 MB</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <button
              type="button"
              onClick={() => inputRef.current?.click()}
              onDragOver={(e) => e.preventDefault()}
              onDrop={(e) => { e.preventDefault(); pick(e.dataTransfer.files[0]); }}
              className="flex w-full flex-col items-center justify-center gap-3 rounded-xl border-2 border-dashed border-border bg-muted/40 px-6 py-10 text-center transition-colors hover:border-primary hover:bg-secondary"
            >
              <span className="grid size-12 place-items-center rounded-full bg-primary-gradient text-primary-foreground"><Upload className="size-5" /></span>
              <span className="text-sm font-medium">Click or drop an audio file here</span>
            </button>
            <input ref={inputRef} type="file" accept="audio/*" className="hidden" onChange={(e) => pick(e.target.files?.[0])} />
            {file && url && (
              <div className="space-y-3 rounded-lg border border-border/70 p-3">
                <div className="flex items-center gap-2 text-sm"><FileAudio className="size-4 text-primary" /><span className="truncate font-medium">{file.name}</span><span className="ml-auto text-xs text-muted-foreground">{(file.size / 1024 / 1024).toFixed(2)} MB</span></div>
                <audio controls src={url} className="w-full" />
                <div>
                  <p className="mb-1 text-xs font-medium text-muted-foreground">Sound level over time</p>
                  <AudioWaveform file={file} />
                </div>
              </div>
            )}
            <Button className="w-full" disabled={!file || loading} onClick={analyse}>
              {loading ? <><Loader2 className="size-4 animate-spin" /> Analysing…</> : "Detect leak"}
            </Button>
          </CardContent>
        </Card>

        <Card className="border-border/70">
          <CardHeader>
            <CardTitle className="font-display text-lg">Result</CardTitle>
            <CardDescription>AI acoustic classification</CardDescription>
          </CardHeader>
          <CardContent>
            {!result && !loading && <p className="py-10 text-center text-sm text-muted-foreground">Upload a recording and press “Detect leak” to see the result.</p>}
            {loading && <div className="flex flex-col items-center gap-3 py-10 text-sm text-muted-foreground"><Loader2 className="size-6 animate-spin text-primary" />Listening to the recording…</div>}
            {result && (
              <div className="space-y-5 animate-fade-up">
                <div className={`flex items-center gap-3 rounded-xl p-4 ${result.leak ? "bg-destructive/10 text-destructive" : "bg-success/10 text-success"}`}>
                  {result.leak ? <TriangleAlert className="size-8" /> : <CheckCircle2 className="size-8" />}
                  <div>
                    <p className="font-display text-xl font-semibold">{result.leak ? "Leak detected" : "No leak detected"}</p>
                    {result.leak && <Badge variant="outline" className="mt-1 capitalize">{result.severity} severity</Badge>}
                  </div>
                </div>
                <div className="space-y-2">
                  <div className="flex justify-between text-sm"><span>Confidence</span><span className="font-medium">{result.confidence}%</span></div>
                  <Progress value={result.confidence} />
                </div>
                {result.explanation && <p className="text-sm leading-relaxed text-muted-foreground">{result.explanation}</p>}
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
