"use client";

/**
 * PostgreSQL Configuration Page
 * Settings: shared_buffers, effective_cache_size, work_mem, max_connections, pool_size
 */

import { useState, useEffect } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Database, Save, RefreshCw, AlertCircle, CheckCircle } from "lucide-react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";
import { Slider } from "@/components/ui/slider";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import { systemApi } from "@/lib/api";

interface PostgresConfig {
  shared_buffers: string;
  effective_cache_size: string;
  work_mem: string;
  maintenance_work_mem: string;
  max_connections: number;
  pool_size: number;
  max_overflow: number;
  echo_queries: boolean;
}

const defaultConfig: PostgresConfig = {
  shared_buffers: "128MB",
  effective_cache_size: "256MB",
  work_mem: "2MB",
  maintenance_work_mem: "32MB",
  max_connections: 100,
  pool_size: 5,
  max_overflow: 5,
  echo_queries: false,
};

export default function PostgresConfigPage() {
  const queryClient = useQueryClient();
  const [config, setConfig] = useState<PostgresConfig>(defaultConfig);
  const [hasChanges, setHasChanges] = useState(false);

  const { data: health } = useQuery({
    queryKey: ["postgres-health"],
    queryFn: () => systemApi.getHealth(),
    refetchInterval: 30000,
  });

  const { data: savedConfig, isLoading } = useQuery({
    queryKey: ["postgres-config"],
    queryFn: async () => {
      const response = await systemApi.getConfig<PostgresConfig>("postgres");
      return response;
    },
  });

  useEffect(() => {
    if (savedConfig) {
      setConfig(savedConfig);
    }
  }, [savedConfig]);

  const saveMutation = useMutation({
    mutationFn: (newConfig: PostgresConfig) => systemApi.updateConfig("postgres", newConfig),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["postgres-config"] });
      setHasChanges(false);
    },
  });

  const updateConfig = <K extends keyof PostgresConfig>(key: K, value: PostgresConfig[K]) => {
    setConfig((prev) => ({ ...prev, [key]: value }));
    setHasChanges(true);
  };

  const parseMemoryValue = (value: string): number => {
    const match = value.match(/^(\d+)(MB|GB)$/i);
    if (!match) return 128;
    const num = parseInt(match[1], 10);
    return match[2].toUpperCase() === "GB" ? num * 1024 : num;
  };

  const formatMemoryValue = (mb: number): string => {
    return mb >= 1024 ? `${mb / 1024}GB` : `${mb}MB`;
  };

  const isHealthy = health?.services?.some(
    (s: { name: string; status: string }) => 
      s.name.toLowerCase().includes("postgres") && s.status === "healthy"
  );

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold flex items-center gap-2">
            <Database className="h-6 w-6" />
            PostgreSQL Configuration
          </h1>
          <p className="text-muted-foreground">
            Configure database connection pool and memory settings
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Badge variant={isHealthy ? "default" : "destructive"}>
            {isHealthy ? (
              <CheckCircle className="mr-1 h-3 w-3" />
            ) : (
              <AlertCircle className="mr-1 h-3 w-3" />
            )}
            {isHealthy ? "Connected" : "Disconnected"}
          </Badge>
        </div>
      </div>

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
                Configure PostgreSQL memory allocation for optimal performance
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <Label htmlFor="shared_buffers">Shared Buffers</Label>
                  <span className="text-sm font-mono text-muted-foreground">
                    {config.shared_buffers}
                  </span>
                </div>
                <Slider
                  id="shared_buffers"
                  min={64}
                  max={2048}
                  step={64}
                  value={[parseMemoryValue(config.shared_buffers)]}
                  onValueChange={(values: number[]) => updateConfig("shared_buffers", formatMemoryValue(values[0]))}
                />
                <p className="text-xs text-muted-foreground">
                  Memory for caching data. Recommended: 25% of system RAM.
                </p>
              </div>

              <Separator />

              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <Label htmlFor="effective_cache_size">Effective Cache Size</Label>
                  <span className="text-sm font-mono text-muted-foreground">
                    {config.effective_cache_size}
                  </span>
                </div>
                <Slider
                  id="effective_cache_size"
                  min={128}
                  max={4096}
                  step={128}
                  value={[parseMemoryValue(config.effective_cache_size)]}
                  onValueChange={(values: number[]) => updateConfig("effective_cache_size", formatMemoryValue(values[0]))}
                />
                <p className="text-xs text-muted-foreground">
                  Planner estimate of available cache. Recommended: 50-75% of system RAM.
                </p>
              </div>

              <Separator />

              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <Label htmlFor="work_mem">Work Memory</Label>
                  <span className="text-sm font-mono text-muted-foreground">
                    {config.work_mem}
                  </span>
                </div>
                <Slider
                  id="work_mem"
                  min={1}
                  max={256}
                  step={1}
                  value={[parseMemoryValue(config.work_mem)]}
                  onValueChange={(values: number[]) => updateConfig("work_mem", formatMemoryValue(values[0]))}
                />
                <p className="text-xs text-muted-foreground">
                  Memory per operation (sorts, joins). Be careful with high values.
                </p>
              </div>

              <Separator />

              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <Label htmlFor="maintenance_work_mem">Maintenance Work Memory</Label>
                  <span className="text-sm font-mono text-muted-foreground">
                    {config.maintenance_work_mem}
                  </span>
                </div>
                <Slider
                  id="maintenance_work_mem"
                  min={16}
                  max={512}
                  step={16}
                  value={[parseMemoryValue(config.maintenance_work_mem)]}
                  onValueChange={(values: number[]) => updateConfig("maintenance_work_mem", formatMemoryValue(values[0]))}
                />
                <p className="text-xs text-muted-foreground">
                  Memory for VACUUM, CREATE INDEX, etc.
                </p>
              </div>
            </CardContent>
          </Card>

          {/* Connection Pool Settings */}
          <Card>
            <CardHeader>
              <CardTitle>Connection Pool</CardTitle>
              <CardDescription>
                Configure database connection pooling for SQLAlchemy
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="space-y-2">
                <Label htmlFor="max_connections">Max Connections</Label>
                <Input
                  id="max_connections"
                  type="number"
                  min={10}
                  max={500}
                  value={config.max_connections}
                  onChange={(e) => updateConfig("max_connections", parseInt(e.target.value, 10))}
                />
                <p className="text-xs text-muted-foreground">
                  Maximum database connections allowed (PostgreSQL setting)
                </p>
              </div>

              <Separator />

              <div className="space-y-2">
                <Label htmlFor="pool_size">Pool Size</Label>
                <Input
                  id="pool_size"
                  type="number"
                  min={1}
                  max={50}
                  value={config.pool_size}
                  onChange={(e) => updateConfig("pool_size", parseInt(e.target.value, 10))}
                />
                <p className="text-xs text-muted-foreground">
                  Number of connections to keep in the pool
                </p>
              </div>

              <Separator />

              <div className="space-y-2">
                <Label htmlFor="max_overflow">Max Overflow</Label>
                <Input
                  id="max_overflow"
                  type="number"
                  min={0}
                  max={50}
                  value={config.max_overflow}
                  onChange={(e) => updateConfig("max_overflow", parseInt(e.target.value, 10))}
                />
                <p className="text-xs text-muted-foreground">
                  Additional connections allowed beyond pool_size
                </p>
              </div>

              <Separator />

              <div className="flex items-center justify-between">
                <div className="space-y-0.5">
                  <Label htmlFor="echo_queries">Echo SQL Queries</Label>
                  <p className="text-xs text-muted-foreground">
                    Log all SQL queries (development only)
                  </p>
                </div>
                <Switch
                  id="echo_queries"
                  checked={config.echo_queries}
                  onCheckedChange={(checked) => updateConfig("echo_queries", checked)}
                />
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
