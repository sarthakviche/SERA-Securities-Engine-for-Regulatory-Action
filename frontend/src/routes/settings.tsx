import { createFileRoute } from "@tanstack/react-router";
import { AppShell } from "@/components/sera/app-shell";
import { PageHeader } from "@/components/sera/page-header";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { useTheme } from "@/lib/theme";
import {
  Moon,
  Sun,
  Building2,
  KeyRound,
  Bell,
  Users,
  Mail,
  MonitorSmartphone,
  Loader2,
} from "lucide-react";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { toast } from "sonner";

export const Route = createFileRoute("/settings")({
  head: () => ({ meta: [{ title: "Settings · SERA" }] }),
  component: Settings,
});

type SettingsTab = "Organization" | "Team & Roles" | "Security" | "Notifications";

function Settings() {
  const { theme, toggle } = useTheme();
  const [activeTab, setActiveTab] = useState<SettingsTab>("Organization");

  return (
    <AppShell>
      <PageHeader
        title="Settings"
        description="Preferences, security, and organization configuration."
      />

      <div className="grid gap-6 lg:grid-cols-[220px_1fr]">
        <nav className="space-y-1 text-sm">
          {(
            [
              { icon: Building2, label: "Organization" },
              { icon: Users, label: "Team & Roles" },
              { icon: KeyRound, label: "Security" },
              { icon: Bell, label: "Notifications" },
            ] as { icon: React.ElementType; label: SettingsTab }[]
          ).map((s) => {
            const Icon = s.icon;
            return (
              <button
                key={s.label}
                onClick={() => setActiveTab(s.label)}
                className={
                  "flex w-full items-center gap-2 rounded-md px-3 py-2 text-left " +
                  (activeTab === s.label
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
          {activeTab === "Organization" && (
            <>
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
                      (theme === "light"
                        ? "border-primary ring-2 ring-primary/20"
                        : "border-border")
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
                      (theme === "dark"
                        ? "border-primary ring-2 ring-primary/20"
                        : "border-border")
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
            </>
          )}

          {activeTab === "Notifications" && <NotificationsTab />}

          {(activeTab === "Team & Roles" || activeTab === "Security") && (
            <Card className="rounded-2xl p-6">
              <div className="text-sm font-semibold">{activeTab}</div>
              <p className="mt-2 text-xs text-muted-foreground">
                This section is coming soon.
              </p>
            </Card>
          )}
        </div>
      </div>
    </AppShell>
  );
}

// ── Notifications Tab ──────────────────────────────────────────────────────────

function NotificationsTab() {
  const [inApp, setInApp] = useState(true);
  const [email, setEmail] = useState(true);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    api
      .getNotificationPreferences()
      .then((data) => {
        if (data?.in_app_enabled !== undefined) {
          setInApp(data.in_app_enabled);
          setEmail(data.email_enabled);
        }
      })
      .catch(() => {
        // Backend unavailable — keep defaults
      })
      .finally(() => setLoading(false));
  }, []);

  const handleSave = async () => {
    setSaving(true);
    try {
      await api.updateNotificationPreferences({
        in_app_enabled: inApp,
        email_enabled: email,
      });
      toast.success("Notification preferences saved.");
    } catch {
      toast.error("Failed to save preferences. Please try again.");
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <Card className="rounded-2xl p-6 flex items-center justify-center gap-2 text-muted-foreground text-sm">
        <Loader2 className="h-4 w-4 animate-spin" /> Loading preferences…
      </Card>
    );
  }

  return (
    <Card className="rounded-2xl p-6">
      <div className="text-sm font-semibold">Notification Preferences</div>
      <p className="mt-1 text-xs text-muted-foreground">
        Control how SERA notifies you about compliance events.
      </p>

      <div className="mt-6 space-y-4">
        <PreferenceToggle
          id="pref-in-app"
          Icon={MonitorSmartphone}
          label="In-App Notifications"
          description="Show notifications inside the SERA interface in real time."
          checked={inApp}
          onChange={setInApp}
        />
        <PreferenceToggle
          id="pref-email"
          Icon={Mail}
          label="Email Notifications"
          description="Receive an email for important compliance events such as overdue tasks, evidence rejection, and gap detection."
          checked={email}
          onChange={setEmail}
        />
      </div>

      <div className="mt-6 flex justify-end">
        <Button onClick={handleSave} disabled={saving} className="gap-2">
          {saving && <Loader2 className="h-3.5 w-3.5 animate-spin" />}
          Save preferences
        </Button>
      </div>
    </Card>
  );
}

function PreferenceToggle({
  id,
  Icon,
  label,
  description,
  checked,
  onChange,
}: {
  id: string;
  Icon: React.ElementType;
  label: string;
  description: string;
  checked: boolean;
  onChange: (v: boolean) => void;
}) {
  return (
    <div className="flex items-start gap-4 rounded-xl border border-border p-4">
      <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-surface-2">
        <Icon className="h-4 w-4 text-muted-foreground" />
      </div>
      <div className="flex-1">
        <div className="text-sm font-medium text-foreground">{label}</div>
        <div className="mt-0.5 text-xs text-muted-foreground">{description}</div>
      </div>
      {/* Toggle switch */}
      <button
        id={id}
        type="button"
        role="switch"
        aria-checked={checked}
        onClick={() => onChange(!checked)}
        className={
          "relative mt-0.5 inline-flex h-5 w-9 shrink-0 cursor-pointer rounded-full border-2 " +
          "border-transparent transition-colors duration-200 ease-in-out focus:outline-none " +
          "focus:ring-2 focus:ring-primary focus:ring-offset-2 " +
          (checked ? "bg-primary" : "bg-muted")
        }
      >
        <span
          className={
            "pointer-events-none inline-block h-4 w-4 transform rounded-full bg-white shadow " +
            "ring-0 transition duration-200 ease-in-out " +
            (checked ? "translate-x-4" : "translate-x-0")
          }
        />
      </button>
    </div>
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
