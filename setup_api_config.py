import os

base = "C:/Users/Palivela Pranay/attendance-web"
os.makedirs(f"{base}/lib", exist_ok=True)

# 1. Create lib/api.ts
with open(f"{base}/lib/api.ts", "w", encoding="utf-8") as f:
    f.write('''export const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL?.replace(/\\/+$/, "") || "http://127.0.0.1:8000";
''')

# Update references in frontend pages
files_to_update = [
    f"{base}/app/page.tsx",
    f"{base}/components/AttendanceClient.tsx",
    f"{base}/app/login/page.tsx",
    f"{base}/app/dashboard/page.tsx",
    f"{base}/app/admin/page.tsx",
    f"{base}/app/admin/login/page.tsx"
]

for filepath in files_to_update:
    if os.path.exists(filepath):
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
        
        # Replace hardcoded URLs with dynamic config
        if "http://127.0.0.1:8000" in content:
            new_content = content.replace("http://127.0.0.1:8000", "${API_BASE_URL}")
            # Insert import if missing
            if 'import { API_BASE_URL }' not in new_content:
                new_content = 'import { API_BASE_URL } from "@/lib/api";\n' + new_content
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(new_content)
            print(f"[+] Updated: {filepath}")

print("[+] Dynamic API configuration complete!")