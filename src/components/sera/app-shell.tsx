import { Link, useRouterState, useNavigate } from "@tanstack/react-router";
import {
  Bell,
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
  Sparkles,
  Play,
  RotateCcw,
  ArrowRight,
  ChevronRight,
} from "lucide-react";
import type { ReactNode } from "react";
import { cn } from "@/lib/utils";
import { useTheme } from "@/lib/theme";
import { Button } from "@/components/ui/button";
import { nav } from "@/lib/mock-data";
import { useDemo } from "@/lib/demo";
import { toast } from "sonner";

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

export function AppShell({ children }: { children: ReactNode }) {
  const { theme, toggle } = useTheme();
  const path = useRouterState({ select: (s) => s.location.pathname });

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
              placeholder="Search circulars, entities, or tasks…"
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
            <Button variant="ghost" size="icon" className="relative" aria-label="Notifications">
              <Bell className="h-4 w-4" />
              <span className="absolute right-2.5 top-2.5 h-1.5 w-1.5 rounded-full bg-destructive" />
            </Button>
            <Button variant="ghost" size="icon" aria-label="Help">
              <HelpCircle className="h-4 w-4" />
            </Button>
            <div className="mx-3 h-6 w-px bg-border" />
            <div className="hidden text-right leading-tight md:block">
              <div className="text-sm font-semibold">Devansh Narlawar</div>
              <div className="text-[10px] font-medium uppercase tracking-[0.14em] text-muted-foreground">
                Super Administrator
              </div>
            </div>
            <div className="ml-3 flex h-9 w-9 items-center justify-center rounded-full bg-primary/15 text-xs font-semibold text-primary">
              DN
            </div>
          </div>
        </header>

        <main className="mx-auto w-full max-w-[1400px] px-8 py-8">{children}</main>

        <button
          type="button"
          aria-label="AI Assist"
          className="fixed bottom-6 right-6 z-40 flex h-12 w-12 items-center justify-center rounded-full bg-primary text-primary-foreground shadow-lg shadow-primary/30 transition hover:scale-105"
        >
          <Sparkles className="h-5 w-5" />
        </button>

        <FloatingDemoBar />
      </div>
    </div>
  );
}

function FloatingDemoBar() {
  const { demoStage, setDemoStage, resetDemo, isDemoActive } = useDemo();
  const navigate = useNavigate();

  if (!isDemoActive) return null;

  const stagesInfo: Record<string, { label: string; desc: string; next?: string; nextStage?: any; route?: string }> = {
    DETECTED: {
      label: "Circular Ingestion",
      desc: "Simulating SEBI document parsing...",
      next: "View Inbox",
      nextStage: "ANALYZED",
      route: "/inbox",
    },
    ANALYZED: {
      label: "Regulatory Inbox",
      desc: "Circular detected. Open Workspace to review analysis.",
      next: "Review Analysis",
      nextStage: "INTERPRETATION_APPROVED",
      route: "/workspace",
    },
    INTERPRETATION_APPROVED: {
      label: "Workspace Approved",
      desc: "AI analysis approved. Check obligations register.",
      next: "View Impact Map",
      nextStage: "IMPACT_MAPPED",
      route: "/impact-map",
    },
    IMPACT_MAPPED: {
      label: "Impact Mapped",
      desc: "Organization scope mapped. Approve action plan.",
      next: "View Action Plan",
      nextStage: "PLAN_APPROVED",
      route: "/implementation-plan",
    },
    PLAN_APPROVED: {
      label: "Tasks Created (Stage 1)",
      desc: "Implementation plan locked. Advance tasks to dev.",
      next: "Advance: Dev Complete",
      nextStage: "IMPLEMENTING",
      route: "/implementation-tracker",
    },
    IMPLEMENTING: {
      label: "Development (Stage 2)",
      desc: "SOP updated, IT configs complete. Advance to QA.",
      next: "Advance: QA Complete",
      nextStage: "EVIDENCE_REVIEW",
      route: "/implementation-tracker",
    },
    EVIDENCE_REVIEW: {
      label: "Evidence Review (Stage 3)",
      desc: "QA tests passed, files uploaded. Seal compliance.",
      next: "Verify & Seal Compliant",
      nextStage: "COMPLIANT",
      route: "/implementation-tracker",
    },
    COMPLIANT: {
      label: "Compliant & Monitored",
      desc: "Obligation OB-MIRSD-104 sealed & compliant. Demo complete!",
      next: "Reset Demo",
      nextStage: "OFF",
      route: "/",
    },
  };

  const current = stagesInfo[demoStage];
  if (!current) return null;

  const handleNext = () => {
    if (current.nextStage === "OFF") {
      resetDemo();
      toast.success("Demo Mode reset successfully.");
      navigate({ to: "/" });
    } else {
      setDemoStage(current.nextStage);
      toast.success(`Demo Advanced: ${stagesInfo[current.nextStage]?.label || current.nextStage}`);
      if (current.route) {
        navigate({ to: current.route });
      }
    }
  };

  const handleReset = () => {
    resetDemo();
    toast.success("Demo Mode reset successfully.");
    navigate({ to: "/" });
  };

  return (
    <div className="fixed bottom-6 left-1/2 -translate-x-1/2 z-50 flex items-center gap-4 bg-background/95 dark:bg-zinc-950/95 border border-amber-500/35 px-4 py-2 rounded-full shadow-2xl backdrop-blur max-w-lg md:max-w-2xl transition hover:border-amber-500/50">
      <div className="flex items-center gap-2 py-0.5">
        <span className="flex h-5 w-5 items-center justify-center rounded-full bg-amber-500/15 text-amber-600 dark:text-amber-400 font-mono text-[9px] font-bold shrink-0">
          D
        </span>
        <div className="leading-none shrink-0 text-left">
          <div className="text-[8px] font-bold text-amber-500 uppercase tracking-widest">Demo Control</div>
          <div className="text-[11px] font-bold text-foreground flex items-center gap-1 mt-0.5">
            {current.label} 
            {demoStage !== "COMPLIANT" && <ChevronRight className="h-3 w-3 text-muted-foreground" />}
          </div>
        </div>
      </div>

      <div className="h-5 w-px bg-border shrink-0 hidden md:block" />

      <p className="text-[10px] text-muted-foreground hidden md:block max-w-[200px] truncate leading-normal text-left">
        {current.desc}
      </p>

      <div className="flex items-center gap-1 ml-auto">
        <Button
          size="sm"
          variant="ghost"
          onClick={handleReset}
          className="h-7 text-[10px] text-muted-foreground hover:text-foreground cursor-pointer px-2 rounded-full border-none bg-transparent hover:bg-muted"
        >
          <RotateCcw className="h-3 w-3 mr-1" /> Reset
        </Button>
        <Button
          size="sm"
          onClick={handleNext}
          className="h-7 text-[10px] bg-gradient-to-r from-amber-500 to-orange-600 hover:from-amber-600 hover:to-orange-700 text-white font-semibold cursor-pointer border-none shadow px-3 rounded-full gap-1"
        >
          {demoStage === "COMPLIANT" ? "Reset Demo" : current.next} <ArrowRight className="h-3 w-3" />
        </Button>
      </div>
    </div>
  );
}
