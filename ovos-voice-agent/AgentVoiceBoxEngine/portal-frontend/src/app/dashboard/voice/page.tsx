"use client";

/**
 * Voice Configuration Page
 * Implements Requirements B9.1-B9.6: Voice settings, TTS voice selection, persona config
 */

import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Mic, Volume2, Play, Save, AlertCircle } from "lucide-react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { Skeleton } from "@/components/ui/skeleton";
import { Textarea } from "@/components/ui/textarea";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { voiceApi, VoiceConfig, Voice } from "@/lib/api";
import { useToast } from "@/components/ui/use-toast";
import { DashboardLayout } from "@/components/layout/DashboardLayout";

// Kokoro voices from CONFIGURATION_REPORT.md
const KOKORO_VOICES = [
  { id: "am_onyx", name: "Onyx", gender: "male", language: "en-US" },
  { id: "am_adam", name: "Adam", gender: "male", language: "en-US" },
  { id: "af_sarah", name: "Sarah", gender: "female", language: "en-US" },
  { id: "af_nicole", name: "Nicole", gender: "female", language: "en-US" },
  { id: "bf_emma", name: "Emma", gender: "female", language: "en-GB" },
  { id: "bm_george", name: "George", gender: "male", language: "en-GB" },
];

export default function VoiceConfigPage() {
  const { toast } = useToast();
  const queryClient = useQueryClient();
  const [previewText, setPreviewText] = useState("Hello, I am your voice assistant.");
  const [isPlaying, setIsPlaying] = useState(false);

  const { data: config, isLoading, error } = useQuery({
    queryKey: ["voice-config"],
    queryFn: voiceApi.getConfig,
  });

  const [localConfig, setLocalConfig] = useState<Partial<VoiceConfig>>({});

  // Merge fetched config with local changes
  const currentConfig = { ...config, ...localConfig };

  const updateMutation = useMutation({
    mutationFn: (data: Partial<VoiceConfig>) => voiceApi.updateConfig(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["voice-config"] });
      setLocalConfig({});
      toast({ title: "Voice configuration saved" });
    },
    onError: () => {
      toast({ title: "Failed to save configuration", variant: "destructive" });
    },
  });

  const handleVoiceChange = (voiceId: string) => {
    setLocalConfig({ ...localConfig, default_voice: voiceId });
  };

  const handleSpeedChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setLocalConfig({ ...localConfig, speed: parseFloat(e.target.value) });
  };

  const handleSave = () => {
    updateMutation.mutate(localConfig);
  };

  const handlePreview = async () => {
    const voice = currentConfig.default_voice || "am_onyx";
    const previewUrl = voiceApi.previewVoice(voice, previewText);
    
    setIsPlaying(true);
    try {
      const audio = new Audio(previewUrl);
      audio.onended = () => setIsPlaying(false);
      audio.onerror = () => {
        setIsPlaying(false);
        toast({ title: "Preview failed", variant: "destructive" });
      };
      await audio.play();
    } catch {
      setIsPlaying(false);
      toast({ title: "Preview not available", variant: "destructive" });
    }
  };

  if (isLoading) {
    return (
      <DashboardLayout title="Voice Configuration" description="Configure voice settings">
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
      <DashboardLayout title="Voice Configuration" description="Configure voice settings">
        <Card>
          <CardContent className="py-8 text-center">
            <AlertCircle className="mx-auto h-12 w-12 text-muted-foreground mb-4" />
            <p className="text-muted-foreground">Unable to load voice configuration</p>
          </CardContent>
        </Card>
      </DashboardLayout>
    );
  }

  const hasChanges = Object.keys(localConfig).length > 0;

  return (
    <DashboardLayout title="Voice Configuration" description="Configure voice settings for your organization">
      <div className="space-y-6">
        {/* Voice Selection */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Mic className="h-5 w-5" />
              TTS Voice
            </CardTitle>
            <CardDescription>
              Select the default voice for text-to-speech synthesis
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <Label>Default Voice</Label>
              <Select
                value={currentConfig.default_voice || "am_onyx"}
                onValueChange={handleVoiceChange}
              >
                <SelectTrigger>
                  <SelectValue placeholder="Select a voice" />
                </SelectTrigger>
                <SelectContent>
                  {KOKORO_VOICES.map((voice) => (
                    <SelectItem key={voice.id} value={voice.id}>
                      {voice.name} ({voice.gender}, {voice.language})
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            {/* Voice Preview */}
            <div className="space-y-2">
              <Label>Preview Text</Label>
              <div className="flex gap-2">
                <Textarea
                  value={previewText}
                  onChange={(e: React.ChangeEvent<HTMLTextAreaElement>) => setPreviewText(e.target.value)}
                  placeholder="Enter text to preview..."
                  className="flex-1"
                  rows={2}
                />
                <Button
                  variant="outline"
                  onClick={handlePreview}
                  disabled={isPlaying || !previewText}
                >
                  {isPlaying ? (
                    <Volume2 className="h-4 w-4 animate-pulse" />
                  ) : (
                    <Play className="h-4 w-4" />
                  )}
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Voice Speed */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Volume2 className="h-5 w-5" />
              Voice Speed
            </CardTitle>
            <CardDescription>
              Adjust the speaking rate (0.5x to 2.0x)
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <Label>Speed: {(currentConfig.speed || 1.0).toFixed(1)}x</Label>
              </div>
              <Input
                type="range"
                value={currentConfig.speed || 1.0}
                onChange={handleSpeedChange}
                min={0.5}
                max={2.0}
                step={0.1}
                className="w-full"
              />
              <div className="flex justify-between text-xs text-muted-foreground">
                <span>0.5x (Slow)</span>
                <span>1.0x (Normal)</span>
                <span>2.0x (Fast)</span>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Language */}
        <Card>
          <CardHeader>
            <CardTitle>Language</CardTitle>
            <CardDescription>
              Default language for speech recognition and synthesis
            </CardDescription>
          </CardHeader>
          <CardContent>
            <Select
              value={currentConfig.language || "en-US"}
              onValueChange={(value) => setLocalConfig({ ...localConfig, language: value })}
            >
              <SelectTrigger className="w-full max-w-xs">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="en-US">English (US)</SelectItem>
                <SelectItem value="en-GB">English (UK)</SelectItem>
                <SelectItem value="es-ES">Spanish (Spain)</SelectItem>
                <SelectItem value="fr-FR">French (France)</SelectItem>
                <SelectItem value="de-DE">German (Germany)</SelectItem>
                <SelectItem value="it-IT">Italian (Italy)</SelectItem>
                <SelectItem value="pt-BR">Portuguese (Brazil)</SelectItem>
                <SelectItem value="ja-JP">Japanese</SelectItem>
                <SelectItem value="ko-KR">Korean</SelectItem>
                <SelectItem value="zh-CN">Chinese (Simplified)</SelectItem>
              </SelectContent>
            </Select>
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
