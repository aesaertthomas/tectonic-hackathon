import { useNavigate } from "react-router-dom";
import { useAuth } from "../auth";
import { Screen } from "../components/Screen";
import { eur, longDate } from "../format";
import type { Account, Overview } from "../types";
import { useLoad } from "../useLoad";

const ACCOUNT_TYPES: Record<Account["type"], string> = {
  current: "Current account",
  savings: "Savings account",
  credit_card: "Credit card",
};

export function Home() {
  const { me, logout } = useAuth();
  const navigate = useNavigate();
  const { data, error } = useLoad<Overview>("/overview");

  async function onLogout() {
    await logout();
    navigate("/", { replace: true });
  }

  return (
    <Screen
      title={`Hi ${me.display_name}`}
      action={
        <button type="button" className="link-btn" onClick={onLogout}>
          Log out
        </button>
      }
    >
      {error && <p className="error">{error}</p>}
      {!data && !error && <p className="muted">Loading…</p>}
      {data && (
        <>
          <h2 className="section-title">Accounts</h2>
          <div className="stack">
            {data.accounts.map((a) => (
              <div className="card row" key={a.id}>
                <div className="grow">
                  <div className="account-name">{a.name}</div>
                  <div className="account-number">
                    {ACCOUNT_TYPES[a.type]} · {a.number}
                  </div>
                </div>
                <div className={`amount ${a.balance_cents < 0 ? "neg" : ""}`}>{eur(a.balance_cents)}</div>
              </div>
            ))}
          </div>
          <p className="muted small">
            {data.coverage_note} Data up to {longDate(data.as_of)}.
          </p>
        </>
      )}
    </Screen>
  );
}
