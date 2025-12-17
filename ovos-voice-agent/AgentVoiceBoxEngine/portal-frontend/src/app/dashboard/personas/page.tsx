"use client";

/**
 * Persona Management Page
 * Implements Requirements B12.1-B12.6: AI persona creation and management
 */

import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Bot, Plus, Edit, Trash2, Play, Star, AlertCircle, GripVertical } from "lucide-react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { Skeleton } from "@/components/ui/skeleton";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Badge } from "@/components/ui/badge";
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

// Available OVOS Solver Plugins from CONFIGURATION_REPORT.md
const SOLVER_PLUGINS = [
  { id: "ovos-solver-wikipedia-plugin", name: "Wikipedia", description: "Wikipedia knowledge", offline: false },
  { id: "ovos-solver-ddg-plugin", name: "DuckDuckGo", description: "Web search", offline: false },
  { id: "ovos-solver-plugin-wolfram-alpha", name: "Wolfram Alpha", description: "Math/science", offline: false },
  { id: "ovos-solver-wordnet-plugin", name: "WordNet", description: "Dictionary", offline: true },
  { id: "ovos-solver-rivescript-plugin", name: "RiveScript", description: "Scripted responses", offline: true },
  { id: "ovos-solver-openai-plugin", name: "OpenAI GPT", description: "OpenAI LLM", offline: false },
  { id: "ovos-solver-groq-plugin", name: "Groq LLM", description: "Groq LLM", offline: false },
];

// Kokoro voices
const VOICES = [
  { id: "am_onyx", name: "Onyx (Male, US)" },
  { id: "am_adam", name: "Adam (Male, US)" },
  { id: "af_sarah", name: "Sarah (Female, US)" },
  { id: "af_nicole", name: "Nicole (Female, US)" },
  { id: "bf_emma", name: "Emma (Female, UK)" },
  { id: "bm_george", name: "George (Male, UK)" },
];

interface Persona {
  id: string;
  name: string;
  description: string;
  system_prompt: string;
  voice: string;
  solvers: string[];
  is_default: boolean;
  usage_count: number;
  created_at: string;
}

interface PersonaFormData {
  name: string;
  description: string;
  system_prompt: string;
  voice: string;
  solvers: string[];
}

// API functions
const personaApi = {
  list: () => apiRequest<Persona[]>("/api/v1/personas"),
  create: (data: PersonaFormData) =>
    apiRequest<Persona>("/api/v1/personas", {
      method: "POST",
      body: JSON.stringify(data),
    }),
  update: (id: string, data: Partial<PersonaFormData>) =>
    apiRequest<Persona>(`/api/v1/personas/${id}`, {
      method: "PATCH",
      body: JSON.stringify(data),
    }),
  delete: (id: string) =>
    apiRequest<void>(`/api/v1/personas/${id}`, { method: "DELETE" }),
  setDefault: (id: string) =>
    apiRequest<Persona>(`/api/v1/personas/${id}/default`, { method: "POST" }),
  test: (id: string, message: string) =>
    apiRequest<{ response: string }>(`/api/v1/personas/${id}/test`, {
      method: "POST",
      body: JSON.stringify({ message }),
    }),
};

const defaultFormData: PersonaFormData = {
  name: "",
  description: "",
  system_prompt: "You are a helpful voice assistant.",
  voice: "am_onyx",
  solvers: [],
};

export default function PersonasPage() {
  const { toast } = useToast();
  const queryClient = useQueryClient();
  const [isDialogOpen, setIsDialogOpen] = useState(false);
  const [editingPersona, setEditingPersona] = useState<Persona | null>(null);
  const [formData, setFormData] = useState<PersonaFormData>(defaultFormData);
  const [testMessage, setTestMessage] = useState("Hello, how can you help me?");
  const [testResponse, setTestResponse] = useState<string | null>(null);
  const [isTesting, setIsTesting] = useState(false);
  const [testingPersonaId, setTestingPersonaId] = useState<string | null>(null);

  const { data: personas, isLoading, error } = useQuery({
    queryKey: ["personas"],
    queryFn: personaApi.list,
  });

  const createMutation = useMutation({
    mutationFn: personaApi.create,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["personas"] });
      setIsDialogOpen(false);
      setFormData(defaultFormData);
      toast({ title: "Persona created" });
    },
    onError: () => {
      toast({ title: "Failed to create persona", variant: "destructive" });
    },
  });

  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: string; data: Partial<PersonaFormData> }) =>
      personaApi.update(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["personas"] });
      setIsDialogOpen(false);
      setEditingPersona(null);
      setFormData(defaultFormData);
      toast({ title: "Persona updated" });
    },
    onError: () => {
      toast({ title: "Failed to update persona", variant: "destructive" });
    },
  });

  const deleteMutation = useMutation({
    mutationFn: personaApi.delete,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["personas"] });
      toast({ title: "Persona deleted" });
    },
    onError: () => {
      toast({ title: "Failed to delete persona", variant: "destructive" });
    },
  });

  const setDefaultMutation = useMutation({
    mutationFn: personaApi.setDefault,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["personas"] });
      toast({ title: "Default persona updated" });
    },
    onError: () => {
      toast({ title: "Failed to set default", variant: "destructive" });
    },
  });

  const handleOpenCreate = () => {
    setEditingPersona(null);
    setFormData(defaultFormData);
    setIsDialogOpen(true);
  };

  const handleOpenEdit = (persona: Persona) => {
    setEditingPersona(persona);
    setFormData({
      name: persona.name,
      description: persona.description,
      system_prompt: persona.system_prompt,
      voice: persona.voice,
      solvers: persona.solvers,
    });
    setIsDialogOpen(true);
  };

  const handleSubmit = () => {
    if (editingPersona) {
      updateMutation.mutate({ id: editingPersona.id, data: formData });
    } else {
      createMutation.mutate(formData);
    }
  };

  const handleTest = async (personaId: string) => {
    setIsTesting(true);
    setTestingPersonaId(personaId);
    setTestResponse(null);
    
    try {
      const result = await personaApi.test(personaId, testMessage);
      setTestResponse(result.response);
    } catch {
      toast({ title: "Test failed", variant: "destructive" });
    } finally {
      setIsTesting(false);
    }
  };

  const toggleSolver = (solverId: string) => {
    const newSolvers = formData.solvers.includes(solverId)
      ? formData.solvers.filter((s) => s !== solverId)
      : [...formData.solvers, solverId];
    setFormData({ ...formData, solvers: newSolvers });
  };

  if (isLoading) {
    return (
      <DashboardLayout title="Personas" description="Manage AI personas">
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
      <DashboardLayout title="Personas" description="Manage AI personas">
        <Card>
          <CardContent className="py-8 text-center">
            <AlertCircle className="mx-auto h-12 w-12 text-muted-foreground mb-4" />
            <p className="text-muted-foreground">Unable to load personas</p>
          </CardContent>
        </Card>
      </DashboardLayout>
    );
  }

  return (
    <DashboardLayout title="Personas" description="Create and manage AI personas for your voice assistant">
      <div className="space-y-6">
        {/* Header with Create Button */}
        <div className="flex justify-end">
          <Button onClick={handleOpenCreate}>
            <Plus className="mr-2 h-4 w-4" />
            Create Persona
          </Button>
        </div>

        {/* Personas List */}
        {personas && personas.length === 0 ? (
          <Card>
            <CardContent className="py-12 text-center">
              <Bot className="mx-auto h-12 w-12 text-muted-foreground mb-4" />
              <h3 className="text-lg font-medium mb-2">No personas yet</h3>
              <p className="text-muted-foreground mb-4">
                Create your first persona to customize your voice assistant
              </p>
              <Button onClick={handleOpenCreate}>
                <Plus className="mr-2 h-4 w-4" />
                Create Persona
              </Button>
            </CardContent>
          </Card>
        ) : (
          <div className="grid gap-4">
            {personas?.map((persona) => (
              <Card key={persona.id}>
                <CardHeader>
                  <div className="flex items-start justify-between">
                    <div className="flex items-center gap-3">
                      <Bot className="h-8 w-8 text-primary" />
                      <div>
                        <CardTitle className="flex items-center gap-2">
                          {persona.name}
                          {persona.is_default && (
                            <Badge variant="secondary">
                              <Star className="mr-1 h-3 w-3" />
                              Default
                            </Badge>
                          )}
                        </CardTitle>
                        <CardDescription>{persona.description}</CardDescription>
                      </div>
                    </div>
                    <div className="flex gap-2">
                      {!persona.is_default && (
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => setDefaultMutation.mutate(persona.id)}
                        >
                          <Star className="h-4 w-4" />
                        </Button>
                      )}
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => handleOpenEdit(persona)}
                      >
                        <Edit className="h-4 w-4" />
                      </Button>
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => {
                          if (confirm("Delete this persona?")) {
                            deleteMutation.mutate(persona.id);
                          }
                        }}
                        disabled={persona.is_default}
                      >
                        <Trash2 className="h-4 w-4" />
                      </Button>
                    </div>
                  </div>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="grid gap-4 md:grid-cols-3 text-sm">
                    <div>
                      <span className="text-muted-foreground">Voice:</span>{" "}
                      {VOICES.find((v) => v.id === persona.voice)?.name || persona.voice}
                    </div>
                    <div>
                      <span className="text-muted-foreground">Solvers:</span>{" "}
                      {persona.solvers.length || "None"}
                    </div>
                    <div>
                      <span className="text-muted-foreground">Usage:</span>{" "}
                      {persona.usage_count} sessions
                    </div>
                  </div>

                  {/* Test Section */}
                  <div className="border-t pt-4">
                    <div className="flex gap-2">
                      <Input
                        value={testingPersonaId === persona.id ? testMessage : "Hello, how can you help me?"}
                        onChange={(e) => {
                          setTestingPersonaId(persona.id);
                          setTestMessage(e.target.value);
                        }}
                        placeholder="Test message..."
                        className="flex-1"
                      />
                      <Button
                        variant="outline"
                        onClick={() => handleTest(persona.id)}
                        disabled={isTesting && testingPersonaId === persona.id}
                      >
                        <Play className="mr-2 h-4 w-4" />
                        {isTesting && testingPersonaId === persona.id ? "Testing..." : "Test"}
                      </Button>
                    </div>
                    {testResponse && testingPersonaId === persona.id && (
                      <div className="mt-2 rounded-md bg-muted p-3 text-sm">
                        {testResponse}
                      </div>
                    )}
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        )}

        {/* Create/Edit Dialog */}
        <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
          <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
            <DialogHeader>
              <DialogTitle>
                {editingPersona ? "Edit Persona" : "Create Persona"}
              </DialogTitle>
              <DialogDescription>
                Configure the personality and capabilities of your AI assistant
              </DialogDescription>
            </DialogHeader>

            <div className="space-y-4 py-4">
              <div className="grid gap-4 md:grid-cols-2">
                <div className="space-y-2">
                  <Label>Name</Label>
                  <Input
                    value={formData.name}
                    onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                    placeholder="e.g., Customer Support"
                  />
                </div>
                <div className="space-y-2">
                  <Label>Voice</Label>
                  <Select
                    value={formData.voice}
                    onValueChange={(value) => setFormData({ ...formData, voice: value })}
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      {VOICES.map((voice) => (
                        <SelectItem key={voice.id} value={voice.id}>
                          {voice.name}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
              </div>

              <div className="space-y-2">
                <Label>Description</Label>
                <Input
                  value={formData.description}
                  onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                  placeholder="Brief description of this persona"
                />
              </div>

              <div className="space-y-2">
                <Label>System Prompt</Label>
                <Textarea
                  value={formData.system_prompt}
                  onChange={(e) => setFormData({ ...formData, system_prompt: e.target.value })}
                  placeholder="Instructions that define the assistant's behavior..."
                  rows={4}
                />
              </div>

              <div className="space-y-2">
                <Label>Solver Plugins</Label>
                <p className="text-sm text-muted-foreground mb-2">
                  Select knowledge sources for this persona (drag to reorder)
                </p>
                <div className="grid gap-2">
                  {SOLVER_PLUGINS.map((solver) => (
                    <div
                      key={solver.id}
                      className={`flex items-center gap-3 p-3 rounded-md border cursor-pointer transition-colors ${
                        formData.solvers.includes(solver.id)
                          ? "border-primary bg-primary/5"
                          : "border-border hover:border-primary/50"
                      }`}
                      onClick={() => toggleSolver(solver.id)}
                    >
                      <GripVertical className="h-4 w-4 text-muted-foreground" />
                      <div className="flex-1">
                        <div className="font-medium">{solver.name}</div>
                        <div className="text-sm text-muted-foreground">{solver.description}</div>
                      </div>
                      {solver.offline && (
                        <Badge variant="outline">Offline</Badge>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            </div>

            <DialogFooter>
              <Button variant="outline" onClick={() => setIsDialogOpen(false)}>
                Cancel
              </Button>
              <Button
                onClick={handleSubmit}
                disabled={!formData.name || createMutation.isPending || updateMutation.isPending}
              >
                {createMutation.isPending || updateMutation.isPending
                  ? "Saving..."
                  : editingPersona
                  ? "Update"
                  : "Create"}
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>
    </DashboardLayout>
  );
}
