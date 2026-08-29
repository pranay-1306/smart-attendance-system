import { API_BASE_URL } from "@/lib/api";
"use client";

import React, { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { UserCheck, Lock, Mail, ArrowRight, Camera } from "lucide-react";

export default function LoginPage() {
  const router = useRouter();
  const [emailOrCode, setEmailOrCode] = useState("EMP001");
  const [password, setPassword] = useState("123456");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError("");

    try {
      const formData = new FormData();
      formData.append("email_or_code", emailOrCode);
      formData.append("password", password);

      const res = await fetch("${API_BASE_URL}/api/v1/auth/login", {
        method: "POST",
        body: formData,
      });

      const data = await res.json();
      if (res.ok && data.success) {
        localStorage.setItem("currentUser", JSON.stringify(data.employee));
        router.push("/dashboard");
      } else {
        setError(data.detail || "Invalid credentials.");
      }
    } catch {
      setError("Unable to reach backend server on port 8000.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex items-center justify-center p-4">
      <div className="max-w-sm w-full bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-2xl space-y-6">
        
        <div className="text-center space-y-1">
          <div className="w-12 h-12 bg-blue-600/20 border border-blue-500/30 rounded-xl flex items-center justify-center mx-auto text-blue-400 mb-2">
            <UserCheck className="w-6 h-6" />
          </div>
          <h1 className="text-xl font-bold text-white">Employee Login</h1>
          <p className="text-xs text-slate-400">View your personal attendance history</p>
        </div>

        {error && (
          <div className="p-3 bg-rose-950/50 border border-rose-800/50 rounded-lg text-xs text-rose-300 text-center">
            {error}
          </div>
        )}

        <form onSubmit={handleLogin} className="space-y-4">
          <div>
            <label className="block text-xs font-medium text-slate-300 mb-1">Email or Employee Code</label>
            <div className="relative">
              <Mail className="w-4 h-4 text-slate-500 absolute left-3 top-1/2 -translate-y-1/2" />
              <input
                type="text"
                required
                value={emailOrCode}
                onChange={(e) => setEmailOrCode(e.target.value)}
                placeholder="e.g. EMP001"
                className="w-full bg-slate-950 border border-slate-800 rounded-lg pl-9 pr-3 py-2.5 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-blue-500 transition"
              />
            </div>
          </div>

          <div>
            <label className="block text-xs font-medium text-slate-300 mb-1">Password</label>
            <div className="relative">
              <Lock className="w-4 h-4 text-slate-500 absolute left-3 top-1/2 -translate-y-1/2" />
              <input
                type="password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="Default: 123456"
                className="w-full bg-slate-950 border border-slate-800 rounded-lg pl-9 pr-3 py-2.5 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-blue-500 transition"
              />
            </div>
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full py-2.5 bg-blue-600 hover:bg-blue-500 text-white text-xs font-semibold rounded-lg shadow-lg flex items-center justify-center gap-2 transition"
          >
            {loading ? "Signing In..." : "Sign In to Dashboard"} <ArrowRight className="w-3.5 h-3.5" />
          </button>
        </form>

        <div className="border-t border-slate-800 pt-4 text-center">
          <Link
            href="/"
            className="inline-flex items-center gap-1 text-xs text-slate-400 hover:text-slate-200 transition"
          >
            <Camera className="w-3.5 h-3.5 text-blue-400" /> Go to Camera Check-In
          </Link>
        </div>

      </div>
    </div>
  );
}
