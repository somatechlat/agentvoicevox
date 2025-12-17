"use client";

/**
 * OPA Policies Configuration Page
 * Manage Open Policy Agent policies for access control
 */

import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { FileCode, Save, RefreshCw, Play, CheckCircle, XCircle, Plus } from "lucide-react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";
import { Badge } from "@/components/ui/badge";
import { Textarea } from "@/components/ui/textarea";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { securityApi, OPAPolicy } from "@/lib/api";

export default function OPAPoliciesPage() {
  const queryClient = useQueryClient();
  const [selectedPolicy, setSelectedPolicy] = useState<OPAPolicy | null>(null);
  const [testInput, setTestInput] = useState("{}");
  const [testResult, setTestResult] = useState<{ allowed: boolean; reason?: string } | null>(null);

  const { data: policies, isLoading } = useQuery({
    queryKey: ["opa-policies"],
    queryFn: () => securityApi.getOPAPolicies(),
  });

  const updateMutation = useMutation({
    mutationFn: ({ id, updates }: { id: string; updates: Partial<OPAPolicy> }) =>
      securityApi.updateOPAPolicy(id, updates),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["opa-policies"] });
    },
  });

  const testMutation = useMutation({
    mutationFn: ({ id, input }: { id: string; input: Record<string, unknown> }) =>
      securityApi.testOPAPolicy(id, input),
    onSuccess: (result) => {
      setTestResult(result);
    },
  });

  const handleTest = () => {
    if (!selectedPolicy) return;
    try {
      const input = JSON.parse(testInput);
      testMutation.mutate({ id: selectedPolicy.id, input });
    } catch {
      setTestResult({ allowed: false, reason: "Invalid JSON input" });
    }
  };

  const handleTogglePolicy = (policy: OPAPolicy) => {
    updateMutation.mutate({
      id: policy.id,
      updates: { enabled: !policy.enabled },
    });
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold flex items-center gap-2">
            <FileCode className="h-6 w-6" />
            OPA Policies
          </h1>
          <p className="text-muted-foreground">
            Manage Open Policy Agent policies for fine-grained access control
          </p>
        </div>
        <Dialog>
          <DialogTrigger asChild>
            <Button>
              <Plus className="mr-2 h-4 w-4" />
              New Policy
            </Button>
          </DialogTrigger>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Create New Policy</DialogTitle>
              <DialogDescription>
                Define a new Rego policy for access control
              </DialogDescription>
            </DialogHeader>
            <div className="space-y-4 py-4">
              <div className="space-y-2">
                <Label>Policy Name</Label>
                <Input placeholder="my_policy" />
              </div>
              <div className="space-y-2">
                <Label>Description</Label>
                <Input placeholder="Describe what this policy does" />
              </div>
              <div className="space-y-2">
                <Label>Rego Code</Label>
                <Textarea
                  className="font-mono text-sm"
                  rows={10}
                  placeholder={`package mypackage

default allow = false

allow {
  input.user.role == "admin"
}`}
                />
              </div>
            </div>
            <div className="flex justify-end">
              <Button>Create Policy</Button>
            </div>
          </DialogContent>
        </Dialog>
      </div>

      {isLoading ? (
        <div className="flex items-center justify-center py-12">
          <RefreshCw className="h-8 w-8 animate-spin text-muted-foreground" />
        </div>
      ) : (
        <div className="grid gap-6 lg:grid-cols-2">
          {/* Policy List */}
          <Card>
            <CardHeader>
              <CardTitle>Policies</CardTitle>
              <CardDescription>
                Click a policy to view and edit its Rego code
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-2">
              {policies?.map((policy) => (
                <div
                  key={policy.id}
                  className={`flex items-center justify-between rounded-lg border p-4 cursor-pointer transition-colors ${
                    selectedPolicy?.id === policy.id
                      ? "border-primary bg-primary/5"
                      : "hover:bg-accent"
                  }`}
                  onClick={() => setSelectedPolicy(policy)}
                >
                  <div className="space-y-1">
                    <div className="font-medium">{policy.name}</div>
                    <div className="text-sm text-muted-foreground">
                      {policy.description}
                    </div>
                    <div className="text-xs text-muted-foreground">
                      Updated: {new Date(policy.last_updated).toLocaleDateString()}
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <Badge variant={policy.enabled ? "default" : "secondary"}>
                      {policy.enabled ? "Enabled" : "Disabled"}
                    </Badge>
                    <Switch
                      checked={policy.enabled}
                      onCheckedChange={() => handleTogglePolicy(policy)}
                      onClick={(e) => e.stopPropagation()}
                    />
                  </div>
                </div>
              ))}

              {(!policies || policies.length === 0) && (
                <div className="text-center py-8 text-muted-foreground">
                  No policies configured
                </div>
              )}
            </CardContent>
          </Card>

          {/* Policy Editor */}
          <Card>
            <CardHeader>
              <CardTitle>
                {selectedPolicy ? selectedPolicy.name : "Policy Editor"}
              </CardTitle>
              <CardDescription>
                {selectedPolicy
                  ? selectedPolicy.description
                  : "Select a policy to view and edit"}
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              {selectedPolicy ? (
                <>
                  <div className="space-y-2">
                    <Label>Rego Code</Label>
                    <Textarea
                      className="font-mono text-sm"
                      rows={12}
                      value={selectedPolicy.rego_code}
                      onChange={(e) =>
                        setSelectedPolicy({
                          ...selectedPolicy,
                          rego_code: e.target.value,
                        })
                      }
                    />
                  </div>

                  <div className="flex gap-2">
                    <Button
                      onClick={() =>
                        updateMutation.mutate({
                          id: selectedPolicy.id,
                          updates: { rego_code: selectedPolicy.rego_code },
                        })
                      }
                      disabled={updateMutation.isPending}
                    >
                      {updateMutation.isPending ? (
                        <RefreshCw className="mr-2 h-4 w-4 animate-spin" />
                      ) : (
                        <Save className="mr-2 h-4 w-4" />
                      )}
                      Save
                    </Button>
                  </div>

                  <div className="border-t my-4" />

                  <div className="space-y-2">
                    <Label>Test Policy</Label>
                    <Textarea
                      className="font-mono text-sm"
                      rows={4}
                      value={testInput}
                      onChange={(e) => setTestInput(e.target.value)}
                      placeholder='{"user": {"role": "admin"}, "resource": "sessions"}'
                    />
                    <Button
                      variant="outline"
                      onClick={handleTest}
                      disabled={testMutation.isPending}
                    >
                      {testMutation.isPending ? (
                        <RefreshCw className="mr-2 h-4 w-4 animate-spin" />
                      ) : (
                        <Play className="mr-2 h-4 w-4" />
                      )}
                      Test
                    </Button>

                    {testResult && (
                      <div
                        className={`mt-2 rounded-lg p-3 ${
                          testResult.allowed
                            ? "bg-green-500/10 text-green-500"
                            : "bg-destructive/10 text-destructive"
                        }`}
                      >
                        <div className="flex items-center gap-2">
                          {testResult.allowed ? (
                            <CheckCircle className="h-4 w-4" />
                          ) : (
                            <XCircle className="h-4 w-4" />
                          )}
                          <span className="font-medium">
                            {testResult.allowed ? "Allowed" : "Denied"}
                          </span>
                        </div>
                        {testResult.reason && (
                          <p className="mt-1 text-sm">{testResult.reason}</p>
                        )}
                      </div>
                    )}
                  </div>
                </>
              ) : (
                <div className="flex items-center justify-center py-12 text-muted-foreground">
                  Select a policy from the list to edit
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  );
}
