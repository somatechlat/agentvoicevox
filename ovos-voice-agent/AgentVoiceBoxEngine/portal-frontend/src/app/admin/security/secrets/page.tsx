"use client";

/**
 * Vault Secrets Management Page
 * Browse and manage secrets stored in HashiCorp Vault
 */

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Key, RefreshCw, Eye, EyeOff, FolderOpen, File, Plus, Trash2, ShieldCheck, ShieldOff } from "lucide-react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { systemApi } from "@/lib/api";

interface SecretPath {
  path: string;
  type: "folder" | "secret";
  version?: number;
  created_at?: string;
}

export default function SecretsPage() {
  const [currentPath, setCurrentPath] = useState("/");
  const [showValues, setShowValues] = useState<Record<string, boolean>>({});
  const [newSecretKey, setNewSecretKey] = useState("");
  const [newSecretValue, setNewSecretValue] = useState("");

  const { data: vaultStatus } = useQuery({
    queryKey: ["vault-status"],
    queryFn: () => systemApi.getVaultStatus(),
    refetchInterval: 30000,
  });

  // Mock data for secrets browser - in real implementation, this would come from Vault API
  const secrets: SecretPath[] = [
    { path: "database", type: "folder" },
    { path: "api-keys", type: "folder" },
    { path: "tls", type: "folder" },
    { path: "postgres_password", type: "secret", version: 3, created_at: "2025-12-01T10:00:00Z" },
    { path: "redis_password", type: "secret", version: 1, created_at: "2025-12-01T10:00:00Z" },
    { path: "jwt_secret", type: "secret", version: 2, created_at: "2025-12-05T14:30:00Z" },
  ];

  const isSealed = vaultStatus?.sealed ?? true;
  const isInitialized = vaultStatus?.initialized ?? false;

  const toggleShowValue = (path: string) => {
    setShowValues((prev) => ({ ...prev, [path]: !prev[path] }));
  };

  const navigateToPath = (path: string) => {
    if (path === "..") {
      const parts = currentPath.split("/").filter(Boolean);
      parts.pop();
      setCurrentPath("/" + parts.join("/"));
    } else {
      setCurrentPath(currentPath === "/" ? `/${path}` : `${currentPath}/${path}`);
    }
  };

  const breadcrumbs = currentPath.split("/").filter(Boolean);

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold flex items-center gap-2">
            <Key className="h-6 w-6" />
            Secrets Management
          </h1>
          <p className="text-muted-foreground">
            Browse and manage secrets stored in HashiCorp Vault
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
        </div>
      </div>

      {isSealed ? (
        <Card>
          <CardContent className="py-12">
            <div className="text-center space-y-4">
              <ShieldOff className="mx-auto h-12 w-12 text-muted-foreground" />
              <div>
                <h3 className="text-lg font-medium">Vault is Sealed</h3>
                <p className="text-muted-foreground">
                  Vault must be unsealed before you can access secrets.
                </p>
              </div>
              <Button variant="outline">
                Go to Vault Configuration
              </Button>
            </div>
          </CardContent>
        </Card>
      ) : !isInitialized ? (
        <Card>
          <CardContent className="py-12">
            <div className="text-center space-y-4">
              <Key className="mx-auto h-12 w-12 text-muted-foreground" />
              <div>
                <h3 className="text-lg font-medium">Vault Not Initialized</h3>
                <p className="text-muted-foreground">
                  Vault needs to be initialized before use.
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      ) : (
        <>
          {/* Breadcrumb Navigation */}
          <Card>
            <CardContent className="py-3">
              <div className="flex items-center gap-2">
                <button
                  onClick={() => setCurrentPath("/")}
                  className="text-sm text-primary hover:underline"
                >
                  root
                </button>
                {breadcrumbs.map((crumb, index) => (
                  <div key={index} className="flex items-center gap-2">
                    <span className="text-muted-foreground">/</span>
                    <button
                      onClick={() =>
                        setCurrentPath("/" + breadcrumbs.slice(0, index + 1).join("/"))
                      }
                      className="text-sm text-primary hover:underline"
                    >
                      {crumb}
                    </button>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>

          <div className="grid gap-6 lg:grid-cols-3">
            {/* Secrets Browser */}
            <Card className="lg:col-span-2">
              <CardHeader className="flex flex-row items-center justify-between">
                <div>
                  <CardTitle>Secrets</CardTitle>
                  <CardDescription>
                    Path: {currentPath}
                  </CardDescription>
                </div>
                <Dialog>
                  <DialogTrigger asChild>
                    <Button size="sm">
                      <Plus className="mr-2 h-4 w-4" />
                      New Secret
                    </Button>
                  </DialogTrigger>
                  <DialogContent>
                    <DialogHeader>
                      <DialogTitle>Create New Secret</DialogTitle>
                      <DialogDescription>
                        Add a new secret to {currentPath}
                      </DialogDescription>
                    </DialogHeader>
                    <div className="space-y-4 py-4">
                      <div className="space-y-2">
                        <Label>Key</Label>
                        <Input
                          value={newSecretKey}
                          onChange={(e) => setNewSecretKey(e.target.value)}
                          placeholder="my_secret_key"
                        />
                      </div>
                      <div className="space-y-2">
                        <Label>Value</Label>
                        <Input
                          type="password"
                          value={newSecretValue}
                          onChange={(e) => setNewSecretValue(e.target.value)}
                          placeholder="secret value"
                        />
                      </div>
                    </div>
                    <div className="flex justify-end">
                      <Button>Create Secret</Button>
                    </div>
                  </DialogContent>
                </Dialog>
              </CardHeader>
              <CardContent>
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Name</TableHead>
                      <TableHead>Type</TableHead>
                      <TableHead>Version</TableHead>
                      <TableHead>Created</TableHead>
                      <TableHead className="w-[100px]">Actions</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {currentPath !== "/" && (
                      <TableRow
                        className="cursor-pointer hover:bg-accent"
                        onClick={() => navigateToPath("..")}
                      >
                        <TableCell className="flex items-center gap-2">
                          <FolderOpen className="h-4 w-4 text-muted-foreground" />
                          ..
                        </TableCell>
                        <TableCell>-</TableCell>
                        <TableCell>-</TableCell>
                        <TableCell>-</TableCell>
                        <TableCell>-</TableCell>
                      </TableRow>
                    )}
                    {secrets.map((secret) => (
                      <TableRow
                        key={secret.path}
                        className={secret.type === "folder" ? "cursor-pointer hover:bg-accent" : ""}
                        onClick={() => secret.type === "folder" && navigateToPath(secret.path)}
                      >
                        <TableCell className="flex items-center gap-2">
                          {secret.type === "folder" ? (
                            <FolderOpen className="h-4 w-4 text-primary" />
                          ) : (
                            <File className="h-4 w-4 text-muted-foreground" />
                          )}
                          {secret.path}
                        </TableCell>
                        <TableCell>
                          <Badge variant={secret.type === "folder" ? "outline" : "secondary"}>
                            {secret.type}
                          </Badge>
                        </TableCell>
                        <TableCell>{secret.version || "-"}</TableCell>
                        <TableCell>
                          {secret.created_at
                            ? new Date(secret.created_at).toLocaleDateString()
                            : "-"}
                        </TableCell>
                        <TableCell>
                          {secret.type === "secret" && (
                            <div className="flex items-center gap-1">
                              <Button
                                variant="ghost"
                                size="icon"
                                onClick={(e) => {
                                  e.stopPropagation();
                                  toggleShowValue(secret.path);
                                }}
                              >
                                {showValues[secret.path] ? (
                                  <EyeOff className="h-4 w-4" />
                                ) : (
                                  <Eye className="h-4 w-4" />
                                )}
                              </Button>
                              <Button
                                variant="ghost"
                                size="icon"
                                className="text-destructive"
                                onClick={(e) => e.stopPropagation()}
                              >
                                <Trash2 className="h-4 w-4" />
                              </Button>
                            </div>
                          )}
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </CardContent>
            </Card>

            {/* Quick Stats */}
            <div className="space-y-6">
              <Card>
                <CardHeader>
                  <CardTitle>Vault Status</CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Status</span>
                    <Badge variant="default">Unsealed</Badge>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Storage</span>
                    <span>{vaultStatus?.storage_type || "file"}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Version</span>
                    <span>{vaultStatus?.version || "1.15.0"}</span>
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle>Secret Engines</CardTitle>
                </CardHeader>
                <CardContent className="space-y-2">
                  <div className="flex items-center justify-between rounded-lg border p-3">
                    <div>
                      <div className="font-medium">kv-v2</div>
                      <div className="text-xs text-muted-foreground">Key-Value Store</div>
                    </div>
                    <Badge>Enabled</Badge>
                  </div>
                  <div className="flex items-center justify-between rounded-lg border p-3">
                    <div>
                      <div className="font-medium">transit</div>
                      <div className="text-xs text-muted-foreground">Encryption as a Service</div>
                    </div>
                    <Badge variant="secondary">Disabled</Badge>
                  </div>
                  <div className="flex items-center justify-between rounded-lg border p-3">
                    <div>
                      <div className="font-medium">pki</div>
                      <div className="text-xs text-muted-foreground">PKI Certificates</div>
                    </div>
                    <Badge variant="secondary">Disabled</Badge>
                  </div>
                </CardContent>
              </Card>
            </div>
          </div>
        </>
      )}
    </div>
  );
}
