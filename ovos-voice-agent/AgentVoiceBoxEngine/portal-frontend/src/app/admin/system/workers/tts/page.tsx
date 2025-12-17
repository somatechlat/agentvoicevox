"use client";

/**
 * TTS Worker Configuration Page (Kokoro)
 * Settings: default_voice, default_speed, sample_rate, audio_format, cache
 */

import { useState, useEffect } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Volume2, Save, RefreshCw, AlertCircle, CheckCircle, Play, Pause } from "lucide-react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";
import { Slider } from "@/components/ui/slider";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { systemApi } from "@/lib/api";

interface TTSConfig {
  default_voice: string;
  default_speed: number;
  model_dir: string;
  sample_rate: number;
  audio_format: string;
  chunk_size: number;
  cache_enabled: boolean;
  cache_max_size: string;
}

const voices = [
  { id: "am_onyx", name: "Onyx", gender: "Male", language: "American", style: "Professional" },
  { id: "am_adam", name: "Adam", gender: "Male", language: "American", style: "Casual" },
  { id: "af_sarah", name: "Sarah", gender: "Female", language: "American", style: "Warm" },
  { id: "af_nicole", name: "Nicole", gender: "Female", language: "American", style: "Friendly" },
  { id: "bf_emma", name: "Emma", gender: "Female", language: "British", style: "Elegant" },
  { id: "bm_george", name: "George", gender: "Male", language: "British", style: "Formal" },
  { id: "am_michael", name: "Michael", gender: "Male", language: "American", style: "News" },
  { id: "af_bella", name: "Bella", gender: "Female", language: "American", style: "Young" },
];

const sampleRates = [
  { value: 16000, label: "16 kHz (Phone)" },
  { value: 22050, label: "22.05 kHz (Standard)" },
  { value: 24000, label: "24 kHz (High Quality)" },
  { value: 44100, label: "44.1 kHz (CD Quality)" },
];

const audioFormats = [
  { value: "pcm16", label: "PCM 16-bit (Raw)" },
  { value: "float32", label: "Float32 (High Precision)" },
  { value: "mp3", label: "MP3 (Compressed)" },
  { value: "opus", label: "Opus (WebRTC)" },
];

const defaultConfig: TTSConfig = {
  default_voice: "am_onyx",
  default_speed: 1.1,
  model_dir: "/models/kokoro",
  sample_rate: 24000,
  audio_format: "pcm16",
  chunk_size: 4096,
  cache_enabled: true,
  cache_max_size: "100MB",
};

export default function TTSConfigPage() {
  const queryClient = useQueryClient();
  const [config, setConfig] = useState<TTSConfig>(defaultConfig);
  const [hasChanges, setHasChanges] = useState(false);
  const [playingVoice, setPlayingVoice] = useState<string | null>(null);
  const [testText, setTestText] = useState("Hello, this is a test of the voice system.");

  const { data: health } = useQuery({
    queryKey: ["tts-health"],
    queryFn: () => systemApi.getHealth(),
    refetchInterval: 30000,
  });

  const { data: savedConfig, isLoading } = useQuery({
    queryKey: ["tts-config"],
    queryFn: async () => {
      const response = await systemApi.getConfig<TTSConfig>("tts");
      return response;
    },
  });

  useEffect(() => {
    if (savedConfig) {
      setConfig(savedConfig);
    }
  }, [savedConfig]);

  const { data: stats } = useQuery({
    queryKey: ["tts-stats"],
    queryFn: () => systemApi.getWorkerStats().then((s) => s?.tts),
    refetchInterval: 10000,
  });

  const saveMutation = useMutation({
    mutationFn: (newConfig: TTSConfig) => systemApi.updateConfig("tts", newConfig),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["tts-config"] });
      setHasChanges(false);
    },
  });

  const playVoicePreview = (voiceId: string) => {
    const audioUrl = systemApi.previewVoice(voiceId, testText);
    setPlayingVoice(voiceId);
    const audio = new Audio(audioUrl);
    audio.onended = () => setPlayingVoice(null);
    audio.play();
  };

  const updateConfig = <K extends keyof TTSConfig>(key: K, value: TTSConfig[K]) => {
    setConfig((prev) => ({ ...prev, [key]: value }));
    setHasChanges(true);
  };

  const parseMemoryValue = (value: string): number => {
    const match = value.match(/^(\d+)(MB|GB)$/i);
    if (!match) return 100;
    const num = parseInt(match[1], 10);
    return match[2].toUpperCase() === "GB" ? num * 1024 : num;
  };

  const formatMemoryValue = (mb: number): string => {
    return mb >= 1024 ? `${mb / 1024}GB` : `${mb}MB`;
  };

  const isHealthy = health?.services?.some(
    (s: { name: string; status: string }) => 
      s.name.toLowerCase().includes("tts") && s.status === "healthy"
  );

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold flex items-center gap-2">
            <Volume2 className="h-6 w-6" />
            TTS Worker Configuration
          </h1>
          <p className="text-muted-foreground">
            Configure Kokoro text-to-speech settings
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
              <CardDescription>Generations/min</CardDescription>
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
              <CardDescription>Cache Hit Rate</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{stats.cache_hit_rate || 0}%</div>
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
        </div>
      )}

      {isLoading ? (
        <div className="flex items-center justify-center py-12">
          <RefreshCw className="h-8 w-8 animate-spin text-muted-foreground" />
        </div>
      ) : (
        <div className="grid gap-6 lg:grid-cols-2">
          {/* Voice Selection */}
          <Card className="lg:col-span-2">
            <CardHeader>
              <CardTitle>Voice Selection</CardTitle>
              <CardDescription>
                Choose the default voice for text-to-speech synthesis
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
                {voices.map((voice) => (
                  <button
                    key={voice.id}
                    onClick={() => updateConfig("default_voice", voice.id)}
                    className={`relative rounded-lg border p-4 text-left transition-colors ${
                      config.default_voice === voice.id
                        ? "border-primary bg-primary/10"
                        : "border-border hover:bg-accent"
                    }`}
                  >
                    <div className="mb-2 flex items-center justify-between">
                      <span className="text-2xl">
                        {voice.gender === "Male" ? "🎙️" : "🎤"}
                      </span>
                      <Button
                        size="icon"
                        variant="ghost"
                        className="h-8 w-8"
                        onClick={(e) => {
                          e.stopPropagation();
                          if (playingVoice === voice.id) {
                            setPlayingVoice(null);
                          } else {
                            playVoicePreview(voice.id);
                          }
                        }}
                      >
                        {playingVoice === voice.id ? (
                          <Pause className="h-4 w-4" />
                        ) : (
                          <Play className="h-4 w-4" />
                        )}
                      </Button>
                    </div>
                    <div className="font-medium">{voice.name}</div>
                    <div className="text-xs text-muted-foreground">
                      {voice.gender} • {voice.language}
                    </div>
                    <div className="text-xs text-muted-foreground">{voice.style}</div>
                  </button>
                ))}
              </div>

              <Separator />

              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <Label>Speech Speed</Label>
                  <span className="text-sm font-mono">{config.default_speed}x</span>
                </div>
                <Slider
                  min={0.5}
                  max={2.0}
                  step={0.1}
                  value={[config.default_speed]}
                  onValueChange={(values: number[]) => updateConfig("default_speed", values[0])}
                />
                <div className="flex justify-between text-xs text-muted-foreground">
                  <span>0.5x (Slow)</span>
                  <span>1.0x (Normal)</span>
                  <span>2.0x (Fast)</span>
                </div>
              </div>

              <div className="space-y-2">
                <Label>Test Text</Label>
                <Input
                  value={testText}
                  onChange={(e) => setTestText(e.target.value)}
                  placeholder="Enter text to preview..."
                />
              </div>
            </CardContent>
          </Card>

          {/* Audio Settings */}
          <Card>
            <CardHeader>
              <CardTitle>Audio Settings</CardTitle>
              <CardDescription>
                Configure audio output format and quality
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="space-y-2">
                <Label>Sample Rate</Label>
                <Select
                  value={config.sample_rate.toString()}
                  onValueChange={(v) => updateConfig("sample_rate", parseInt(v, 10))}
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {sampleRates.map((rate) => (
                      <SelectItem key={rate.value} value={rate.value.toString()}>
                        {rate.label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              <div className="space-y-2">
                <Label>Audio Format</Label>
                <Select
                  value={config.audio_format}
                  onValueChange={(v) => updateConfig("audio_format", v)}
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {audioFormats.map((format) => (
                      <SelectItem key={format.value} value={format.value}>
                        {format.label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              <div className="space-y-2">
                <Label>Chunk Size (bytes)</Label>
                <Input
                  type="number"
                  min={1024}
                  max={16384}
                  step={1024}
                  value={config.chunk_size}
                  onChange={(e) => updateConfig("chunk_size", parseInt(e.target.value, 10))}
                />
                <p className="text-xs text-muted-foreground">
                  Size of audio chunks for streaming
                </p>
              </div>
            </CardContent>
          </Card>

          {/* Cache Settings */}
          <Card>
            <CardHeader>
              <CardTitle>Cache Settings</CardTitle>
              <CardDescription>
                Configure voice synthesis caching
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="flex items-center justify-between">
                <div className="space-y-0.5">
                  <Label>Enable Cache</Label>
                  <p className="text-xs text-muted-foreground">
                    Cache synthesized audio for repeated phrases
                  </p>
                </div>
                <Switch
                  checked={config.cache_enabled}
                  onCheckedChange={(checked) => updateConfig("cache_enabled", checked)}
                />
              </div>

              {config.cache_enabled && (
                <>
                  <Separator />
                  <div className="space-y-3">
                    <div className="flex items-center justify-between">
                      <Label>Max Cache Size</Label>
                      <span className="text-sm font-mono">{config.cache_max_size}</span>
                    </div>
                    <Slider
                      min={50}
                      max={1024}
                      step={50}
                      value={[parseMemoryValue(config.cache_max_size)]}
                      onValueChange={(values: number[]) => updateConfig("cache_max_size", formatMemoryValue(values[0]))}
                    />
                  </div>
                </>
              )}

              <Separator />

              <div className="space-y-2">
                <Label>Model Directory</Label>
                <Input
                  value={config.model_dir}
                  onChange={(e) => updateConfig("model_dir", e.target.value)}
                  placeholder="/models/kokoro"
                />
                <p className="text-xs text-muted-foreground">
                  Path to Kokoro model files
                </p>
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Save Button */}
      <div className="flex justify-end gap-2">
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
  );
}
