import { API_BASE_URL } from "@/lib/api";
"use client";

import React, { useState, useEffect, useMemo } from "react";
import Link from "next/link";
import {
  Users,
  CheckCircle2,
  Clock,
  Download,
  Search,
  Calendar,
  RefreshCw,
  ArrowLeft,
  ShieldCheck,
  MapPin,
  Percent
} from "lucide-react";

interface AttendanceRecord {
  id: number;
  name: string;
  employee_code?: string;
  timestamp: string;
  type?: string;
  distance_meters?: number;
  confidence?: number;
  status?: string;
}

export default function AdminDashboard() {
  const [records, setRecords] = useState<AttendanceRecord[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [searchTerm, setSearchTerm] = useState<string>("");
  const [selectedDate, setSelectedDate] = useState<string>(
    new Date().toISOString().split("T")[0]
  );

  const fetchLogs = async () => {
    setLoading(true);
    try {
      const res = await fetch("${API_BASE_URL}/api/v1/attendance/logs");
      if (res.ok) {
        const data = await res.json();
        setRecords(data);
      }
    } catch (err) {
      console.error("Failed to fetch logs:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchLogs();
  }, []);

  const filteredRecords = useMemo(() => {
    return records.filter((rec) => {
      const recordDate = rec.timestamp ? rec.timestamp.split("T")[0] : "";
      const matchesDate = !selectedDate || recordDate === selectedDate;
      const matchesSearch =
        (rec.name && rec.name.toLowerCase().includes(searchTerm.toLowerCase())) ||
        (rec.employee_code && rec.employee_code.toLowerCase().includes(searchTerm.toLowerCase()));

      return matchesDate && matchesSearch;
    });
  }, [records, searchTerm, selectedDate]);

  const metrics = useMemo(() => {
    const todayStr = new Date().toISOString().split("T")[0];
    const todayLogs = records.filter((r) => r.timestamp && r.timestamp.startsWith(todayStr));
    const avgConfidence =
      records.length > 0
        ? Math.round(records.reduce((acc, curr) => acc + (curr.confidence || 0), 0) / records.length)
        : 0;

    return {
      todayCount: todayLogs.length,
      totalCount: records.length,
      avgConfidence,
      verifiedCount: records.filter((r) => r.status === "VERIFIED").length,
    };
  }, [records]);

  const exportToCSV = () => {
    if (filteredRecords.length === 0) {
      alert("No records to export.");
      return;
    }

    const headers = ["Log ID", "Employee Name", "Employee Code", "Type", "Date & Time", "Distance (m)", "Confidence (%)", "Status"];
    const rows = filteredRecords.map((r) => [
      r.id,
      `"${r.name}"`,
      r.employee_code || "EMP001",
      r.type || "CHECK_IN",
      new Date(r.timestamp).toLocaleString(),
      r.distance_meters || 0,
      `${r.confidence || 0}%`,
      r.status || "VERIFIED"
    ]);

    const csvContent = [headers.join(","), ...rows.map((row) => row.join(","))].join("\n");
    const blob = new Blob([csvContent], { type: "text/csv;charset=utf-8;" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.setAttribute("href", url);
    link.setAttribute("download", `attendance_logs_${selectedDate || "all"}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 p-6 md:p-10">
      <div className="max-w-7xl mx-auto space-y-8">
        
        {/* Top Navigation & Header */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-800 pb-6">
          <div className="space-y-1">
            <Link
              href="/"
              className="inline-flex items-center gap-1.5 text-xs text-slate-400 hover:text-slate-200 transition mb-2"
            >
              <ArrowLeft className="w-4 h-4" /> Back to Check-In Portal
            </Link>
            <h1 className="text-2xl md:text-3xl font-bold tracking-tight text-white">
              Attendance Administration
            </h1>
            <p className="text-xs text-slate-400">
              Live biometric records, GPS proximity verification, and compliance reports.
            </p>
          </div>

          <div className="flex items-center gap-3">
            <button
              onClick={fetchLogs}
              disabled={loading}
              className="px-3.5 py-2 bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-medium rounded-lg border border-slate-700 transition flex items-center gap-2"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${loading ? "animate-spin text-blue-400" : ""}`} />
              Refresh
            </button>

            <button
              onClick={exportToCSV}
              className="px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white text-xs font-medium rounded-lg shadow-lg transition flex items-center gap-2"
            >
              <Download className="w-3.5 h-3.5" />
              Export CSV
            </button>
          </div>
        </div>

        {/* Metrics Grid */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 space-y-2">
            <div className="flex items-center justify-between text-slate-400">
              <span className="text-xs font-medium">Today's Check-Ins</span>
              <Clock className="w-4 h-4 text-blue-400" />
            </div>
            <p className="text-2xl font-bold text-white">{metrics.todayCount}</p>
            <p className="text-[11px] text-slate-500">Live attendance for current date</p>
          </div>

          <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 space-y-2">
            <div className="flex items-center justify-between text-slate-400">
              <span className="text-xs font-medium">Total Verified</span>
              <CheckCircle2 className="w-4 h-4 text-emerald-400" />
            </div>
            <p className="text-2xl font-bold text-white">{metrics.verifiedCount}</p>
            <p className="text-[11px] text-slate-500">Valid biometric + GPS logs</p>
          </div>

          <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 space-y-2">
            <div className="flex items-center justify-between text-slate-400">
              <span className="text-xs font-medium">Avg Match Confidence</span>
              <Percent className="w-4 h-4 text-purple-400" />
            </div>
            <p className="text-2xl font-bold text-white">{metrics.avgConfidence}%</p>
            <p className="text-[11px] text-slate-500">Feature vector similarity score</p>
          </div>

          <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 space-y-2">
            <div className="flex items-center justify-between text-slate-400">
              <span className="text-xs font-medium">Total Historical Logs</span>
              <Users className="w-4 h-4 text-amber-400" />
            </div>
            <p className="text-2xl font-bold text-white">{metrics.totalCount}</p>
            <p className="text-[11px] text-slate-500">Stored in SQLite database</p>
          </div>
        </div>

        {/* Filters and Controls */}
        <div className="flex flex-col md:flex-row items-center justify-between gap-4 bg-slate-900/60 border border-slate-800/80 p-4 rounded-xl">
          <div className="flex flex-wrap items-center gap-3 w-full md:w-auto">
            <div className="relative flex-1 sm:w-64">
              <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-slate-500" />
              <input
                type="text"
                placeholder="Search name or employee code..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full bg-slate-950 border border-slate-800 rounded-lg pl-9 pr-3 py-2 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-blue-500 transition"
              />
            </div>

            <div className="relative flex items-center">
              <Calendar className="w-4 h-4 absolute left-3 text-slate-500 pointer-events-none" />
              <input
                type="date"
                value={selectedDate}
                onChange={(e) => setSelectedDate(e.target.value)}
                className="bg-slate-950 border border-slate-800 rounded-lg pl-9 pr-3 py-2 text-xs text-slate-200 focus:outline-none focus:border-blue-500 transition"
              />
            </div>

            {selectedDate && (
              <button
                onClick={() => setSelectedDate("")}
                className="text-xs text-slate-400 hover:text-slate-200 underline"
              >
                Clear Date
              </button>
            )}
          </div>

          <div className="text-xs text-slate-500">
            Showing <span className="font-semibold text-slate-300">{filteredRecords.length}</span> records
          </div>
        </div>

        {/* Live Attendance Table */}
        <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden shadow-xl">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-950/80 border-b border-slate-800 text-slate-400 uppercase tracking-wider text-[10px]">
                <tr>
                  <th className="py-3.5 px-4 font-semibold">Employee</th>
                  <th className="py-3.5 px-4 font-semibold">Type</th>
                  <th className="py-3.5 px-4 font-semibold">Timestamp</th>
                  <th className="py-3.5 px-4 font-semibold">Office Proximity</th>
                  <th className="py-3.5 px-4 font-semibold">Confidence</th>
                  <th className="py-3.5 px-4 font-semibold">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60">
                {loading ? (
                  <tr>
                    <td colSpan={6} className="text-center py-12 text-slate-500">
                      <RefreshCw className="w-5 h-5 animate-spin mx-auto mb-2 text-blue-400" />
                      Loading records...
                    </td>
                  </tr>
                ) : filteredRecords.length === 0 ? (
                  <tr>
                    <td colSpan={6} className="text-center py-12 text-slate-500">
                      No attendance records found matching your filters.
                    </td>
                  </tr>
                ) : (
                  filteredRecords.map((log) => (
                    <tr key={log.id} className="hover:bg-slate-800/30 transition">
                      <td className="py-3.5 px-4">
                        <div className="font-medium text-slate-200">{log.name}</div>
                        <div className="text-[11px] text-slate-500">{log.employee_code || "EMP001"}</div>
                      </td>

                      <td className="py-3.5 px-4">
                        <span className="inline-flex items-center px-2 py-0.5 rounded text-[10px] font-semibold bg-blue-950 text-blue-300 border border-blue-800/40">
                          {log.type || "CHECK_IN"}
                        </span>
                      </td>

                      <td className="py-3.5 px-4 text-slate-300">
                        {new Date(log.timestamp).toLocaleString()}
                      </td>

                      <td className="py-3.5 px-4">
                        <div className="flex items-center gap-1.5 text-slate-300">
                          <MapPin className="w-3.5 h-3.5 text-slate-500" />
                          <span>{log.distance_meters || 0}m</span>
                        </div>
                      </td>

                      <td className="py-3.5 px-4">
                        <div className="flex items-center gap-2">
                          <div className="w-16 bg-slate-800 rounded-full h-1.5 overflow-hidden">
                            <div
                              className="bg-emerald-400 h-full"
                              style={{ width: `${Math.min(100, log.confidence || 95)}%` }}
                            />
                          </div>
                          <span className="font-mono text-slate-300">{log.confidence || 95}%</span>
                        </div>
                      </td>

                      <td className="py-3.5 px-4">
                        <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[10px] font-medium bg-emerald-950/60 text-emerald-300 border border-emerald-800/50">
                          <ShieldCheck className="w-3 h-3 text-emerald-400" />
                          {log.status || "VERIFIED"}
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
