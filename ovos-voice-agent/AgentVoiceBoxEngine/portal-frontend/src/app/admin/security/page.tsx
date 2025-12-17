"use client";

/**
 * Security Configuration Overview
 * Links to Keycloak, OPA Policies, and Secrets management
 */

import Link from "next/link";
import { Shield, Lock, FileCode, Key, ArrowRight, CheckCircle, AlertCircle } from "lucide-react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { useQuery } from "@tanstack/react-query";
import { systemApi } from "@/lib/api";

const securityServices = [
  {
    name: "Keycloak",
    description: "Identity and access management",
    href: "/admin/security/keycloak",
    icon: Lock,
    settings: ["Realm Settings", "Token Lifespans", "Brute Force Protection", "Identity Providers"],
  },
  {
    name: "OPA Policies",
    description: "Policy-based access control",
    href: "/admin/security/policies",
    icon: FileCode,
    settings: ["Tenant Isolation", "API Key Access", "Rate Limiting", "Resource Ownership"],
  },
  {
    name: "Secrets",
    description: "Vault secrets management",
    href: "/admin/security/secrets",
    icon: Key,
    settings: ["Secret Engines", "Access Policies", "Audit Logs"],
  },
];

export default function SecurityPage() {
  const { data: health } = useQuery({
    queryKey: ["system-health"],
    queryFn: systemApi.getHealth,
    refetchInterval: 30000,
  });

  const getServiceStatus = (serviceName: string) => {
    if (!health?.services) return "unknown";
    const service = health.services.find(
      (s: { name: string; status: string }) => 
        s.name.toLowerCase().includes(serviceName.toLowerCase())
    );
    return service?.status || "unknown";
  };

  return (
    <div className="space-y-6">
      <div>
        <div className="flex items-center gap-2">
          <Shield className="h-6 w-6 text-primary" />
          <h1 className="text-2xl font-bold">Security Configuration</h1>
        </div>
        <p className="text-muted-foreground">
          Configure authentication, authorization, and secrets management
        </p>
      </div>

      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
        {securityServices.map((service) => {
          const status = getServiceStatus(service.name);
          const isHealthy = status === "healthy" || status === "running";

          return (
            <Link key={service.name} href={service.href}>
              <Card className="h-full transition-colors hover:bg-accent/50 cursor-pointer">
                <CardHeader>
                  <div className="flex items-center justify-between">
                    <service.icon className="h-8 w-8 text-primary" />
                    <Badge variant={isHealthy ? "default" : "secondary"}>
                      {isHealthy ? (
                        <CheckCircle className="mr-1 h-3 w-3" />
                      ) : (
                        <AlertCircle className="mr-1 h-3 w-3" />
                      )}
                      {status}
                    </Badge>
                  </div>
                  <CardTitle className="mt-4">{service.name}</CardTitle>
                  <CardDescription>{service.description}</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-2">
                    <p className="text-sm font-medium text-muted-foreground">
                      Configurable Settings:
                    </p>
                    <ul className="text-sm text-muted-foreground space-y-1">
                      {service.settings.map((setting) => (
                        <li key={setting} className="flex items-center gap-2">
                          <span className="h-1 w-1 rounded-full bg-primary" />
                          {setting}
                        </li>
                      ))}
                    </ul>
                  </div>
                  <div className="mt-4 flex items-center text-sm text-primary">
                    Configure <ArrowRight className="ml-1 h-4 w-4" />
                  </div>
                </CardContent>
              </Card>
            </Link>
          );
        })}
      </div>
    </div>
  );
}
