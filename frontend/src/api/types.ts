/**
 * DTO types mirroring the backend's Pydantic models (STORY-015a AC3).
 * `backend/src/api/v1/components/models.py::ComponentDTO` is the source of
 * truth this mirrors — id/name/status, status a plain string (the backend
 * serializes the `ComponentStatus` enum's `.value`: "operational",
 * "degraded", "partial_outage", "major_outage").
 */
export interface ComponentDTO {
  id: string
  name: string
  status: string
}
