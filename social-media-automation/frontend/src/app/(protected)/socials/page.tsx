"use client";

import { Camera, ExternalLink, Music2, Trash2, Tv, Users } from "lucide-react";
import { Suspense, useEffect } from "react";
import { useSearchParams } from "next/navigation";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { getToken } from "@/lib/api/client";
import { useDeleteSocial, useSocials } from "@/lib/api/hooks";

const PLATFORMS = [
  { key: "meta", label: "Facebook + Instagram", icon: Camera, color: "text-blue-600", help: "One OAuth flow connects both your FB Pages and the IG Business account linked to them." },
  { key: "youtube", label: "YouTube", icon: Tv, color: "text-red-600", help: "Connect your YouTube channel for Shorts and long-form uploads." },
  { key: "tiktok", label: "TikTok", icon: Music2, color: "text-pink-600", help: "Connect your TikTok account for Content Posting." },
  { key: "linkedin", label: "LinkedIn", icon: Users, color: "text-blue-700", help: "Connect your LinkedIn member account for long-format posts." },
];

const API_URL = process.env.NEXT_PUBLIC_API_URL?.replace(/\/$/, "") || "http://localhost:8000";

export default function SocialsPage() {
  return (
    <Suspense fallback={<p className="text-sm text-slate-500">Loading…</p>}>
      <SocialsInner />
    </Suspense>
  );
}

function SocialsInner() {
  const socials = useSocials();
  const del = useDeleteSocial();
  const searchParams = useSearchParams();

  // Show a toast when we return from an OAuth callback (?connected=youtube or ?error=...).
  useEffect(() => {
    const connected = searchParams.get("connected");
    const error = searchParams.get("error");
    if (connected) {
      toast.success(`${connected} connected!`);
      socials.refetch();
      window.history.replaceState({}, "", "/socials");
    } else if (error) {
      toast.error(`Connection failed: ${error}`);
      window.history.replaceState({}, "", "/socials");
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [searchParams]);

  function startConnect(platform: string) {
    const token = getToken();
    if (!token) {
      toast.error("Sign in first");
      return;
    }
    // The /connect endpoint accepts the JWT as a ?token= query param because a
    // full-page browser redirect can't send an Authorization header.
    toast.info("Redirecting to " + platform + "…");
    window.location.href = `${API_URL}/api/oauth/${platform}/connect?token=${encodeURIComponent(token)}`;
  }

  function platformIcon(name: string) {
    if (name === "instagram") return <Camera className="h-5 w-5 text-pink-500" />;
    if (name === "facebook") return <Camera className="h-5 w-5 text-blue-600" />;
    if (name === "youtube") return <Tv className="h-5 w-5 text-red-600" />;
    if (name === "tiktok") return <Music2 className="h-5 w-5 text-pink-600" />;
    if (name === "linkedin") return <Users className="h-5 w-5 text-blue-700" />;
    return null;
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Social Accounts</h1>
        <p className="mt-1 text-sm text-slate-500">
          Connect the social platforms you want to post to. Tokens are encrypted at rest.
        </p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Connect a platform</CardTitle>
          <CardDescription>
            You&apos;ll be redirected to the platform&apos;s consent screen, then back here.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
            {PLATFORMS.map(({ key, label, icon: Icon, color, help }) => (
              <button
                key={key}
                onClick={() => startConnect(key)}
                className="flex items-start gap-3 rounded-md border border-slate-200 bg-white p-4 text-left transition-all hover:border-slate-400 hover:shadow-sm"
              >
                <Icon className={`mt-0.5 h-5 w-5 ${color}`} />
                <div className="min-w-0 flex-1">
                  <p className="text-sm font-medium text-slate-900">{label}</p>
                  <p className="mt-0.5 text-xs text-slate-500">{help}</p>
                </div>
                <ExternalLink className="h-4 w-4 text-slate-400" />
              </button>
            ))}
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Connected accounts</CardTitle>
        </CardHeader>
        <CardContent>
          {socials.isLoading ? (
            <p className="text-sm text-slate-500">Loading…</p>
          ) : socials.data && socials.data.items.length > 0 ? (
            <ul className="divide-y divide-slate-100">
              {socials.data.items.map((s) => (
                <li key={s.id} className="flex items-center justify-between py-3">
                  <div className="flex items-center gap-3">
                    {platformIcon(s.platform)}
                    <div>
                      <p className="text-sm font-medium text-slate-900">{s.account_handle}</p>
                      <p className="mt-0.5 text-xs text-slate-500">
                        {s.platform} · {s.status}
                        {s.refresh_token_expires_at
                          ? ` · expires ${new Date(s.refresh_token_expires_at).toLocaleDateString()}`
                          : ""}
                      </p>
                    </div>
                  </div>
                  <Button
                    variant="ghost"
                    size="icon"
                    onClick={() => {
                      if (confirm(`Disconnect ${s.account_handle}?`)) {
                        del.mutate(s.id, {
                          onSuccess: () => toast.success("Disconnected"),
                          onError: () => toast.error("Disconnect failed"),
                        });
                      }
                    }}
                  >
                    <Trash2 className="h-4 w-4 text-red-500" />
                  </Button>
                </li>
              ))}
            </ul>
          ) : (
            <p className="py-6 text-center text-sm text-slate-500">
              No accounts connected yet.
            </p>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
