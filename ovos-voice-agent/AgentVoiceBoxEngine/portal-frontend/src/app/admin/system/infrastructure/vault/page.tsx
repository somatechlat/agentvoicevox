"use client";

/**
 * Vault Configuration Page
 * Settings: storage_backend, api_addr, ui_enabled, seal_type
 */

import { useState, useEffect } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Lock, Save, RefreshCw, AlertCircle, CheckCircle, ShieldCheck, ShieldOff } from "lucide-react";
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

interface VaultConfig {
  storage_backend: string;
  api_addr: string;
  cluster_addr: string;
  ui_enabled: boolean;
  seal_type: string;
}

const storageBackends = [
  { value: "file", label: "File", description: "Local file storage (single node)" },
  { value: "consul", label: "Consul", description: "HashiCorp Consul (HA)" },
  { value: "raft", label: "Raft", description: "Integrated storage (HA)" },
  { value: "postgresql", label: "PostgreSQL", description: "PostgreSQL database" },
];

const sealTypes = [
  { value: "shamir", label: "Shamir", description: "Key shares for unsealing" },
  { value: "awskms", label: "AWS KMS", description: "Auto-unseal with AWS KMS" },
  { value: "gcpckms", label: "GCP Cloud KMS", description: "Auto-unseal with GCP" },
  { value: "azurekeyvault", label: "Azure Key Vault", description: "Auto-unseal with Azure" },
];

const defaultConfig: VaultConfig = {
  storage_backend: "file",
  api_addr: "http://vault:8200",
  cluster_addr: "",
  ui_enabled: true,
  seal_type: "shamir",
};

export default function VaultConfigPage() {
  const queryClient = useQueryClient();
  const [config, setConfig] = useState<VaultConfig>(defaultConfig);
  const [hasChanges, setHasChanges] = useState(false);

  const { data: health } = useQuery({
    queryKey: ["vault-health"],
    queryFn: () => systemApi.getHealth(),
    refetchInterval: 30000,
  });

  const { data: vaultStatus } = useQuery({
    queryKey: ["vault-status"],
    queryFn: () => systemApi.getVaultStatus(),
    refetchInterval: 10000,
  });

  const { data: savedConfig, isLoading } = useQuery({
    queryKey: ["vault-config"],
    queryFn: async () => {
      const response = await systemApi.getConfig<VaultConfig>("vault");
      return response;
    },
  });

  useEffect(() => {
    if (savedConfig) {
      setConfig(savedConfig);
    }
  }, [savedConfig]);

  const saveMutation = useMutation({
    mutationFn: (newConfig: VaultConfig) => systemApi.updateConfig("vault", newConfig),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["vault-config"] });
      setHasChanges(false);
    },
  });

  const unsealMutation = useMutation({
    mutationFn: (key: string) => systemApi.unsealVault(key),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["vault-status"] });
    },
  });

  const updateConfig = <K extends keyof VaultConfig>(key: K, value: VaultConfig[K]) => {
    setConfig((prev) => ({ ...prev, [key]: value }));
    setHasChanges(true);
  };

  const isHealthy = health?.services?.some(
    (s: { name: string; status: string }) => 
      s.name.toLowerCase().includes("vault") && s.status === "healthy"
  );

  const isSealed = vaultStatus?.sealed ?? true;
  const isInitialized = vaultStatus?.initialized ?? false;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold flex items-center gap-2">
            <Lock className="h-6 w-6" />
            Vault Configuration
          </h1>
          <p className="text-muted-foreground">
            Configure secrets management and encryption
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Badge variant={isSealed ? "destructive" : "default"}>
            {isSealed ? (
              <ShieldOff className="mr-1 h-3 w-3" />
            ) : (
              <ShieldCheck className="mr-1 h-3 w-3" />
            )}
            {isSealed ? "Sealed" : "Unsealed"}
          </Badge>
          <Badge variant={isHealthy ? "default" : "secondary"}>
            {isHealthy ? (
              <CheckCircle className="mr-1 h-3 w-3" />
            ) : (
              <AlertCircle className="mr-1 h-3 w-3" />
            )}
            {isHealthy ? "Running" : "Stopped"}
          </Badge>
        </div>
      </div>

      {/* Status Cards */}
      <div className="grid gap-4 md:grid-cols-4">
        <Card>
          <CardHeader className="pb-2">
            <CardDescription>Status</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {isInitialized ? "Initialized" : "Not Initialized"}
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardDescription>Seal Status</CardDescription>
          </CardHeader>
          <CardContent>
            <div className={`text-2xl font-bold ${isSealed ? "text-destructive" : "text-green-500"}`}>
              {isSealed ? "Sealed" : "Unsealed"}
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardDescription>Storage Backend</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold capitalize">
              {vaultStatus?.storage_type || config.storage_backend}
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardDescription>Version</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{vaultStatus?.version || "N/A"}</div>
          </CardContent>
        </Card>
      </div>

      {isLoading ? (
        <div className="flex items-center justify-center py-12">
          <RefreshCw className="h-8 w-8 animate-spin text-muted-foreground" />
        </div>
      ) : (
        <div className="grid gap-6 lg:grid-cols-2">
          {/* Storage & Network */}
          <Card>
            <CardHeader>
              <CardTitle>Storage & Network</CardTitle>
              <CardDescription>
                Configure Vault storage backend and network addresses
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="space-y-2">
                <Label htmlFor="storage_backend">Storage Backend</Label>
                <Select
                  value={config.storage_backend}
                  onValueChange={(v) => updateConfig("storage_backend", v)}
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {storageBackends.map((backend) => (
                      <SelectItem key={backend.value} value={backend.value}>
                        <div>
                          <div className="font-medium">{backend.label}</div>
                          <div className="text-xs text-muted-foreground">
                            {backend.description}
                          </div>
                        </div>
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              <Separator />

              <div className="space-y-2">
                <Label htmlFor="api_addr">API Address</Label>
                <Input
                  id="api_addr"
                  type="url"
                  value={config.api_addr}
                  onChange={(e) => updateConfig("api_addr", e.target.value)}
                  placeholder="http://vault:8200"
                />
                <p className="text-xs text-muted-foreground">
                  Address for Vault API requests
                </p>
              </div>

              <div className="space-y-2">
                <Label htmlFor="cluster_addr">Cluster Address</Label>
                <Input
                  id="cluster_addr"
                  type="url"
                  value={config.cluster_addr}
                  onChange={(e) => updateConfig("cluster_addr", e.target.value)}
                  placeholder="https://vault:8201"
                />
                <p className="text-xs text-muted-foreground">
                  Address for cluster communication (HA mode)
                </p>
              </div>
            </CardContent>
          </Card>

          {/* Security Settings */}
          <Card>
            <CardHeader>
              <CardTitle>Security Settings</CardTitle>
              <CardDescription>
                Configure seal mechanism and UI access
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="space-y-2">
                <Label htmlFor="seal_type">Seal Type</Label>
                <Select
                  value={config.seal_type}
                  onValueChange={(v) => updateConfig("seal_type", v)}
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {sealTypes.map((seal) => (
                      <SelectItem key={seal.value} value={seal.value}>
                        <div>
                          <div className="font-medium">{seal.label}</div>
                          <div className="text-xs text-muted-foreground">
                            {seal.description}
                          </div>
                        </div>
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
                <p className="text-xs text-muted-foreground">
                  How Vault protects its master key
                </p>
              </div>

              <Separator />

              <div className="flex items-center justify-between">
                <div className="space-y-0.5">
                  <Label htmlFor="ui_enabled">Enable Web UI</Label>
                  <p className="text-xs text-muted-foreground">
                    Allow access to Vault web interface
                  </p>
                </div>
                <Switch
                  id="ui_enabled"
                  checked={config.ui_enabled}
                  onCheckedChange={(checked) => updateConfig("ui_enabled", checked)}
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
