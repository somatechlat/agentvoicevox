"use client";

/**
 * Skills Management Page
 * Implements Requirements E2/F2: OVOS Skills management for tenant
 */

import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Puzzle, Plus, Settings, AlertCircle, Search } from "lucide-react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { Skeleton } from "@/components/ui/skeleton";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Switch } from "@/components/ui/switch";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { skillsApi, Skill, SkillStoreItem, SkillConfig } from "@/lib/api";
import { useToast } from "@/components/ui/use-toast";
import { DashboardLayout } from "@/components/layout/DashboardLayout";

// Types imported from @/lib/api: Skill, SkillStoreItem, SkillConfig

export default function SkillsPage() {
  const { toast } = useToast();
  const queryClient = useQueryClient();
  const [searchQuery, setSearchQuery] = useState("");
  const [isInstallDialogOpen, setIsInstallDialogOpen] = useState(false);
  const [storeSearchQuery, setStoreSearchQuery] = useState("");
  const [selectedSkill, setSelectedSkill] = useState<Skill | null>(null);
  const [isConfigDialogOpen, setIsConfigDialogOpen] = useState(false);

  const { data: skills, isLoading, error } = useQuery({
    queryKey: ["skills"],
    queryFn: skillsApi.list,
  });

  const { data: storeResults, isLoading: isSearching } = useQuery({
    queryKey: ["skill-store", storeSearchQuery],
    queryFn: () => skillsApi.searchStore(storeSearchQuery),
    enabled: storeSearchQuery.length > 2,
  });

  const installMutation = useMutation({
    mutationFn: skillsApi.install,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["skills"] });
      setIsInstallDialogOpen(false);
      toast({ title: "Skill installed" });
    },
    onError: () => {
      toast({ title: "Failed to install skill", variant: "destructive" });
    },
  });

  const uninstallMutation = useMutation({
    mutationFn: skillsApi.uninstall,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["skills"] });
      toast({ title: "Skill uninstalled" });
    },
    onError: () => {
      toast({ title: "Failed to uninstall skill", variant: "destructive" });
    },
  });

  const enableMutation = useMutation({
    mutationFn: skillsApi.enable,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["skills"] });
      toast({ title: "Skill enabled" });
    },
    onError: () => {
      toast({ title: "Failed to enable skill", variant: "destructive" });
    },
  });

  const disableMutation = useMutation({
    mutationFn: skillsApi.disable,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["skills"] });
      toast({ title: "Skill disabled" });
    },
    onError: () => {
      toast({ title: "Failed to disable skill", variant: "destructive" });
    },
  });

  const filteredSkills = skills?.filter(
    (skill) =>
      skill.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      skill.description.toLowerCase().includes(searchQuery.toLowerCase())
  );

  if (isLoading) {
    return (
      <DashboardLayout title="Skills" description="Manage OVOS skills">
        <div className="space-y-6">
          {[...Array(3)].map((_, i) => (
            <Card key={i}>
              <CardHeader>
                <Skeleton className="h-6 w-32" />
              </CardHeader>
              <CardContent>
                <Skeleton className="h-20 w-full" />
              </CardContent>
            </Card>
          ))}
        </div>
      </DashboardLayout>
    );
  }

  if (error) {
    return (
      <DashboardLayout title="Skills" description="Manage OVOS skills">
        <Card>
          <CardContent className="py-8 text-center">
            <AlertCircle className="mx-auto h-12 w-12 text-muted-foreground mb-4" />
            <p className="text-muted-foreground">Unable to load skills</p>
          </CardContent>
        </Card>
      </DashboardLayout>
    );
  }

  return (
    <DashboardLayout title="Skills" description="Manage OVOS skills for your voice assistant">
      <div className="space-y-6">
        {/* Header */}
        <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
          <div className="relative flex-1 max-w-sm">
            <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
            <Input
              placeholder="Search installed skills..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-9"
            />
          </div>
          <Button onClick={() => setIsInstallDialogOpen(true)}>
            <Plus className="mr-2 h-4 w-4" />
            Install Skill
          </Button>
        </div>

        {/* Skills List */}
        {filteredSkills && filteredSkills.length === 0 ? (
          <Card>
            <CardContent className="py-12 text-center">
              <Puzzle className="mx-auto h-12 w-12 text-muted-foreground mb-4" />
              <h3 className="text-lg font-medium mb-2">No skills installed</h3>
              <p className="text-muted-foreground mb-4">
                Install skills from the OVOS skill store to extend your voice assistant
              </p>
              <Button onClick={() => setIsInstallDialogOpen(true)}>
                <Plus className="mr-2 h-4 w-4" />
                Install Skill
              </Button>
            </CardContent>
          </Card>
        ) : (
          <div className="grid gap-4">
            {filteredSkills?.map((skill) => (
              <Card key={skill.id}>
                <CardHeader>
                  <div className="flex items-start justify-between">
                    <div className="flex items-center gap-3">
                      <Puzzle className="h-8 w-8 text-primary" />
                      <div>
                        <CardTitle className="flex items-center gap-2">
                          {skill.name}
                          <Badge variant="outline">v{skill.version}</Badge>
                          <Badge
                            variant={skill.status === "enabled" ? "default" : skill.status === "error" ? "destructive" : "secondary"}
                          >
                            {skill.status}
                          </Badge>
                        </CardTitle>
                        <CardDescription>{skill.description}</CardDescription>
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      <Switch
                        checked={skill.status === "enabled"}
                        onCheckedChange={(checked) =>
                          checked ? enableMutation.mutate(skill.id) : disableMutation.mutate(skill.id)
                        }
                        disabled={enableMutation.isPending || disableMutation.isPending}
                      />
                      <Button
                        variant="outline"
                        size="icon"
                        onClick={() => {
                          setSelectedSkill(skill);
                          setIsConfigDialogOpen(true);
                        }}
                      >
                        <Settings className="h-4 w-4" />
                      </Button>
                    </div>
                  </div>
                </CardHeader>
                <CardContent>
                  <div className="grid gap-4 md:grid-cols-3 text-sm">
                    <div>
                      <span className="text-muted-foreground">Author:</span> {skill.author}
                    </div>
                    <div>
                      <span className="text-muted-foreground">Intents:</span> {skill.intents.length}
                    </div>
                    <div>
                      <span className="text-muted-foreground">Installed:</span>{" "}
                      {new Date(skill.installed_at).toLocaleDateString()}
                    </div>
                  </div>
                  {skill.intents.length > 0 && (
                    <div className="mt-4">
                      <Label className="text-sm text-muted-foreground">Supported Intents:</Label>
                      <div className="flex flex-wrap gap-2 mt-2">
                        {skill.intents.slice(0, 5).map((intent) => (
                          <Badge key={intent} variant="outline">
                            {intent}
                          </Badge>
                        ))}
                        {skill.intents.length > 5 && (
                          <Badge variant="outline">+{skill.intents.length - 5} more</Badge>
                        )}
                      </div>
                    </div>
                  )}
                </CardContent>
              </Card>
            ))}
          </div>
        )}

        {/* Install Dialog */}
        <Dialog open={isInstallDialogOpen} onOpenChange={setIsInstallDialogOpen}>
          <DialogContent className="max-w-2xl">
            <DialogHeader>
              <DialogTitle>Install Skill</DialogTitle>
              <DialogDescription>
                Search the OVOS skill store to find and install new skills
              </DialogDescription>
            </DialogHeader>

            <div className="space-y-4 py-4">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
                <Input
                  placeholder="Search skills..."
                  value={storeSearchQuery}
                  onChange={(e) => setStoreSearchQuery(e.target.value)}
                  className="pl-9"
                />
              </div>

              {isSearching && (
                <div className="space-y-2">
                  {[...Array(3)].map((_, i) => (
                    <Skeleton key={i} className="h-16 w-full" />
                  ))}
                </div>
              )}

              {storeResults && storeResults.length > 0 && (
                <div className="space-y-2 max-h-64 overflow-y-auto">
                  {storeResults.map((item) => (
                    <div
                      key={item.id}
                      className="flex items-center justify-between p-3 rounded-md border hover:bg-muted/50"
                    >
                      <div>
                        <p className="font-medium">{item.name}</p>
                        <p className="text-sm text-muted-foreground">{item.description}</p>
                        <p className="text-xs text-muted-foreground">
                          by {item.author} • {item.downloads} downloads
                        </p>
                      </div>
                      <Button
                        size="sm"
                        onClick={() => installMutation.mutate(item.id)}
                        disabled={installMutation.isPending}
                      >
                        Install
                      </Button>
                    </div>
                  ))}
                </div>
              )}

              {storeSearchQuery.length > 2 && !isSearching && storeResults?.length === 0 && (
                <p className="text-center text-muted-foreground py-4">
                  No skills found matching &quot;{storeSearchQuery}&quot;
                </p>
              )}
            </div>

            <DialogFooter>
              <Button variant="outline" onClick={() => setIsInstallDialogOpen(false)}>
                Close
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>

        {/* Config Dialog */}
        <Dialog open={isConfigDialogOpen} onOpenChange={setIsConfigDialogOpen}>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Configure {selectedSkill?.name}</DialogTitle>
              <DialogDescription>
                Adjust settings for this skill
              </DialogDescription>
            </DialogHeader>

            <div className="py-4">
              <p className="text-sm text-muted-foreground">
                Skill configuration options will be loaded from the skill&apos;s settings schema.
              </p>
            </div>

            <DialogFooter>
              <Button variant="outline" onClick={() => setIsConfigDialogOpen(false)}>
                Close
              </Button>
              <Button
                variant="destructive"
                onClick={() => {
                  if (selectedSkill && confirm("Uninstall this skill?")) {
                    uninstallMutation.mutate(selectedSkill.id);
                    setIsConfigDialogOpen(false);
                  }
                }}
              >
                Uninstall
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>
    </DashboardLayout>
  );
}
