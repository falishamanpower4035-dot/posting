"use client";

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { useMe } from "@/lib/api/hooks";

export default function SettingsPage() {
  const me = useMe();
  const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Settings</h1>
        <p className="mt-1 text-sm text-slate-500">Account + deployment info.</p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Account</CardTitle>
        </CardHeader>
        <CardContent className="space-y-2">
          <Row label="Email">{me.data?.email ?? "—"}</Row>
          <Row label="Role">{me.data?.role ?? "—"}</Row>
          <Row label="Tenant">{me.data?.tenant_name ?? "—"} (id {me.data?.tenant_id ?? "—"})</Row>
          <Row label="Subscription">{me.data?.subscription_status ?? "—"}</Row>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Deployment</CardTitle>
          <CardDescription>Backend connection details.</CardDescription>
        </CardHeader>
        <CardContent className="space-y-2">
          <Row label="Backend API URL">
            <code className="rounded bg-slate-100 px-1.5 py-0.5 text-xs">{apiUrl}</code>
          </Row>
          <Row label="Docs">
            <a href={`${apiUrl}/docs`} target="_blank" rel="noreferrer" className="text-sm text-blue-600 underline">
              Swagger UI at {apiUrl}/docs
            </a>
          </Row>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Password change</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-slate-500">
            Password change UI ships in Phase 4 with the productization work. For now you can rotate the password by
            updating <code className="rounded bg-slate-100 px-1 py-0.5 text-xs">ADMIN_PASSWORD</code> in the backend{" "}
            <code className="rounded bg-slate-100 px-1 py-0.5 text-xs">.env</code> and restarting.
          </p>
        </CardContent>
      </Card>
    </div>
  );
}

function Row({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div className="flex justify-between gap-4 py-1.5 text-sm">
      <span className="text-slate-500">{label}</span>
      <span className="font-medium text-slate-900">{children}</span>
    </div>
  );
}
