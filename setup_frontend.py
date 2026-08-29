import os

base = "C:/Users/Palivela Pranay/attendance-web"
os.makedirs(f"{base}/app/login", exist_ok=True)
os.makedirs(f"{base}/app/dashboard", exist_ok=True)
os.makedirs(f"{base}/components", exist_ok=True)

# 1. components/AttendanceClient.tsx
with open(f"{base}/components/AttendanceClient.tsx", "w", encoding="utf-8") as f:
    f.write('''"use client";

import React, { useRef, useState, useEffect } from "react";
import Link from "next/link";
import { Camera, MapPin, CheckCircle, AlertCircle, RefreshCw, Eye, LogIn, LogOut, User, Shield } from "lucide-react";
import { useGeolocation } from "../hooks/useGeolocation";
import { useFaceLiveness } from "../hooks/useFaceLiveness";
import { CheckInStep, VerificationResponse } from "../types/attendance";

interface ExtendedVerificationResponse extends VerificationResponse {
  type?: "CHECK_IN" | "CHECK_OUT";
  employee_code?: string;
}

export default function AttendanceClient() {
  const videoRef = useRef<HTMLVideoElement | null>(null);
  const [attendanceType, setAttendanceType] = useState<"CHECK_IN" | "CHECK_OUT">("CHECK_IN");
  const [step, setStep] = useState<CheckInStep>("INITIALIZING");
  const [statusMessage, setStatusMessage] = useState<string>("Initializing camera and AI models...");
  const [apiResult, setApiResult] = useState<ExtendedVerificationResponse | null>(null);

  const { latitude, longitude, accuracy, getCoordinates } = useGeolocation();
  const { modelsLoaded, hasFace, blinkDetected, startDetection, stopDetection } = useFaceLiveness(videoRef);

  const startCamera = async () => {
    try {
      setStep("INITIALIZING");
      setStatusMessage("Starting camera stream...");
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { width: { ideal: 640 }, height: { ideal: 480 }, facingMode: "user" },
        audio: false,
      });

      if (videoRef.current) {
        videoRef.current.srcObject = stream;
        videoRef.current.onloadedmetadata = () => {
          videoRef.current?.play();
          setStep("DETECTING_FACE");
          setStatusMessage("Align your face inside the circle");
          startDetection();
        };
      }
    } catch {
      setStep("PERMISSION_REQUIRED");
      setStatusMessage("Camera permission is required to proceed.");
    }
  };

  useEffect(() => {
    if (modelsLoaded) {
      startCamera();
    }
  }, [modelsLoaded]);

  useEffect(() => {
    if (step === "DETECTING_FACE" && hasFace) {
      setStep("LIVENESS_CHALLENGE");
      setStatusMessage("Please blink your eyes naturally to verify liveness.");
    } else if (step === "LIVENESS_CHALLENGE" && !hasFace) {
      setStep("DETECTING_FACE");
      setStatusMessage("Face lost. Please look into the camera.");
    }
  }, [hasFace, step]);

  useEffect(() => {
    if (blinkDetected && step === "LIVENESS_CHALLENGE") {
      stopDetection();
      handleCaptureAndSubmit();
    }
  }, [blinkDetected, step]);

  const handleCaptureAndSubmit = async () => {
    setStep("SUBMITTING");
    const actionText = attendanceType === "CHECK_IN" ? "Check-In" : "Check-Out";
    setStatusMessage(`Verifying location and recording ${actionText}...`);

    try {
      const coords = await getCoordinates();

      if (!videoRef.current) throw new Error("Camera not accessible.");

      const video = videoRef.current;
      const canvas = document.createElement("canvas");
      canvas.width = video.videoWidth;
      canvas.height = video.videoHeight;
      const ctx = canvas.getContext("2d");
      ctx?.drawImage(video, 0, 0, canvas.width, canvas.height);

      canvas.toBlob(async (blob) => {
        if (!blob) throw new Error("Image capture failed.");

        const formData = new FormData();
        formData.append("file", blob, "checkin_frame.jpg");
        formData.append("latitude", coords.latitude.toString());
        formData.append("longitude", coords.longitude.toString());
        formData.append("type", attendanceType);
        formData.append("accuracy", coords.accuracy.toString());

        const response = await fetch("http://127.0.0.1:8000/api/v1/attendance/check-in", {
          method: "POST",
          body: formData,
        });

        const data: ExtendedVerificationResponse = await response.json();

        if (response.ok && data.success) {
          setApiResult(data);
          setStep("SUCCESS");
          setStatusMessage(`${actionText} verified successfully!`);
        } else {
          setApiResult(data);
          setStep("ERROR");
          setStatusMessage(data.detail || data.message || `${actionText} failed.`);
        }
      }, "image/jpeg", 0.95);
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : "An error occurred during submission.";
      setStep("ERROR");
      setStatusMessage(message);
    }
  };

  const handleReset = () => {
    setApiResult(null);
    setStep("DETECTING_FACE");
    setStatusMessage("Align your face inside the circle");
    startDetection();
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col items-center justify-center p-4">
      <div className="max-w-md w-full bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-2xl space-y-5">
        
        {/* Navigation Header */}
        <div className="flex items-center justify-between border-b border-slate-800 pb-4">
          <div>
            <h1 className="text-lg font-bold tracking-tight text-white">Workplace Portal</h1>
            <p className="text-xs text-slate-400">Biometric & GPS Attendance</p>
          </div>
          <div className="flex items-center gap-2">
            <Link
              href="/login"
              className="text-[11px] font-medium text-slate-300 hover:text-white bg-slate-800 border border-slate-700 px-2.5 py-1.5 rounded-lg transition flex items-center gap-1"
            >
              <User className="w-3 h-3 text-blue-400" /> Employee Login
            </Link>
            <Link
              href="/admin"
              className="text-[11px] font-medium text-amber-300 hover:text-amber-200 bg-amber-950/60 border border-amber-800/50 px-2.5 py-1.5 rounded-lg transition flex items-center gap-1"
            >
              <Shield className="w-3 h-3 text-amber-400" /> Admin
            </Link>
          </div>
        </div>

        {/* CHECK_IN vs CHECK_OUT Toggle */}
        <div className="grid grid-cols-2 gap-1 p-1 bg-slate-950 rounded-xl border border-slate-800">
          <button
            type="button"
            onClick={() => {
              setAttendanceType("CHECK_IN");
              if (step === "SUCCESS" || step === "ERROR") handleReset();
            }}
            className={`py-2 text-xs font-semibold rounded-lg flex items-center justify-center gap-1.5 transition ${
              attendanceType === "CHECK_IN"
                ? "bg-emerald-600 text-white shadow-md"
                : "text-slate-400 hover:text-slate-200"
            }`}
          >
            <LogIn className="w-3.5 h-3.5" /> Check In
          </button>

          <button
            type="button"
            onClick={() => {
              setAttendanceType("CHECK_OUT");
              if (step === "SUCCESS" || step === "ERROR") handleReset();
            }}
            className={`py-2 text-xs font-semibold rounded-lg flex items-center justify-center gap-1.5 transition ${
              attendanceType === "CHECK_OUT"
                ? "bg-rose-600 text-white shadow-md"
                : "text-slate-400 hover:text-slate-200"
            }`}
          >
            <LogOut className="w-3.5 h-3.5" /> Check Out
          </button>
        </div>

        {/* Camera Viewport */}
        <div className="relative aspect-[4/3] w-full bg-black rounded-xl overflow-hidden border border-slate-800 flex items-center justify-center">
          <video
            ref={videoRef}
            playsInline
            muted
            className="w-full h-full object-cover transform -scale-x-100"
          />

          <div
            className={`absolute inset-0 border-2 rounded-full m-8 pointer-events-none transition-colors duration-300 ${
              hasFace
                ? blinkDetected
                  ? attendanceType === "CHECK_IN" ? "border-emerald-400" : "border-rose-400"
                  : "border-blue-400"
                : "border-slate-600 border-dashed"
            }`}
          />

          <div className="absolute bottom-3 inset-x-4">
            <div className="bg-slate-950/85 backdrop-blur-md px-3 py-2 rounded-lg border border-slate-700/50 flex items-center gap-2">
              {step === "SUBMITTING" && <RefreshCw className="w-4 h-4 text-blue-400 animate-spin" />}
              {step === "LIVENESS_CHALLENGE" && <Eye className="w-4 h-4 text-amber-400 animate-pulse" />}
              {step === "SUCCESS" && <CheckCircle className="w-4 h-4 text-emerald-400" />}
              {step === "ERROR" && <AlertCircle className="w-4 h-4 text-rose-400" />}
              <span className="text-xs font-medium text-slate-200">{statusMessage}</span>
            </div>
          </div>
        </div>

        {/* GPS Status */}
        <div className="bg-slate-950 rounded-lg p-3 border border-slate-800 text-xs space-y-1">
          <div className="flex items-center justify-between text-slate-400">
            <span className="flex items-center gap-1.5">
              <MapPin className="w-3.5 h-3.5 text-slate-500" /> Current Location:
            </span>
            <span className={latitude ? "text-emerald-400 font-mono" : "text-amber-400"}>
              {latitude ? `${latitude.toFixed(5)}, ${longitude?.toFixed(5)}` : "Acquiring GPS..."}
            </span>
          </div>
          {accuracy && (
            <div className="flex justify-between text-slate-500">
              <span>Accuracy:</span>
              <span>±{Math.round(accuracy)}m</span>
            </div>
          )}
        </div>

        {/* Success Card */}
        {step === "SUCCESS" && apiResult && (
          <div className={`p-4 rounded-xl border text-center space-y-1.5 ${
            attendanceType === "CHECK_IN"
              ? "bg-emerald-950/40 border-emerald-800/50 text-emerald-300"
              : "bg-rose-950/40 border-rose-800/50 text-rose-300"
          }`}>
            <p className="text-sm font-semibold">
              {attendanceType === "CHECK_IN" ? "Checked In Successfully!" : "Checked Out Successfully!"}
            </p>
            <p className="text-xs opacity-90">Welcome, {apiResult.user_name}</p>
            <p className="text-[11px] opacity-75">
              Proximity: {apiResult.distance_meters}m from office | Confidence: {apiResult.confidence}%
            </p>
          </div>
        )}

        {/* Error Card */}
        {step === "ERROR" && (
          <div className="p-4 bg-rose-950/40 border border-rose-800/50 rounded-xl space-y-3 text-center">
            <p className="text-xs text-rose-300">{statusMessage}</p>
            <button
              onClick={handleReset}
              className="w-full py-2 bg-rose-600 hover:bg-rose-500 text-white text-xs font-medium rounded-lg transition"
            >
              Try Again
            </button>
          </div>
        )}

        {step === "PERMISSION_REQUIRED" && (
          <button
            onClick={startCamera}
            className="w-full py-2.5 bg-blue-600 hover:bg-blue-500 text-white text-sm font-medium rounded-xl flex items-center justify-center gap-2 transition"
          >
            <Camera className="w-4 h-4" /> Grant Permissions & Start
          </button>
        )}
      </div>
    </div>
  );
}
''')

# 2. app/login/page.tsx
with open(f"{base}/app/login/page.tsx", "w", encoding="utf-8") as f:
    f.write('''"use client";

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

      const res = await fetch("http://127.0.0.1:8000/api/v1/auth/login", {
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
''')

# 3. app/dashboard/page.tsx
with open(f"{base}/app/dashboard/page.tsx", "w", encoding="utf-8") as f:
    f.write('''"use client";

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
      const res = await fetch(`http://127.0.0.1:8000/api/v1/employee/${user.id}/dashboard`);
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
''')

print("[+] All frontend files generated successfully!")