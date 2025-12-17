"use client";

/**
 * Wake Word Configuration Page
 * Implements Requirements E4.1-E4.6: Wake word configuration and analytics
 * Reference: OVOS wake word plugins (Precise, Porcupine, Snowboy)
 */

import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  Mic,
  Plus,
  Trash2,
  AlertCircle,
  Play,
  Square,
  Volume2,
} from "lucide-react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { Skeleton } from "@/components/ui/skeleton";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Switch } from "@/components/ui/switch";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { apiRequest } from "@/lib/api";
import { useToast } from "@/components/ui/use-toast";
import { DashboardLayout } from "@/components/layout/DashboardLayout";

interface WakeWord {
  id: string;
  phrase: string;
  sensitivity: number;
  is_enabled: boolean;
  detection_count: number;
  false_positive_count: number;
  missed_activation_count: number;
  created_at: string;
  last_detected_at?: string;
}

interface WakeWordAnalytics {
  total_detections: number;
  false_positive_rate: number;
  missed_activation_rate: number;
  avg_confidence: number;
}

interface WakeWordFormData {
  phrase: string;
  sensitivity: number;
}

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:25001";

// API functions
const wakeWordsApi = {
  list: () => apiRequest<WakeWord[]>("/api/v1/wake-words"),
  create: (data: WakeWordFormData) =>
    apiRequest<WakeWord>("/api/v1/wake-words", {
      method: "POST",
      body: JSON.stringify(data),
    }),
  update: (id: string, data: Partial<WakeWordFormData & { is_enabled: boolean }>) =>
    apiRequest<WakeWord>(`/api/v1/wake-words/${id}`, {
      method: "PATCH",
      body: JSON.stringify(data),
    }),
  delete: (id: string) =>
    apiRequest<void>(`/api/v1/wake-words/${id}`, { method: "DELETE" }),
  test: (id: string, audioBlob: Blob) => {
    const formData = new FormData();
    formData.append("audio", audioBlob);
    return fetch(`${API_BASE_URL}/api/v1/wake-words/${id}/test`, {
      method: "POST",
      body: formData,
      headers: {
        Authorization: `Bearer ${sessionStorage.getItem("access_token")}`,
      },
    }).then((res) => res.json());
  },
  getAnalytics: () => apiRequest<WakeWordAnalytics>("/api/v1/wake-words/analytics"),
};

const defaultFormData: WakeWordFormData = {
  phrase: "",
  sensitivity: 0.5,
};

export default function WakeWordsPage() {
  const { toast } = useToast();
  const queryClient = useQueryClient();
  const [isDialogOpen, setIsDialogOpen] = useState(false);
  const [formData, setFormData] = useState<WakeWordFormData>(defaultFormData);
  const [isRecording, setIsRecording] = useState(false);
  const [testingWakeWordId, setTestingWakeWordId] = useState<string | null>(null);
  const [testResult, setTestResult] = useState<{ confidence: number } | null>(null);
  const [mediaRecorder, setMediaRecorder] = useState<MediaRecorder | null>(null);

  const { data: wakeWords, isLoading, error } = useQuery({
    queryKey: ["wake-words"],
    queryFn: wakeWordsApi.list,
  });

  const { data: analytics } = useQuery({
    queryKey: ["wake-words-analytics"],
    queryFn: wakeWordsApi.getAnalytics,
    refetchInterval: 60000,
  });

  const createMutation = useMutation({
    mutationFn: wakeWordsApi.create,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["wake-words"] });
      setIsDialogOpen(false);
      setFormData(defaultFormData);
      toast({ title: "Wake word added" });
    },
    onError: () => {
      toast({ title: "Failed to add wake word", variant: "destructive" });
    },
  });

  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: string; data: Partial<WakeWordFormData & { is_enabled: boolean }> }) =>
      wakeWordsApi.update(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["wake-words"] });
      toast({ title: "Wake word updated" });
    },
    onError: () => {
      toast({ title: "Failed to update wake word", variant: "destructive" });
    },
  });

  const deleteMutation = useMutation({
    mutationFn: wakeWordsApi.delete,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["wake-words"] });
      toast({ title: "Wake word deleted" });
    },
    onError: () => {
      toast({ title: "Failed to delete wake word", variant: "destructive" });
    },
  });

  const handleStartRecording = async (wakeWordId: string) => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const recorder = new MediaRecorder(stream);
      const chunks: Blob[] = [];

      recorder.ondataavailable = (e) => chunks.push(e.data);
      recorder.onstop = async () => {
        const audioBlob = new Blob(chunks, { type: "audio/webm" });
        stream.getTracks().forEach((track) => track.stop());
        
        try {
          const result = await wakeWordsApi.test(wakeWordId, audioBlob);
          setTestResult(result);
          toast({
            title: result.confidence > 0.5 ? "Wake word detected!" : "Wake word not detected",
            description: `Confidence: ${(result.confidence * 100).toFixed(1)}%`,
          });
        } catch {
          toast({ title: "Test failed", variant: "destructive" });
        }
        setIsRecording(false);
        setTestingWakeWordId(null);
      };

      setMediaRecorder(recorder);
      setTestingWakeWordId(wakeWordId);
      setIsRecording(true);
      recorder.start();

      setTimeout(() => {
        if (recorder.state === "recording") {
          recorder.stop();
        }
      }, 3000);
    } catch {
      toast({ title: "Microphone access denied", variant: "destructive" });
    }
  };

  const handleStopRecording = () => {
    if (mediaRecorder && mediaRecorder.state === "recording") {
      mediaRecorder.stop();
    }
  };

  const handleSubmit = () => {
    if (!formData.phrase.trim()) {
      toast({ title: "Please enter a wake word phrase", variant: "destructive" });
      return;
    }
    createMutation.mutate(formData);
  };

  if (isLoading) {
    return (
      <DashboardLayout title="Wake Words" description="Configure wake word detection">
        <div className="space-y-6">
          {[...Array(3)].map((_, i) => (
            <Card key={i}>
              <CardHeader><Skeleton className="h-6 w-32" /></CardHeader>
              <CardContent><Skeleton className="h-20 w-full" /></CardContent>
            </Card>
          ))}
        </div>
      </DashboardLayout>
    );
  }

  if (error) {
    return (
      <DashboardLayout title="Wake Words" description="Configure wake word detection">
        <Card>
          <CardContent className="py-8 text-center">
            <AlertCircle className="mx-auto h-12 w-12 text-muted-foreground mb-4" />
            <p className="text-muted-foreground">Unable to load wake words</p>
          </CardContent>
        </Card>
      </DashboardLayout>
    );
  }

  return (
    <DashboardLayout title="Wake Words" description="Configure wake word detection for your voice assistant">
      <div className="space-y-6">
        {analytics && (
          <div className="grid gap-4 md:grid-cols-4">
            <Card>
              <CardHeader className="pb-2">
                <CardDescription>Total Detections</CardDescription>
                <CardTitle className="text-2xl">{analytics.total_detections.toLocaleString()}</CardTitle>
              </CardHeader>
            </Card>
            <Card>
              <CardHeader className="pb-2">
                <CardDescription>Avg Confidence</CardDescription>
                <CardTitle className="text-2xl">{(analytics.avg_confidence * 100).toFixed(1)}%</CardTitle>
              </CardHeader>
            </Card>
            <Card>
              <CardHeader className="pb-2">
                <CardDescription>False Positive Rate</CardDescription>
                <CardTitle className="text-2xl">{(analytics.false_positive_rate * 100).toFixed(2)}%</CardTitle>
              </CardHeader>
            </Card>
            <Card>
              <CardHeader className="pb-2">
                <CardDescription>Missed Activations</CardDescription>
                <CardTitle className="text-2xl">{(analytics.missed_activation_rate * 100).toFixed(2)}%</CardTitle>
              </CardHeader>
            </Card>
          </div>
        )}

        <div className="flex justify-between items-center">
          <div>
            <h2 className="text-lg font-semibold">Configured Wake Words</h2>
            <p className="text-sm text-muted-foreground">
              {wakeWords?.filter((w) => w.is_enabled).length || 0} active
            </p>
          </div>
          <Button onClick={() => setIsDialogOpen(true)}>
            <Plus className="mr-2 h-4 w-4" />
            Add Wake Word
          </Button>
        </div>

        {wakeWords && wakeWords.length === 0 ? (
          <Card>
            <CardContent className="py-12 text-center">
              <Mic className="mx-auto h-12 w-12 text-muted-foreground mb-4" />
              <h3 className="text-lg font-medium mb-2">No wake words configured</h3>
              <p className="text-muted-foreground mb-4">Add a wake word to activate your voice assistant</p>
              <Button onClick={() => setIsDialogOpen(true)}>
                <Plus className="mr-2 h-4 w-4" />
                Add Wake Word
              </Button>
            </CardContent>
          </Card>
        ) : (
          <div className="grid gap-4">
            {wakeWords?.map((wakeWord) => (
              <Card key={wakeWord.id}>
                <CardHeader>
                  <div className="flex items-start justify-between">
                    <div className="flex items-center gap-3">
                      <Volume2 className="h-8 w-8 text-primary" />
                      <div>
                        <CardTitle className="flex items-center gap-2">
                          &quot;{wakeWord.phrase}&quot;
                          <Badge variant={wakeWord.is_enabled ? "default" : "secondary"}>
                            {wakeWord.is_enabled ? "Active" : "Disabled"}
                          </Badge>
                        </CardTitle>
                        <CardDescription>Sensitivity: {(wakeWord.sensitivity * 100).toFixed(0)}%</CardDescription>
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      <Switch
                        checked={wakeWord.is_enabled}
                        onCheckedChange={(checked) =>
                          updateMutation.mutate({ id: wakeWord.id, data: { is_enabled: checked } })
                        }
                      />
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => {
                          if (confirm("Delete this wake word?")) {
                            deleteMutation.mutate(wakeWord.id);
                          }
                        }}
                      >
                        <Trash2 className="h-4 w-4" />
                      </Button>
                    </div>
                  </div>
                </CardHeader>
                <CardContent>
                  <div className="grid gap-4 md:grid-cols-4 text-sm mb-4">
                    <div><span className="text-muted-foreground">Detections:</span> {wakeWord.detection_count.toLocaleString()}</div>
                    <div><span className="text-muted-foreground">False Positives:</span> {wakeWord.false_positive_count}</div>
                    <div><span className="text-muted-foreground">Missed:</span> {wakeWord.missed_activation_count}</div>
                    <div><span className="text-muted-foreground">Last:</span> {wakeWord.last_detected_at ? new Date(wakeWord.last_detected_at).toLocaleString() : "Never"}</div>
                  </div>

                  <div className="space-y-2 mb-4">
                    <div className="flex items-center justify-between">
                      <Label className="text-sm">Sensitivity</Label>
                      <span className="text-sm text-muted-foreground">{(wakeWord.sensitivity * 100).toFixed(0)}%</span>
                    </div>
                    <Input
                      type="range"
                      min={0.1}
                      max={1.0}
                      step={0.05}
                      value={wakeWord.sensitivity}
                      onChange={(e) =>
                        updateMutation.mutate({ id: wakeWord.id, data: { sensitivity: parseFloat(e.target.value) } })
                      }
                      className="w-full"
                    />
                  </div>

                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() =>
                      isRecording && testingWakeWordId === wakeWord.id
                        ? handleStopRecording()
                        : handleStartRecording(wakeWord.id)
                    }
                    disabled={isRecording && testingWakeWordId !== wakeWord.id}
                  >
                    {isRecording && testingWakeWordId === wakeWord.id ? (
                      <><Square className="mr-2 h-4 w-4 animate-pulse text-red-500" />Recording...</>
                    ) : (
                      <><Play className="mr-2 h-4 w-4" />Test Detection</>
                    )}
                  </Button>
                  {testResult && testingWakeWordId === wakeWord.id && (
                    <span className="ml-2 text-sm text-muted-foreground">
                      Confidence: {(testResult.confidence * 100).toFixed(1)}%
                    </span>
                  )}
                </CardContent>
              </Card>
            ))}
          </div>
        )}

        <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Add Wake Word</DialogTitle>
              <DialogDescription>Configure a new wake word phrase for voice activation</DialogDescription>
            </DialogHeader>
            <div className="space-y-4 py-4">
              <div className="space-y-2">
                <Label>Wake Word Phrase</Label>
                <Input
                  value={formData.phrase}
                  onChange={(e) => setFormData({ ...formData, phrase: e.target.value })}
                  placeholder='e.g., "Hey Assistant"'
                />
                <p className="text-xs text-muted-foreground">Use 2-4 syllables for best accuracy</p>
              </div>
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <Label>Initial Sensitivity</Label>
                  <span className="text-sm text-muted-foreground">{(formData.sensitivity * 100).toFixed(0)}%</span>
                </div>
                <Input
                  type="range"
                  min={0.1}
                  max={1.0}
                  step={0.05}
                  value={formData.sensitivity}
                  onChange={(e) => setFormData({ ...formData, sensitivity: parseFloat(e.target.value) })}
                  className="w-full"
                />
              </div>
            </div>
            <DialogFooter>
              <Button variant="outline" onClick={() => setIsDialogOpen(false)}>Cancel</Button>
              <Button onClick={handleSubmit} disabled={!formData.phrase.trim() || createMutation.isPending}>
                {createMutation.isPending ? "Adding..." : "Add Wake Word"}
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>
    </DashboardLayout>
  );
}
