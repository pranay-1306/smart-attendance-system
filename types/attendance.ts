export type CheckInStep =
  | "INITIALIZING"
  | "PERMISSION_REQUIRED"
  | "DETECTING_FACE"
  | "LIVENESS_CHALLENGE"
  | "SUBMITTING"
  | "SUCCESS"
  | "ERROR";

export interface GeoLocationState {
  latitude: number | null;
  longitude: number | null;
  accuracy: number | null;
  error: string | null;
  loading: boolean;
}

export interface VerificationResponse {
  success: boolean;
  message?: string;
  detail?: string;
  user_name?: string;
  distance_meters?: number;
  confidence?: number;
  timestamp?: string;
}
