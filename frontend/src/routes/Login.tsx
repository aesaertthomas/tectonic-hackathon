import { useState, type FormEvent } from "react";
import { api, errorMessage } from "../api";
import logo from "../assets/logo.svg";
import type { Me } from "../types";

export function Login({ onLoggedIn }: { onLoggedIn: (me: Me) => void }) {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function submit(e: FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError(null);
    try {
      onLoggedIn(await api.post<Me>("/auth/login", { username, password }));
    } catch (err) {
      setError(errorMessage(err));
      setBusy(false);
    }
  }

  return (
    <form className="login" onSubmit={submit}>
      <img src={logo} alt="KBC" className="login-logo" />
      <h1>Time Machine</h1>
      <div className="stack">
        <label className="field">
          Username
          <input value={username} onChange={(e) => setUsername(e.target.value)} autoComplete="username" required maxLength={64} />
        </label>
        <label className="field">
          Password
          <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} autoComplete="current-password" required maxLength={128} />
        </label>
        {error && <p className="error">{error}</p>}
      </div>
      <button className="btn btn-primary" disabled={busy}>
        {busy ? "Logging in…" : "Log in"}
      </button>
    </form>
  );
}
