import os

base = "C:/Users/Palivela Pranay/attendance-web"

# 1. Update types/attendance.ts
with open(f"{base}/types/attendance.ts", "w", encoding="utf-8") as f:
    f.write('''export type CheckInStep =
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
''')

# 2. Update app/page.tsx and components/AttendanceClient.tsx interfaces
target_files = [f"{base}/app/page.tsx", f"{base}/components/AttendanceClient.tsx"]
for filepath in target_files:
    if os.path.exists(filepath):
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
        
        old_interface = '''interface ExtendedVerificationResponse extends VerificationResponse {
  type?: "CHECK_IN" | "CHECK_OUT";
  employee_code?: string;
}'''
        new_interface = '''interface ExtendedVerificationResponse extends VerificationResponse {
  type?: "CHECK_IN" | "CHECK_OUT";
  employee_code?: string;
  detail?: string;
}'''
        if old_interface in content:
            content = content.replace(old_interface, new_interface)
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(content)
            print(f"[+] Updated interface in: {os.path.basename(filepath)}")

print("[+] Types fixed successfully!")