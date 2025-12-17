"use client";

/**
 * Admin Portal Sidebar Navigation
 * Implements comprehensive system configuration UI
 * Organized by: System, Security, Billing, Operations
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
  ChevronLeft,
  ChevronRight,
  ChevronDown,
  Mic,
  Phone,
  UserCog,
  Database,
  Server,
  HardDrive,
  Lock,
  Key,
  FileCode,
  BarChart3,
  LineChart,
  ScrollText,
  Cpu,
  Volume2,
  Brain,
  Network,
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
  children?: NavItem[];
}

const adminNavigation: NavItem[] = [
  { name: "Dashboard", href: "/admin/dashboard", icon: LayoutDashboard },
  
  // System Configuration
  {
    name: "System",
    href: "/admin/system",
    icon: Server,
    permission: "system:configure",
    children: [
      { name: "Infrastructure", href: "/admin/system/infrastructure", icon: Database },
      { name: "Workers", href: "/admin/system/workers", icon: Cpu },
      { name: "Gateway", href: "/admin/system/gateway", icon: Network },
      { name: "Observability", href: "/admin/system/observability", icon: BarChart3 },
    ],
  },
  
  // Security
  {
    name: "Security",
    href: "/admin/security",
    icon: Shield,
    permission: "system:configure",
    children: [
      { name: "Keycloak", href: "/admin/security/keycloak", icon: Lock },
      { name: "Policies", href: "/admin/security/policies", icon: FileCode },
      { name: "Secrets", href: "/admin/security/secrets", icon: Key },
    ],
  },
  
  // Billing
  {
    name: "Billing",
    href: "/admin/billing",
    icon: CreditCard,
    permission: "billing:view",
    children: [
      { name: "Overview", href: "/admin/billing", icon: CreditCard },
      { name: "Plans", href: "/admin/billing/plans", icon: Package },
      { name: "Metering", href: "/admin/billing/metering", icon: BarChart3 },
    ],
  },
  
  // Operations
  { name: "Tenants", href: "/admin/tenants", icon: Users, permission: "tenant:view" },
  { name: "Users", href: "/admin/users", icon: UserCog, permission: "tenant:manage" },
  { name: "Sessions", href: "/admin/sessions", icon: Phone, permission: "tenant:view" },
  { name: "Monitoring", href: "/admin/monitoring", icon: Activity, permission: "system:configure" },
  { name: "Audit Log", href: "/admin/audit", icon: FileText, permission: "tenant:view" },
];

interface AdminSidebarProps {
  onClose?: () => void;
}

function NavItemComponent({
  item,
  pathname,
  collapsed,
  onNavClick,
  hasPermission,
  expandedSections,
  toggleSection,
}: {
  item: NavItem;
  pathname: string;
  collapsed: boolean;
  onNavClick: () => void;
  hasPermission: (p: Permission) => boolean;
  expandedSections: Set<string>;
  toggleSection: (name: string) => void;
}) {
  const isActive = pathname === item.href || pathname.startsWith(`${item.href}/`);
  const hasChildren = item.children && item.children.length > 0;
  const isExpanded = expandedSections.has(item.name);

  if (hasChildren) {
    const visibleChildren = item.children!.filter(
      (child) => !child.permission || hasPermission(child.permission)
    );
    if (visibleChildren.length === 0) return null;

    return (
      <div>
        <button
          onClick={() => toggleSection(item.name)}
          className={cn(
            "flex w-full items-center gap-3 px-3 py-2 text-sm font-medium transition-colors rounded-md",
            isActive
              ? "bg-accent text-accent-foreground"
              : "text-muted-foreground hover:bg-accent hover:text-accent-foreground",
            collapsed && "justify-center px-2"
          )}
          title={collapsed ? item.name : undefined}
        >
          <item.icon className="h-5 w-5 flex-shrink-0" aria-hidden="true" />
          {!collapsed && (
            <>
              <span className="flex-1 text-left">{item.name}</span>
              <ChevronDown
                className={cn(
                  "h-4 w-4 transition-transform",
                  isExpanded && "rotate-180"
                )}
              />
            </>
          )}
        </button>
        {!collapsed && isExpanded && (
          <div className="ml-4 mt-1 space-y-1 border-l border-border pl-2">
            {visibleChildren.map((child) => {
              const childActive = pathname === child.href || pathname.startsWith(`${child.href}/`);
              return (
                <Link
                  key={child.name}
                  href={child.href}
                  onClick={onNavClick}
                  className={cn(
                    "flex items-center gap-3 px-3 py-2 text-sm font-medium transition-colors rounded-md",
                    childActive
                      ? "bg-primary text-primary-foreground"
                      : "text-muted-foreground hover:bg-accent hover:text-accent-foreground"
                  )}
                  aria-current={childActive ? "page" : undefined}
                >
                  <child.icon className="h-4 w-4 flex-shrink-0" aria-hidden="true" />
                  {child.name}
                </Link>
              );
            })}
          </div>
        )}
      </div>
    );
  }

  return (
    <Link
      href={item.href}
      onClick={onNavClick}
      className={cn(
        "flex items-center gap-3 px-3 py-2 text-sm font-medium transition-colors rounded-md",
        isActive
          ? "bg-primary text-primary-foreground"
          : "text-muted-foreground hover:bg-accent hover:text-accent-foreground",
        collapsed && "justify-center px-2"
      )}
      aria-current={isActive ? "page" : undefined}
      title={collapsed ? item.name : undefined}
    >
      <item.icon className="h-5 w-5 flex-shrink-0" aria-hidden="true" />
      {!collapsed && item.name}
    </Link>
  );
}

export function AdminSidebar({ onClose }: AdminSidebarProps) {
  const pathname = usePathname();
  const { user, logout, hasPermission } = useAuth();
  const [collapsed, setCollapsed] = useState(false);
  const [expandedSections, setExpandedSections] = useState<Set<string>>(
    new Set(["System", "Security", "Billing"])
  );

  const toggleSection = (name: string) => {
    setExpandedSections((prev) => {
      const next = new Set(prev);
      if (next.has(name)) {
        next.delete(name);
      } else {
        next.add(name);
      }
      return next;
    });
  };

  // Filter navigation items based on permissions
  const visibleNavigation = adminNavigation.filter(
    (item) => !item.permission || hasPermission(item.permission)
  );

  const handleNavClick = () => {
    onClose?.();
  };

  const handleLogout = async () => {
    await logout();
    onClose?.();
  };

  return (
    <aside 
      className={cn(
        "flex h-full flex-col border-r bg-card transition-all duration-300",
        collapsed ? "w-16" : "w-64"
      )}
      role="navigation" 
      aria-label="Admin navigation"
    >
      {/* Logo */}
      <div className="flex h-16 items-center justify-between border-b px-4">
        {!collapsed && (
          <div className="flex items-center gap-2">
            <Shield className="h-8 w-8 text-primary" aria-hidden="true" />
            <span className="text-lg font-semibold">Admin</span>
          </div>
        )}
        {collapsed && (
          <Shield className="h-8 w-8 text-primary mx-auto" aria-hidden="true" />
        )}
        <Button
          variant="ghost"
          size="icon"
          onClick={() => setCollapsed(!collapsed)}
          className="hidden md:flex"
          aria-label={collapsed ? "Expand sidebar" : "Collapse sidebar"}
        >
          {collapsed ? (
            <ChevronRight className="h-4 w-4" />
          ) : (
            <ChevronLeft className="h-4 w-4" />
          )}
        </Button>
      </div>

      {/* Main Navigation */}
      <nav className="flex-1 space-y-1 px-2 py-4 overflow-y-auto" aria-label="Admin">
        {visibleNavigation.map((item) => (
          <NavItemComponent
            key={item.name}
            item={item}
            pathname={pathname}
            collapsed={collapsed}
            onNavClick={handleNavClick}
            hasPermission={hasPermission}
            expandedSections={expandedSections}
            toggleSection={toggleSection}
          />
        ))}
      </nav>

      {/* Theme Toggle */}
      {!collapsed && (
        <div className="border-t px-3 py-4">
          <div className="flex items-center gap-3 px-3 py-2">
            <ThemeToggleSimple />
            <span className="text-sm text-muted-foreground">Theme</span>
          </div>
        </div>
      )}

      {/* User Section */}
      <div className="border-t p-4">
        <div className={cn("flex items-center gap-3", collapsed && "justify-center")}>
          <div className="flex h-10 w-10 items-center justify-center rounded-full bg-destructive text-destructive-foreground">
            {user?.username?.charAt(0).toUpperCase() || user?.email?.charAt(0).toUpperCase() || "A"}
          </div>
          {!collapsed && (
            <>
              <div className="flex-1 truncate">
                <p className="text-sm font-medium truncate">{user?.username || "Admin"}</p>
                <p className="text-xs text-muted-foreground truncate">{user?.email}</p>
              </div>
              <Button
                variant="ghost"
                size="icon"
                onClick={handleLogout}
                aria-label="Sign out"
                title="Sign out"
              >
                <LogOut className="h-4 w-4" aria-hidden="true" />
              </Button>
            </>
          )}
        </div>
      </div>
    </aside>
  );
}
