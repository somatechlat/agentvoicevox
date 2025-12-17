"use client";

/**
 * LLM Configuration Page
 * Implements Requirements B11.1-B11.6: LLM settings, provider selection, BYOK
 */

import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Brain, Save, AlertCircle, Send, Eye, EyeOff } from "lucide-react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { Skeleton } from "@/components/ui/skeleton";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
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

// LLM Providers and Models from CONFIGURATION_REPORT.md
const LLM_PROVIDERS = [
  {
    id: "groq",
    name: "Groq",
    models: [
      { id: "llama-3.1-70b-versatile", name: "Llama 3.1 70B Versatile" },
      { id: "llama-3.1-8b-instant", name: "Llama 3.1 8B Instant" },
      { id: "mixtral-8x7b-32768", name: "Mixtral 8x7B" },
      { id: "gemma2-9b-it", name: "Gemma 2 9B" },
    ],
  },
  {
    id: "openai",
    name: "OpenAI",
    models: [
      { id: "gpt-4o", name: "GPT-4o" },
      { id: "gpt-4o-mini", name: "GPT-4o Mini" },
      { id: "gpt-4-turbo", name: "GPT-4 Turbo" },
      { id: "gpt-3.5-turbo", name: "GPT-3.5 Turbo" },
    ],
  },
  {
    id: "ollama",
    name: "Ollama (Self-hosted)",
    models: [
      { id: "llama3.1", name: "Llama 3.1" },
      { id: "mistral", name: "Mistral" },
      { id: "codellama", name: "Code Llama" },
    ],
  },
];

interface LLMConfig {
  provider: string;
  model: string;
  temperature: number;
  max_tokens: number;
  openai_api_key?: string;
  groq_api_key?: string;
  ollama_base_url?: string;
}

// API functions
const llmApi = {
  getConfig: () => apiRequest<LLMConfig>("/api/v1/llm/config"),
  updateConfig: (data: Partial<LLMConfig>) =>
    apiRequest<LLMConfig>("/api/v1/llm/config", {
      method: "PATCH",
      body: JSON.stringify(data),
    }),
  testPrompt: (prompt: string) =>
    apiRequest<{ response: string }>("/api/v1/llm/test", {
      method: "POST",
      body: JSON.stringify({ prompt }),
    }),
};

export default function LLMConfigPage() {
  const { toast } = useToast();
  const queryClient = useQueryClient();
  const [localConfig, setLocalConfig] = useState<Partial<LLMConfig>>({});
  const [testPrompt, setTestPrompt] = useState("Hello, how are you?");
  const [testResponse, setTestResponse] = useState<string | null>(null);
  const [isTesting, setIsTesting] = useState(false);
  const [showApiKey, setShowApiKey] = useState(false);

  const { data: config, isLoading, error } = useQuery({
    queryKey: ["llm-config"],
    queryFn: llmApi.getConfig,
  });

  const currentConfig = { ...config, ...localConfig };
  const selectedProvider = LLM_PROVIDERS.find((p) => p.id === currentConfig.provider) || LLM_PROVIDERS[0];

  const updateMutation = useMutation({
    mutationFn: (data: Partial<LLMConfig>) => llmApi.updateConfig(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["llm-config"] });
      setLocalConfig({});
      toast({ title: "LLM configuration saved" });
    },
    onError: () => {
      toast({ title: "Failed to save configuration", variant: "destructive" });
    },
  });

  const handleProviderChange = (provider: string) => {
    const newProvider = LLM_PROVIDERS.find((p) => p.id === provider);
    setLocalConfig({
      ...localConfig,
      provider,
      model: newProvider?.models[0]?.id || "",
    });
  };

  const handleSave = () => {
    updateMutation.mutate(localConfig);
  };

  const handleTestPrompt = async () => {
    if (!testPrompt.trim()) return;
    
    setIsTesting(true);
    setTestResponse(null);
    
    try {
      const result = await llmApi.testPrompt(testPrompt);
      setTestResponse(result.response);
    } catch {
      toast({ title: "Test failed", variant: "destructive" });
    } finally {
      setIsTesting(false);
    }
  };

  if (isLoading) {
    return (
      <DashboardLayout title="LLM Configuration" description="Configure language model settings">
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
      <DashboardLayout title="LLM Configuration" description="Configure language model settings">
        <Card>
          <CardContent className="py-8 text-center">
            <AlertCircle className="mx-auto h-12 w-12 text-muted-foreground mb-4" />
            <p className="text-muted-foreground">Unable to load LLM configuration</p>
          </CardContent>
        </Card>
      </DashboardLayout>
    );
  }

  const hasChanges = Object.keys(localConfig).length > 0;

  return (
    <DashboardLayout title="LLM Configuration" description="Configure language model settings for your organization">
      <div className="space-y-6">
        {/* Provider Selection */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Brain className="h-5 w-5" />
              LLM Provider
            </CardTitle>
            <CardDescription>
              Select the AI provider and model for your voice assistant
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid gap-4 md:grid-cols-2">
              <div className="space-y-2">
                <Label>Provider</Label>
                <Select
                  value={currentConfig.provider || "groq"}
                  onValueChange={handleProviderChange}
                >
                  <SelectTrigger>
                    <SelectValue placeholder="Select provider" />
                  </SelectTrigger>
                  <SelectContent>
                    {LLM_PROVIDERS.map((provider) => (
                      <SelectItem key={provider.id} value={provider.id}>
                        {provider.name}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              <div className="space-y-2">
                <Label>Model</Label>
                <Select
                  value={currentConfig.model || selectedProvider.models[0]?.id}
                  onValueChange={(value) => setLocalConfig({ ...localConfig, model: value })}
                >
                  <SelectTrigger>
                    <SelectValue placeholder="Select model" />
                  </SelectTrigger>
                  <SelectContent>
                    {selectedProvider.models.map((model) => (
                      <SelectItem key={model.id} value={model.id}>
                        {model.name}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Model Parameters */}
        <Card>
          <CardHeader>
            <CardTitle>Model Parameters</CardTitle>
            <CardDescription>
              Fine-tune the model behavior for your use case
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <Label>Temperature: {(currentConfig.temperature ?? 0.7).toFixed(1)}</Label>
                <span className="text-sm text-muted-foreground">
                  {(currentConfig.temperature ?? 0.7) < 0.5 ? "More focused" : (currentConfig.temperature ?? 0.7) > 1.0 ? "More creative" : "Balanced"}
                </span>
              </div>
              <Input
                type="range"
                value={currentConfig.temperature ?? 0.7}
                onChange={(e) => setLocalConfig({ ...localConfig, temperature: parseFloat(e.target.value) })}
                min={0}
                max={2}
                step={0.1}
                className="w-full"
              />
              <div className="flex justify-between text-xs text-muted-foreground">
                <span>0.0 (Deterministic)</span>
                <span>1.0 (Default)</span>
                <span>2.0 (Creative)</span>
              </div>
            </div>

            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <Label>Max Output Tokens: {currentConfig.max_tokens ?? 1024}</Label>
              </div>
              <Input
                type="range"
                value={currentConfig.max_tokens ?? 1024}
                onChange={(e) => setLocalConfig({ ...localConfig, max_tokens: parseInt(e.target.value) })}
                min={256}
                max={4096}
                step={256}
                className="w-full"
              />
              <div className="flex justify-between text-xs text-muted-foreground">
                <span>256 (Short)</span>
                <span>1024 (Default)</span>
                <span>4096 (Long)</span>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* API Keys (BYOK) */}
        <Card>
          <CardHeader>
            <CardTitle>API Keys (Bring Your Own Key)</CardTitle>
            <CardDescription>
              Optionally provide your own API keys for OpenAI or Groq
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {currentConfig.provider === "openai" && (
              <div className="space-y-2">
                <Label>OpenAI API Key</Label>
                <div className="flex gap-2">
                  <Input
                    type={showApiKey ? "text" : "password"}
                    value={localConfig.openai_api_key ?? ""}
                    onChange={(e) => setLocalConfig({ ...localConfig, openai_api_key: e.target.value })}
                    placeholder="sk-..."
                    className="flex-1"
                  />
                  <Button
                    variant="outline"
                    size="icon"
                    onClick={() => setShowApiKey(!showApiKey)}
                  >
                    {showApiKey ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                  </Button>
                </div>
              </div>
            )}

            {currentConfig.provider === "groq" && (
              <div className="space-y-2">
                <Label>Groq API Key</Label>
                <div className="flex gap-2">
                  <Input
                    type={showApiKey ? "text" : "password"}
                    value={localConfig.groq_api_key ?? ""}
                    onChange={(e) => setLocalConfig({ ...localConfig, groq_api_key: e.target.value })}
                    placeholder="gsk_..."
                    className="flex-1"
                  />
                  <Button
                    variant="outline"
                    size="icon"
                    onClick={() => setShowApiKey(!showApiKey)}
                  >
                    {showApiKey ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                  </Button>
                </div>
              </div>
            )}

            {currentConfig.provider === "ollama" && (
              <div className="space-y-2">
                <Label>Ollama Base URL</Label>
                <Input
                  type="text"
                  value={localConfig.ollama_base_url ?? "http://localhost:11434"}
                  onChange={(e) => setLocalConfig({ ...localConfig, ollama_base_url: e.target.value })}
                  placeholder="http://localhost:11434"
                />
              </div>
            )}
          </CardContent>
        </Card>

        {/* Test LLM */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Send className="h-5 w-5" />
              Test Configuration
            </CardTitle>
            <CardDescription>
              Send a test prompt to verify your LLM configuration
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <Label>Test Prompt</Label>
              <Textarea
                value={testPrompt}
                onChange={(e) => setTestPrompt(e.target.value)}
                placeholder="Enter a test prompt..."
                rows={3}
              />
            </div>
            <Button
              onClick={handleTestPrompt}
              disabled={!testPrompt.trim() || isTesting}
            >
              {isTesting ? "Processing..." : "Send Test"}
            </Button>
            {testResponse && (
              <div className="rounded-md bg-muted p-4">
                <Label className="text-sm font-medium">Response:</Label>
                <p className="mt-1 text-sm whitespace-pre-wrap">{testResponse}</p>
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
