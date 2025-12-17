"use client";

/**
 * User Portal Layout
 * Implements Requirements C1-C4: User portal with limited navigation
 */

import { ReactNode } from "react";
import { useAuth } from "@/contexts/AuthContext";
import { UserSidebar } from "@/components/layout/UserSidebar";

interface UserLayoutProps {
  children: ReactNode;
}

export default function UserLayout({ children }: UserLayoutProps) {
  const { isLoading } = useAuth();

  if (isLoading) {
    return (
      <div className="flex h-screen items-center justify-center">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary" />
      </div>
    );
  }

  return (
    <div className="flex h-screen">
      <UserSidebar />
      <main className="flex-1 overflow-auto bg-background">
        {children}
      </main>
    </div>
  );
}
