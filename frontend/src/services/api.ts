import type { TokenResponse } from "../types";

const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

export async function fetchToken(
  identity: string,
  room?: string
): Promise<TokenResponse> {
  const response = await fetch(`${API_URL}/api/token`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      identity,
      room: room || "health-desk",
      name: "Patient",
    }),
  });
  if (!response.ok) {
    throw new Error(`Failed to fetch token: ${response.statusText}`);
  }
  return response.json();
}
