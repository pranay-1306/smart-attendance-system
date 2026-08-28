"use client";

import { useState, useEffect, useRef, useCallback } from "react";

function distance(p1: { x: number; y: number }, p2: { x: number; y: number }) {
  return Math.hypot(p1.x - p2.x, p1.y - p2.y);
}

function calculateEAR(eye: { x: number; y: number }[]) {
  const A = distance(eye[1], eye[5]);
  const B = distance(eye[2], eye[4]);
  const C = distance(eye[0], eye[3]);
  return (A + B) / (2.0 * C);
}

export function useFaceLiveness(videoRef: React.RefObject<HTMLVideoElement | null>) {
  const [modelsLoaded, setModelsLoaded] = useState(false);
  const [hasFace, setHasFace] = useState(false);
  const [blinkDetected, setBlinkDetected] = useState(false);
  const faceapiRef = useRef<any>(null);
  const isEyeClosedRef = useRef(false);
  const animFrameId = useRef<number | null>(null);

  // Dynamically load face-api ONLY in the browser to prevent SSR TextEncoder crash
  useEffect(() => {
    let isMounted = true;

    async function loadModels() {
      try {
        const faceapi = await import("@vladmandic/face-api");
        faceapiRef.current = faceapi;

        // Load models directly from high-speed CDN to avoid corrupted local weights
        const MODEL_URL = "https://cdn.jsdelivr.net/npm/@vladmandic/face-api/model/";
        await faceapi.nets.tinyFaceDetector.loadFromUri(MODEL_URL);
        await faceapi.nets.faceLandmark68TinyNet.loadFromUri(MODEL_URL);

        if (isMounted) {
          setModelsLoaded(true);
        }
      } catch (err) {
        console.error("Failed to load face-api models:", err);
      }
    }

    if (typeof window !== "undefined") {
      loadModels();
    }

    return () => {
      isMounted = false;
      if (animFrameId.current) {
        cancelAnimationFrame(animFrameId.current);
      }
    };
  }, []);

  const detectLiveness = useCallback(async () => {
    const faceapi = faceapiRef.current;
    if (!videoRef.current || !faceapi || !modelsLoaded || videoRef.current.paused || videoRef.current.ended) {
      return;
    }

    const video = videoRef.current;
    const options = new faceapi.TinyFaceDetectorOptions({ inputSize: 224, scoreThreshold: 0.5 });

    try {
      const detection = await faceapi.detectSingleFace(video, options).withFaceLandmarks(true);

      if (detection) {
        setHasFace(true);
        const landmarks = detection.landmarks;
        const leftEye = landmarks.getLeftEye();
        const rightEye = landmarks.getRightEye();

        const leftEAR = calculateEAR(leftEye);
        const rightEAR = calculateEAR(rightEye);
        const avgEAR = (leftEAR + rightEAR) / 2;

        // Blink detection thresholds
        if (avgEAR < 0.22) {
          isEyeClosedRef.current = true;
        } else if (avgEAR > 0.27 && isEyeClosedRef.current) {
          isEyeClosedRef.current = false;
          setBlinkDetected(true);
        }
      } else {
        setHasFace(false);
      }
    } catch (err) {
      console.error("Face detection loop error:", err);
    }

    animFrameId.current = requestAnimationFrame(detectLiveness);
  }, [modelsLoaded, videoRef]);

  const startDetection = useCallback(() => {
    setBlinkDetected(false);
    isEyeClosedRef.current = false;
    detectLiveness();
  }, [detectLiveness]);

  const stopDetection = useCallback(() => {
    if (animFrameId.current) {
      cancelAnimationFrame(animFrameId.current);
      animFrameId.current = null;
    }
  }, []);

  return {
    modelsLoaded,
    hasFace,
    blinkDetected,
    startDetection,
    stopDetection,
  };
}
