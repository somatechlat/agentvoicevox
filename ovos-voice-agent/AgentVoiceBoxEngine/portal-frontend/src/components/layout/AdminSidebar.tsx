"use client";

/**
 * Admin Portal Sidebar Navigation
 * Clean, minimal design matching the design system
 */

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  LayoutDashboard,
  Users,
  CreditCard,
  Package,
  Activity,
  FileText,
  Settings,
  LogOut,
  Shield,
  ChevronDown,
  Mic,
  Phone,
  UserCog,
  Database,
  Server,
  HardDrive,
  Lock,
  Key,
  BarChart3,
  Cpu,
  Network,
  Building2,
  Bell,
  Palette,
  ScrollText,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { useAuth } from "@/contexts/AuthContext";
import { Button } from "@/components/ui/button";
import { ThemeToggleSimple } from "@/components/ui/theme-toggle";
import { Permission } from "@/services/auth-service";
import { useState } from "react";

interface NavItem {
  name: string;
  href: string;
  icon: React.ElementType;
  permission?: Permission;
  badge?: string | number;
  children?: NavItem[];
}

// Navigation organized by sections matching the design screenshots
const navigationSections = [
  {
    title: "CORE",
    items: [
      { name: "Dashboard", href: "/admin/dashboard", icon: LayoutDashboard },
      { name: "Tenants", href: "/admin/tenants", icon: Building2, badge: 5 },
      { name: "Sessions", href: "/admin/sessions", icon: Phone },
    ],
  },
  {
    title: "PLATFORM",
    items: [
      { name: "Users", href: "/admin/users", icon: Users, badge: 8 },
      { name: "Billing", href: "/admin/billing", icon: CreditCard },
      { name: "Plans", href: "/admin/plans", icon: Package },
    ],
  },
  {
    title: "SYSTEM",
    items: [
      { name: "Monitoring", href: "/admin/monitoring", icon: Activity },
      { name: "Audit Log", href: "/admin/audit", icon: ScrollText },
      { name: "Settings", href: "/admin/settings", icon: Settings },
    ],
  },
];

interface AdminSidebarProps {
  onClose?: () => void;
}

export function AdminSidebar({ onClose }: AdminSidebarProps) {
  const pathname = usePathname();
  const { user, logout, hasPermission } = useAuth();
  const [searchQuery, setSearchQuery] = useState("");

  const handleNavClick = () => {
    onClose?.();
  };

  const handleLogout = async () => {
    await logout();
    onClose?.();
  };

  return (
    <aside className="flex h-full w-64 flex-col border-r border-border bg-card">
      {/* Logo */}
      <div className="flex h-14 items-center gap-3 border-b border-border px-4">
        <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-foreground">
          <Shield className="h-4 w-4 text-background" />
        </div>
        <span className="font-semibold text-foreground">Admin Portal</span>
      </div>

      {/* Environment Badges */}
      <div className="flex items-center gap-1 px-4 py-3 border-b border-border">
        <span className="px-2 py-0.5 text-[10px] font-medium bg-muted text-muted-foreground rounded">STG</span>
        <span className="px-2 py-0.5 text-[10px] font-medium bg-foreground text-background rounded">ADM</span>
        <span className="px-2 py-0.5 text-[10px] font-medium bg-muted text-muted-foreground rounded">DEV</span>
      </div>

      {/* Search */}
      <div className="px-3 py-3">
        <div className="relative">
          <svg
            className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
          </svg>
          <input
            type="text"
            placeholder="Search..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full h-9 pl-9 pr-3 text-sm bg-muted border-0 rounded-lg placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring"
          />
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex-1 overflow-y-auto px-3 py-2">
        {navigationSections.map((section) => (
          <div key={section.title} className="mb-6">
            <div className="px-3 py-2 text-[11px] font-medium text-muted-foreground tracking-wider">
              {section.title}
            </div>
            <div className="space-y-1">
              {section.items.map((item) => {
                const isActive = pathname === item.href || pathname.startsWith(`${item.href}/`);
                return (
                  <Link
                    key={item.name}
                    href={item.href}
                    onClick={handleNavClick}
                    className={cn(
                      "flex items-center gap-3 px-3 py-2 text-sm font-medium rounded-lg transition-colors",
                      isActive
                        ? "bg-accent text-foreground"
                        : "text-muted-foreground hover:bg-accent hover:text-foreground"
                    )}
                  >
                    <item.icon className="h-4 w-4 flex-shrink-0" />
                    <span className="flex-1">{item.name}</span>
                    {item.badge && (
                      <span className="px-1.5 py-0.5 text-[10px] font-medium bg-muted text-muted-foreground rounded">
                        {item.badge}
                      </span>
                    )}
                  </Link>
                );
              })}
            </div>
          </div>
        ))}
      </nav>

      {/* Theme Toggle */}
      <div className="border-t border-border px-3 py-3">
        <div className="flex items-center gap-3 px-3 py-2 text-sm text-muted-foreground">
          <Palette className="h-4 w-4" />
          <span className="flex-1">Theme</span>
          <ThemeToggleSimple />
        </div>
      </div>

      {/* User Section */}
      <div className="border-t border-border p-3">
        <div className="flex items-center gap-3 px-2">
          <div className="flex h-9 w-9 items-center justify-center rounded-full bg-muted text-sm font-medium text-foreground">
            {user?.username?.charAt(0).toUpperCase() || user?.email?.charAt(0).toUpperCase() || "A"}
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-sm font-medium text-foreground truncate">
              {user?.username || "Admin"}
            </p>
            <p className="text-xs text-muted-foreground truncate">
              {user?.email || "admin@example.com"}
            </p>
          </div>
          <Button
            variant="ghost"
            size="icon"
            onClick={handleLogout}
            className="h-8 w-8 text-muted-foreground hover:text-foreground"
          >
            <LogOut className="h-4 w-4" />
          </Button>
        </div>
      </div>
    </aside>
  );
}
