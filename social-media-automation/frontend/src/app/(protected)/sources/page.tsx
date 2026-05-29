"use client";

import { Play, Plus, Trash2 } from "lucide-react";
import { useState } from "react";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input, Label, Textarea } from "@/components/ui/input";
import { api, ApiError } from "@/lib/api/client";
import {
  useCreateTopicSource,
  useNiches,
  useRunTopicSourceNow,
  useTopicSources,
} from "@/lib/api/hooks";
import { formatRelativeDate } from "@/lib/utils";

const KINDS = [
  { value: "ai_generated", label: "AI-generated", help: "LLM generates topic ideas from your niche config. Zero external setup." },
  { value: "manual", label: "Manual", help: "Paste a list of topics in the config." },
  { value: "rss", label: "RSS feeds", help: "Pulls items from RSS feeds you provide." },
  { value: "news", label: "News API", help: "Uses NewsData.io to pull articles matching your niche keywords." },
];

export default function TopicSourcesPage() {
  const sources = useTopicSources();
  const niches = useNiches();
  const create = useCreateTopicSource();
  const runNow = useRunTopicSourceNow();
  const [showAdd, setShowAdd] = useState(false);
  const [draft, setDraft] = useState({
    niche_id: 0,
    kind: "ai_generated",
    config_raw: '{"count": 8}',
    enabled: true,
  });

  function onCreate(e: React.FormEvent) {
    e.preventDefault();
    let config_json: Record<string, unknown>;
    try {
      config_json = JSON.parse(draft.config_raw);
    } catch {
      toast.error("config_json must be valid JSON");
      return;
    }
    if (!draft.niche_id) {
      toast.error("Pick a niche");
      return;
    }
    create.mutate(
      {
        niche_id: draft.niche_id,
        kind: draft.kind,
        config_json,
        enabled: draft.enabled,
      },
      {
        onSuccess: () => {
          toast.success("Topic source added");
          setShowAdd(false);
        },
        onError: (err) => toast.error(err instanceof ApiError ? err.message : "Failed"),
      },
    );
  }

  async function onDelete(id: number) {
    if (!confirm("Delete this topic source?")) return;
    try {
      await api(`/api/topic-sources/${id}`, { method: "DELETE" });
      toast.success("Deleted");
      sources.refetch();
    } catch {
      toast.error("Delete failed");
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Topic Sources</h1>
          <p className="mt-1 text-sm text-slate-500">
            Where your topics come from. The worker checks enabled sources every 30 minutes.
          </p>
        </div>
        <Button onClick={() => setShowAdd((v) => !v)}>
          <Plus className="h-4 w-4" />
          {showAdd ? "Cancel" : "New source"}
        </Button>
      </div>

      {showAdd && (
        <Card>
          <CardHeader>
            <CardTitle>Add topic source</CardTitle>
            <CardDescription>One source per niche, per kind.</CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={onCreate} className="space-y-4">
              <div className="space-y-2">
                <Label>Niche</Label>
                <select
                  value={draft.niche_id}
                  onChange={(e) => setDraft({ ...draft, niche_id: Number(e.target.value) })}
                  className="flex h-10 w-full rounded-md border border-slate-200 bg-white px-3 py-2 text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-slate-300"
                  required
                >
                  <option value={0}>Select a niche…</option>
                  {niches.data?.items.map((n) => (
                    <option key={n.id} value={n.id}>
                      {n.name}
                    </option>
                  ))}
                </select>
              </div>
              <div className="space-y-2">
                <Label>Kind</Label>
                <select
                  value={draft.kind}
                  onChange={(e) => {
                    const defaults: Record<string, string> = {
                      ai_generated: '{"count": 8}',
                      manual: '{"topics": [{"title": "...", "content": "..."}]}',
                      rss: '{"feed_urls": ["https://..."]}',
                      news: '{"api_key": "newsdata-key", "max_results": 20}',
                    };
                    setDraft({ ...draft, kind: e.target.value, config_raw: defaults[e.target.value] || "{}" });
                  }}
                  className="flex h-10 w-full rounded-md border border-slate-200 bg-white px-3 py-2 text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-slate-300"
                >
                  {KINDS.map((k) => (
                    <option key={k.value} value={k.value}>
                      {k.label}
                    </option>
                  ))}
                </select>
                <p className="text-xs text-slate-500">{KINDS.find((k) => k.value === draft.kind)?.help}</p>
              </div>
              <div className="space-y-2">
                <Label>Configuration (JSON)</Label>
                <Textarea
                  rows={6}
                  value={draft.config_raw}
                  onChange={(e) => setDraft({ ...draft, config_raw: e.target.value })}
                  className="font-mono text-xs"
                />
              </div>
              <Button type="submit" disabled={create.isPending}>
                {create.isPending ? "Adding…" : "Add source"}
              </Button>
            </form>
          </CardContent>
        </Card>
      )}

      <Card>
        <CardHeader>
          <CardTitle>Configured sources</CardTitle>
        </CardHeader>
        <CardContent>
          {sources.isLoading ? (
            <p className="text-sm text-slate-500">Loading…</p>
          ) : sources.data && sources.data.items.length > 0 ? (
            <ul className="divide-y divide-slate-100">
              {sources.data.items.map((s) => (
                <li key={s.id} className="flex items-center justify-between py-3">
                  <div>
                    <p className="text-sm font-medium text-slate-900">
                      {KINDS.find((k) => k.value === s.kind)?.label || s.kind}
                      {!s.enabled && <span className="ml-2 text-xs text-slate-400">(disabled)</span>}
                    </p>
                    <p className="mt-0.5 text-xs text-slate-500">
                      niche #{s.niche_id} ·{" "}
                      {s.last_run_at ? `last run ${formatRelativeDate(s.last_run_at)}` : "never run"}
                    </p>
                  </div>
                  <div className="flex gap-1">
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() =>
                        runNow.mutate(s.id, {
                          onSuccess: (d) => {
                            const msg = (d as { message?: string } | undefined)?.message ?? "Source run complete";
                            toast.success(msg);
                          },
                          onError: (err) => toast.error(err instanceof ApiError ? err.message : "Run failed"),
                        })
                      }
                      disabled={runNow.isPending}
                    >
                      <Play className="h-4 w-4" /> Run now
                    </Button>
                    <Button variant="ghost" size="icon" onClick={() => onDelete(s.id)}>
                      <Trash2 className="h-4 w-4 text-red-500" />
                    </Button>
                  </div>
                </li>
              ))}
            </ul>
          ) : (
            <p className="py-6 text-center text-sm text-slate-500">
              No sources yet. Add one above so the worker has something to discover.
            </p>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
