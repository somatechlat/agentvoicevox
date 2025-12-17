"use client";

/**
 * STT Worker Configuration Page (Faster-Whisper)
 * Settings: model, device, compute_type, batch_size, language, vad, beam_size, temperature
 */

import { useState, useEffect } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Mic, Save, RefreshCw, AlertCircle, CheckCircle, Play } from "lucide-react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";
import { Slider } from "@/components/ui/slider";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import { Textarea } from "@/components/ui/textarea";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "@/components/ui/collapsible";
import { systemApi } from "@/lib/api";

interface STTConfig {
  model: string;
  device: string;
  compute_type: string;
  batch_size: number;
  language: string;
  vad_enabled: boolean;
  vad_threshold: number;
  beam_size: number;
  best_of: number;
  temperature: number;
  compression_ratio_threshold: number;
  log_prob_threshold: number;
  no_speech_threshold: number;
  word_timestamps: boolean;
  initial_prompt: string;
}

const models = [
  { value: "tiny", label: "Tiny", accuracy: 1, speed: 10, ram: "1GB" },
  { value: "base", label: "Base", accuracy: 3, speed: 8, ram: "1GB" },
  { value: "small", label: "Small", accuracy: 5, speed: 6, ram: "2GB" },
  { value: "medium", label: "Medium", accuracy: 7, speed: 4, ram: "5GB" },
  { value: "large-v2", label: "Large v2", accuracy: 9, speed: 2, ram: "10GB" },
  { value: "large-v3", label: "Large v3", accuracy: 10, speed: 1, ram: "10GB" },
];

const devices = [
  { value: "cpu", label: "CPU" },
  { value: "cuda", label: "CUDA (GPU)" },
];

const computeTypes = [
  { value: "int8", label: "INT8 (Fastest)" },
  { value: "float16", label: "Float16 (Balanced)" },
  { value: "float32", label: "Float32 (Most Accurate)" },
];

const languages = [
  { value: "auto", label: "Auto-detect" },
  { value: "en", label: "English" },
  { value: "es", label: "Spanish" },
  { value: "fr", label: "French" },
  { value: "de", label: "German" },
  { value: "it", label: "Italian" },
  { value: "pt", label: "Portuguese" },
  { value: "nl", label: "Dutch" },
  { value: "ja", label: "Japanese" },
  { value: "zh", label: "Chinese" },
  { value: "ko", label: "Korean" },
  { value: "ar", label: "Arabic" },
];

const defaultConfig: STTConfig = {
  model: "tiny",
  device: "cpu",
  compute_type: "int8",
  batch_size: 2,
  language: "auto",
  vad_enabled: true,
  vad_threshold: 0.5,
  beam_size: 5,
  best_of: 1,
  temperature: 0.0,
  compression_ratio_threshold: 2.4,
  log_prob_threshold: -1.0,
  no_speech_threshold: 0.6,
  word_timestamps: false,
  initial_prompt: "",
};

export default function STTConfigPage() {
  const queryClient = useQueryClient();
  const [config, setConfig] = useState<STTConfig>(defaultConfig);
  const [hasChanges, setHasChanges] = useState(false);
  const [advancedOpen, setAdvancedOpen] = useState(false);

  const { data: health } = useQuery({
    queryKey: ["stt-health"],
    queryFn: () => systemApi.getHealth(),
    refetchInterval: 30000,
  });

  const { data: savedConfig, isLoading } = useQuery({
    queryKey: ["stt-config"],
    queryFn: async () => {
      const response = await systemApi.getConfig<STTConfig>("stt");
      return response;
    },
  });

  useEffect(() => {
    if (savedConfig) {
      setConfig(savedConfig);
    }
  }, [savedConfig]);

  const { data: stats } = useQuery({
    queryKey: ["stt-stats"],
    queryFn: () => systemApi.getWorkerStats().then((s) => s?.stt),
    refetchInterval: 10000,
  });

  const saveMutation = useMutation({
    mutationFn: (newConfig: STTConfig) => systemApi.updateConfig("stt", newConfig),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["stt-config"] });
      setHasChanges(false);
    },
  });

  const testMutation = useMutation({
    mutationFn: () => systemApi.testSTT(),
  });

  const updateConfig = <K extends keyof STTConfig>(key: K, value: STTConfig[K]) => {
    setConfig((prev) => ({ ...prev, [key]: value }));
    setHasChanges(true);
  };

  const isHealthy = health?.services?.some(
    (s: { name: string; status: string }) => 
      s.name.toLowerCase().includes("stt") && s.status === "healthy"
  );

  const selectedModel = models.find((m) => m.value === config.model);

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold flex items-center gap-2">
            <Mic className="h-6 w-6" />
            STT Worker Configuration
          </h1>
          <p className="text-muted-foreground">
            Configure Faster-Whisper speech-to-text settings
          </p>
        </div>
        <Badge variant={isHealthy ? "default" : "destructive"}>
          {isHealthy ? (
            <CheckCircle className="mr-1 h-3 w-3" />
          ) : (
            <AlertCircle className="mr-1 h-3 w-3" />
          )}
          {isHealthy ? "Running" : "Stopped"}
        </Badge>
      </div>

      {/* Stats Cards */}
      {stats && (
        <div className="grid gap-4 md:grid-cols-4">
          <Card>
            <CardHeader className="pb-2">
              <CardDescription>Transcriptions/min</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{stats.requests_per_min || 0}</div>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="pb-2">
              <CardDescription>Avg Latency</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{stats.avg_latency_ms || 0}ms</div>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="pb-2">
              <CardDescription>Queue Depth</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{stats.queue_depth || 0}</div>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="pb-2">
              <CardDescription>Error Rate</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{stats.error_rate || 0}%</div>
            </CardContent>
          </Card>
        </div>
      )}

      {isLoading ? (
        <div className="flex items-center justify-center py-12">
          <RefreshCw className="h-8 w-8 animate-spin text-muted-foreground" />
        </div>
      ) : (
        <div className="grid gap-6 lg:grid-cols-2">
          {/* Model Selection */}
          <Card>
            <CardHeader>
              <CardTitle>Model Selection</CardTitle>
              <CardDescription>
                Choose Whisper model size based on accuracy vs speed tradeoff
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="grid grid-cols-3 gap-2 sm:grid-cols-6">
                {models.map((model) => (
                  <button
                    key={model.value}
                    onClick={() => updateConfig("model", model.value)}
                    className={`rounded-lg border p-3 text-center transition-colors ${
                      config.model === model.value
                        ? "border-primary bg-primary/10"
                        : "border-border hover:bg-accent"
                    }`}
                  >
                    <div className="font-medium">{model.label}</div>
                    <div className="text-xs text-muted-foreground">{model.ram}</div>
                  </button>
                ))}
              </div>

              {selectedModel && (
                <div className="space-y-2 rounded-lg bg-muted/50 p-4">
                  <div className="flex items-center justify-between text-sm">
                    <span>Accuracy</span>
                    <div className="flex gap-1">
                      {Array.from({ length: 10 }).map((_, i) => (
                        <div
                          key={i}
                          className={`h-2 w-3 rounded ${
                            i < selectedModel.accuracy ? "bg-primary" : "bg-muted"
                          }`}
                        />
                      ))}
                    </div>
                  </div>
                  <div className="flex items-center justify-between text-sm">
                    <span>Speed</span>
                    <div className="flex gap-1">
                      {Array.from({ length: 10 }).map((_, i) => (
                        <div
                          key={i}
                          className={`h-2 w-3 rounded ${
                            i < selectedModel.speed ? "bg-green-500" : "bg-muted"
                          }`}
                        />
                      ))}
                    </div>
                  </div>
                  <div className="flex items-center justify-between text-sm">
                    <span>RAM Required</span>
                    <span className="font-mono">{selectedModel.ram}</span>
                  </div>
                </div>
              )}

              <Separator />

              <div className="grid gap-4 sm:grid-cols-2">
                <div className="space-y-2">
                  <Label>Device</Label>
                  <Select
                    value={config.device}
                    onValueChange={(v) => updateConfig("device", v)}
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      {devices.map((d) => (
                        <SelectItem key={d.value} value={d.value}>
                          {d.label}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                <div className="space-y-2">
                  <Label>Precision</Label>
                  <Select
                    value={config.compute_type}
                    onValueChange={(v) => updateConfig("compute_type", v)}
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      {computeTypes.map((ct) => (
                        <SelectItem key={ct.value} value={ct.value}>
                          {ct.label}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
              </div>

              <div className="space-y-2">
                <Label>Language</Label>
                <Select
                  value={config.language}
                  onValueChange={(v) => updateConfig("language", v)}
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {languages.map((lang) => (
                      <SelectItem key={lang.value} value={lang.value}>
                        {lang.label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            </CardContent>
          </Card>

          {/* VAD & Processing */}
          <Card>
            <CardHeader>
              <CardTitle>Voice Activity Detection</CardTitle>
              <CardDescription>
                Configure VAD to filter silence and improve accuracy
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="flex items-center justify-between">
                <div className="space-y-0.5">
                  <Label>Enable VAD</Label>
                  <p className="text-xs text-muted-foreground">
                    Filter out silence before transcription
                  </p>
                </div>
                <Switch
                  checked={config.vad_enabled}
                  onCheckedChange={(checked) => updateConfig("vad_enabled", checked)}
                />
              </div>

              {config.vad_enabled && (
                <>
                  <Separator />
                  <div className="space-y-3">
                    <div className="flex items-center justify-between">
                      <Label>VAD Sensitivity</Label>
                      <span className="text-sm font-mono">{config.vad_threshold}</span>
                    </div>
                    <Slider
                      min={0}
                      max={1}
                      step={0.05}
                      value={[config.vad_threshold]}
                      onValueChange={(values: number[]) => updateConfig("vad_threshold", values[0])}
                    />
                    <p className="text-xs text-muted-foreground">
                      Lower = more sensitive, Higher = stricter filtering
                    </p>
                  </div>

                  <div className="space-y-3">
                    <div className="flex items-center justify-between">
                      <Label>No Speech Threshold</Label>
                      <span className="text-sm font-mono">{config.no_speech_threshold}</span>
                    </div>
                    <Slider
                      min={0}
                      max={1}
                      step={0.05}
                      value={[config.no_speech_threshold]}
                      onValueChange={(values: number[]) => updateConfig("no_speech_threshold", values[0])}
                    />
                  </div>
                </>
              )}

              <Separator />

              <Collapsible open={advancedOpen} onOpenChange={setAdvancedOpen}>
                <CollapsibleTrigger asChild>
                  <Button variant="ghost" className="w-full justify-between">
                    Advanced Settings
                    <span className="text-xs text-muted-foreground">
                      {advancedOpen ? "Hide" : "Show"}
                    </span>
                  </Button>
                </CollapsibleTrigger>
                <CollapsibleContent className="space-y-4 pt-4">
                  <div className="grid gap-4 sm:grid-cols-2">
                    <div className="space-y-2">
                      <Label>Beam Size</Label>
                      <Input
                        type="number"
                        min={1}
                        max={10}
                        value={config.beam_size}
                        onChange={(e) => updateConfig("beam_size", parseInt(e.target.value, 10))}
                      />
                    </div>
                    <div className="space-y-2">
                      <Label>Best Of</Label>
                      <Input
                        type="number"
                        min={1}
                        max={5}
                        value={config.best_of}
                        onChange={(e) => updateConfig("best_of", parseInt(e.target.value, 10))}
                      />
                    </div>
                  </div>

                  <div className="space-y-3">
                    <div className="flex items-center justify-between">
                      <Label>Temperature</Label>
                      <span className="text-sm font-mono">{config.temperature}</span>
                    </div>
                    <Slider
                      min={0}
                      max={1}
                      step={0.1}
                      value={[config.temperature]}
                      onValueChange={(values: number[]) => updateConfig("temperature", values[0])}
                    />
                  </div>

                  <div className="flex items-center justify-between">
                    <div className="space-y-0.5">
                      <Label>Word Timestamps</Label>
                      <p className="text-xs text-muted-foreground">
                        Include word-level timing
                      </p>
                    </div>
                    <Switch
                      checked={config.word_timestamps}
                      onCheckedChange={(checked) => updateConfig("word_timestamps", checked)}
                    />
                  </div>

                  <div className="space-y-2">
                    <Label>Initial Prompt</Label>
                    <Textarea
                      value={config.initial_prompt}
                      onChange={(e) => updateConfig("initial_prompt", e.target.value)}
                      placeholder="Optional context for transcription..."
                      rows={2}
                    />
                  </div>
                </CollapsibleContent>
              </Collapsible>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Actions */}
      <div className="flex justify-between">
        <Button
          variant="outline"
          onClick={() => testMutation.mutate()}
          disabled={testMutation.isPending}
        >
          {testMutation.isPending ? (
            <RefreshCw className="mr-2 h-4 w-4 animate-spin" />
          ) : (
            <Play className="mr-2 h-4 w-4" />
          )}
          Test STT
        </Button>
        <div className="flex gap-2">
          <Button
            variant="outline"
            onClick={() => {
              if (savedConfig) setConfig(savedConfig);
              setHasChanges(false);
            }}
            disabled={!hasChanges}
          >
            Reset
          </Button>
          <Button
            onClick={() => saveMutation.mutate(config)}
            disabled={!hasChanges || saveMutation.isPending}
          >
            {saveMutation.isPending ? (
              <RefreshCw className="mr-2 h-4 w-4 animate-spin" />
            ) : (
              <Save className="mr-2 h-4 w-4" />
            )}
            Save Changes
          </Button>
        </div>
      </div>
    </div>
  );
}
