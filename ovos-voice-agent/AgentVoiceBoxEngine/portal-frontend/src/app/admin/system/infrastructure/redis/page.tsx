"use client";

/**
 * Redis Configuration Page
 * Settings: maxmemory, maxmemory_policy, appendonly, tcp_keepalive
 */

import { useState, useEffect } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { HardDrive, Save, RefreshCw, AlertCircle, CheckCircle, Info } from "lucide-react";
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
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import { systemApi } from "@/lib/api";

interface RedisConfig {
  maxmemory: string;
  maxmemory_policy: string;
  appendonly: boolean;
  tcp_keepalive: number;
}

const evictionPolicies = [
  { value: "volatile-lru", label: "Volatile LRU", description: "Remove least recently used keys with expiry" },
  { value: "allkeys-lru", label: "All Keys LRU", description: "Remove any least recently used key" },
  { value: "volatile-lfu", label: "Volatile LFU", description: "Remove least frequently used keys with expiry" },
  { value: "allkeys-lfu", label: "All Keys LFU", description: "Remove any least frequently used key" },
  { value: "volatile-random", label: "Volatile Random", description: "Remove random keys with expiry" },
  { value: "allkeys-random", label: "All Keys Random", description: "Remove any random key" },
  { value: "volatile-ttl", label: "Volatile TTL", description: "Remove keys with shortest TTL" },
  { value: "noeviction", label: "No Eviction", description: "Return errors when memory full" },
];

const defaultConfig: RedisConfig = {
  maxmemory: "400MB",
  maxmemory_policy: "volatile-lru",
  appendonly: true,
  tcp_keepalive: 60,
};

export default function RedisConfigPage() {
  const queryClient = useQueryClient();
  const [config, setConfig] = useState<RedisConfig>(defaultConfig);
  const [hasChanges, setHasChanges] = useState(false);

  const { data: health } = useQuery({
    queryKey: ["redis-health"],
    queryFn: () => systemApi.getHealth(),
    refetchInterval: 30000,
  });

  const { data: savedConfig, isLoading } = useQuery({
    queryKey: ["redis-config"],
    queryFn: async () => {
      const response = await systemApi.getConfig<RedisConfig>("redis");
      return response;
    },
  });

  useEffect(() => {
    if (savedConfig) {
      setConfig(savedConfig);
    }
  }, [savedConfig]);

  const { data: stats } = useQuery({
    queryKey: ["redis-stats"],
    queryFn: () => systemApi.getRedisStats(),
    refetchInterval: 10000,
  });

  const saveMutation = useMutation({
    mutationFn: (newConfig: RedisConfig) => systemApi.updateConfig("redis", newConfig),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["redis-config"] });
      setHasChanges(false);
    },
  });

  const updateConfig = <K extends keyof RedisConfig>(key: K, value: RedisConfig[K]) => {
    setConfig((prev) => ({ ...prev, [key]: value }));
    setHasChanges(true);
  };

  const parseMemoryValue = (value: string): number => {
    const match = value.match(/^(\d+)(MB|GB)$/i);
    if (!match) return 400;
    const num = parseInt(match[1], 10);
    return match[2].toUpperCase() === "GB" ? num * 1024 : num;
  };

  const formatMemoryValue = (mb: number): string => {
    return mb >= 1024 ? `${mb / 1024}GB` : `${mb}MB`;
  };

  const isHealthy = health?.services?.some(
    (s: { name: string; status: string }) => 
      s.name.toLowerCase().includes("redis") && s.status === "healthy"
  );

  const memoryUsedPercent = stats?.used_memory && stats?.maxmemory
    ? Math.round((stats.used_memory / stats.maxmemory) * 100)
    : 0;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold flex items-center gap-2">
            <HardDrive className="h-6 w-6" />
            Redis Configuration
          </h1>
          <p className="text-muted-foreground">
            Configure in-memory cache and session storage
          </p>
        </div>
        <Badge variant={isHealthy ? "default" : "destructive"}>
          {isHealthy ? (
            <CheckCircle className="mr-1 h-3 w-3" />
          ) : (
            <AlertCircle className="mr-1 h-3 w-3" />
          )}
          {isHealthy ? "Connected" : "Disconnected"}
        </Badge>
      </div>

      {/* Stats Cards */}
      {stats && (
        <div className="grid gap-4 md:grid-cols-4">
          <Card>
            <CardHeader className="pb-2">
              <CardDescription>Memory Used</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{stats.used_memory_human || "N/A"}</div>
              <div className="mt-2 h-2 rounded-full bg-secondary">
                <div
                  className={`h-full rounded-full ${
                    memoryUsedPercent > 90 ? "bg-destructive" : 
                    memoryUsedPercent > 70 ? "bg-warning" : "bg-primary"
                  }`}
                  style={{ width: `${memoryUsedPercent}%` }}
                />
              </div>
              <p className="mt-1 text-xs text-muted-foreground">{memoryUsedPercent}% of limit</p>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="pb-2">
              <CardDescription>Connected Clients</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{stats.connected_clients || 0}</div>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="pb-2">
              <CardDescription>Total Keys</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{stats.total_keys?.toLocaleString() || 0}</div>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="pb-2">
              <CardDescription>Hit Rate</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{stats.hit_rate || "N/A"}%</div>
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
          {/* Memory Settings */}
          <Card>
            <CardHeader>
              <CardTitle>Memory Settings</CardTitle>
              <CardDescription>
                Configure Redis memory limits and eviction behavior
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <Label htmlFor="maxmemory">Max Memory</Label>
                  <span className="text-sm font-mono text-muted-foreground">
                    {config.maxmemory}
                  </span>
                </div>
                <Slider
                  id="maxmemory"
                  min={100}
                  max={4096}
                  step={100}
                  value={[parseMemoryValue(config.maxmemory)]}
                  onValueChange={(values: number[]) => updateConfig("maxmemory", formatMemoryValue(values[0]))}
                />
                <p className="text-xs text-muted-foreground">
                  Maximum memory Redis can use before eviction starts
                </p>
              </div>

              <Separator />

              <div className="space-y-2">
                <div className="flex items-center gap-2">
                  <Label htmlFor="maxmemory_policy">Eviction Policy</Label>
                  <TooltipProvider>
                    <Tooltip>
                      <TooltipTrigger>
                        <Info className="h-4 w-4 text-muted-foreground" />
                      </TooltipTrigger>
                      <TooltipContent className="max-w-xs">
                        <p>Determines how Redis removes keys when memory limit is reached</p>
                      </TooltipContent>
                    </Tooltip>
                  </TooltipProvider>
                </div>
                <Select
                  value={config.maxmemory_policy}
                  onValueChange={(v) => updateConfig("maxmemory_policy", v)}
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {evictionPolicies.map((policy) => (
                      <SelectItem key={policy.value} value={policy.value}>
                        <div>
                          <div className="font-medium">{policy.label}</div>
                          <div className="text-xs text-muted-foreground">
                            {policy.description}
                          </div>
                        </div>
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            </CardContent>
          </Card>

          {/* Persistence & Connection */}
          <Card>
            <CardHeader>
              <CardTitle>Persistence & Connection</CardTitle>
              <CardDescription>
                Configure data persistence and connection settings
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="flex items-center justify-between">
                <div className="space-y-0.5">
                  <Label htmlFor="appendonly">Append Only File (AOF)</Label>
                  <p className="text-xs text-muted-foreground">
                    Enable persistent storage with AOF logging
                  </p>
                </div>
                <Switch
                  id="appendonly"
                  checked={config.appendonly}
                  onCheckedChange={(checked) => updateConfig("appendonly", checked)}
                />
              </div>

              <Separator />

              <div className="space-y-2">
                <Label htmlFor="tcp_keepalive">TCP Keepalive (seconds)</Label>
                <Input
                  id="tcp_keepalive"
                  type="number"
                  min={0}
                  max={300}
                  value={config.tcp_keepalive}
                  onChange={(e) => updateConfig("tcp_keepalive", parseInt(e.target.value, 10))}
                />
                <p className="text-xs text-muted-foreground">
                  Interval for TCP keepalive packets. 0 to disable.
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
