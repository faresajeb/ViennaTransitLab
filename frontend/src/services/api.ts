
import type { TransportStop } from "../types/transport";

const API_URL = "http://localhost:8000/api/v1";

export async function getStops(): Promise<TransportStop[]> {
  const response = await fetch(`${API_URL}/stops`);

  if (!response.ok) {
    throw new Error("Failed to fetch transport stops");
  }

  return response.json();
}
