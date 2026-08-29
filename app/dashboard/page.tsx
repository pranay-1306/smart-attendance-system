import { API_BASE_URL } from "@/lib/api";
"use client";

import React, { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import {
  Calendar,
  CheckCircle2,
  Camera,
  LogOut,
  MapPin,
  Percent,
  ShieldCheck,
  RefreshCw
} from "lucide-react";

interface EmployeeProfile {
  id: number;
  name: string;
  email: string;
  employee_code: string;
  department: string;
  designation: string;
}

interface DashboardData {
  employee: EmployeeProfile;
  today: {
    checked_in: string | null;
    checked_out: string | null;
    status: string;
  };
  metrics: {
    days_present_month: number;
    total_punches: number;
    on_time_rate: number;
  };
  history: Array<{
    id: number;
    timestamp: string;
    type: string;
    distance_meters: number;
    confidence: number;
    status: string;
  }>;
}

export default function EmployeeDashboard() {
  const router = useRouter();
  const [data, setData] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState<boolean>(true);

  const fetchPersonalData = async () => {
    setLoading(true);
    const storedUser = localStorage.getItem("currentUser");
    if (!storedUser) {
      router.push("/login");
      return;
    }

    try {
      const user: EmployeeProfile = JSON.parse(storedUser);
      const res = await fetch(`${API_BASE_URL}/api/v1/employee/${user.id}/dashboard`);
      if (res.ok) {
        const dashboardData = await res.json();
        setData(dashboardData);
      }
    } catch (err) {
      console.error("Failed to load dashboard", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchPersonalData();
  }, []);

  const handleLogout = () => {
    localStorage.removeItem("currentUser");
    router.push("/login");
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-slate-950 text-slate-100 flex items-center justify-center">
        <div className="flex items-center gap-2 text-xs text-slate-400">
          <RefreshCw className="w-4 h-4 animate-spin text-blue-400" /> Loading your personal dashboard...
        </div>
      </div>
    );
  }

  if (!data) return null;

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 p-6 md:p-10">
      <div className="max-w-6xl mx-auto space-y-8">
        
        {/* Header */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-800 pb-6">
          <div className="flex items-center gap-3">
            <div className="w-12 h-12 rounded-full bg-blue-600/20 border border-blue-500/30 flex items-center justify-center text-blue-400 font-bold text-lg">
              {data.employee.name.charAt(0)}
            </div>
            <div>
              <h1 className="text-xl font-bold text-white">{data.employee.name}</h1>
              <div className="flex items-center gap-2 text-xs text-slate-400">
                <span className="text-blue-400 font-mono">{data.employee.employee_code}</span>
                <span>•</span>
                <span>{data.employee.designation}</span>
                <span>•</span>
                <span className="text-slate-500">{data.employee.department}</span>
              </div>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <Link
              href="/"
              className="px-3.5 py-2 bg-blue-600 hover:bg-blue-500 text-white text-xs font-semibold rounded-lg shadow transition flex items-center gap-1.5"
            >
              <Camera className="w-3.5 h-3.5" /> Mark Check-In / Out
            </Link>

            <button
              onClick={handleLogout}
              className="px-3 py-2 bg-slate-900 hover:bg-slate-800 text-slate-300 text-xs font-medium rounded-lg border border-slate-800 transition flex items-center gap-1.5"
            >
              <LogOut className="w-3.5 h-3.5" /> Sign Out
            </button>
          </div>
        </div>

        {/* Presence & Metrics */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div className="md:col-span-2 bg-slate-900 border border-slate-800 rounded-xl p-5 space-y-4">
            <div className="flex items-center justify-between">
              <span className="text-xs font-medium text-slate-400 flex items-center gap-1.5">
                <Calendar className="w-4 h-4 text-blue-400" /> Today's Presence
              </span>
              <span className={`text-[10px] font-semibold px-2 py-0.5 rounded-full border ${
                data.today.status === "PRESENT"
                  ? "bg-emerald-950 text-emerald-300 border-emerald-800/50"
                  : "bg-slate-950 text-slate-400 border-slate-800"
              }`}>
                {data.today.status === "PRESENT" ? "MARKED PRESENT" : "NOT CHECKED IN"}
              </span>
            </div>

            <div className="grid grid-cols-2 gap-4 pt-1">
              <div className="bg-slate-950/60 p-3 rounded-lg border border-slate-800/60">
                <p className="text-[11px] text-slate-400">First Arrival (Check-In)</p>
                <p className="text-base font-bold text-emerald-400 mt-1">
                  {data.today.checked_in || "--:--"}
                </p>
              </div>

              <div className="bg-slate-950/60 p-3 rounded-lg border border-slate-800/60">
                <p className="text-[11px] text-slate-400">Last Departure (Check-Out)</p>
                <p className="text-base font-bold text-rose-400 mt-1">
                  {data.today.checked_out || "--:--"}
                </p>
              </div>
            </div>
          </div>

          <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 space-y-2">
            <div className="flex items-center justify-between text-slate-400">
              <span className="text-xs font-medium">Monthly Present Days</span>
              <CheckCircle2 className="w-4 h-4 text-emerald-400" />
            </div>
            <p className="text-3xl font-bold text-white">{data.metrics.days_present_month}</p>
            <p className="text-[11px] text-slate-500">Current calendar month</p>
          </div>

          <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 space-y-2">
            <div className="flex items-center justify-between text-slate-400">
              <span className="text-xs font-medium">Punctuality Score</span>
              <Percent className="w-4 h-4 text-purple-400" />
            </div>
            <p className="text-3xl font-bold text-white">{data.metrics.on_time_rate}%</p>
            <p className="text-[11px] text-slate-500">Compliance rate</p>
          </div>
        </div>

        {/* History Table */}
        <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden shadow-xl space-y-4 p-5">
          <div className="flex items-center justify-between">
            <h2 className="text-sm font-semibold text-white">Your Attendance History</h2>
            <span className="text-xs text-slate-500">Total {data.history.length} events</span>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-950/80 border-b border-slate-800 text-slate-400 uppercase tracking-wider text-[10px]">
                <tr>
                  <th className="py-3 px-4 font-semibold">Event</th>
                  <th className="py-3 px-4 font-semibold">Timestamp</th>
                  <th className="py-3 px-4 font-semibold">Distance</th>
                  <th className="py-3 px-4 font-semibold">Confidence</th>
                  <th className="py-3 px-4 font-semibold">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60">
                {data.history.length === 0 ? (
                  <tr>
                    <td colSpan={5} className="text-center py-10 text-slate-500">
                      No attendance punches recorded yet.
                    </td>
                  </tr>
                ) : (
                  data.history.map((log) => (
                    <tr key={log.id} className="hover:bg-slate-800/30 transition">
                      <td className="py-3 px-4">
                        <span className={`inline-flex items-center px-2 py-0.5 rounded text-[10px] font-semibold border ${
                          log.type === "CHECK_OUT"
                            ? "bg-rose-950/60 text-rose-300 border-rose-800/50"
                            : "bg-emerald-950/60 text-emerald-300 border-emerald-800/50"
                        }`}>
                          {log.type === "CHECK_OUT" ? "CHECK_OUT" : "CHECK_IN"}
                        </span>
                      </td>
                      <td className="py-3 px-4 text-slate-300">{new Date(log.timestamp).toLocaleString()}</td>
                      <td className="py-3 px-4 text-slate-300">{log.distance_meters}m</td>
                      <td className="py-3 px-4 font-mono text-slate-300">{log.confidence}%</td>
                      <td className="py-3 px-4">
                        <span className="inline-flex items-center gap-1 text-emerald-400 font-medium text-[11px]">
                          <ShieldCheck className="w-3.5 h-3.5" /> {log.status}
                        </span>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>

      </div>
    </div>
  );
}
