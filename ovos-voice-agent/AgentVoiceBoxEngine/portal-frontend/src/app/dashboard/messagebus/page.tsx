"use client";

/**
 * OVOS Messagebus Management Page
 * Implements Requirement F1: Messagebus status, monitoring, and message sending
 */

import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  Radio,
  RefreshCw,
  Send,
  Activity,
  AlertCircle,
  CheckCircle2,
  XCircle,
} from "lucide-react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Skeleton } from "@/components/ui/skeleton";
import { Badge } from "@/components/ui/badge";
import { Textarea } from "@/components/ui/textarea";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { messagebusApi } from "@/lib/api";
import { useToast } from "@/components/ui/use-toast";
import { DashboardLayout } from "@/components/layout/DashboardLayout";

export default function MessagebusPage() {
  const { toast } = useToast();
  const queryClient = useQueryClient();
  const [isSendDialogOpen, setIsSendDialogOpen] = useState(false);
  const [messageType, setMessageType] = useState("");
  const [messageData, setMessageData] = useState("{}");

  const { data: status, isLoading: statusLoading, error: statusError } = useQuery({
    queryKey: ["messagebus-status"],
    queryFn: messagebusApi.getStatus,
    refetchInterval: 5000,
  });

  const { data: messages, isLoading: messagesLoading } = useQuery({
    queryKey: ["messagebus-messages"],
    queryFn: () => messagebusApi.getRecentMessages(50),
    refetchInterval: 3000,
  });

  const { data: subscriptions } = useQuery({
    queryKey: ["messagebus-subscriptions"],
    queryFn: messagebusApi.getSubscriptions,
  });

  const reconnectMutation = useMutation({
    mutationFn: messagebusApi.reconnect,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["messagebus-status"] });
      toast({ title: "Reconnecting to messagebus..." });
    },
    onError: () => {
      toast({ title: "Failed to reconnect", variant: "destructive" });
    },
  });

  const sendMutation = useMutation({
    mutationFn: ({ type, data }: { type: string; data: Record<string, unknown> }) =>
      messagebusApi.sendMessage(type, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["messagebus-messages"] });
      setIsSendDialogOpen(false);
      setMessageType("");
      setMessageData("{}");
      toast({ title: "Message sent" });
    },
    onError: () => {
      toast({ title: "Failed to send message", variant: "destructive" });
    },
  });

  const handleSendMessage = () => {
    try {
      const data = JSON.parse(messageData);
      sendMutation.mutate({ type: messageType, data });
    } catch {
      toast({ title: "Invalid JSON data", variant: "destructive" });
    }
  };

  const formatUptime = (seconds: number) => {
    const days = Math.floor(seconds / 86400);
    const hours = Math.floor((seconds % 86400) / 3600);
    const mins = Math.floor((seconds % 3600) / 60);
    if (days > 0) return `${days}d ${hours}h`;
    if (hours > 0) return `${hours}h ${mins}m`;
    return `${mins}m`;
  };

  if (statusLoading) {
    return (
      <DashboardLayout title="Messagebus" description="OVOS Messagebus management">
        <div className="space-y-6">
          <Skeleton className="h-32 w-full" />
          <Skeleton className="h-64 w-full" />
        </div>
      </DashboardLayout>
    );
  }

  if (statusError) {
    return (
      <DashboardLayout title="Messagebus" description="OVOS Messagebus management">
        <Card>
          <CardContent className="py-8 text-center">
            <AlertCircle className="mx-auto h-12 w-12 text-muted-foreground mb-4" />
            <p className="text-muted-foreground">Unable to connect to messagebus</p>
            <Button className="mt-4" onClick={() => reconnectMutation.mutate()}>
              <RefreshCw className="mr-2 h-4 w-4" />
              Retry Connection
            </Button>
          </CardContent>
        </Card>
      </DashboardLayout>
    );
  }

  return (
    <DashboardLayout title="Messagebus" description="Monitor and manage OVOS messagebus connection">
      <div className="space-y-6">
        {/* Status Card */}
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <Radio className="h-6 w-6 text-primary" />
                <div>
                  <CardTitle>Connection Status</CardTitle>
                  <CardDescription>OVOS Messagebus WebSocket connection</CardDescription>
                </div>
              </div>
              <div className="flex items-center gap-2">
                <Badge variant={status?.connected ? "default" : "destructive"}>
                  {status?.connected ? (
                    <>
                      <CheckCircle2 className="mr-1 h-3 w-3" />
                      Connected
                    </>
                  ) : (
                    <>
                      <XCircle className="mr-1 h-3 w-3" />
                      Disconnected
                    </>
                  )}
                </Badge>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => reconnectMutation.mutate()}
                  disabled={reconnectMutation.isPending}
                >
                  <RefreshCw className={`mr-2 h-4 w-4 ${reconnectMutation.isPending ? "animate-spin" : ""}`} />
                  Reconnect
                </Button>
              </div>
            </div>
          </CardHeader>
          <CardContent>
            <div className="grid gap-4 md:grid-cols-4">
              <div className="rounded-lg border p-4">
                <p className="text-sm text-muted-foreground">Host</p>
                <p className="text-lg font-medium">{status?.host}:{status?.port}</p>
              </div>
              <div className="rounded-lg border p-4">
                <p className="text-sm text-muted-foreground">Uptime</p>
                <p className="text-lg font-medium">{status ? formatUptime(status.uptime_seconds) : "-"}</p>
              </div>
              <div className="rounded-lg border p-4">
                <p className="text-sm text-muted-foreground">Messages Sent</p>
                <p className="text-lg font-medium">{status?.messages_sent.toLocaleString()}</p>
              </div>
              <div className="rounded-lg border p-4">
                <p className="text-sm text-muted-foreground">Messages Received</p>
                <p className="text-lg font-medium">{status?.messages_received.toLocaleString()}</p>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Actions */}
        <div className="flex gap-2">
          <Button onClick={() => setIsSendDialogOpen(true)}>
            <Send className="mr-2 h-4 w-4" />
            Send Message
          </Button>
        </div>

        {/* Subscriptions */}
        {subscriptions && subscriptions.length > 0 && (
          <Card>
            <CardHeader>
              <CardTitle>Active Subscriptions</CardTitle>
              <CardDescription>Message types being monitored</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="flex flex-wrap gap-2">
                {subscriptions.map((sub) => (
                  <Badge key={sub.id} variant={sub.active ? "default" : "secondary"}>
                    {sub.message_type}
                  </Badge>
                ))}
              </div>
            </CardContent>
          </Card>
        )}

        {/* Recent Messages */}
        <Card>
          <CardHeader>
            <div className="flex items-center gap-2">
              <Activity className="h-5 w-5" />
              <CardTitle>Recent Messages</CardTitle>
            </div>
            <CardDescription>Last 50 messages on the bus</CardDescription>
          </CardHeader>
          <CardContent>
            {messagesLoading ? (
              <div className="space-y-2">
                {[...Array(5)].map((_, i) => (
                  <Skeleton key={i} className="h-12 w-full" />
                ))}
              </div>
            ) : messages && messages.length > 0 ? (
              <div className="space-y-2 max-h-96 overflow-y-auto">
                {messages.map((msg) => (
                  <div
                    key={msg.id}
                    className="flex items-start justify-between rounded-md border p-3 text-sm"
                  >
                    <div className="flex-1">
                      <p className="font-mono font-medium">{msg.type}</p>
                      <p className="text-xs text-muted-foreground mt-1">
                        {new Date(msg.timestamp).toLocaleTimeString()}
                      </p>
                    </div>
                    <code className="text-xs bg-muted px-2 py-1 rounded max-w-xs truncate">
                      {JSON.stringify(msg.data).slice(0, 50)}...
                    </code>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-center text-muted-foreground py-8">No recent messages</p>
            )}
          </CardContent>
        </Card>

        {/* Send Message Dialog */}
        <Dialog open={isSendDialogOpen} onOpenChange={setIsSendDialogOpen}>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Send Message</DialogTitle>
              <DialogDescription>
                Send a message to the OVOS messagebus
              </DialogDescription>
            </DialogHeader>
            <div className="space-y-4 py-4">
              <div className="space-y-2">
                <Label htmlFor="msg-type">Message Type</Label>
                <Input
                  id="msg-type"
                  placeholder="e.g., recognizer_loop:utterance"
                  value={messageType}
                  onChange={(e) => setMessageType(e.target.value)}
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="msg-data">Data (JSON)</Label>
                <Textarea
                  id="msg-data"
                  placeholder='{"utterances": ["hello"]}'
                  value={messageData}
                  onChange={(e) => setMessageData(e.target.value)}
                  className="font-mono text-sm"
                  rows={5}
                />
              </div>
            </div>
            <DialogFooter>
              <Button variant="outline" onClick={() => setIsSendDialogOpen(false)}>
                Cancel
              </Button>
              <Button
                onClick={handleSendMessage}
                disabled={!messageType || sendMutation.isPending}
              >
                Send
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>
    </DashboardLayout>
  );
}
