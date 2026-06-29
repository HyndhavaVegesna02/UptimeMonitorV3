export interface ComponentDTO {
  id: string;
  name: string;
  status: string; // e.g. 'up' | 'down' | 'degraded' | 'maintenance'
}

export const API_BASE = '/api';

export async function fetchComponents(): Promise<ComponentDTO[]> {
  const response = await fetch(`${API_BASE}/v1/components`);
  if (!response.ok) {
    throw new Error(`Failed to fetch components: ${response.status} ${response.statusText}`);
  }
  return response.json();
}
