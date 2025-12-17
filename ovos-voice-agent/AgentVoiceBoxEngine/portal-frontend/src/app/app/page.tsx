"use client";

/**
 * User Dashboard Page
 * Implements Requirements C1.1-C1.6: Read-only usage summary for end users
 */

import { useQuery } from "@tanstack/react-query";
import { Activity, AlertCircle } from "lucide-react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { dashboardApi, DashboardResponse } from "@/lib/api";
import { useAuth } from "@/contexts/AuthContext";
import { formatNumber, getStatusColor } from "@/lib/utils";

function DashboardSkeleton() {
  return (
    <div className="space-y-6">
      <div className="grid gap-4 md:grid-cols-2">
        {[...Array(2)].map((_, i) => (
          <Card key={i}>
            <CardHeader className="pb-2">
              <Skeleton className="h-4 w-24" />
            </CardHeader>
            <CardContent>
              <Skeleton className="h-8 w-16 mb-1" />
              <Skeleton className="h-3 w-32" />
            </CardContent>
          </Card>
        ))}
      </div>
      <Card>
        <CardHeader>
          <Skeleton className="h-5 w-32" />
        </CardHeader>
        <CardContent className="space-y-4">
          {[...Array(4)].map((_, i) => (
            <Skeleton key={i} className="h-8 w-full" />
          ))}
        </CardContent>
      </Card>
    </div>
  );
}

export default function UserDashboardPage() {
  const { hasPermission } = useAuth();

  const { data, isLoading, error } = useQuery<DashboardResponse>({
    queryKey: ["user-dashboard"],
    queryFn: dashboardApi.getAll,
    refetchInterval: 60000,
  });

  if (isLoading) {
    return (
      <div className="p-6">
        <div className="mb-6">
          <h1 className="text-2xl font-semibold">Dashboard</h1>
          <p className="text-muted-foreground">Your account overview</p>
        </div>
        <DashboardSkeleton />
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="p-6">
        <div className="mb-6">
          <h1 className="text-2xl font-semibold">Dashboard</h1>
          <p className="text-muted-foreground">Your account overview</p>
        </div>
        <Card>
          <CardContent className="py-8 text-center">
            <AlertCircle className="mx-auto h-12 w-12 text-muted-foreground mb-4" />
            <p className="text-muted-foreground">Unable to load dashboard data</p>
          </CardContent>
        </Card>
      </div>
    );
  }

  const { health, recent_activity } = data;

  return (
    <div className="p-6">
      <div className="mb-6">
        <h1 className="text-2xl font-semibold">Dashboard</h1>
        <p className="text-muted-foreground">Your account overview</p>
      </div>

      <div className="space-y-6">
        {/* System Status - Read Only */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Activity className="h-5 w-5" aria-hidden="true" />
              System Status
            </CardTitle>
            <CardDescription>
              Current service availability
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              <div className="flex items-center justify-between p-3 rounded-lg border">
                <span className="font-medium">Overall Status</span>
                <Badge className={getStatusColor(health.overall)}>
                  {health.overall}
                </Badge>
              </div>
              {Object.entries(health.services).map(([service, status]) => (
                <div key={service} className="flex items-center justify-between text-sm">
                  <span className="capitalize">{service}</span>
                  <Badge variant="outline" className={getStatusColor(status)}>
                    {status}
                  </Badge>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* Recent Activity - Based on Permissions */}
        {hasPermission("usage:view") && (
          <Card>
            <CardHeader>
              <CardTitle>Recent Activity</CardTitle>
              <CardDescription>Latest events in your organization</CardDescription>
            </CardHeader>
            <CardContent>
              {recent_activity.length === 0 ? (
                <p className="text-center text-muted-foreground py-4">
                  No recent activity
                </p>
              ) : (
                <div className="space-y-4">
                  {recent_activity.slice(0, 5).map((item) => (
                    <div
                      key={item.id}
                      className="flex items-start gap-4 border-b pb-4 last:border-0 last:pb-0"
                    >
                      <div className="flex-1 space-y-1">
                        <p className="text-sm">{item.description}</p>
                        <p className="text-xs text-muted-foreground">
                          {new Date(item.timestamp).toLocaleString()}
                        </p>
                      </div>
                      <Badge variant="outline">{item.type}</Badge>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        )}

        {/* Permission Notice */}
        {!hasPermission("billing:view") && (
          <Card className="border-dashed">
            <CardContent className="py-6 text-center">
              <p className="text-sm text-muted-foreground">
                Contact your administrator for access to billing information.
              </p>
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  );
}
