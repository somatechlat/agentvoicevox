"use client";

/**
 * User API Keys Page - View Only
 * Implements Requirements C4.1-C4.6: View-only API keys based on permissions
 */

import { useQuery } from "@tanstack/react-query";
import { Key, AlertCircle, Lock, Copy, Check } from "lucide-react";
import { useState } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { apiKeysApi, ApiKey } from "@/lib/api";
import { useAuth } from "@/contexts/AuthContext";
import { formatDateTime } from "@/lib/utils";

export default function UserApiKeysPage() {
  const { hasPermission } = useAuth();
  const [copiedId, setCopiedId] = useState<string | null>(null);

  const canViewKeys = hasPermission("api_keys:view");

  const { data: keys, isLoading, error } = useQuery({
    queryKey: ["user-api-keys"],
    queryFn: () => apiKeysApi.list(false),
    enabled: canViewKeys,
  });

  const copyPrefix = async (prefix: string, id: string) => {
    await navigator.clipboard.writeText(prefix);
    setCopiedId(id);
    setTimeout(() => setCopiedId(null), 2000);
  };

  // No permission state
  if (!canViewKeys) {
    return (
      <div className="p-6">
        <div className="mb-6">
          <h1 className="text-2xl font-semibold">API Keys</h1>
          <p className="text-muted-foreground">Authentication credentials</p>
        </div>
        <Card>
          <CardContent className="py-12 text-center">
            <Lock className="mx-auto h-12 w-12 text-muted-foreground mb-4" />
            <h3 className="text-lg font-medium mb-2">Access Restricted</h3>
            <p className="text-muted-foreground max-w-md mx-auto">
              You don&apos;t have permission to view API keys. 
              Contact your administrator to request access.
            </p>
          </CardContent>
        </Card>
      </div>
    );
  }

  if (isLoading) {
    return (
      <div className="p-6">
        <div className="mb-6">
          <h1 className="text-2xl font-semibold">API Keys</h1>
          <p className="text-muted-foreground">Authentication credentials</p>
        </div>
        <Card>
          <CardContent className="py-6">
            <div className="space-y-4">
              {[...Array(3)].map((_, i) => (
                <Skeleton key={i} className="h-12 w-full" />
              ))}
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-6">
        <div className="mb-6">
          <h1 className="text-2xl font-semibold">API Keys</h1>
          <p className="text-muted-foreground">Authentication credentials</p>
        </div>
        <Card>
          <CardContent className="py-8 text-center">
            <AlertCircle className="mx-auto h-12 w-12 text-muted-foreground mb-4" />
            <p className="text-muted-foreground">Unable to load API keys</p>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="p-6">
      <div className="mb-6">
        <h1 className="text-2xl font-semibold">API Keys</h1>
        <p className="text-muted-foreground">Authentication credentials (read-only)</p>
      </div>

      {/* Notice about read-only access */}
      <Card className="mb-6 border-dashed">
        <CardContent className="py-4">
          <p className="text-sm text-muted-foreground">
            You have view-only access to API keys. Contact your administrator to create or manage keys.
          </p>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Key className="h-5 w-5" />
            API Keys
          </CardTitle>
          <CardDescription>
            {keys?.length || 0} active keys
          </CardDescription>
        </CardHeader>
        <CardContent>
          {!keys || keys.length === 0 ? (
            <div className="text-center py-8">
              <Key className="mx-auto h-12 w-12 text-muted-foreground mb-4" />
              <p className="text-muted-foreground">No API keys available</p>
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Name</TableHead>
                  <TableHead>Prefix</TableHead>
                  <TableHead>Scopes</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Last Used</TableHead>
                  <TableHead>Created</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {keys.map((key: ApiKey) => (
                  <TableRow key={key.id}>
                    <TableCell className="font-medium">{key.name}</TableCell>
                    <TableCell>
                      <div className="flex items-center gap-2">
                        <code className="text-sm bg-muted px-2 py-1 rounded">
                          {key.prefix}...
                        </code>
                        <Button
                          variant="ghost"
                          size="icon"
                          className="h-6 w-6"
                          onClick={() => copyPrefix(key.prefix, key.id)}
                          title="Copy prefix"
                        >
                          {copiedId === key.id ? (
                            <Check className="h-3 w-3 text-green-500" />
                          ) : (
                            <Copy className="h-3 w-3" />
                          )}
                        </Button>
                      </div>
                    </TableCell>
                    <TableCell>
                      <div className="flex flex-wrap gap-1">
                        {key.scopes.slice(0, 2).map((scope) => (
                          <Badge key={scope} variant="secondary" className="text-xs">
                            {scope}
                          </Badge>
                        ))}
                        {key.scopes.length > 2 && (
                          <Badge variant="secondary" className="text-xs">
                            +{key.scopes.length - 2}
                          </Badge>
                        )}
                      </div>
                    </TableCell>
                    <TableCell>
                      <Badge variant={key.is_active ? "default" : "secondary"}>
                        {key.is_active ? "Active" : "Inactive"}
                      </Badge>
                    </TableCell>
                    <TableCell className="text-muted-foreground">
                      {key.last_used_at ? formatDateTime(key.last_used_at) : "Never"}
                    </TableCell>
                    <TableCell className="text-muted-foreground">
                      {formatDateTime(key.created_at)}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
