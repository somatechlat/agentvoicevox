"use client";

/**
 * Gateway Configuration Page
 * Settings: gunicorn workers, WebSocket, rate limiting
 */

import { useState, useEffect } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Network, Save, RefreshCw, AlertCircle, CheckCircle } from "lucide-react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";
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

interface GatewayConfig {
  gateway_id: string;
  gunicorn_workers: number;
  worker_class: string;
  worker_connections: number;
  timeout: number;
  keepalive: number;
  max_requests: number;
  graceful_timeout: number;
  ws_ping_interval: number;
  ws_ping_timeout: number;
  ws_max_message_size: number;
  ws_compression: boolean;
  rate_limit_enabled: boolean;
  rate_limit_requests: number;
  rate_limit_window: number;
  rate_limit_burst: number;
}

const workerClasses = [
  { value: "sync", label: "Sync", description: "Synchronous workers" },
  { value: "gevent", label: "Gevent", description: "Async with greenlets (recommended)" },
  { value: "eventlet", label: "Eventlet", description: "Async with eventlet" },
  { value: "uvicorn.workers.UvicornWorker", label: "Uvicorn", description: "ASGI worker" },
];

const defaultConfig: GatewayConfig = {
  gateway_id: "gateway-1",
  gunicorn_workers: 2,
  worker_class: "gevent",
  worker_connections: 1000,
  timeout: 30,
  keepalive: 2,
  max_requests: 1000,
  graceful_timeout: 30,
  ws_ping_interval: 25,
  ws_ping_timeout: 20,
  ws_max_message_size: 1048576,
  ws_compression: true,
  rate_limit_enabled: true,
  rate_limit_requests: 100,
  rate_limit_window: 60,
  rate_limit_burst: 20,
};

export default function GatewayConfigPage() {
  const queryClient = useQueryClient();
  const [config, setConfig] = useState<GatewayConfig>(defaultConfig);
  const [hasChanges, setHasChanges] = useState(false);

  const { data: health } = useQuery({
    queryKey: ["gateway-health"],
    queryFn: () => systemApi.getHealth(),
    refetchInterval: 30000,
  });

  const { data: savedConfig, isLoading } = useQuery({
    queryKey: ["gateway-config"],
    queryFn: async () => {
      const response = await systemApi.getConfig<GatewayConfig>("gateway");
      return response;
    },
  });

  useEffect(() => {
    if (savedConfig) {
      setConfig(savedConfig);
    }
  }, [savedConfig]);

  const saveMutation = useMutation({
    mutationFn: (newConfig: GatewayConfig) => systemApi.updateConfig("gateway", newConfig),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["gateway-config"] });
      setHasChanges(false);
    },
  });

  const updateConfig = <K extends keyof GatewayConfig>(key: K, value: GatewayConfig[K]) => {
    setConfig((prev) => ({ ...prev, [key]: value }));
    setHasChanges(true);
  };

  const isHealthy = health?.services?.some(
    (s: { name: string; status: string }) => 
      s.name.toLowerCase().includes("gateway") && s.status === "healthy"
  );

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold flex items-center gap-2">
            <Network className="h-6 w-6" />
            Gateway Configuration
          </h1>
          <p className="text-muted-foreground">
            Configure API gateway, WebSocket, and rate limiting settings
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

      {isLoading ? (
        <div className="flex items-center justify-center py-12">
          <RefreshCw className="h-8 w-8 animate-spin text-muted-foreground" />
        </div>
      ) : (
        <div className="grid gap-6 lg:grid-cols-2">
          {/* Gunicorn Settings */}
          <Card>
            <CardHeader>
              <CardTitle>Gunicorn Workers</CardTitle>
              <CardDescription>
                Configure worker processes and connections
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="space-y-2">
                <Label>Gateway ID</Label>
                <Input
                  value={config.gateway_id}
                  onChange={(e) => updateConfig("gateway_id", e.target.value)}
                />
              </div>

              <div className="grid gap-4 sm:grid-cols-2">
                <div className="space-y-2">
                  <Label>Workers</Label>
                  <Input
                    type="number"
                    min={1}
                    max={16}
                    value={config.gunicorn_workers}
                    onChange={(e) => updateConfig("gunicorn_workers", parseInt(e.target.value, 10))}
                  />
                  <p className="text-xs text-muted-foreground">Recommended: 2 × CPU cores + 1</p>
                </div>
                <div className="space-y-2">
                  <Label>Worker Class</Label>
                  <Select
                    value={config.worker_class}
                    onValueChange={(v) => updateConfig("worker_class", v)}
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      {workerClasses.map((wc) => (
                        <SelectItem key={wc.value} value={wc.value}>
                          {wc.label}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
              </div>

              <div className="grid gap-4 sm:grid-cols-2">
                <div className="space-y-2">
                  <Label>Worker Connections</Label>
                  <Input
                    type="number"
                    min={100}
                    max={10000}
                    value={config.worker_connections}
                    onChange={(e) => updateConfig("worker_connections", parseInt(e.target.value, 10))}
                  />
                </div>
                <div className="space-y-2">
                  <Label>Max Requests</Label>
                  <Input
                    type="number"
                    min={0}
                    max={10000}
                    value={config.max_requests}
                    onChange={(e) => updateConfig("max_requests", parseInt(e.target.value, 10))}
                  />
                  <p className="text-xs text-muted-foreground">0 = unlimited</p>
                </div>
              </div>

              <Separator />

              <div className="grid gap-4 sm:grid-cols-3">
                <div className="space-y-2">
                  <Label>Timeout (s)</Label>
                  <Input
                    type="number"
                    min={5}
                    max={300}
                    value={config.timeout}
                    onChange={(e) => updateConfig("timeout", parseInt(e.target.value, 10))}
                  />
                </div>
                <div className="space-y-2">
                  <Label>Keepalive (s)</Label>
                  <Input
                    type="number"
                    min={0}
                    max={60}
                    value={config.keepalive}
                    onChange={(e) => updateConfig("keepalive", parseInt(e.target.value, 10))}
                  />
                </div>
                <div className="space-y-2">
                  <Label>Graceful Timeout (s)</Label>
                  <Input
                    type="number"
                    min={5}
                    max={120}
                    value={config.graceful_timeout}
                    onChange={(e) => updateConfig("graceful_timeout", parseInt(e.target.value, 10))}
                  />
                </div>
              </div>
            </CardContent>
          </Card>

          {/* WebSocket Settings */}
          <Card>
            <CardHeader>
              <CardTitle>WebSocket Settings</CardTitle>
              <CardDescription>
                Configure WebSocket connection parameters
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="grid gap-4 sm:grid-cols-2">
                <div className="space-y-2">
                  <Label>Ping Interval (s)</Label>
                  <Input
                    type="number"
                    min={5}
                    max={60}
                    value={config.ws_ping_interval}
                    onChange={(e) => updateConfig("ws_ping_interval", parseInt(e.target.value, 10))}
                  />
                </div>
                <div className="space-y-2">
                  <Label>Ping Timeout (s)</Label>
                  <Input
                    type="number"
                    min={5}
                    max={60}
                    value={config.ws_ping_timeout}
                    onChange={(e) => updateConfig("ws_ping_timeout", parseInt(e.target.value, 10))}
                  />
                </div>
              </div>

              <div className="space-y-2">
                <Label>Max Message Size (bytes)</Label>
                <Input
                  type="number"
                  min={65536}
                  max={16777216}
                  step={65536}
                  value={config.ws_max_message_size}
                  onChange={(e) => updateConfig("ws_max_message_size", parseInt(e.target.value, 10))}
                />
                <p className="text-xs text-muted-foreground">
                  Current: {(config.ws_max_message_size / 1024 / 1024).toFixed(1)} MB
                </p>
              </div>

              <div className="flex items-center justify-between">
                <div className="space-y-0.5">
                  <Label>Enable Compression</Label>
                  <p className="text-xs text-muted-foreground">
                    Compress WebSocket messages (permessage-deflate)
                  </p>
                </div>
                <Switch
                  checked={config.ws_compression}
                  onCheckedChange={(checked) => updateConfig("ws_compression", checked)}
                />
              </div>
            </CardContent>
          </Card>

          {/* Rate Limiting */}
          <Card className="lg:col-span-2">
            <CardHeader>
              <CardTitle>Rate Limiting</CardTitle>
              <CardDescription>
                Configure API rate limiting to protect against abuse
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="flex items-center justify-between">
                <div className="space-y-0.5">
                  <Label>Enable Rate Limiting</Label>
                  <p className="text-xs text-muted-foreground">
                    Limit requests per client to prevent abuse
                  </p>
                </div>
                <Switch
                  checked={config.rate_limit_enabled}
                  onCheckedChange={(checked) => updateConfig("rate_limit_enabled", checked)}
                />
              </div>

              {config.rate_limit_enabled && (
                <>
                  <Separator />
                  <div className="grid gap-4 sm:grid-cols-3">
                    <div className="space-y-2">
                      <Label>Requests per Window</Label>
                      <Input
                        type="number"
                        min={10}
                        max={10000}
                        value={config.rate_limit_requests}
                        onChange={(e) => updateConfig("rate_limit_requests", parseInt(e.target.value, 10))}
                      />
                    </div>
                    <div className="space-y-2">
                      <Label>Window (seconds)</Label>
                      <Input
                        type="number"
                        min={1}
                        max={3600}
                        value={config.rate_limit_window}
                        onChange={(e) => updateConfig("rate_limit_window", parseInt(e.target.value, 10))}
                      />
                    </div>
                    <div className="space-y-2">
                      <Label>Burst Allowance</Label>
                      <Input
                        type="number"
                        min={0}
                        max={100}
                        value={config.rate_limit_burst}
                        onChange={(e) => updateConfig("rate_limit_burst", parseInt(e.target.value, 10))}
                      />
                    </div>
                  </div>
                  <p className="text-sm text-muted-foreground">
                    Allows {config.rate_limit_requests} requests per {config.rate_limit_window} seconds, 
                    with burst of {config.rate_limit_burst} additional requests
                  </p>
                </>
              )}
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
