export const API_BASE_URL =
  (typeof process !== "undefined" && process.env.NEXT_PUBLIC_API_URL
    ? process.env.NEXT_PUBLIC_API_URL
    : "https://smart-attendance-system-nmo4.onrender.com"
  ).replace(/\/+$/, "");
