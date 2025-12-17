"use client";

/**
 * Observability Configuration Overview
 * Links to Prometheus, Grafana, and Logging configuration pages
 */

import Link from "next/link";
import { BarChart3, LineChart, ScrollText, ArrowRight, CheckCircle, AlertCircle } from "lucide-react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { useQuery } from "@tanstack/react-query";
import { systemApi } from "@/lib/api";

const observabilityServices = [
  {
    name: "Prometheus",
    description: "Metrics collection and alerting",
    href: "/admin/system/observability/prometheus",
    icon: BarChart3,
    settings: ["Retention", "Scrape Interval", "Targets"],
  },
  {
    name: "Grafana",
    description: "Metrics visualization and dashboards",
    href: "/admin/system/observability/grafana",
    icon: LineChart,
    settings: ["Admin Access", "Anonymous Access", "Dashboards"],
  },
  {
    name: "Logging",
    description: "Structured logging configuration",
    href: "/admin/system/observability/logging",
    icon: ScrollText,
    settings: ["Log Level", "Format", "Rotation"],
  },
];

export default function ObservabilityPage() {
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
        <h1 className="text-2xl font-bold">Observability Configuration</h1>
        <p className="text-muted-foreground">
          Configure monitoring, metrics, and logging for the platform
        </p>
      </div>

      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
        {observabilityServices.map((service) => {
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
