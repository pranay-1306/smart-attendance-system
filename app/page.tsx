"use client";

import React, { useRef, useState, useEffect } from "react";
import { Camera, MapPin, CheckCircle, AlertCircle, RefreshCw, Eye } from "lucide-react";
import { useGeolocation } from "../hooks/useGeolocation";
import { useFaceLiveness } from "../hooks/useFaceLiveness";
import { CheckInStep, VerificationResponse } from "../types/attendance";

export default function AttendancePage() {
  const videoRef = useRef<HTMLVideoElement | null>(null);
  const [step, setStep] = useState<CheckInStep>("INITIALIZING");
  const [statusMessage, setStatusMessage] = useState<string>("Initializing system...");
  const [apiResult, setApiResult] = useState<VerificationResponse | null>(null);

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
    setStatusMessage("Verifying location and biometric match...");

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
        formData.append("accuracy", coords.accuracy.toString());

        const response = await fetch("/api/v1/attendance/check-in", {
          method: "POST",
          body: formData,
        });

        const data: VerificationResponse = await response.json();

        if (response.ok && data.success) {
          setApiResult(data);
          setStep("SUCCESS");
          setStatusMessage("Attendance verified successfully!");
        } else {
          setApiResult(data);
          setStep("ERROR");
          setStatusMessage(data.message || "Verification failed.");
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
      <div className="max-w-md w-full bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-2xl space-y-6">
        <div className="text-center space-y-1">
          <h1 className="text-xl font-semibold tracking-tight text-white">Workplace Check-In</h1>
          <p className="text-xs text-slate-400">Biometric & GPS Geo-fenced Attendance</p>
        </div>

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
                  ? "border-green-400"
                  : "border-blue-400"
                : "border-slate-600 border-dashed"
            }`}
          />

          <div className="absolute bottom-3 inset-x-4">
            <div className="bg-slate-950/80 backdrop-blur-md px-3 py-2 rounded-lg border border-slate-700/50 flex items-center gap-2">
              {step === "SUBMITTING" && <RefreshCw className="w-4 h-4 text-blue-400 animate-spin" />}
              {step === "LIVENESS_CHALLENGE" && <Eye className="w-4 h-4 text-amber-400 animate-pulse" />}
              {step === "SUCCESS" && <CheckCircle className="w-4 h-4 text-emerald-400" />}
              {step === "ERROR" && <AlertCircle className="w-4 h-4 text-rose-400" />}
              <span className="text-xs font-medium text-slate-200">{statusMessage}</span>
            </div>
          </div>
        </div>

        <div className="bg-slate-950 rounded-lg p-3 border border-slate-800 text-xs space-y-1">
          <div className="flex items-center justify-between text-slate-400">
            <span className="flex items-center gap-1.5">
              <MapPin className="w-3.5 h-3.5 text-slate-500" /> GPS Status:
            </span>
            <span className={latitude ? "text-emerald-400 font-mono" : "text-amber-400"}>
              {latitude ? `${latitude.toFixed(5)}, ${longitude?.toFixed(5)}` : "Awaiting fix..."}
            </span>
          </div>
          {accuracy && (
            <div className="flex justify-between text-slate-500">
              <span>Accuracy:</span>
              <span>±{Math.round(accuracy)}m</span>
            </div>
          )}
        </div>

        {step === "SUCCESS" && apiResult && (
          <div className="p-4 bg-emerald-950/40 border border-emerald-800/50 rounded-xl space-y-2 text-center">
            <p className="text-sm font-semibold text-emerald-300">Welcome, {apiResult.user_name}!</p>
            <p className="text-xs text-emerald-400/80">
              Verified within office zone ({apiResult.distance_meters}m from center)
            </p>
          </div>
        )}

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
