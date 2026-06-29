import { useState, useEffect, useCallback, useRef } from 'react';
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
  // Track mount status to skip state updates on unmounted components.
  const mountedRef = useRef<boolean>(true);

  useEffect(() => {
    mountedRef.current = true;
    return () => {
      mountedRef.current = false;
    };
  }, []);

  useEffect(() => {
    let cancelled = false;

    fetchComponents()
      .then((result) => {
        if (!cancelled && mountedRef.current) {
          setData(result);
          setError(null);
          setLoading(false);
        }
      })
      .catch((err: unknown) => {
        if (!cancelled && mountedRef.current) {
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
