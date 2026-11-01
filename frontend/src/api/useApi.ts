import { useCallback, useEffect, useRef, useState } from "react";

export interface ApiState<T> {
  /** The latest successful result. Kept while a new request runs, so the screen never blanks. */
  data: T | undefined;
  error: string | undefined;
  loading: boolean;
  retry: () => void;
}

/**
 * Run ``load`` whenever ``key`` changes, cancelling the previous request.
 * Pass ``null`` as the key to wait (for example until defaults are known).
 */
export function useApi<T>(key: string | null, load: (signal: AbortSignal) => Promise<T>): ApiState<T> {
  const [data, setData] = useState<T>();
  const [error, setError] = useState<string>();
  const [loading, setLoading] = useState(key !== null);
  const [attempt, setAttempt] = useState(0);
  const loadRef = useRef(load);
  loadRef.current = load;

  useEffect(() => {
    if (key === null) return undefined;
    const controller = new AbortController();
    setLoading(true);
    setError(undefined);
    loadRef.current(controller.signal).then(
      (result) => {
        setData(result);
        setLoading(false);
      },
      (reason: unknown) => {
        if (controller.signal.aborted) return;
        setError(reason instanceof Error ? reason.message : "Something went wrong. Try again.");
        setLoading(false);
      },
    );
    return () => controller.abort();
  }, [key, attempt]);

  const retry = useCallback(() => setAttempt((value) => value + 1), []);
  return { data, error, loading, retry };
}
