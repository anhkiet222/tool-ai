const API_BASE =
  (import.meta.env.VITE_API_BASE as string | undefined) ??
  "http://localhost:8000/api";

export interface StatusResponse {
  ai_available: boolean;
}

export interface CaptionResponse {
  product_name: string;
  bullets: string[];
}

export async function fetchStatus(): Promise<StatusResponse> {
  const res = await fetch(`${API_BASE}/status`);
  if (!res.ok) throw new Error("Cannot reach backend");
  return res.json();
}

export async function generateCaptions(
  description: string,
): Promise<CaptionResponse> {
  const form = new FormData();
  form.append("description", description);
  const res = await fetch(`${API_BASE}/generate-captions`, {
    method: "POST",
    body: form,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: "Unknown error" }));
    throw new Error(err.detail ?? "Failed to generate captions");
  }
  return res.json();
}

export async function generateVideo(payload: {
  images: File[];
  productName: string;
  bullets: string[];
  music: File | null;
}): Promise<Blob> {
  const form = new FormData();
  payload.images.forEach((img) => form.append("images", img));
  form.append("product_name", payload.productName);
  payload.bullets.forEach((b) => form.append("bullets", b));
  if (payload.music) form.append("music", payload.music);

  const res = await fetch(`${API_BASE}/generate`, {
    method: "POST",
    body: form,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: "Unknown error" }));
    throw new Error(err.detail ?? "Video generation failed");
  }
  return res.blob();
}
