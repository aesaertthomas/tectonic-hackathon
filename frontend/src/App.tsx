import { useCallback, useEffect, useMemo, useState } from "react";
import { Navigate, Route, Routes } from "react-router-dom";
import { api } from "./api";
import { AuthContext } from "./auth";
import { Home } from "./routes/Home";
import { Insight } from "./routes/Insight";
import { Login } from "./routes/Login";
import type { Me } from "./types";

export default function App() {
  const [me, setMe] = useState<Me | null | undefined>(undefined);

  useEffect(() => {
    api.get<Me>("/me").then(setMe, () => setMe(null));
  }, []);

  const expire = useCallback(() => setMe(null), []);
  const logout = useCallback(async () => {
    try {
      await api.post("/auth/logout");
    } finally {
      setMe(null);
    }
  }, []);
  const auth = useMemo(() => (me ? { me, logout, expire } : null), [me, logout, expire]);

  return (
    <div className="backdrop">
      <div className="device">
        {me === undefined && <div className="center muted">Loading…</div>}
        {me === null && <Login onLoggedIn={setMe} />}
        {auth && (
          <AuthContext.Provider value={auth}>
            <Routes>
              <Route path="/" element={<Home />} />
              <Route path="/insights/:key" element={<Insight />} />
              <Route path="*" element={<Navigate to="/" replace />} />
            </Routes>
          </AuthContext.Provider>
        )}
      </div>
    </div>
  );
}
