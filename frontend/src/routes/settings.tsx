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
import { Link } from "@tanstack/react-router";
import { Input } from "@/components/ui/input";
import { providerLabel, useMeta } from "@/lib/sera";
import { toast } from "sonner";

export const Route = createFileRoute("/settings")({
  head: () => ({ meta: [{ title: "Settings · SERA" }] }),
  component: Settings,
});

type SettingsTab = "Organization" | "Identity" | "AI Engine" | "Notifications";

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
              { icon: Users, label: "Identity" },
              { icon: KeyRound, label: "AI Engine" },
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

              <OrgCard />
            </>
          )}

          {activeTab === "Notifications" && <NotificationsTab />}

          {activeTab === "Identity" && <IdentityCard />}
          {activeTab === "AI Engine" && <EngineCard />}
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

function OrgCard() {
  const { data } = useMeta();
  const labels = Object.fromEntries((data?.entity_types ?? []).map((e) => [e.key, e.label]));
  return (
    <Card className="rounded-2xl p-6">
      <div className="text-sm font-semibold">Organization profile</div>
      <p className="mt-1 text-xs text-muted-foreground">Drives applicability (which obligations apply to you) and impact mapping.</p>
      <div className="mt-4 grid gap-4 md:grid-cols-2">
        <Field label="Organization Name" value={data?.org.name ?? "-"} />
        <Field label="Registered as" value={(data?.org.entity_types ?? []).map((e) => labels[e] ?? e).join(", ") || "-"} />
        <Field label="Departments" value={`${data?.org.departments.length ?? 0} configured`} />
        <Field label="Systems" value={`${data?.org.systems.length ?? 0} configured`} />
      </div>
      <div className="mt-6 flex justify-end">
        <Button asChild><Link to="/onboarding">Edit profile</Link></Button>
      </div>
    </Card>
  );
}

function IdentityCard() {
  const [name, setName] = useState("");
  useEffect(() => setName(localStorage.getItem("sera-actor") || "Compliance Officer"), []);
  return (
    <Card className="rounded-2xl p-6">
      <div className="text-sm font-semibold">Acting as</div>
      <p className="mt-1 text-xs text-muted-foreground">Recorded against approvals, task updates and evidence in the audit trail. This local build has no login.</p>
      <div className="mt-4 flex max-w-md gap-2">
        <Input value={name} onChange={(e) => setName(e.target.value)} />
        <Button onClick={() => { localStorage.setItem("sera-actor", name.trim() || "Compliance Officer"); toast.success("Saved"); }}>Save</Button>
      </div>
    </Card>
  );
}

function EngineCard() {
  const { data } = useMeta();
  return (
    <Card className="rounded-2xl p-6 text-sm">
      <div className="font-semibold">Analysis engine</div>
      <div className="mt-2 text-2xl font-semibold">{providerLabel(data?.provider)}</div>
      <p className="mt-3 text-muted-foreground">
        SERA always runs its deterministic, citation-verified engine locally. Add <code className="rounded bg-muted px-1">ANTHROPIC_API_KEY</code> (Claude) or{" "}
        <code className="rounded bg-muted px-1">GROQ_API_KEY</code> to <code className="rounded bg-muted px-1">backend/.env</code> and restart. The LLM then proposes obligations,
        and SERA only accepts those whose quoted text is found verbatim in the circular.
      </p>
    </Card>
  );
}
