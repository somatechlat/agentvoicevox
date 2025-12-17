"use client";

/**
 * LLM Worker Configuration Page
 * Settings: provider, api_key, model, temperature, max_tokens, circuit_breaker
 */

import { useState, useEffect } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Brain, Save, RefreshCw, AlertCircle, CheckCircle, Play, Eye, EyeOff } from "lucide-react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
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
import { systemApi } from "@/lib/api";

interface LLMConfig {
  default_provider: string;
  groq_api_key: string;
  openai_api_key: string;
  ollama_base_url: string;
  default_model: string;
  temperature: number;
  max_tokens: number;
  top_p: number;
  frequency_penalty: number;
  presence_penalty: number;
  circuit_breaker_threshold: number;
  circuit_breaker_timeout: number;
  retry_attempts: number;
  timeout: number;
}

const providers = [
  { value: "groq", label: "Groq", description: "Fast inference with Llama models" },
  { value: "openai", label: "OpenAI", description: "GPT-4 and GPT-3.5 models" },
  { value: "ollama", label: "Ollama", description: "Self-hosted local models" },
];

const modelsByProvider: Record<string, { value: string; label: string }[]> = {
  groq: [
    { value: "llama-3.1-70b-versatile", label: "Llama 3.1 70B Versatile" },
    { value: "llama-3.1-8b-instant", label: "Llama 3.1 8B Instant" },
    { value: "mixtral-8x7b-32768", label: "Mixtral 8x7B" },
    { value: "gemma2-9b-it", label: "Gemma 2 9B" },
  ],
  openai: [
    { value: "gpt-4o", label: "GPT-4o" },
    { value: "gpt-4o-mini", label: "GPT-4o Mini" },
    { value: "gpt-4-turbo", label: "GPT-4 Turbo" },
    { value: "gpt-3.5-turbo", label: "GPT-3.5 Turbo" },
  ],
  ollama: [
    { value: "llama3", label: "Llama 3" },
    { value: "mistral", label: "Mistral" },
    { value: "codellama", label: "Code Llama" },
    { value: "phi3", label: "Phi-3" },
  ],
};

const defaultConfig: LLMConfig = {
  default_provider: "groq",
  groq_api_key: "",
  openai_api_key: "",
  ollama_base_url: "http://ollama:11434",
  default_model: "llama-3.1-70b-versatile",
  temperature: 0.7,
  max_tokens: 1024,
  top_p: 1.0,
  frequency_penalty: 0.0,
  presence_penalty: 0.0,
  circuit_breaker_threshold: 5,
  circuit_breaker_timeout: 30,
  retry_attempts: 3,
  timeout: 30,
};

export default function LLMConfigPage() {
  const queryClient = useQueryClient();
  const [config, setConfig] = useState<LLMConfig>(defaultConfig);
  const [hasChanges, setHasChanges] = useState(false);
  const [showApiKey, setShowApiKey] = useState(false);
  const [testPrompt, setTestPrompt] = useState("Explain quantum computing in one sentence.");

  const { data: health } = useQuery({
    queryKey: ["llm-health"],
    queryFn: () => systemApi.getHealth(),
    refetchInterval: 30000,
  });

  const { data: savedConfig, isLoading } = useQuery({
    queryKey: ["llm-config"],
    queryFn: async () => {
      const response = await systemApi.getConfig<LLMConfig>("llm");
      return response;
    },
  });

  useEffect(() => {
    if (savedConfig) {
      setConfig(savedConfig);
    }
  }, [savedConfig]);

  const { data: stats } = useQuery({
    queryKey: ["llm-stats"],
    queryFn: () => systemApi.getWorkerStats().then((s) => s?.llm),
    refetchInterval: 10000,
  });

  const saveMutation = useMutation({
    mutationFn: (newConfig: LLMConfig) => systemApi.updateConfig("llm", newConfig),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["llm-config"] });
      setHasChanges(false);
    },
  });

  const testMutation = useMutation({
    mutationFn: () => systemApi.testLLM(testPrompt),
  });

  const updateConfig = <K extends keyof LLMConfig>(key: K, value: LLMConfig[K]) => {
    setConfig((prev) => ({ ...prev, [key]: value }));
    setHasChanges(true);
  };

  const isHealthy = health?.services?.some(
    (s: { name: string; status: string }) => 
      s.name.toLowerCase().includes("llm") && s.status === "healthy"
  );

  const currentApiKeyField = config.default_provider === "groq" 
    ? "groq_api_key" 
    : config.default_provider === "openai" 
      ? "openai_api_key" 
      : null;

  const availableModels = modelsByProvider[config.default_provider] || [];

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold flex items-center gap-2">
            <Brain className="h-6 w-6" />
            LLM Worker Configuration
          </h1>
          <p className="text-muted-foreground">
            Configure language model provider and generation settings
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
              <CardDescription>Requests/min</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{stats.requests_per_min || 0}</div>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="pb-2">
              <CardDescription>Tokens/min</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{stats.tokens_per_min?.toLocaleString() || 0}</div>
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
          {/* Provider Selection */}
          <Card>
            <CardHeader>
              <CardTitle>Provider</CardTitle>
              <CardDescription>
                Select LLM provider and configure API access
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="flex gap-2">
                {providers.map((provider) => (
                  <button
                    key={provider.value}
                    onClick={() => {
                      updateConfig("default_provider", provider.value);
                      // Reset model when provider changes
                      const firstModel = modelsByProvider[provider.value]?.[0]?.value;
                      if (firstModel) updateConfig("default_model", firstModel);
                    }}
                    className={`flex-1 rounded-lg border p-4 text-center transition-colors ${
                      config.default_provider === provider.value
                        ? "border-primary bg-primary/10"
                        : "border-border hover:bg-accent"
                    }`}
                  >
                    <div className="font-medium">{provider.label}</div>
                    <div className="text-xs text-muted-foreground">{provider.description}</div>
                  </button>
                ))}
              </div>

              <Separator />

              {currentApiKeyField && (
                <div className="space-y-2">
                  <Label>API Key</Label>
                  <div className="flex gap-2">
                    <div className="relative flex-1">
                      <Input
                        type={showApiKey ? "text" : "password"}
                        value={config[currentApiKeyField]}
                        onChange={(e) => updateConfig(currentApiKeyField, e.target.value)}
                        placeholder={`Enter ${config.default_provider} API key...`}
                      />
                      <Button
                        type="button"
                        variant="ghost"
                        size="icon"
                        className="absolute right-0 top-0 h-full"
                        onClick={() => setShowApiKey(!showApiKey)}
                      >
                        {showApiKey ? (
                          <EyeOff className="h-4 w-4" />
                        ) : (
                          <Eye className="h-4 w-4" />
                        )}
                      </Button>
                    </div>
                    <Button variant="outline">Test</Button>
                  </div>
                </div>
              )}

              {config.default_provider === "ollama" && (
                <div className="space-y-2">
                  <Label>Ollama Base URL</Label>
                  <Input
                    value={config.ollama_base_url}
                    onChange={(e) => updateConfig("ollama_base_url", e.target.value)}
                    placeholder="http://ollama:11434"
                  />
                </div>
              )}

              <div className="space-y-2">
                <Label>Model</Label>
                <Select
                  value={config.default_model}
                  onValueChange={(v) => updateConfig("default_model", v)}
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {availableModels.map((model) => (
                      <SelectItem key={model.value} value={model.value}>
                        {model.label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            </CardContent>
          </Card>

          {/* Generation Parameters */}
          <Card>
            <CardHeader>
              <CardTitle>Generation Parameters</CardTitle>
              <CardDescription>
                Fine-tune model output behavior
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <Label>Temperature</Label>
                  <span className="text-sm font-mono">{config.temperature}</span>
                </div>
                <Slider
                  min={0}
                  max={2}
                  step={0.1}
                  value={[config.temperature]}
                  onValueChange={(values: number[]) => updateConfig("temperature", values[0])}
                />
                <div className="flex justify-between text-xs text-muted-foreground">
                  <span>Deterministic</span>
                  <span>Creative</span>
                </div>
              </div>

              <div className="space-y-2">
                <Label>Max Tokens</Label>
                <Input
                  type="number"
                  min={256}
                  max={4096}
                  value={config.max_tokens}
                  onChange={(e) => updateConfig("max_tokens", parseInt(e.target.value, 10))}
                />
              </div>

              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <Label>Top P (Nucleus Sampling)</Label>
                  <span className="text-sm font-mono">{config.top_p}</span>
                </div>
                <Slider
                  min={0}
                  max={1}
                  step={0.05}
                  value={[config.top_p]}
                  onValueChange={(values: number[]) => updateConfig("top_p", values[0])}
                />
              </div>

              <div className="grid gap-4 sm:grid-cols-2">
                <div className="space-y-3">
                  <div className="flex items-center justify-between">
                    <Label>Frequency Penalty</Label>
                    <span className="text-sm font-mono">{config.frequency_penalty}</span>
                  </div>
                  <Slider
                    min={-2}
                    max={2}
                    step={0.1}
                    value={[config.frequency_penalty]}
                    onValueChange={(values: number[]) => updateConfig("frequency_penalty", values[0])}
                  />
                </div>
                <div className="space-y-3">
                  <div className="flex items-center justify-between">
                    <Label>Presence Penalty</Label>
                    <span className="text-sm font-mono">{config.presence_penalty}</span>
                  </div>
                  <Slider
                    min={-2}
                    max={2}
                    step={0.1}
                    value={[config.presence_penalty]}
                    onValueChange={(values: number[]) => updateConfig("presence_penalty", values[0])}
                  />
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Reliability Settings */}
          <Card className="lg:col-span-2">
            <CardHeader>
              <CardTitle>Reliability</CardTitle>
              <CardDescription>
                Configure circuit breaker and retry behavior
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid gap-6 sm:grid-cols-4">
                <div className="space-y-2">
                  <Label>Circuit Breaker Threshold</Label>
                  <Input
                    type="number"
                    min={1}
                    max={20}
                    value={config.circuit_breaker_threshold}
                    onChange={(e) => updateConfig("circuit_breaker_threshold", parseInt(e.target.value, 10))}
                  />
                  <p className="text-xs text-muted-foreground">Failures before opening</p>
                </div>
                <div className="space-y-2">
                  <Label>Circuit Breaker Timeout (s)</Label>
                  <Input
                    type="number"
                    min={5}
                    max={300}
                    value={config.circuit_breaker_timeout}
                    onChange={(e) => updateConfig("circuit_breaker_timeout", parseInt(e.target.value, 10))}
                  />
                  <p className="text-xs text-muted-foreground">Recovery wait time</p>
                </div>
                <div className="space-y-2">
                  <Label>Retry Attempts</Label>
                  <Input
                    type="number"
                    min={0}
                    max={10}
                    value={config.retry_attempts}
                    onChange={(e) => updateConfig("retry_attempts", parseInt(e.target.value, 10))}
                  />
                  <p className="text-xs text-muted-foreground">With exponential backoff</p>
                </div>
                <div className="space-y-2">
                  <Label>Request Timeout (s)</Label>
                  <Input
                    type="number"
                    min={5}
                    max={120}
                    value={config.timeout}
                    onChange={(e) => updateConfig("timeout", parseInt(e.target.value, 10))}
                  />
                  <p className="text-xs text-muted-foreground">Per-request timeout</p>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Test Section */}
      <Card>
        <CardHeader>
          <CardTitle>Test Prompt</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <Textarea
            value={testPrompt}
            onChange={(e) => setTestPrompt(e.target.value)}
            placeholder="Enter a test prompt..."
            rows={2}
          />
          <div className="flex items-center justify-between">
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
              Test Prompt
            </Button>
            {testMutation.data && (
              <div className="rounded-lg bg-muted p-3 text-sm">
                {testMutation.data}
              </div>
            )}
          </div>
        </CardContent>
      </Card>

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
