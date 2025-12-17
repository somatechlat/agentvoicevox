"use client";

/**
 * Workers Configuration Overview
 * Links to STT, TTS, and LLM worker configuration pages
 */

import Link from "next/link";
import { Mic, Volume2, Brain, ArrowRight, CheckCircle, AlertCircle, Activity } from "lucide-react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { useQuery } from "@tanstack/react-query";
import { systemApi } from "@/lib/api";

const workers = [
  {
    name: "STT Worker",
    description: "Speech-to-Text using Faster-Whisper",
    href: "/admin/system/workers/stt",
    icon: Mic,
    settings: ["Model Size", "Compute Device", "VAD Settings", "Language"],
    metrics: ["Transcriptions/min", "Avg Latency", "Queue Depth"],
  },
  {
    name: "TTS Worker",
    description: "Text-to-Speech using Kokoro models",
    href: "/admin/system/workers/tts",
    icon: Volume2,
    settings: ["Voice Selection", "Speech Rate", "Audio Format", "Cache"],
    metrics: ["Generations/min", "Avg Latency", "Cache Hit Rate"],
  },
  {
    name: "LLM Worker",
    description: "Language Model integration (Groq/OpenAI/Ollama)",
    href: "/admin/system/workers/llm",
    icon: Brain,
    settings: ["Provider", "Model", "Temperature", "Circuit Breaker"],
    metrics: ["Requests/min", "Tokens/min", "Error Rate"],
  },
];

export default function WorkersPage() {
  const { data: health } = useQuery({
    queryKey: ["system-health"],
    queryFn: systemApi.getHealth,
    refetchInterval: 30000,
  });

  const { data: workerStats } = useQuery({
    queryKey: ["worker-stats"],
    queryFn: systemApi.getWorkerStats,
    refetchInterval: 10000,
  });

  const getWorkerStatus = (workerName: string) => {
    if (!health?.services) return "unknown";
    const service = health.services.find(
      (s: { name: string; status: string }) => 
        s.name.toLowerCase().includes(workerName.toLowerCase().replace(" worker", ""))
    );
    return service?.status || "unknown";
  };

  const getWorkerMetrics = (workerName: string) => {
    if (!workerStats) return null;
    const key = workerName.toLowerCase().replace(" worker", "") as keyof typeof workerStats;
    return workerStats[key];
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Worker Configuration</h1>
        <p className="text-muted-foreground">
          Configure voice processing workers: Speech-to-Text, Text-to-Speech, and Language Models
        </p>
      </div>

      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
        {workers.map((worker) => {
          const status = getWorkerStatus(worker.name);
          const isHealthy = status === "healthy" || status === "running";
          const metrics = getWorkerMetrics(worker.name);

          return (
            <Link key={worker.name} href={worker.href}>
              <Card className="h-full transition-colors hover:bg-accent/50 cursor-pointer">
                <CardHeader>
                  <div className="flex items-center justify-between">
                    <worker.icon className="h-8 w-8 text-primary" />
                    <Badge variant={isHealthy ? "default" : "destructive"}>
                      {isHealthy ? (
                        <CheckCircle className="mr-1 h-3 w-3" />
                      ) : (
                        <AlertCircle className="mr-1 h-3 w-3" />
                      )}
                      {status}
                    </Badge>
                  </div>
                  <CardTitle className="mt-4">{worker.name}</CardTitle>
                  <CardDescription>{worker.description}</CardDescription>
                </CardHeader>
                <CardContent>
                  {/* Live Metrics */}
                  {metrics && (
                    <div className="mb-4 grid grid-cols-3 gap-2 rounded-lg bg-muted/50 p-3">
                      <div className="text-center">
                        <div className="text-lg font-bold">{metrics.requests_per_min || 0}</div>
                        <div className="text-xs text-muted-foreground">req/min</div>
                      </div>
                      <div className="text-center">
                        <div className="text-lg font-bold">{metrics.avg_latency_ms || 0}ms</div>
                        <div className="text-xs text-muted-foreground">latency</div>
                      </div>
                      <div className="text-center">
                        <div className="text-lg font-bold">{"queue_depth" in metrics ? metrics.queue_depth : 0}</div>
                        <div className="text-xs text-muted-foreground">queued</div>
                      </div>
                    </div>
                  )}

                  <div className="space-y-2">
                    <p className="text-sm font-medium text-muted-foreground">
                      Configurable Settings:
                    </p>
                    <ul className="text-sm text-muted-foreground space-y-1">
                      {worker.settings.map((setting) => (
                        <li key={setting} className="flex items-center gap-2">
                          <span className="h-1 w-1 rounded-full bg-primary" />
                          {setting}
                        </li>
                      ))}
                    </ul>
                  </div>
                  <div className="mt-4 flex items-center text-sm text-primary">
                    Configure <ArrowRight className="ml-1 h-4 w-4" />
                  </div>
                </CardContent>
              </Card>
            </Link>
          );
        })}
      </div>
    </div>
  );
}
