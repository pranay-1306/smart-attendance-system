import { API_BASE_URL } from "@/lib/api";
"use client";

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

        const response = await fetch("${API_BASE_URL}/api/v1/attendance/check-in", {
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
