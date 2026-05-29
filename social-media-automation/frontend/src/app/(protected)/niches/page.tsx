"use client";

import { Plus, Trash2 } from "lucide-react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input, Label, Textarea } from "@/components/ui/input";
import { ApiError } from "@/lib/api/client";
import { useCreateNiche, useDeleteNiche, useNiches } from "@/lib/api/hooks";

export default function NichesPage() {
  const router = useRouter();
  const niches = useNiches();
  const createNiche = useCreateNiche();
  const deleteNiche = useDeleteNiche();
  const [showCreate, setShowCreate] = useState(false);

  // Form state for create
  const [form, setForm] = useState({
    name: "",
    description: "",
    target_audience: "",
    tone: "friendly, informative",
    voice_id: "EXAVITQu4vr4xnSDxMaL",
    content_pillars_raw: "",
  });

  function onCreate(e: React.FormEvent) {
    e.preventDefault();
    createNiche.mutate(
      {
        name: form.name,
        description: form.description,
        target_audience: form.target_audience,
        tone: form.tone,
        language: "en",
        content_pillars: form.content_pillars_raw
          .split("\n")
          .map((s) => s.trim())
          .filter(Boolean),
        forbidden_topics: [],
        cta: "",
        hashtag_seeds: [],
        video_length_default: "short",
        image_aspect_default: "9:16",
        image_count_short: 10,
        image_count_long: 20,
        llm_provider: "openai",
        llm_model: "gpt-4o-mini",
        image_provider: "pexels",
        voice_provider: "elevenlabs",
        voice_id: form.voice_id,
        voice_model: null,
        music_provider: "elevenlabs",
        music_enabled: true,
        topic_score_threshold: 7.0,
      },
      {
        onSuccess: (data) => {
          toast.success("Niche created");
          setShowCreate(false);
          const created = data as unknown as { id: number };
          router.push(`/niches/${created.id}`);
        },
        onError: (err) => {
          toast.error(err instanceof ApiError ? err.message : "Failed to create niche");
        },
      },
    );
  }

  async function onDelete(id: number) {
    if (!confirm("Delete this niche? Posts and topics will be cascaded.")) return;
    deleteNiche.mutate(id, {
      onSuccess: () => toast.success("Niche deleted"),
      onError: () => toast.error("Delete failed"),
    });
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Niches</h1>
          <p className="mt-1 text-sm text-slate-500">
            A niche defines what content your bot produces, who it's for, and which AI providers to use.
          </p>
        </div>
        <Button onClick={() => setShowCreate((v) => !v)}>
          <Plus className="h-4 w-4" />
          {showCreate ? "Cancel" : "New niche"}
        </Button>
      </div>

      {showCreate && (
        <Card>
          <CardHeader>
            <CardTitle>Create niche</CardTitle>
            <CardDescription>Fill in the basics — you can fine-tune providers and prompts later.</CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={onCreate} className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="n-name">Name</Label>
                <Input
                  id="n-name"
                  placeholder="e.g. Daily Fitness Tips"
                  value={form.name}
                  onChange={(e) => setForm({ ...form, name: e.target.value })}
                  required
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="n-desc">Description</Label>
                <Textarea
                  id="n-desc"
                  placeholder="3-5 sentences. State what the niche covers, what it does NOT cover, the angle, and any consistency rules."
                  value={form.description}
                  onChange={(e) => setForm({ ...form, description: e.target.value })}
                  required
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="n-audience">Target audience</Label>
                <Input
                  id="n-audience"
                  placeholder="Who is this content for?"
                  value={form.target_audience}
                  onChange={(e) => setForm({ ...form, target_audience: e.target.value })}
                  required
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="n-tone">Tone</Label>
                <Input
                  id="n-tone"
                  value={form.tone}
                  onChange={(e) => setForm({ ...form, tone: e.target.value })}
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="n-pillars">
                  Content pillars{" "}
                  <span className="text-xs font-normal text-slate-500">(one per line)</span>
                </Label>
                <Textarea
                  id="n-pillars"
                  placeholder={"5-minute desk-friendly workouts\nmeal prep hacks\nhabit-stacking for consistency"}
                  value={form.content_pillars_raw}
                  onChange={(e) => setForm({ ...form, content_pillars_raw: e.target.value })}
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="n-voice">ElevenLabs voice ID</Label>
                <Input
                  id="n-voice"
                  value={form.voice_id}
                  onChange={(e) => setForm({ ...form, voice_id: e.target.value })}
                />
                <p className="text-xs text-slate-500">
                  Find voice IDs at elevenlabs.io → Voice Library. Default is &quot;Sarah&quot;.
                </p>
              </div>
              <Button type="submit" disabled={createNiche.isPending}>
                {createNiche.isPending ? "Creating…" : "Create niche"}
              </Button>
            </form>
          </CardContent>
        </Card>
      )}

      <Card>
        <CardHeader>
          <CardTitle>Your niches</CardTitle>
        </CardHeader>
        <CardContent>
          {niches.isLoading ? (
            <p className="text-sm text-slate-500">Loading…</p>
          ) : niches.data && niches.data.items.length > 0 ? (
            <ul className="divide-y divide-slate-100">
              {niches.data.items.map((n) => (
                <li key={n.id} className="flex items-center justify-between py-3">
                  <div>
                    <Link
                      href={`/niches/${n.id}`}
                      className="text-sm font-medium text-slate-900 hover:underline"
                    >
                      {n.name}
                    </Link>
                    <p className="mt-0.5 text-xs text-slate-500">
                      {n.target_audience} · {n.llm_model} · {n.video_length_default}
                    </p>
                  </div>
                  <Button
                    variant="ghost"
                    size="icon"
                    onClick={() => onDelete(n.id)}
                    disabled={deleteNiche.isPending}
                  >
                    <Trash2 className="h-4 w-4 text-red-500" />
                  </Button>
                </li>
              ))}
            </ul>
          ) : (
            <p className="py-6 text-center text-sm text-slate-500">
              No niches yet. Click &quot;New niche&quot; above to get started.
            </p>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
