import { useEffect, useState } from "react";
import { useAxiom } from "../store";
import { Save } from "lucide-react";

export default function Onboarding() {
  const { business, saveBusiness, fetchAll } = useAxiom();
  const [form, setForm] = useState({
    name: "", industry: "", stage: "Seed",
    website: "", description: "", goals: "",
  });
  const [saved, setSaved] = useState(false);

  useEffect(() => { fetchAll(); }, []);
  useEffect(() => {
    if (business) setForm({
      name: business.name || "",
      industry: business.industry || "",
      stage: business.stage || "Seed",
      website: business.website || "",
      description: business.description || "",
      goals: business.goals || "",
    });
  }, [business]);

  const handleSave = async () => {
    await saveBusiness(form);
    setSaved(true);
    setTimeout(() => setSaved(false), 2000);
  };

  const field = (k: keyof typeof form, label: string, ta = false, ph = "") => (
    <div>
      <label className="block text-[10px] uppercase tracking-widest text-muted font-mono mb-1.5">{label}</label>
      {ta ? (
        <textarea
          value={form[k]}
          onChange={(e) => setForm({ ...form, [k]: e.target.value })}
          rows={3}
          placeholder={ph}
          className="w-full bg-surface border border-border rounded px-3 py-2 text-sm focus:outline-none focus:border-mint/50 font-mono"
        />
      ) : (
        <input
          value={form[k]}
          onChange={(e) => setForm({ ...form, [k]: e.target.value })}
          placeholder={ph}
          className="w-full bg-surface border border-border rounded px-3 py-2 text-sm focus:outline-none focus:border-mint/50 font-mono"
        />
      )}
    </div>
  );

  return (
    <div className="p-6 max-w-2xl mx-auto">
      <header className="mb-6">
        <div className="text-[10px] uppercase tracking-widest text-muted font-mono">Discover · onboarding</div>
        <h1 className="text-2xl font-bold mt-1">Business profile</h1>
        <p className="text-muted text-sm mt-1">
          The context every agent works from. Change it anytime — agents will pick up new context on the next boardroom run.
        </p>
      </header>

      <div className="bg-surface border border-border rounded p-5 space-y-4">
        <div className="grid grid-cols-2 gap-4">
          {field("name", "Business name", false, "GlowVeda Skincare")}
          {field("industry", "Industry", false, "D2C Skincare")}
        </div>
        <div className="grid grid-cols-2 gap-4">
          {field("stage", "Stage", false, "Series A")}
          {field("website", "Website", false, "https://…")}
        </div>
        {field("description", "Description", true, "What do you sell, to whom, and what's your positioning?")}
        {field("goals", "Goals this year", true, "Revenue targets, unit economics, product bets…")}

        <div className="flex items-center justify-end gap-3 pt-2">
          {saved && <div className="text-mint text-xs font-mono">✓ Saved</div>}
          <button
            onClick={handleSave}
            className="flex items-center gap-2 bg-mint text-bg font-medium text-sm py-2 px-4 rounded hover:bg-mint/90 transition"
          >
            <Save size={14} /> Save profile
          </button>
        </div>
      </div>
    </div>
  );
}
