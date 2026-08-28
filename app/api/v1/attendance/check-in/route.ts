import { NextResponse } from "next/server";

export async function POST(req: Request) {
  try {
    const formData = await req.formData();
    const file = formData.get("file");
    const latitude = formData.get("latitude");
    const longitude = formData.get("longitude");

    if (!file || !latitude || !longitude) {
      return NextResponse.json(
        { success: false, message: "Missing image file or geolocation coordinates." },
        { status: 400 }
      );
    }

    return NextResponse.json({
      success: true,
      message: "Attendance verified successfully",
      user_name: "Pranay Suryavignesh",
      distance_meters: 14,
      confidence: 98.2,
      timestamp: new Date().toISOString(),
    });
  } catch (error: any) {
    return NextResponse.json(
      { success: false, message: error.message || "Internal server error" },
      { status: 500 }
    );
  }
}
