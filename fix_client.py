import os

base = "C:/Users/Palivela Pranay/attendance-web"
files = [
    f"{base}/app/page.tsx",
    f"{base}/app/login/page.tsx",
    f"{base}/app/dashboard/page.tsx",
    f"{base}/app/admin/page.tsx",
    f"{base}/app/admin/login/page.tsx",
    f"{base}/components/AttendanceClient.tsx"
]

for filepath in files:
    if os.path.exists(filepath):
        with open(filepath, "r", encoding="utf-8") as f:
            lines = f.readlines()
        
        # Strip out any misplaced 'use client' or duplicate imports
        filtered = [
            l for l in lines 
            if '"use client"' not in l 
            and "'use client'" not in l 
            and "import { API_BASE_URL }" not in l
        ]
        
        # Reconstruct file with 'use client' strictly on Line 1
        new_content = '"use client";\n\nimport { API_BASE_URL } from "@/lib/api";\n' + "".join(filtered).lstrip()
        
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(new_content)
        print(f"[+] Fixed: {os.path.basename(filepath)}")

print("\n[+] Success: 'use client' is now strictly Line 1 on all pages!")