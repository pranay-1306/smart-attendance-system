"use client";

import { useState, useCallback } from "react";
import { GeoLocationState } from "../types/attendance";

export function useGeolocation() {
  const [location, setLocation] = useState<GeoLocationState>({
    latitude: null,
    longitude: null,
    accuracy: null,
    error: null,
    loading: false,
  });

  const getCoordinates = useCallback((): Promise<{ latitude: number; longitude: number; accuracy: number }> => {
    return new Promise((resolve, reject) => {
      if (typeof window === "undefined" || !navigator.geolocation) {
        const err = "Geolocation is not supported by your browser.";
        setLocation((prev) => ({ ...prev, error: err, loading: false }));
        return reject(new Error(err));
      }

      setLocation((prev) => ({ ...prev, loading: true, error: null }));

      navigator.geolocation.getCurrentPosition(
        (pos) => {
          const coords = {
            latitude: pos.coords.latitude,
            longitude: pos.coords.longitude,
            accuracy: pos.coords.accuracy,
          };
          setLocation({
            ...coords,
            error: null,
            loading: false,
          });
          resolve(coords);
        },
        (err) => {
          let errorMsg = "Unable to retrieve your location.";
          if (err.code === 1) {
            errorMsg = "Location permission denied. Please allow GPS access in your browser.";
          } else if (err.code === 2) {
            errorMsg = "Location information is currently unavailable.";
          } else if (err.code === 3) {
            errorMsg = "Location request timed out. Please try again.";
          }
          setLocation((prev) => ({ ...prev, error: errorMsg, loading: false }));
          reject(new Error(errorMsg));
        },
        {
          enableHighAccuracy: true,
          timeout: 10000,
          maximumAge: 0,
        }
      );
    });
  }, []);

  return { ...location, getCoordinates };
}
