"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { getToken, getUser, clearAuth, type AuthUser } from "@/lib/auth-client";

interface UsageData {
  period: { start: string; end: string };
  usage: { compile: number; qa: number };
}

export default function DashboardPage() {
  const router = useRouter();
  const [user, setUser] = useState<AuthUser | null>(null);
  const [usage, setUsage] = useState<UsageData | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const token = getToken();
    const userData = getUser();

    if (!token || !userData) {
      router.push("/login");
      return;
    }

    setUser(userData);

    // Fetch usage
    fetch("/api/usage/current", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ token }),
    })
      .then((res) => res.json())
      .then((data) => {
        if (data.usage) setUsage(data);
      })
      .catch(console.error)
      .finally(() => setLoading(false));
  }, [router]);

  const handleLogout = () => {
    clearAuth();
    router.push("/");
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-surface-dark flex items-center justify-center">
        <p className="text-text-on-dark-muted">Loading...</p>
      </div>
    );
  }

  if (!user) return null;

  return (
    <div className="min-h-screen bg-surface-dark">
      {/* Header */}
      <div className="border-b border-white/10">
        <div className="max-w-5xl mx-auto px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-brand-blue to-brand-purple" />
            <span className="text-lg font-bold text-white">KnowledgeBase</span>
          </div>
          <div className="flex items-center gap-4">
            <span className="text-sm text-text-on-dark-muted">{user.email}</span>
            <button
              onClick={handleLogout}
              className="text-sm text-text-on-dark-muted hover:text-white transition-colors"
            >
              Sign out
            </button>
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="max-w-5xl mx-auto px-6 py-10">
        <h1 className="text-2xl font-bold text-white mb-8">Dashboard</h1>

        {/* Plan card */}
        <div className="bg-gradient-to-r from-brand-blue/20 to-brand-purple/20 border border-white/10 rounded-2xl p-6 mb-8">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-text-on-dark-muted mb-1">Current Plan</p>
              <p className="text-3xl font-bold text-white capitalize">
                {user.tier || "trial"}
              </p>
              {usage && (
                <p className="text-sm text-text-on-dark-muted mt-2">
                  This period: {usage.usage.compile} compilations,{" "}
                  {usage.usage.qa} Q&A queries
                </p>
              )}
            </div>
            <Link
              href="/#pricing"
              className="px-5 py-2 bg-white/10 text-white text-sm font-medium rounded-lg hover:bg-white/20 transition-colors"
            >
              Manage Plan
            </Link>
          </div>
        </div>

        {/* Quick actions */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="bg-white/5 border border-white/10 rounded-xl p-5">
            <h3 className="text-sm font-semibold text-white mb-2">
              Download App
            </h3>
            <p className="text-sm text-text-on-dark-muted mb-4">
              Get the desktop app for macOS, Windows, or Linux.
            </p>
            <div className="flex gap-2">
              <a
                href="#"
                className="px-4 py-2 bg-white/10 text-white text-xs font-medium rounded-lg hover:bg-white/20 transition-colors"
              >
                macOS
              </a>
              <a
                href="#"
                className="px-4 py-2 bg-white/10 text-white text-xs font-medium rounded-lg hover:bg-white/20 transition-colors"
              >
                Windows
              </a>
              <a
                href="#"
                className="px-4 py-2 bg-white/10 text-white text-xs font-medium rounded-lg hover:bg-white/20 transition-colors"
              >
                Linux
              </a>
            </div>
          </div>

          <div className="bg-white/5 border border-white/10 rounded-xl p-5">
            <h3 className="text-sm font-semibold text-white mb-2">
              License Token
            </h3>
            <p className="text-sm text-text-on-dark-muted mb-4">
              Use this token to activate the desktop app.
            </p>
            <button
              onClick={() => {
                const token = getToken();
                if (token) {
                  navigator.clipboard.writeText(token);
                  alert("License token copied to clipboard!");
                }
              }}
              className="px-4 py-2 bg-white/10 text-white text-xs font-medium rounded-lg hover:bg-white/20 transition-colors"
            >
              Copy License Token
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
