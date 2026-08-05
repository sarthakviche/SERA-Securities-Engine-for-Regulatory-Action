import { createFileRoute } from "@tanstack/react-router";
import { AppShell } from "@/components/sera/app-shell";
import { PageHeader } from "@/components/sera/page-header";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { useTheme } from "@/lib/theme";
import { Moon, Sun, Building2, KeyRound, Bell, Users } from "lucide-react";

export const Route = createFileRoute("/settings")({
  head: () => ({ meta: [{ title: "Settings · SERA" }] }),
  component: Settings,
});

function Settings() {
  const { theme, toggle } = useTheme();
  return (
    <AppShell>
      <PageHeader title="Settings" description="Preferences, security, and organization configuration." />

      <div className="grid gap-6 lg:grid-cols-[220px_1fr]">
        <nav className="space-y-1 text-sm">
          {[
            { icon: Building2, label: "Organization", active: true },
            { icon: Users, label: "Team & Roles" },
            { icon: KeyRound, label: "Security" },
            { icon: Bell, label: "Notifications" },
          ].map((s) => {
            const Icon = s.icon;
            return (
              <button
                key={s.label}
                className={
                  "flex w-full items-center gap-2 rounded-md px-3 py-2 text-left " +
                  (s.active
                    ? "bg-surface-2 font-medium text-foreground"
                    : "text-muted-foreground hover:bg-surface-2/60 hover:text-foreground")
                }
              >
                <Icon className="h-4 w-4" /> {s.label}
              </button>
            );
          })}
        </nav>

        <div className="space-y-6">
          <Card className="rounded-2xl p-6">
            <div className="text-sm font-semibold">Appearance</div>
            <p className="mt-1 text-xs text-muted-foreground">
              SERA supports full light and dark modes. Your choice is stored locally.
            </p>
            <div className="mt-4 flex gap-3">
              <button
                onClick={() => theme === "dark" && toggle()}
                className={
                  "flex-1 rounded-xl border p-4 text-left transition " +
                  (theme === "light" ? "border-primary ring-2 ring-primary/20" : "border-border")
                }
              >
                <Sun className="h-4 w-4" />
                <div className="mt-2 text-sm font-medium">Light</div>
                <div className="text-xs text-muted-foreground">Cream editorial</div>
              </button>
              <button
                onClick={() => theme === "light" && toggle()}
                className={
                  "flex-1 rounded-xl border p-4 text-left transition " +
                  (theme === "dark" ? "border-primary ring-2 ring-primary/20" : "border-border")
                }
              >
                <Moon className="h-4 w-4" />
                <div className="mt-2 text-sm font-medium">Dark</div>
                <div className="text-xs text-muted-foreground">Late-desk focus</div>
              </button>
            </div>
          </Card>

          <Card className="rounded-2xl p-6">
            <div className="text-sm font-semibold">Organization</div>
            <div className="mt-4 grid gap-4 md:grid-cols-2">
              <Field label="Organization Name" value="Capital Horizons Ltd" />
              <Field label="Intermediary Type" value="SEBI Stock Broker" />
              <Field label="Primary Jurisdiction" value="India" />
              <Field label="Employees" value="500+" />
            </div>
            <div className="mt-6 flex justify-end">
              <Button>Save changes</Button>
            </div>
          </Card>
        </div>
      </div>
    </AppShell>
  );
}

function Field({ label, value }: { label: string; value: string }) {
  return (
    <label className="block">
      <div className="text-[11px] font-semibold uppercase tracking-[0.14em] text-muted-foreground">
        {label}
      </div>
      <input
        defaultValue={value}
        className="mt-1 h-10 w-full rounded-md border border-border bg-surface px-3 text-sm outline-none focus:border-primary focus:ring-2 focus:ring-primary/15"
      />
    </label>
  );
}
