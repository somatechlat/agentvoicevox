"use client";

/**
 * Voice Cloning Page
 * Implements Requirements B13.1-B13.6: Custom voice creation and cloning
 * Based on OVOS TTS plugins and Piper voice training
 * Reference: https://openvoiceos.github.io/ovos-technical-manual/
 */

import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  Mic,
  Upload,
  Play,
  Pause,
  Trash2,
  Star,
  AlertCircle,
  Clock,
  CheckCircle,
  XCircle,
  Volume2,
} from "lucide-react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { Skeleton } from "@/components/ui/skeleton";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Textarea } from "@/components/ui/textarea";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
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

// Supported languages for voice cloning
const LANGUAGES = [
  { code: "en", name: "English" },
  { code: "es", name: "Spanish" },
  { code: "fr", name: "French" },
  { code: "de", name: "German" },
  { code: "it", name: "Italian" },
  { code: "pt", name: "Portuguese" },
  { code: "ja", name: "Japanese" },
  { code: "ko", name: "Korean" },
  { code: "zh", name: "Chinese" },
];

// Quality levels
const QUALITY_LEVELS = [
  { id: "fast", name: "Fast", description: "Quick training, lower quality" },
  { id: "balanced", name: "Balanced", description: "Good balance of speed and quality" },
  { id: "high", name: "High Quality", description: "Best quality, longer training time" },
];

interface CustomVoice {
  id: string;
  name: string;
  language: string;
  quality: string;
  status: "processing" | "ready" | "failed";
  created_at: string;
  sample_duration_seconds: number;
  is_default: boolean;
  error_message?: string;
}

interface VoiceCloningFormData {
  name: string;
  language: string;
  quality: string;
}

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:25001";

// API functions
const voiceCloningApi = {
  list: () => apiRequest<CustomVoice[]>("/api/v1/voice-cloning/voices"),
  create: (formData: FormData) =>
    fetch(`${API_BASE_URL}/api/v1/voice-cloning/voices`, {
      method: "POST",
      body: formData,
      headers: {
        Authorization: `Bearer ${sessionStorage.getItem("access_token")}`,
      },
    }).then((res) => {
      if (!res.ok) throw new Error("Failed to create voice");
      return res.json();
    }),
  delete: (id: string) =>
    apiRequest<void>(`/api/v1/voice-cloning/voices/${id}`, { method: "DELETE" }),
  setDefault: (id: string) =>
    apiRequest<CustomVoice>(`/api/v1/voice-cloning/voices/${id}/default`, { method: "POST" }),
  preview: (id: string, text: string) =>
    `${API_BASE_URL}/api/v1/voice-cloning/voices/${id}/preview?text=${encodeURIComponent(text)}`,
  getStatus: (id: string) =>
    apiRequest<CustomVoice>(`/api/v1/voice-cloning/voices/${id}`),
};

const defaultFormData: VoiceCloningFormData = {
  name: "",
  language: "en",
  quality: "balanced",
};

export default function VoiceCloningPage() {
  const { toast } = useToast();
  const queryClient = useQueryClient();
  const [isDialogOpen, setIsDialogOpen] = useState(false);
  const [formData, setFormData] = useState<VoiceCloningFormData>(defaultFormData);
  const [audioFile, setAudioFile] = useState<File | null>(null);
  const [previewText, setPreviewText] = useState("Hello, this is my custom voice.");
  const [playingVoiceId, setPlayingVoiceId] = useState<string | null>(null);
  const [isUploading, setIsUploading] = useState(false);

  const { data: voices, isLoading, error } = useQuery({
    queryKey: ["custom-voices"],
    queryFn: voiceCloningApi.list,
    refetchInterval: 10000, // Poll for status updates
  });

  const deleteMutation = useMutation({
    mutationFn: voiceCloningApi.delete,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["custom-voices"] });
      toast({ title: "Voice deleted" });
    },
    onError: () => {
      toast({ title: "Failed to delete voice", variant: "destructive" });
    },
  });

  const setDefaultMutation = useMutation({
    mutationFn: voiceCloningApi.setDefault,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["custom-voices"] });
      toast({ title: "Default voice updated" });
    },
    onError: () => {
      toast({ title: "Failed to set default", variant: "destructive" });
    },
  });

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      // Validate file type
      if (!file.type.startsWith("audio/")) {
        toast({ title: "Please upload an audio file (WAV or MP3)", variant: "destructive" });
        return;
      }
      // Validate file size (max 50MB)
      if (file.size > 50 * 1024 * 1024) {
        toast({ title: "File too large. Maximum size is 50MB", variant: "destructive" });
        return;
      }
      setAudioFile(file);
    }
  };

  const handleSubmit = async () => {
    if (!audioFile || !formData.name) {
      toast({ title: "Please provide a name and audio file", variant: "destructive" });
      return;
    }

    setIsUploading(true);
    try {
      const uploadData = new FormData();
      uploadData.append("audio", audioFile);
      uploadData.append("name", formData.name);
      uploadData.append("language", formData.language);
      uploadData.append("quality", formData.quality);

      await voiceCloningApi.create(uploadData);
      queryClient.invalidateQueries({ queryKey: ["custom-voices"] });
      setIsDialogOpen(false);
      setFormData(defaultFormData);
      setAudioFile(null);
      toast({ title: "Voice cloning started. This may take a few minutes." });
    } catch {
      toast({ title: "Failed to start voice cloning", variant: "destructive" });
    } finally {
      setIsUploading(false);
    }
  };

  const handlePreview = async (voiceId: string) => {
    if (playingVoiceId === voiceId) {
      setPlayingVoiceId(null);
      return;
    }

    setPlayingVoiceId(voiceId);
    try {
      const audio = new Audio(voiceCloningApi.preview(voiceId, previewText));
      audio.onended = () => setPlayingVoiceId(null);
      audio.onerror = () => {
        setPlayingVoiceId(null);
        toast({ title: "Preview failed", variant: "destructive" });
      };
      await audio.play();
    } catch {
      setPlayingVoiceId(null);
      toast({ title: "Preview not available", variant: "destructive" });
    }
  };

  const getStatusBadge = (status: CustomVoice["status"]) => {
    switch (status) {
      case "processing":
        return (
          <Badge variant="secondary" className="gap-1">
            <Clock className="h-3 w-3 animate-spin" />
            Processing
          </Badge>
        );
      case "ready":
        return (
          <Badge variant="default" className="gap-1 bg-green-600">
            <CheckCircle className="h-3 w-3" />
            Ready
          </Badge>
        );
      case "failed":
        return (
          <Badge variant="destructive" className="gap-1">
            <XCircle className="h-3 w-3" />
            Failed
          </Badge>
        );
    }
  };

  if (isLoading) {
    return (
      <DashboardLayout title="Voice Cloning" description="Create custom voices">
        <div className="space-y-6">
          {[...Array(3)].map((_, i) => (
            <Card key={i}>
              <CardHeader>
                <Skeleton className="h-6 w-32" />
              </CardHeader>
              <CardContent>
                <Skeleton className="h-20 w-full" />
              </CardContent>
            </Card>
          ))}
        </div>
      </DashboardLayout>
    );
  }

  if (error) {
    return (
      <DashboardLayout title="Voice Cloning" description="Create custom voices">
        <Card>
          <CardContent className="py-8 text-center">
            <AlertCircle className="mx-auto h-12 w-12 text-muted-foreground mb-4" />
            <p className="text-muted-foreground">Unable to load custom voices</p>
          </CardContent>
        </Card>
      </DashboardLayout>
    );
  }

  return (
    <DashboardLayout title="Voice Cloning" description="Create custom voices from audio samples">
      <div className="space-y-6">
        {/* Info Banner */}
        <Card className="border-blue-200 bg-blue-50 dark:border-blue-900 dark:bg-blue-950">
          <CardContent className="py-4">
            <div className="flex items-start gap-3">
              <Mic className="h-5 w-5 text-blue-600 mt-0.5" />
              <div>
                <p className="font-medium text-blue-900 dark:text-blue-100">
                  Voice Cloning Requirements
                </p>
                <ul className="text-sm text-blue-800 dark:text-blue-200 mt-1 space-y-1">
                  <li>• Audio sample: 10 seconds to 5 minutes of clear speech</li>
                  <li>• Format: WAV or MP3 (mono preferred, 16kHz+ sample rate)</li>
                  <li>• Quality: Minimal background noise, consistent volume</li>
                  <li>• Processing time: 2-5 minutes depending on quality setting</li>
                </ul>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Header with Create Button */}
        <div className="flex justify-between items-center">
          <div>
            <h2 className="text-lg font-semibold">Custom Voices</h2>
            <p className="text-sm text-muted-foreground">
              {voices?.length || 0} voice{voices?.length !== 1 ? "s" : ""} created
            </p>
          </div>
          <Button onClick={() => setIsDialogOpen(true)}>
            <Upload className="mr-2 h-4 w-4" />
            Clone New Voice
          </Button>
        </div>

        {/* Preview Text Input */}
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-base">Preview Text</CardTitle>
          </CardHeader>
          <CardContent>
            <Textarea
              value={previewText}
              onChange={(e) => setPreviewText(e.target.value)}
              placeholder="Enter text to preview voices..."
              rows={2}
            />
          </CardContent>
        </Card>

        {/* Voices List */}
        {voices && voices.length === 0 ? (
          <Card>
            <CardContent className="py-12 text-center">
              <Mic className="mx-auto h-12 w-12 text-muted-foreground mb-4" />
              <h3 className="text-lg font-medium mb-2">No custom voices yet</h3>
              <p className="text-muted-foreground mb-4">
                Upload an audio sample to create your first custom voice
              </p>
              <Button onClick={() => setIsDialogOpen(true)}>
                <Upload className="mr-2 h-4 w-4" />
                Clone New Voice
              </Button>
            </CardContent>
          </Card>
        ) : (
          <div className="grid gap-4">
            {voices?.map((voice) => (
              <Card key={voice.id}>
                <CardHeader>
                  <div className="flex items-start justify-between">
                    <div className="flex items-center gap-3">
                      <Volume2 className="h-8 w-8 text-primary" />
                      <div>
                        <CardTitle className="flex items-center gap-2">
                          {voice.name}
                          {voice.is_default && (
                            <Badge variant="secondary">
                              <Star className="mr-1 h-3 w-3" />
                              Default
                            </Badge>
                          )}
                        </CardTitle>
                        <CardDescription>
                          {LANGUAGES.find((l) => l.code === voice.language)?.name || voice.language} •{" "}
                          {QUALITY_LEVELS.find((q) => q.id === voice.quality)?.name || voice.quality}
                        </CardDescription>
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      {getStatusBadge(voice.status)}
                    </div>
                  </div>
                </CardHeader>
                <CardContent>
                  <div className="flex items-center justify-between">
                    <div className="text-sm text-muted-foreground">
                      <span>Sample: {voice.sample_duration_seconds.toFixed(1)}s</span>
                      <span className="mx-2">•</span>
                      <span>Created: {new Date(voice.created_at).toLocaleDateString()}</span>
                    </div>
                    <div className="flex gap-2">
                      {voice.status === "ready" && (
                        <>
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() => handlePreview(voice.id)}
                            disabled={!previewText}
                          >
                            {playingVoiceId === voice.id ? (
                              <Pause className="h-4 w-4" />
                            ) : (
                              <Play className="h-4 w-4" />
                            )}
                          </Button>
                          {!voice.is_default && (
                            <Button
                              variant="outline"
                              size="sm"
                              onClick={() => setDefaultMutation.mutate(voice.id)}
                            >
                              <Star className="h-4 w-4" />
                            </Button>
                          )}
                        </>
                      )}
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => {
                          if (confirm("Delete this voice?")) {
                            deleteMutation.mutate(voice.id);
                          }
                        }}
                        disabled={voice.is_default}
                      >
                        <Trash2 className="h-4 w-4" />
                      </Button>
                    </div>
                  </div>
                  {voice.status === "failed" && voice.error_message && (
                    <div className="mt-3 p-3 rounded-md bg-red-50 dark:bg-red-950 text-sm text-red-800 dark:text-red-200">
                      {voice.error_message}
                    </div>
                  )}
                </CardContent>
              </Card>
            ))}
          </div>
        )}

        {/* Create Dialog */}
        <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
          <DialogContent className="max-w-lg">
            <DialogHeader>
              <DialogTitle>Clone New Voice</DialogTitle>
              <DialogDescription>
                Upload an audio sample to create a custom voice clone
              </DialogDescription>
            </DialogHeader>

            <div className="space-y-4 py-4">
              <div className="space-y-2">
                <Label>Voice Name</Label>
                <Input
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  placeholder="e.g., My Custom Voice"
                />
              </div>

              <div className="grid gap-4 grid-cols-2">
                <div className="space-y-2">
                  <Label>Language</Label>
                  <Select
                    value={formData.language}
                    onValueChange={(value) => setFormData({ ...formData, language: value })}
                  >
                    <SelectTrigger>
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
                </div>

                <div className="space-y-2">
                  <Label>Quality</Label>
                  <Select
                    value={formData.quality}
                    onValueChange={(value) => setFormData({ ...formData, quality: value })}
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      {QUALITY_LEVELS.map((level) => (
                        <SelectItem key={level.id} value={level.id}>
                          {level.name}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
              </div>

              <div className="space-y-2">
                <Label>Audio Sample</Label>
                <div className="border-2 border-dashed rounded-lg p-6 text-center">
                  <Input
                    type="file"
                    accept="audio/wav,audio/mp3,audio/mpeg,audio/*"
                    onChange={handleFileChange}
                    className="hidden"
                    id="audio-upload"
                  />
                  <label htmlFor="audio-upload" className="cursor-pointer">
                    <Upload className="mx-auto h-8 w-8 text-muted-foreground mb-2" />
                    {audioFile ? (
                      <p className="text-sm font-medium">{audioFile.name}</p>
                    ) : (
                      <p className="text-sm text-muted-foreground">
                        Click to upload WAV or MP3 (10s - 5min)
                      </p>
                    )}
                  </label>
                </div>
              </div>
            </div>

            <DialogFooter>
              <Button variant="outline" onClick={() => setIsDialogOpen(false)}>
                Cancel
              </Button>
              <Button
                onClick={handleSubmit}
                disabled={!formData.name || !audioFile || isUploading}
              >
                {isUploading ? "Uploading..." : "Start Cloning"}
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>
    </DashboardLayout>
  );
}
