import { useCallback, useEffect, useMemo, useState } from "react";
import { Navigate, Route, Routes } from "react-router-dom";
import { api } from "./api";
import { AuthContext } from "./auth";
import { AppShell } from "./components/AppShell";
import { GoalForm } from "./routes/GoalForm";
import { Goals } from "./routes/Goals";
import { Home } from "./routes/Home";
import { Insight } from "./routes/Insight";
import { Login } from "./routes/Login";
import { Scenario } from "./routes/Scenario";
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
    <>
      {me === undefined && <div className="loading">Loading…</div>}
      {me === null && <Login onLoggedIn={setMe} />}
      {auth && (
        <AuthContext.Provider value={auth}>
          <AppShell>
            <Routes>
              <Route path="/" element={<Home />} />
              <Route path="/insights/:key" element={<Insight />} />
              <Route path="/insights/:key/scenario" element={<Scenario />} />
              <Route path="/goals" element={<Goals />} />
              <Route path="/goals/new" element={<GoalForm />} />
              <Route path="/goals/:id" element={<GoalForm />} />
              <Route path="*" element={<Navigate to="/" replace />} />
            </Routes>
          </AppShell>
        </AuthContext.Provider>
      )}
    </>
  );
}
