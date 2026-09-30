import { useEffect, useState } from "react";
import { ApiError, api, errorMessage } from "./api";
import { useAuth } from "./auth";

type LoadState<T> = { data?: T; error?: string; loading: boolean };

/** GET a resource; refetches when `path` changes or `reload()` is called. A 401 logs the user out. */
export function useLoad<T>(path: string) {
  const { expire } = useAuth();
  const [state, setState] = useState<LoadState<T>>({ loading: true });
  const [version, setVersion] = useState(0);

  useEffect(() => {
    let cancelled = false;
    setState((s) => ({ ...s, loading: true }));
    api.get<T>(path).then(
      (data) => {
        if (!cancelled) setState({ data, loading: false });
      },
      (e: unknown) => {
        if (cancelled) return;
        if (e instanceof ApiError && e.status === 401) {
          expire();
          return;
        }
        setState({ error: errorMessage(e), loading: false });
      },
    );
    return () => {
      cancelled = true;
    };
  }, [path, version, expire]);

  return { ...state, reload: () => setVersion((v) => v + 1) };
}
