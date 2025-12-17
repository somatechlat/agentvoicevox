"use client";

/**
 * User Sessions Page - View Only
 * Implements Requirements C3.1-C3.6: View-only sessions based on permissions
 */

import { useQuery } from "@tanstack/react-query";
import { useState } from "react";
import { Phone, AlertCircle, Lock } from "lucide-react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { sessionsApi, Session } from "@/lib/api";
import { useAuth } from "@/contexts/AuthContext";
import { formatDateTime, getStatusColor } from "@/lib/utils";

export default function UserSessionsPage() {
  const { hasPermission } = useAuth();
  const [page] = useState(1);

  const canViewSessions = hasPermission("usage:view");

  const { data, isLoading, error } = useQuery({
    queryKey: ["user-sessions", page],
    queryFn: () => sessionsApi.list({ page, per_page: 20 }),
    enabled: canViewSessions,
  });

  // No permission state
  if (!canViewSessions) {
    return (
      <div className="p-6">
        <div className="mb-6">
          <h1 className="text-2xl font-semibold">Sessions</h1>
          <p className="text-muted-foreground">Voice conversation history</p>
        </div>
        <Card>
          <CardContent className="py-12 text-center">
            <Lock className="mx-auto h-12 w-12 text-muted-foreground mb-4" />
            <h3 className="text-lg font-medium mb-2">Access Restricted</h3>
            <p className="text-muted-foreground max-w-md mx-auto">
              You don&apos;t have permission to view sessions. 
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
          <h1 className="text-2xl font-semibold">Sessions</h1>
          <p className="text-muted-foreground">Voice conversation history</p>
        </div>
        <Card>
          <CardContent className="py-6">
            <div className="space-y-4">
              {[...Array(5)].map((_, i) => (
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
          <h1 className="text-2xl font-semibold">Sessions</h1>
          <p className="text-muted-foreground">Voice conversation history</p>
        </div>
        <Card>
          <CardContent className="py-8 text-center">
            <AlertCircle className="mx-auto h-12 w-12 text-muted-foreground mb-4" />
            <p className="text-muted-foreground">Unable to load sessions</p>
          </CardContent>
        </Card>
      </div>
    );
  }

  const sessions = data?.sessions || [];

  return (
    <div className="p-6">
      <div className="mb-6">
        <h1 className="text-2xl font-semibold">Sessions</h1>
        <p className="text-muted-foreground">Voice conversation history (read-only)</p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Phone className="h-5 w-5" />
            Recent Sessions
          </CardTitle>
          <CardDescription>
            {data?.total || 0} total sessions
          </CardDescription>
        </CardHeader>
        <CardContent>
          {sessions.length === 0 ? (
            <div className="text-center py-8">
              <Phone className="mx-auto h-12 w-12 text-muted-foreground mb-4" />
              <p className="text-muted-foreground">No sessions found</p>
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Session ID</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Model</TableHead>
                  <TableHead>Voice</TableHead>
                  <TableHead>Created</TableHead>
                  <TableHead>Duration</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {sessions.map((session: Session) => (
                  <TableRow key={session.id}>
                    <TableCell className="font-mono text-sm">
                      {session.id.slice(0, 8)}...
                    </TableCell>
                    <TableCell>
                      <Badge className={getStatusColor(session.status)}>
                        {session.status}
                      </Badge>
                    </TableCell>
                    <TableCell>{session.model}</TableCell>
                    <TableCell>{session.voice}</TableCell>
                    <TableCell className="text-muted-foreground">
                      {formatDateTime(session.created_at)}
                    </TableCell>
                    <TableCell>
                      {session.duration_seconds 
                        ? `${Math.floor(session.duration_seconds / 60)}m ${session.duration_seconds % 60}s`
                        : "-"}
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
