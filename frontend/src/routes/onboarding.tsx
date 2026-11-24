import { createFileRoute, useNavigate } from "@tanstack/react-router";
import { useEffect, useState } from "react";
import { ArrowRight, Check, Loader2, Plus, X } from "lucide-react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { sera, useMeta, useSeraMutation } from "@/lib/sera";
import { cn } from "@/lib/utils";

export const Route = createFileRoute("/onboarding")({
  head: () => ({ meta: [{ title: "Set up your organisation · SERA" }] }),
  component: Onboarding,
});

function Onboarding() {
  const { data: meta } = useMeta();
  const navigate = useNavigate();
  const [name, setName] = useState("");
  const [officer, setOfficer] = useState("");
  const [entities, setEntities] = useState<string[]>([]);
  const [depts, setDepts] = useState<string[]>([]);
  const [systems, setSystems] = useState<string[]>([]);
  const save = useSeraMutation(() => sera.updateOrg({ name, officer_name: officer, entity_types: entities, departments: depts, systems }));

  useEffect(() => {
    if (!meta) return;
    setName(meta.org.name);
    setOfficer(meta.org.officer_name ?? "");
    setEntities(meta.org.entity_types);
    setDepts(meta.org.departments);
    setSystems(meta.org.systems);
  }, [meta]);

  const submit = () =>
    save.mutate(undefined, {
      onSuccess: () => {
        if (officer.trim()) localStorage.setItem("sera-actor", officer.trim());
        toast.success("Organisation profile saved. Applicability uses it from the next analysis.");
        navigate({ to: "/" });
      },
      onError: (e) => toast.error(e.message),
    });

  return (
    <div className="min-h-screen bg-background px-6 py-12">
      <div className="mx-auto max-w-3xl">
        <div className="font-display text-3xl">SERA</div>
        <h1 className="mt-6 font-display text-4xl leading-tight">Tell SERA who you are</h1>
        <p className="mt-2 max-w-xl text-muted-foreground">
          SERA uses this profile to decide which obligations apply to you and which departments and systems they affect. It is stored only in your local database.
        </p>
        {!meta ? (
          <div className="mt-10 flex items-center gap-2 text-sm text-muted-foreground"><Loader2 className="h-4 w-4 animate-spin" /> Connecting to backend…</div>
        ) : (
          <div className="mt-8 space-y-6">
            <Card className="grid gap-4 rounded-2xl p-6 md:grid-cols-2">
              <label className="text-sm">
                <div className="mb-1.5 font-medium">Organisation name</div>
                <Input value={name} onChange={(e) => setName(e.target.value)} />
              </label>
              <label className="text-sm">
                <div className="mb-1.5 font-medium">Compliance officer</div>
                <Input value={officer} onChange={(e) => setOfficer(e.target.value)} placeholder="Your name" />
              </label>
            </Card>
            <Card className="rounded-2xl p-6">
              <div className="font-medium">SEBI registrations</div>
              <div className="mb-4 text-sm text-muted-foreground">Select every intermediary category you are registered as.</div>
              <div className="grid gap-2 sm:grid-cols-2 md:grid-cols-3">
                {meta.entity_types.map((e) => {
                  const on = entities.includes(e.key);
                  return (
                    <button key={e.key} onClick={() => setEntities((s) => (on ? s.filter((x) => x !== e.key) : [...s, e.key]))} className={cn("flex items-center justify-between rounded-lg border px-3 py-2.5 text-left text-sm transition", on ? "border-primary bg-primary/5" : "border-border hover:border-primary/40")}>
                      {e.label}
                      {on && <Check className="h-4 w-4 text-primary" />}
                    </button>
                  );
                })}
              </div>
            </Card>
            <ChipEditor title="Departments" hint="Owners SERA can assign obligations and tasks to." items={depts} setItems={setDepts} />
            <ChipEditor title="Systems" hint="Platforms SERA can flag for change." items={systems} setItems={setSystems} />
            <div className="flex justify-end gap-3">
              <Button variant="ghost" onClick={() => navigate({ to: "/" })}>Skip</Button>
              <Button disabled={!name.trim() || entities.length === 0 || save.isPending} onClick={submit}>
                {save.isPending && <Loader2 className="mr-1.5 h-4 w-4 animate-spin" />} Save and continue <ArrowRight className="ml-1.5 h-4 w-4" />
              </Button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

function ChipEditor({ title, hint, items, setItems }: { title: string; hint: string; items: string[]; setItems: (f: (s: string[]) => string[]) => void }) {
  const [v, setV] = useState("");
  const add = () => {
    const t = v.trim();
    if (t && !items.includes(t)) setItems((s) => [...s, t]);
    setV("");
  };
  return (
    <Card className="rounded-2xl p-6">
      <div className="font-medium">{title}</div>
      <div className="mb-4 text-sm text-muted-foreground">{hint}</div>
      <div className="flex flex-wrap gap-2">
        {items.map((i) => (
          <span key={i} className="inline-flex items-center gap-1 rounded-full border border-border bg-surface px-3 py-1 text-sm">
            {i}
            <button onClick={() => setItems((s) => s.filter((x) => x !== i))} aria-label={`Remove ${i}`}><X className="h-3 w-3 text-muted-foreground hover:text-foreground" /></button>
          </span>
        ))}
      </div>
      <div className="mt-3 flex max-w-sm gap-2">
        <Input value={v} onChange={(e) => setV(e.target.value)} onKeyDown={(e) => e.key === "Enter" && add()} placeholder={`Add ${title.toLowerCase().slice(0, -1)}`} />
        <Button variant="outline" onClick={add}><Plus className="h-4 w-4" /></Button>
      </div>
    </Card>
  );
}
