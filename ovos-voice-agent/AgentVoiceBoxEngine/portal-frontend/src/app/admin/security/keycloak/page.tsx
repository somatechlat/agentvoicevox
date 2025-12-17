"use client";

/**
 * Keycloak Configuration Page
 * Settings: realm, registration, login, brute force, token lifespans
 */

import { useState, useEffect } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Lock, Save, RefreshCw, AlertCircle, CheckCircle, AlertTriangle } from "lucide-react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { securityApi, systemApi } from "@/lib/api";

interface KeycloakConfig {
  realm_name: string;
  display_name: string;
  ssl_required: string;
  registration_allowed: boolean;
  registration_email_as_username: boolean;
  remember_me: boolean;
  verify_email: boolean;
  login_with_email: boolean;
  reset_password_allowed: boolean;
  brute_force_protected: boolean;
  max_failure_wait_seconds: number;
  failure_factor: number;
  access_token_lifespan: number;
  sso_session_idle_timeout: number;
  sso_session_max_lifespan: number;
}

const sslOptions = [
  { value: "none", label: "None", warning: true },
  { value: "external", label: "External", description: "Required for external requests" },
  { value: "all", label: "All", description: "Required for all requests" },
];

const defaultConfig: KeycloakConfig = {
  realm_name: "agentvoicebox",
  display_name: "AgentVoiceBox",
  ssl_required: "none",
  registration_allowed: true,
  registration_email_as_username: true,
  remember_me: true,
  verify_email: false,
  login_with_email: true,
  reset_password_allowed: true,
  brute_force_protected: true,
  max_failure_wait_seconds: 900,
  failure_factor: 5,
  access_token_lifespan: 300,
  sso_session_idle_timeout: 1800,
  sso_session_max_lifespan: 36000,
};

export default function KeycloakConfigPage() {
  const queryClient = useQueryClient();
  const [config, setConfig] = useState<KeycloakConfig>(defaultConfig);
  const [hasChanges, setHasChanges] = useState(false);

  const { data: health } = useQuery({
    queryKey: ["keycloak-health"],
    queryFn: () => systemApi.getHealth(),
    refetchInterval: 30000,
  });

  const { data: savedConfig, isLoading } = useQuery({
    queryKey: ["keycloak-config"],
    queryFn: () => securityApi.getKeycloakConfig(),
  });

  useEffect(() => {
    if (savedConfig) {
      setConfig(savedConfig);
    }
  }, [savedConfig]);

  const saveMutation = useMutation({
    mutationFn: (newConfig: Partial<KeycloakConfig>) => securityApi.updateKeycloakConfig(newConfig),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["keycloak-config"] });
      setHasChanges(false);
    },
  });

  const updateConfig = <K extends keyof KeycloakConfig>(key: K, value: KeycloakConfig[K]) => {
    setConfig((prev) => ({ ...prev, [key]: value }));
    setHasChanges(true);
  };

  const formatSeconds = (seconds: number): string => {
    if (seconds < 60) return `${seconds}s`;
    if (seconds < 3600) return `${Math.floor(seconds / 60)}m`;
    return `${Math.floor(seconds / 3600)}h`;
  };

  const isHealthy = health?.services?.some(
    (s: { name: string; status: string }) => 
      s.name.toLowerCase().includes("keycloak") && s.status === "healthy"
  );

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold flex items-center gap-2">
            <Lock className="h-6 w-6" />
            Keycloak Configuration
          </h1>
          <p className="text-muted-foreground">
            Configure identity and access management settings
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

      {config.ssl_required === "none" && (
        <Alert variant="destructive">
          <AlertTriangle className="h-4 w-4" />
          <AlertDescription>
            SSL is disabled. Set to &quot;external&quot; or &quot;all&quot; for production environments.
          </AlertDescription>
        </Alert>
      )}

      {isLoading ? (
        <div className="flex items-center justify-center py-12">
          <RefreshCw className="h-8 w-8 animate-spin text-muted-foreground" />
        </div>
      ) : (
        <Tabs defaultValue="realm" className="space-y-6">
          <TabsList>
            <TabsTrigger value="realm">Realm</TabsTrigger>
            <TabsTrigger value="tokens">Tokens</TabsTrigger>
            <TabsTrigger value="security">Security</TabsTrigger>
          </TabsList>

          <TabsContent value="realm" className="space-y-6">
            <div className="grid gap-6 lg:grid-cols-2">
              {/* Realm Settings */}
              <Card>
                <CardHeader>
                  <CardTitle>Realm Settings</CardTitle>
                  <CardDescription>
                    Basic realm configuration
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-6">
                  <div className="space-y-2">
                    <Label>Display Name</Label>
                    <Input
                      value={config.display_name}
                      onChange={(e) => updateConfig("display_name", e.target.value)}
                    />
                  </div>

                  <div className="space-y-2">
                    <Label>SSL Requirement</Label>
                    <Select
                      value={config.ssl_required}
                      onValueChange={(v) => updateConfig("ssl_required", v)}
                    >
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        {sslOptions.map((opt) => (
                          <SelectItem key={opt.value} value={opt.value}>
                            <div className="flex items-center gap-2">
                              {opt.label}
                              {opt.warning && (
                                <AlertTriangle className="h-3 w-3 text-destructive" />
                              )}
                            </div>
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                </CardContent>
              </Card>

              {/* Registration */}
              <Card>
                <CardHeader>
                  <CardTitle>Registration</CardTitle>
                  <CardDescription>
                    User self-registration settings
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-6">
                  <div className="flex items-center justify-between">
                    <div className="space-y-0.5">
                      <Label>Allow Self-Registration</Label>
                      <p className="text-xs text-muted-foreground">
                        Users can create their own accounts
                      </p>
                    </div>
                    <Switch
                      checked={config.registration_allowed}
                      onCheckedChange={(checked) => updateConfig("registration_allowed", checked)}
                    />
                  </div>

                  <Separator />

                  <div className="flex items-center justify-between">
                    <div className="space-y-0.5">
                      <Label>Email as Username</Label>
                      <p className="text-xs text-muted-foreground">
                        Use email address as the username
                      </p>
                    </div>
                    <Switch
                      checked={config.registration_email_as_username}
                      onCheckedChange={(checked) => updateConfig("registration_email_as_username", checked)}
                    />
                  </div>

                  <Separator />

                  <div className="flex items-center justify-between">
                    <div className="space-y-0.5">
                      <Label>Verify Email</Label>
                      <p className="text-xs text-muted-foreground">
                        Require email verification before login
                      </p>
                    </div>
                    <Switch
                      checked={config.verify_email}
                      onCheckedChange={(checked) => updateConfig("verify_email", checked)}
                    />
                  </div>
                </CardContent>
              </Card>

              {/* Login Options */}
              <Card className="lg:col-span-2">
                <CardHeader>
                  <CardTitle>Login Options</CardTitle>
                  <CardDescription>
                    Configure login behavior
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="grid gap-6 sm:grid-cols-3">
                    <div className="flex items-center justify-between">
                      <div className="space-y-0.5">
                        <Label>Login with Email</Label>
                        <p className="text-xs text-muted-foreground">
                          Allow email for login
                        </p>
                      </div>
                      <Switch
                        checked={config.login_with_email}
                        onCheckedChange={(checked) => updateConfig("login_with_email", checked)}
                      />
                    </div>

                    <div className="flex items-center justify-between">
                      <div className="space-y-0.5">
                        <Label>Remember Me</Label>
                        <p className="text-xs text-muted-foreground">
                          Show remember me option
                        </p>
                      </div>
                      <Switch
                        checked={config.remember_me}
                        onCheckedChange={(checked) => updateConfig("remember_me", checked)}
                      />
                    </div>

                    <div className="flex items-center justify-between">
                      <div className="space-y-0.5">
                        <Label>Password Reset</Label>
                        <p className="text-xs text-muted-foreground">
                          Allow password reset
                        </p>
                      </div>
                      <Switch
                        checked={config.reset_password_allowed}
                        onCheckedChange={(checked) => updateConfig("reset_password_allowed", checked)}
                      />
                    </div>
                  </div>
                </CardContent>
              </Card>
            </div>
          </TabsContent>

          <TabsContent value="tokens" className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle>Token Lifespans</CardTitle>
                <CardDescription>
                  Configure token and session timeouts
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="grid gap-6 sm:grid-cols-3">
                  <div className="space-y-2">
                    <Label>Access Token Lifespan</Label>
                    <div className="flex gap-2">
                      <Input
                        type="number"
                        min={60}
                        max={3600}
                        value={config.access_token_lifespan}
                        onChange={(e) => updateConfig("access_token_lifespan", parseInt(e.target.value, 10))}
                      />
                      <span className="flex items-center text-sm text-muted-foreground">
                        ({formatSeconds(config.access_token_lifespan)})
                      </span>
                    </div>
                    <p className="text-xs text-muted-foreground">Seconds</p>
                  </div>

                  <div className="space-y-2">
                    <Label>SSO Session Idle</Label>
                    <div className="flex gap-2">
                      <Input
                        type="number"
                        min={300}
                        max={86400}
                        value={config.sso_session_idle_timeout}
                        onChange={(e) => updateConfig("sso_session_idle_timeout", parseInt(e.target.value, 10))}
                      />
                      <span className="flex items-center text-sm text-muted-foreground">
                        ({formatSeconds(config.sso_session_idle_timeout)})
                      </span>
                    </div>
                    <p className="text-xs text-muted-foreground">Seconds</p>
                  </div>

                  <div className="space-y-2">
                    <Label>SSO Session Max</Label>
                    <div className="flex gap-2">
                      <Input
                        type="number"
                        min={3600}
                        max={604800}
                        value={config.sso_session_max_lifespan}
                        onChange={(e) => updateConfig("sso_session_max_lifespan", parseInt(e.target.value, 10))}
                      />
                      <span className="flex items-center text-sm text-muted-foreground">
                        ({formatSeconds(config.sso_session_max_lifespan)})
                      </span>
                    </div>
                    <p className="text-xs text-muted-foreground">Seconds</p>
                  </div>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="security" className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle>Brute Force Protection</CardTitle>
                <CardDescription>
                  Protect against password guessing attacks
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-6">
                <div className="flex items-center justify-between">
                  <div className="space-y-0.5">
                    <Label>Enable Brute Force Protection</Label>
                    <p className="text-xs text-muted-foreground">
                      Lock accounts after failed login attempts
                    </p>
                  </div>
                  <Switch
                    checked={config.brute_force_protected}
                    onCheckedChange={(checked) => updateConfig("brute_force_protected", checked)}
                  />
                </div>

                {config.brute_force_protected && (
                  <>
                    <Separator />
                    <div className="grid gap-6 sm:grid-cols-2">
                      <div className="space-y-2">
                        <Label>Failure Factor</Label>
                        <Input
                          type="number"
                          min={1}
                          max={30}
                          value={config.failure_factor}
                          onChange={(e) => updateConfig("failure_factor", parseInt(e.target.value, 10))}
                        />
                        <p className="text-xs text-muted-foreground">
                          Failed attempts before lockout
                        </p>
                      </div>

                      <div className="space-y-2">
                        <Label>Max Wait Time</Label>
                        <div className="flex gap-2">
                          <Input
                            type="number"
                            min={60}
                            max={86400}
                            value={config.max_failure_wait_seconds}
                            onChange={(e) => updateConfig("max_failure_wait_seconds", parseInt(e.target.value, 10))}
                          />
                          <span className="flex items-center text-sm text-muted-foreground">
                            ({formatSeconds(config.max_failure_wait_seconds)})
                          </span>
                        </div>
                        <p className="text-xs text-muted-foreground">
                          Maximum lockout duration
                        </p>
                      </div>
                    </div>
                  </>
                )}
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
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
