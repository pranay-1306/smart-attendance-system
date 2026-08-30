import os
import shutil

base = "C:/Users/Palivela Pranay/attendance-web"

# 1. Ensure lib/api.ts is properly defined
os.makedirs(f"{base}/lib", exist_ok=True)
with open(f"{base}/lib/api.ts", "w", encoding="utf-8") as f:
    f.write('''export const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL?.replace(/\\/+$/, "") || "http://127.0.0.1:8000";
''')

# 2. Update all frontend pages to use API_BASE_URL
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
        
        # Replace hardcoded localhost URLs with dynamic API_BASE_URL
        content = content.replace("http://127.0.0.1:8000", "${API_BASE_URL}")
        content = content.replace("http://localhost:8000", "${API_BASE_URL}")
        
        # Ensure API_BASE_URL is imported right below 'use client';
        if 'import { API_BASE_URL }' not in content:
            if '"use client";' in content:
                content = content.replace('"use client";', '"use client";\n\nimport { API_BASE_URL } from "@/lib/api";')
            elif "'use client';" in content:
                content = content.replace("'use client';", "'use client';\n\nimport { API_BASE_URL } from '@/lib/api';")
        
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"[+] Synced: {os.path.basename(filepath)}")

# 3. Copy latest backend files into attendance-web/backend so Render gets the newest API
backend_src = "C:/Users/Palivela Pranay/backend/app"
backend_dest = f"{base}/backend/app"
if os.path.exists(backend_src):
    os.makedirs(backend_dest, exist_ok=True)
    shutil.copyfile(f"{backend_src}/main.py", f"{backend_dest}/main.py")
    shutil.copyfile(f"{backend_src}/database.py", f"{backend_dest}/database.py")
    shutil.copyfile(f"{backend_src}/face_service.py", f"{backend_dest}/face_service.py")
    shutil.copyfile(f"{backend_src}/geo_service.py", f"{backend_dest}/geo_service.py")
    print("[+] Synced backend files to repository!")

print("\n[+] Production sync complete!")