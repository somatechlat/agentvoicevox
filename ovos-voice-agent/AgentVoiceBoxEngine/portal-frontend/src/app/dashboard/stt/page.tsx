"use client";

/**
 * STT Configuration Page
 * Implements Requirements B10.1-B10.6: Speech-to-text settings
 */

import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Mic, Save, AlertCircle, Upload, Play } from "lucide-react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { Skeleton } from "@/components/ui/skeleton";
import { Switch } from "@/components/ui/switch";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { apiRequest } from "@/lib/api";
import { useToast } from "@/components/ui/use-toast";
import { DashboardLayout } from "@/components/layout/DashboardLayout";

// STT Models from CONFIGURATION_REPORT.md
const STT_MODELS = [
  { id: "tiny", name: "Tiny", description: "Fastest, lowest accuracy", speed: "Very Fast", accuracy: "Low" },
  { id: "base", name: "Base", description: "Good balance for most use cases", speed: "Fast", accuracy: "Medium" },
  { id: "small", name: "Small", description: "Better accuracy, moderate speed", speed: "Medium", accuracy: "Good" },
  { id: "medium", name: "Medium", description: "High accuracy, slower", speed: "Slow", accuracy: "High" },
  { id: "large-v2", name: "Large v2", description: "Best accuracy, slowest", speed: "Very Slow", accuracy: "Very High" },
  { id: "large-v3", name: "Large v3", description: "Latest model, best quality", speed: "Very Slow", accuracy: "Excellent" },
];

const LANGUAGES = [
  { code: "auto", name: "Auto-detect" },
  { code: "en", name: "English" },
  { code: "es", name: "Spanish" },
  { code: "fr", name: "French" },
  { code: "de", name: "German" },
  { code: "it", name: "Italian" },
  { code: "pt", name: "Portuguese" },
  { code: "ja", name: "Japanese" },
  { code: "ko", name: "Korean" },
  { code: "zh", name: "Chinese" },
  { code: "ar", name: "Arabic" },
  { code: "ru", name: "Russian" },
];

interface STTConfig {
  model: string;
  language: string;
  vad_enabled: boolean;
  beam_size: number;
}

interface STTMetrics {
  avg_latency_ms: number;
  total_minutes: number;
  accuracy_estimate: number;
}

// API functions
const sttApi = {
  getConfig: () => apiRequest<STTConfig>("/api/v1/stt/config"),
  updateConfig: (data: Partial<STTConfig>) =>
    apiRequest<STTConfig>("/api/v1/stt/config", {
      method: "PATCH",
      body: JSON.stringify(data),
    }),
  getMetrics: () => apiRequest<STTMetrics>("/api/v1/stt/metrics"),
  testTranscription: (formData: FormData) =>
    fetch(`${process.env.NEXT_PUBLIC_API_URL || "http://localhost:25001"}/api/v1/stt/test`, {
      method: "POST",
      body: formData,
    }).then((res) => res.json()),
};

export default function STTConfigPage() {
  const { toast } = useToast();
  const queryClient = useQueryClient();
  const [localConfig, setLocalConfig] = useState<Partial<STTConfig>>({});
  const [testFile, setTestFile] = useState<File | null>(null);
  const [testResult, setTestResult] = useState<string | null>(null);
  const [isTesting, setIsTesting] = useState(false);

  const { data: config, isLoading, error } = useQuery({
    queryKey: ["stt-config"],
    queryFn: sttApi.getConfig,
  });

  const { data: metrics } = useQuery({
    queryKey: ["stt-metrics"],
    queryFn: sttApi.getMetrics,
    refetchInterval: 60000,
  });

  const currentConfig = { ...config, ...localConfig };

  const updateMutation = useMutation({
    mutationFn: (data: Partial<STTConfig>) => sttApi.updateConfig(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["stt-config"] });
      setLocalConfig({});
      toast({ title: "STT configuration saved" });
    },
    onError: () => {
      toast({ title: "Failed to save configuration", variant: "destructive" });
    },
  });

  const handleSave = () => {
    updateMutation.mutate(localConfig);
  };

  const handleTestTranscription = async () => {
    if (!testFile) return;
    
    setIsTesting(true);
    setTestResult(null);
    
    try {
      const formData = new FormData();
      formData.append("audio", testFile);
      const result = await sttApi.testTranscription(formData);
      setTestResult(result.transcription || "No transcription returned");
    } catch {
      toast({ title: "Transcription test failed", variant: "destructive" });
    } finally {
      setIsTesting(false);
    }
  };

  if (isLoading) {
    return (
      <DashboardLayout title="STT Configuration" description="Configure speech-to-text settings">
        <div className="space-y-6">
          <Card>
            <CardHeader>
              <Skeleton className="h-6 w-32" />
            </CardHeader>
            <CardContent className="space-y-4">
              {[...Array(3)].map((_, i) => (
                <Skeleton key={i} className="h-12 w-full" />
              ))}
            </CardContent>
          </Card>
        </div>
      </DashboardLayout>
    );
  }

  if (error) {
    return (
      <DashboardLayout title="STT Configuration" description="Configure speech-to-text settings">
        <Card>
          <CardContent className="py-8 text-center">
            <AlertCircle className="mx-auto h-12 w-12 text-muted-foreground mb-4" />
            <p className="text-muted-foreground">Unable to load STT configuration</p>
          </CardContent>
        </Card>
      </DashboardLayout>
    );
  }

  const hasChanges = Object.keys(localConfig).length > 0;

  return (
    <DashboardLayout title="STT Configuration" description="Configure speech-to-text settings for your organization">
      <div className="space-y-6">
        {/* STT Metrics */}
        {metrics && (
          <div className="grid gap-4 md:grid-cols-3">
            <Card>
              <CardHeader className="pb-2">
                <CardDescription>Avg Latency</CardDescription>
                <CardTitle className="text-2xl">{metrics.avg_latency_ms.toFixed(0)}ms</CardTitle>
              </CardHeader>
            </Card>
            <Card>
              <CardHeader className="pb-2">
                <CardDescription>Total Minutes</CardDescription>
                <CardTitle className="text-2xl">{metrics.total_minutes.toFixed(1)}</CardTitle>
              </CardHeader>
            </Card>
            <Card>
              <CardHeader className="pb-2">
                <CardDescription>Est. Accuracy</CardDescription>
                <CardTitle className="text-2xl">{(metrics.accuracy_estimate * 100).toFixed(1)}%</CardTitle>
              </CardHeader>
            </Card>
          </div>
        )}

        {/* Model Selection */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Mic className="h-5 w-5" />
              Faster-Whisper Model
            </CardTitle>
            <CardDescription>
              Select the STT model size. Larger models are more accurate but slower.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <Label>Model Size</Label>
              <Select
                value={currentConfig.model || "base"}
                onValueChange={(value) => setLocalConfig({ ...localConfig, model: value })}
              >
                <SelectTrigger>
                  <SelectValue placeholder="Select a model" />
                </SelectTrigger>
                <SelectContent>
                  {STT_MODELS.map((model) => (
                    <SelectItem key={model.id} value={model.id}>
                      <div className="flex flex-col">
                        <span>{model.name}</span>
                        <span className="text-xs text-muted-foreground">
                          {model.speed} • {model.accuracy} accuracy
                        </span>
                      </div>
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </CardContent>
        </Card>

        {/* Language Selection */}
        <Card>
          <CardHeader>
            <CardTitle>Language</CardTitle>
            <CardDescription>
              Select the primary language for transcription or use auto-detect
            </CardDescription>
          </CardHeader>
          <CardContent>
            <Select
              value={currentConfig.language || "auto"}
              onValueChange={(value) => setLocalConfig({ ...localConfig, language: value })}
            >
              <SelectTrigger className="w-full max-w-xs">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {LANGUAGES.map((lang) => (
                  <SelectItem key={lang.code} value={lang.code}>
                    {lang.name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </CardContent>
        </Card>

        {/* VAD Settings */}
        <Card>
          <CardHeader>
            <CardTitle>Voice Activity Detection</CardTitle>
            <CardDescription>
              Filter out non-speech audio to improve transcription quality
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="flex items-center justify-between">
              <div>
                <Label>Enable VAD Filtering</Label>
                <p className="text-sm text-muted-foreground">
                  Recommended for noisy environments
                </p>
              </div>
              <Switch
                checked={currentConfig.vad_enabled ?? true}
                onCheckedChange={(checked) => setLocalConfig({ ...localConfig, vad_enabled: checked })}
              />
            </div>
          </CardContent>
        </Card>

        {/* Test Transcription */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Upload className="h-5 w-5" />
              Test Transcription
            </CardTitle>
            <CardDescription>
              Upload an audio file to test the current STT configuration
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex gap-4">
              <Input
                type="file"
                accept="audio/*"
                onChange={(e) => setTestFile(e.target.files?.[0] || null)}
                className="flex-1"
              />
              <Button
                onClick={handleTestTranscription}
                disabled={!testFile || isTesting}
              >
                {isTesting ? (
                  "Processing..."
                ) : (
                  <>
                    <Play className="mr-2 h-4 w-4" />
                    Test
                  </>
                )}
              </Button>
            </div>
            {testResult && (
              <div className="rounded-md bg-muted p-4">
                <Label className="text-sm font-medium">Transcription Result:</Label>
                <p className="mt-1 text-sm">{testResult}</p>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Save Button */}
        {hasChanges && (
          <div className="flex justify-end">
            <Button onClick={handleSave} disabled={updateMutation.isPending}>
              <Save className="mr-2 h-4 w-4" />
              {updateMutation.isPending ? "Saving..." : "Save Changes"}
            </Button>
          </div>
        )}
      </div>
    </DashboardLayout>
  );
}
