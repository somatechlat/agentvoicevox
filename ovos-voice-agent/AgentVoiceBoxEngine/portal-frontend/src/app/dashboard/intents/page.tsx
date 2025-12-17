"use client";

/**
 * Intent Analytics Page
 * Implements Requirement F5: Intent recognition analytics and performance metrics
 */

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import {
  Brain,
  AlertCircle,
  TrendingUp,
  Clock,
  CheckCircle2,
  XCircle,
  BarChart3,
} from "lucide-react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { Badge } from "@/components/ui/badge";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { intentAnalyticsApi } from "@/lib/api";
import { DashboardLayout } from "@/components/layout/DashboardLayout";

type Period = "24h" | "7d" | "30d";

export default function IntentsPage() {
  const [period, setPeriod] = useState<Period>("7d");

  const { data: stats, isLoading: statsLoading, error: statsError } = useQuery({
    queryKey: ["intent-stats", period],
    queryFn: () => intentAnalyticsApi.getStats(period),
  });

  const { data: timeSeries, isLoading: timeSeriesLoading } = useQuery({
    queryKey: ["intent-timeseries", period],
    queryFn: () => intentAnalyticsApi.getTimeSeries(period),
  });

  const { data: recentIntents, isLoading: recentLoading } = useQuery({
    queryKey: ["intent-recent"],
    queryFn: () => intentAnalyticsApi.getRecent(30),
    refetchInterval: 10000,
  });

  // Calculate summary metrics
  const totalIntents = stats?.reduce((sum, s) => sum + s.count, 0) ?? 0;
  const avgConfidence = stats?.length
    ? stats.reduce((sum, s) => sum + s.avg_confidence * s.count, 0) / totalIntents
    : 0;
  const avgSuccessRate = stats?.length
    ? stats.reduce((sum, s) => sum + s.success_rate * s.count, 0) / totalIntents
    : 0;
  const uniqueIntents = stats?.length ?? 0;

  if (statsLoading) {
    return (
      <DashboardLayout title="Intent Analytics" description="Voice intent recognition metrics">
        <div className="space-y-6">
          <div className="grid gap-4 md:grid-cols-4">
            {[...Array(4)].map((_, i) => (
              <Skeleton key={i} className="h-24" />
            ))}
          </div>
          <Skeleton className="h-64 w-full" />
        </div>
      </DashboardLayout>
    );
  }

  if (statsError) {
    return (
      <DashboardLayout title="Intent Analytics" description="Voice intent recognition metrics">
        <Card>
          <CardContent className="py-8 text-center">
            <AlertCircle className="mx-auto h-12 w-12 text-muted-foreground mb-4" />
            <p className="text-muted-foreground">Unable to load intent analytics</p>
          </CardContent>
        </Card>
      </DashboardLayout>
    );
  }

  return (
    <DashboardLayout title="Intent Analytics" description="Monitor voice intent recognition performance">
      <div className="space-y-6">
        {/* Period Selector */}
        <div className="flex justify-end">
          <Select value={period} onValueChange={(v) => setPeriod(v as Period)}>
            <SelectTrigger className="w-32">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="24h">Last 24h</SelectItem>
              <SelectItem value="7d">Last 7 days</SelectItem>
              <SelectItem value="30d">Last 30 days</SelectItem>
            </SelectContent>
          </Select>
        </div>

        {/* Summary Cards */}
        <div className="grid gap-4 md:grid-cols-4">
          <Card>
            <CardHeader className="pb-2">
              <CardDescription>Total Intents</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="flex items-center gap-2">
                <Brain className="h-5 w-5 text-primary" />
                <span className="text-2xl font-bold">{totalIntents.toLocaleString()}</span>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-2">
              <CardDescription>Unique Intents</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="flex items-center gap-2">
                <BarChart3 className="h-5 w-5 text-blue-500" />
                <span className="text-2xl font-bold">{uniqueIntents}</span>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-2">
              <CardDescription>Avg Confidence</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="flex items-center gap-2">
                <TrendingUp className="h-5 w-5 text-green-500" />
                <span className="text-2xl font-bold">{(avgConfidence * 100).toFixed(1)}%</span>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-2">
              <CardDescription>Success Rate</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="flex items-center gap-2">
                <CheckCircle2 className="h-5 w-5 text-emerald-500" />
                <span className="text-2xl font-bold">{(avgSuccessRate * 100).toFixed(1)}%</span>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Time Series Chart Placeholder */}
        {timeSeriesLoading ? (
          <Skeleton className="h-64 w-full" />
        ) : timeSeries && timeSeries.length > 0 ? (
          <Card>
            <CardHeader>
              <CardTitle>Intent Volume Over Time</CardTitle>
              <CardDescription>Successful vs failed intent recognitions</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="h-64 flex items-end gap-1">
                {timeSeries.slice(-30).map((point, i) => {
                  const total = point.successful + point.failed;
                  const maxTotal = Math.max(...timeSeries.map((p) => p.successful + p.failed));
                  const height = maxTotal > 0 ? (total / maxTotal) * 100 : 0;
                  const successRatio = total > 0 ? point.successful / total : 1;
                  return (
                    <div
                      key={i}
                      className="flex-1 flex flex-col justify-end"
                      title={`${new Date(point.timestamp).toLocaleDateString()}: ${total} intents`}
                    >
                      <div
                        className="bg-emerald-500 rounded-t"
                        style={{ height: `${height * successRatio}%` }}
                      />
                      <div
                        className="bg-red-400"
                        style={{ height: `${height * (1 - successRatio)}%` }}
                      />
                    </div>
                  );
                })}
              </div>
              <div className="flex justify-center gap-4 mt-4 text-sm">
                <div className="flex items-center gap-2">
                  <div className="w-3 h-3 bg-emerald-500 rounded" />
                  <span>Successful</span>
                </div>
                <div className="flex items-center gap-2">
                  <div className="w-3 h-3 bg-red-400 rounded" />
                  <span>Failed</span>
                </div>
              </div>
            </CardContent>
          </Card>
        ) : null}

        {/* Intent Stats Table */}
        <Card>
          <CardHeader>
            <CardTitle>Intent Performance</CardTitle>
            <CardDescription>Breakdown by intent type</CardDescription>
          </CardHeader>
          <CardContent>
            {stats && stats.length > 0 ? (
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Intent</TableHead>
                    <TableHead>Skill</TableHead>
                    <TableHead className="text-right">Count</TableHead>
                    <TableHead className="text-right">Avg Confidence</TableHead>
                    <TableHead className="text-right">Success Rate</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {stats.sort((a, b) => b.count - a.count).map((stat) => (
                    <TableRow key={stat.intent}>
                      <TableCell className="font-mono text-sm">{stat.intent}</TableCell>
                      <TableCell>
                        <Badge variant="outline">{stat.skill}</Badge>
                      </TableCell>
                      <TableCell className="text-right">{stat.count.toLocaleString()}</TableCell>
                      <TableCell className="text-right">
                        <Badge variant={stat.avg_confidence > 0.8 ? "default" : "secondary"}>
                          {(stat.avg_confidence * 100).toFixed(0)}%
                        </Badge>
                      </TableCell>
                      <TableCell className="text-right">
                        <Badge variant={stat.success_rate > 0.9 ? "default" : stat.success_rate > 0.7 ? "secondary" : "destructive"}>
                          {(stat.success_rate * 100).toFixed(0)}%
                        </Badge>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            ) : (
              <p className="text-center text-muted-foreground py-8">
                No intent data for the selected period
              </p>
            )}
          </CardContent>
        </Card>

        {/* Recent Intents */}
        <Card>
          <CardHeader>
            <CardTitle>Recent Intent Recognitions</CardTitle>
            <CardDescription>Latest voice commands processed</CardDescription>
          </CardHeader>
          <CardContent>
            {recentLoading ? (
              <div className="space-y-2">
                {[...Array(5)].map((_, i) => (
                  <Skeleton key={i} className="h-16 w-full" />
                ))}
              </div>
            ) : recentIntents && recentIntents.length > 0 ? (
              <div className="space-y-3 max-h-96 overflow-y-auto">
                {recentIntents.map((intent) => (
                  <div
                    key={intent.id}
                    className="flex items-start justify-between rounded-md border p-3"
                  >
                    <div className="flex-1">
                      <div className="flex items-center gap-2">
                        {intent.success ? (
                          <CheckCircle2 className="h-4 w-4 text-emerald-500" />
                        ) : (
                          <XCircle className="h-4 w-4 text-red-500" />
                        )}
                        <p className="font-medium">{intent.utterance}</p>
                      </div>
                      <div className="flex items-center gap-2 mt-1 text-xs text-muted-foreground">
                        <span className="font-mono">{intent.intent}</span>
                        <span>•</span>
                        <Badge variant="outline" className="text-xs">{intent.skill}</Badge>
                      </div>
                    </div>
                    <div className="text-right text-sm">
                      <Badge variant={intent.confidence > 0.8 ? "default" : "secondary"}>
                        {(intent.confidence * 100).toFixed(0)}%
                      </Badge>
                      <div className="flex items-center gap-1 mt-1 text-xs text-muted-foreground">
                        <Clock className="h-3 w-3" />
                        {intent.response_time_ms}ms
                      </div>
                      <p className="text-xs text-muted-foreground mt-1">
                        {new Date(intent.timestamp).toLocaleTimeString()}
                      </p>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-center text-muted-foreground py-8">
                No recent intent recognitions
              </p>
            )}
          </CardContent>
        </Card>
      </div>
    </DashboardLayout>
  );
}
