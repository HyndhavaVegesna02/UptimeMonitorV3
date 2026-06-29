import { useState, useEffect, useCallback } from 'react';
import { fetchComponents, type ComponentDTO } from '../apiClient';

export interface UseComponentsResult {
  data: ComponentDTO[];
  loading: boolean;
  error: string | null;
  refetch: () => void;
}

export function useComponents(): UseComponentsResult {
  const [data, setData] = useState<ComponentDTO[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  // Incrementing this counter triggers a re-fetch.
  const [fetchCount, setFetchCount] = useState<number>(0);

  useEffect(() => {
    // The `cancelled` closure flag (flipped in cleanup on unmount/re-run) is the
    // canonical guard against post-unmount setState — no separate mounted ref needed.
    let cancelled = false;

    fetchComponents()
      .then((result) => {
        if (!cancelled) {
          setData(result);
          setError(null);
          setLoading(false);
        }
      })
      .catch((err: unknown) => {
        if (!cancelled) {
          setError(
            err instanceof Error ? err.message : 'An unknown error occurred'
          );
          setLoading(false);
        }
      });

    return () => {
      cancelled = true;
    };
  }, [fetchCount]);

  const refetch = useCallback(() => {
    setLoading(true);
    setError(null);
    setFetchCount((c) => c + 1);
  }, []);

  return { data, loading, error, refetch };
}
