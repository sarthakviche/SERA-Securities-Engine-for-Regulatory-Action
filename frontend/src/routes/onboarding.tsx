import { createFileRoute, useNavigate } from "@tanstack/react-router";
import { useState } from "react";
import { Button } from "@/components/ui/button";
import { ArrowRight, Check, Upload } from "lucide-react";
import { cn } from "@/lib/utils";

export const Route = createFileRoute("/onboarding")({
  head: () => ({ meta: [{ title: "Welcome · SERA" }] }),
  component: Onboarding,
});

const STEPS = ["Organisation Setup", "Knowledge Mapping", "Workflow Intelligence", "Finalization"];

function Onboarding() {
  const [step, setStep] = useState(0);
  const navigate = useNavigate();

  return (
    <div className="grid min-h-screen grid-cols-1 md:grid-cols-[minmax(0,42%)_1fr]">
      {/* Left rail */}
      <div className="relative flex flex-col justify-between bg-[oklch(0.22_0.06_145)] p-10 text-[oklch(0.95_0.02_90)] md:p-14">
        <div>
          <div className="text-[11px] font-semibold uppercase tracking-[0.18em] text-white/70">
            Institutional Regulatory Infrastructure
          </div>
          <h1 className="mt-10 font-display text-6xl leading-none tracking-tight">SERA</h1>
          <p className="mt-6 max-w-md text-sm leading-relaxed text-white/80">
            SERA translates regulatory intent into operational action. Building the digital vault
            for high-performance compliance.
          </p>
        </div>
        <ol className="mt-16 space-y-4">
          {STEPS.map((label, i) => {
            const done = i < step;
            const active = i === step;
            return (
              <li key={label} className="flex items-center gap-3">
                <span
                  className={cn(
                    "flex h-7 w-7 items-center justify-center rounded-full border text-xs font-semibold transition",
                    done
                      ? "border-emerald-300 bg-emerald-300 text-[oklch(0.22_0.06_145)]"
                      : active
                        ? "border-emerald-300 bg-emerald-300/20 text-emerald-200"
                        : "border-white/25 text-white/50",
                  )}
                >
                  {done ? <Check className="h-3.5 w-3.5" /> : i + 1}
                </span>
                <span
                  className={cn(
                    "text-sm",
                    active ? "font-medium text-white" : "text-white/60",
                  )}
                >
                  {label}
                </span>
              </li>
            );
          })}
        </ol>
      </div>

      {/* Right pane */}
      <div className="flex flex-col justify-center bg-background px-8 py-16 md:px-16">
        <div className="mx-auto w-full max-w-2xl">
          <h2 className="font-display text-4xl tracking-tight">Welcome to SERA</h2>
          <p className="mt-2 text-sm text-muted-foreground">
            {step === 0 && "Let's define the operational scope of your institution."}
            {step === 1 && "Upload your standing SOPs so SERA can index your obligations."}
            {step === 2 && "Tell SERA how your compliance workflow moves through approvals."}
            {step === 3 && "Review and confirm. You can adjust everything from Settings later."}
          </p>

          <div className="mt-10 space-y-6">
            {step === 0 && <StepOrg />}
            {step === 1 && <StepKnowledge />}
            {step === 2 && <StepWorkflow />}
            {step === 3 && <StepFinal />}
          </div>

          <div className="mt-10 flex justify-between">
            <Button
              variant="outline"
              disabled={step === 0}
              onClick={() => setStep((s) => Math.max(0, s - 1))}
            >
              Back
            </Button>
            {step < STEPS.length - 1 ? (
              <Button className="gap-2" onClick={() => setStep((s) => s + 1)}>
                Next Stage <ArrowRight className="h-4 w-4" />
              </Button>
            ) : (
              <Button className="gap-2" onClick={() => navigate({ to: "/" })}>
                Enter SERA <ArrowRight className="h-4 w-4" />
              </Button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

function Label({ children }: { children: React.ReactNode }) {
  return (
    <div className="text-[11px] font-semibold uppercase tracking-[0.14em] text-muted-foreground">
      {children}
    </div>
  );
}

function TextInput({ placeholder, defaultValue }: { placeholder?: string; defaultValue?: string }) {
  return (
    <input
      placeholder={placeholder}
      defaultValue={defaultValue}
      className="mt-1 h-11 w-full rounded-md border border-border bg-surface px-3 text-sm outline-none focus:border-primary focus:ring-2 focus:ring-primary/15"
    />
  );
}

function StepOrg() {
  const [depts, setDepts] = useState<string[]>(["Compliance", "Risk"]);
  const options = ["Compliance", "Risk", "Operations", "IT Security"];
  return (
    <div className="grid gap-5 md:grid-cols-2">
      <div>
        <Label>Organisation Name</Label>
        <TextInput placeholder="e.g. Capital Horizons Ltd" />
      </div>
      <div>
        <Label>Intermediary Type</Label>
        <select className="mt-1 h-11 w-full rounded-md border border-border bg-surface px-3 text-sm">
          <option>SEBI Stock Broker</option>
          <option>SEBI Portfolio Manager</option>
          <option>SEBI Depository Participant</option>
        </select>
      </div>
      <div>
        <Label>Number of Employees</Label>
        <TextInput defaultValue="500+" />
      </div>
      <div>
        <Label>Primary Jurisdiction</Label>
        <TextInput defaultValue="India" />
      </div>
      <div className="md:col-span-2">
        <Label>Departments to Onboard</Label>
        <div className="mt-2 flex flex-wrap gap-2">
          {options.map((opt) => {
            const on = depts.includes(opt);
            return (
              <button
                key={opt}
                onClick={() =>
                  setDepts((d) => (on ? d.filter((x) => x !== opt) : [...d, opt]))
                }
                className={cn(
                  "flex items-center gap-2 rounded-md border px-3 py-2 text-sm transition",
                  on
                    ? "border-primary bg-primary/10 text-primary"
                    : "border-border text-muted-foreground hover:text-foreground",
                )}
              >
                <span
                  className={cn(
                    "flex h-4 w-4 items-center justify-center rounded border",
                    on ? "border-primary bg-primary text-primary-foreground" : "border-border",
                  )}
                >
                  {on && <Check className="h-3 w-3" />}
                </span>
                {opt}
              </button>
            );
          })}
        </div>
      </div>
    </div>
  );
}

function StepKnowledge() {
  return (
    <div>
      <Label>SOP & Policy Uploads</Label>
      <div className="mt-2 flex flex-col items-center justify-center rounded-xl border border-dashed border-border bg-surface-2/40 px-6 py-12 text-center">
        <div className="flex h-11 w-11 items-center justify-center rounded-full bg-primary/10 text-primary">
          <Upload className="h-5 w-5" />
        </div>
        <div className="mt-3 text-sm font-medium">Drop policies, SOPs or standing circulars</div>
        <div className="mt-1 text-xs text-muted-foreground">
          PDF, DOCX up to 25MB · SERA indexes clauses on ingest
        </div>
        <Button variant="outline" className="mt-4">Browse files</Button>
      </div>
    </div>
  );
}

function StepWorkflow() {
  return (
    <div className="space-y-5">
      {[
        "Who signs off on high-risk obligations?",
        "How many approval stages before a circular becomes an obligation?",
        "Which team receives evidence requests first?",
      ].map((q) => (
        <div key={q}>
          <Label>{q}</Label>
          <TextInput placeholder="Type your answer…" />
        </div>
      ))}
    </div>
  );
}

function StepFinal() {
  return (
    <div className="rounded-xl border border-border bg-surface-2/40 p-6">
      <div className="text-sm font-semibold">Ready to activate SERA</div>
      <p className="mt-2 text-sm text-muted-foreground">
        We'll provision your workspace, seed obligations from your SOPs, and route the first
        circulars to the correct owners. You can refine everything from Settings.
      </p>
    </div>
  );
}
