import { Link, useRouterState, useNavigate } from "@tanstack/react-router";
import { useState } from "react";
import {
  Command,
  HelpCircle,
  LayoutDashboard,
  Inbox,
  Layers,
  ClipboardCheck,
  Network,
  Workflow,
  LineChart,
  ShieldCheck,
  History,
  Settings as SettingsIcon,
  Moon,
  Sun,
  Search,
  Cpu,
} from "lucide-react";
import type { ReactNode } from "react";
import { cn } from "@/lib/utils";
import { useTheme } from "@/lib/theme";
import { Button } from "@/components/ui/button";
import { useMeta, providerLabel } from "@/lib/sera";
import { NotificationPanel } from "@/components/sera/notification-panel";

const iconMap = {
  LayoutDashboard,
  Inbox,
  Layers,
  ClipboardCheck,
  Network,
  Workflow,
  LineChart,
  ShieldCheck,
  History,
};

const nav = [
  { to: "/", label: "Dashboard", icon: "LayoutDashboard" },
  { to: "/inbox", label: "Regulatory Inbox", icon: "Inbox" },
  { to: "/workspace", label: "Regulatory Workspace", icon: "Layers" },
  { to: "/obligations", label: "Obligations", icon: "ClipboardCheck" },
  { to: "/impact-map", label: "Impact Map", icon: "Network" },
  { to: "/implementation-plan", label: "Implementation Plan", icon: "Workflow" },
  { to: "/implementation-tracker", label: "Implementation Tracker", icon: "LineChart" },
  { to: "/compliance-register", label: "Compliance Register", icon: "ShieldCheck" },
  { to: "/audit-trail", label: "Audit Trail", icon: "History" },
] as const;

export function AppShell({ children }: { children: ReactNode }) {
  const { theme, toggle } = useTheme();
  const path = useRouterState({ select: (s) => s.location.pathname });
  const navigate = useNavigate();
  const { data: meta } = useMeta();
  const [q, setQ] = useState("");
  const officer = meta?.org.officer_name || "Compliance Officer";
  const initials = officer.split(/\s+/).map((w) => w[0]).join("").slice(0, 2).toUpperCase();

  return (
    <div className="flex min-h-screen bg-background text-foreground">
      {/* Sidebar */}
      <aside className="sticky top-0 flex h-screen w-64 shrink-0 flex-col bg-sidebar text-sidebar-foreground">
        <div className="px-6 pt-7 pb-8">
          <div className="font-display text-2xl tracking-tight text-sidebar-foreground">SERA</div>
          <div className="mt-1 text-[10px] font-medium uppercase tracking-[0.18em] text-sidebar-foreground/60">
            Regulatory Intelligence
          </div>
        </div>
        <nav className="flex-1 space-y-1 px-3">
          {nav.map((item) => {
            const Icon = iconMap[item.icon as keyof typeof iconMap] ?? LayoutDashboard;
            const active =
              item.to === "/" ? path === "/" : path === item.to || path.startsWith(item.to + "/");
            return (
              <Link
                key={item.to}
                to={item.to}
                className={cn(
                  "group flex items-center gap-3 rounded-md px-3 py-2 text-[13px] font-medium transition-colors",
                  active
                    ? "bg-sidebar-accent text-sidebar-accent-foreground shadow-[inset_2px_0_0_0_var(--sidebar-ring)]"
                    : "text-sidebar-foreground/75 hover:bg-sidebar-accent/60 hover:text-sidebar-foreground",
                )}
              >
                <Icon className="h-4 w-4 opacity-90" />
                <span>{item.label}</span>
              </Link>
            );
          })}
        </nav>
        <div className="px-3 pb-6">
          <Link
            to="/settings"
            className={cn(
              "flex items-center gap-3 rounded-md px-3 py-2 text-[13px] font-medium text-sidebar-foreground/75 hover:bg-sidebar-accent/60 hover:text-sidebar-foreground",
              path.startsWith("/settings") && "bg-sidebar-accent text-sidebar-accent-foreground",
            )}
          >
            <SettingsIcon className="h-4 w-4" />
            Settings
          </Link>
        </div>
      </aside>

      {/* Main column */}
      <div className="flex min-w-0 flex-1 flex-col">
        {/* Topbar */}
        <header className="sticky top-0 z-30 flex h-16 items-center gap-4 border-b border-border bg-background/85 px-8 backdrop-blur">
          <div className="relative flex-1 max-w-2xl">
            <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
            <input
              value={q}
              onChange={(e) => setQ(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter") navigate({ to: "/inbox", search: { q } as never });
              }}
              placeholder="Search circulars by title or reference… (Enter)"
              className="h-10 w-full rounded-full border border-border bg-surface pl-10 pr-16 text-sm outline-none placeholder:text-muted-foreground focus:border-primary focus:ring-2 focus:ring-primary/15"
            />
            <kbd className="absolute right-3 top-1/2 hidden -translate-y-1/2 items-center gap-1 rounded-md border border-border bg-background px-1.5 py-0.5 text-[10px] font-medium text-muted-foreground md:inline-flex">
              <Command className="h-3 w-3" /> K
            </kbd>
          </div>
          <div className="ml-auto flex items-center gap-1.5">
            <Button variant="ghost" size="icon" onClick={toggle} aria-label="Toggle theme">
              {theme === "dark" ? <Sun className="h-4 w-4" /> : <Moon className="h-4 w-4" />}
            </Button>
            <NotificationPanel />
            <Button variant="ghost" size="icon" aria-label="Help">
              <HelpCircle className="h-4 w-4" />
            </Button>
            <div className="mx-3 h-6 w-px bg-border" />
            <div className="hidden text-right leading-tight md:block">
              <div className="text-sm font-semibold">{officer}</div>
              <div className="text-[10px] font-medium uppercase tracking-[0.14em] text-muted-foreground">
                {meta?.org.name ?? "Compliance"}
              </div>
            </div>
            <div className="ml-3 flex h-9 w-9 items-center justify-center rounded-full bg-primary/15 text-xs font-semibold text-primary">
              {initials}
            </div>
          </div>
        </header>

        <main className="mx-auto w-full max-w-[1400px] px-8 py-8">{children}</main>

        <div
          title="Analysis engine in use"
          className="fixed bottom-5 right-6 z-40 flex items-center gap-1.5 rounded-full border border-border bg-background/90 px-3 py-1.5 text-[11px] text-muted-foreground shadow-sm backdrop-blur"
        >
          <Cpu className="h-3.5 w-3.5 text-primary" />
          {providerLabel(meta?.provider)}
        </div>

      </div>
    </div>
  );
}
