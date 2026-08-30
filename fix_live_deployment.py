import os

base = "C:/Users/Palivela Pranay/attendance-web"

# 1. Update lib/api.ts with Render URL as permanent production default
os.makedirs(f"{base}/lib", exist_ok=True)
with open(f"{base}/lib/api.ts", "w", encoding="utf-8") as f:
    f.write('''export const API_BASE_URL =
  (typeof process !== "undefined" && process.env.NEXT_PUBLIC_API_URL
    ? process.env.NEXT_PUBLIC_API_URL
    : "https://smart-attendance-system-nmo4.onrender.com"
  ).replace(/\\/+$/, "");
''')

# 2. Fix error messages and endpoints across all frontend pages
frontend_files = [
    f"{base}/app/page.tsx",
    f"{base}/components/AttendanceClient.tsx",
    f"{base}/app/login/page.tsx",
    f"{base}/app/dashboard/page.tsx",
    f"{base}/app/admin/page.tsx",
    f"{base}/app/admin/login/page.tsx"
]

for filepath in frontend_files:
    if os.path.exists(filepath):
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
        
        # Replace any leftover localhost URLs
        content = content.replace("http://127.0.0.1:8000", "${API_BASE_URL}")
        content = content.replace("http://localhost:8000", "${API_BASE_URL}")
        content = content.replace("Unable to reach backend server on port 8000.", "Connecting to cloud backend... If the server was sleeping, please wait 30 seconds and try again.")
        
        # Ensure API_BASE_URL is imported right below 'use client';
        if 'import { API_BASE_URL }' not in content:
            if '"use client";' in content:
                content = content.replace('"use client";', '"use client";\n\nimport { API_BASE_URL } from "@/lib/api";')
            elif "'use client';" in content:
                content = content.replace("'use client';", "'use client';\n\nimport { API_BASE_URL } from '@/lib/api';")
        
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"[+] Synced: {os.path.basename(filepath)}")

print("[+] All pages configured with live Render cloud backend!")
