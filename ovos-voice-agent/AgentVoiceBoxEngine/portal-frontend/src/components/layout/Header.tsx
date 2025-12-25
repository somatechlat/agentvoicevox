"use client";

/**
 * Header Component - Clean, minimal design
 */

import { Bell, Search, Menu, X, HelpCircle } from "lucide-react";
import { Button } from "@/components/ui/button";
import { useAuth } from "@/contexts/AuthContext";

interface HeaderProps {
  title: string;
  description?: string;
  onMenuClick?: () => void;
  isMobileMenuOpen?: boolean;
}

export function Header({ title, description, onMenuClick, isMobileMenuOpen }: HeaderProps) {
  const { user } = useAuth();

  return (
    <header className="h-14 border-b border-border bg-card flex items-center justify-between px-4 md:px-6">
      {/* Left side - Mobile menu + Title */}
      <div className="flex items-center gap-4">
        {/* Mobile menu button */}
        <Button
          variant="ghost"
          size="icon"
          className="md:hidden h-8 w-8"
          onClick={onMenuClick}
          aria-label={isMobileMenuOpen ? "Close menu" : "Open menu"}
        >
          {isMobileMenuOpen ? (
            <X className="h-4 w-4" />
          ) : (
            <Menu className="h-4 w-4" />
          )}
        </Button>

        {/* Page title */}
        <div>
          <h1 className="text-base font-semibold text-foreground">{title}</h1>
          {description && (
            <p className="text-xs text-muted-foreground">{description}</p>
          )}
        </div>
      </div>

      {/* Right side - Actions */}
      <div className="flex items-center gap-2">
        {/* Search - Desktop only */}
        <div className="hidden lg:block">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
            <input
              type="search"
              placeholder="Search..."
              className="h-9 w-64 pl-9 pr-4 text-sm bg-muted border-0 rounded-lg placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring"
            />
            <kbd className="absolute right-3 top-1/2 -translate-y-1/2 text-[10px] text-muted-foreground bg-background px-1.5 py-0.5 rounded border border-border">
              ⌘K
            </kbd>
          </div>
        </div>

        {/* Help */}
        <Button variant="ghost" size="icon" className="h-8 w-8 text-muted-foreground hover:text-foreground">
          <HelpCircle className="h-4 w-4" />
        </Button>

        {/* Notifications */}
        <Button variant="ghost" size="icon" className="h-8 w-8 text-muted-foreground hover:text-foreground relative">
          <Bell className="h-4 w-4" />
          <span className="absolute top-1.5 right-1.5 h-1.5 w-1.5 rounded-full bg-destructive" />
        </Button>

        {/* User Avatar - Desktop only */}
        <div className="hidden md:flex items-center gap-2 pl-2 border-l border-border ml-2">
          <div className="flex h-8 w-8 items-center justify-center rounded-full bg-muted text-sm font-medium text-foreground">
            {user?.username?.charAt(0).toUpperCase() || user?.email?.charAt(0).toUpperCase() || "U"}
          </div>
          <div className="hidden xl:block">
            <p className="text-sm font-medium text-foreground">
              {user?.username || user?.email?.split("@")[0] || "User"}
            </p>
          </div>
        </div>
      </div>
    </header>
  );
}
