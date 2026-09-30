import { useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { ApiError, api, errorMessage } from "../api";
import { useAuth } from "../auth";
import { BarChart } from "../components/BarChart";
import { Screen } from "../components/Screen";
import { GOAL_LABELS, dayMonth, eur, monthShort } from "../format";
import type { FeedbackResponse, GoalKind, InsightDetail } from "../types";
import { useLoad } from "../useLoad";

const GOAL_KINDS: GoalKind[] = ["car", "home", "emergency", "other"];

export function Insight() {
  const { key = "" } = useParams();
  const path = `/insights/${encodeURIComponent(key)}`;
  const navigate = useNavigate();
  const { expire } = useAuth();
  const { data, error, reload } = useLoad<InsightDetail>(path);
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const [picking, setPicking] = useState(false);
  const [category, setCategory] = useState("");

  async function respond(response: FeedbackResponse, corrected?: string) {
    setBusy(true);
    setMessage(null);
    try {
      await api.post(`${path}/feedback`, corrected ? { response, corrected_category: corrected } : { response });
      if (response === "ongoing") {
        setBusy(false);
        reload();
      } else {
        navigate("/");
      }
    } catch (e) {
      if (e instanceof ApiError && e.status === 401) return expire();
      setMessage(errorMessage(e));
      setBusy(false);
    }
  }

  const isSpending = data?.type === "spending";

  return (
    <Screen title={isSpending ? "Spending" : "Saving"} subtitle={data?.question} back="/">
      {error && <p className="error">{error}</p>}
      {!data && !error && <p className="muted">Loading…</p>}
      {data && (
        <div className="split">
          <div className="split-main">
          <div className="card stack">
            <p className="headline">{data.headline}</p>
            <BarChart
              bars={data.history.map((h, i) => ({
                label: monthShort(h.month),
                value: h.amount_cents,
                highlight: isSpending ? i === data.history.length - 1 : i >= data.history.length - 3,
              }))}
              band={
                data.usual_low_cents !== null && data.usual_high_cents !== null
                  ? { low: data.usual_low_cents, high: data.usual_high_cents }
                  : undefined
              }
            />
            {isSpending && data.usual_low_cents !== null && data.usual_high_cents !== null && (
              <p className="small muted">
                Shaded: your usual range ({eur(data.usual_low_cents)} – {eur(data.usual_high_cents)})
              </p>
            )}
            {data.feedback === "ongoing" && <span className="chip">Noted: you expect this to continue</span>}
          </div>

          {isSpending ? (
            <>
              <div className="card stack">
                <p className="small">{data.question}</p>
                <div className="grid-2">
                  <button type="button" className="btn btn-secondary" disabled={busy} onClick={() => respond("one_off")}>
                    One-off
                  </button>
                  <button type="button" className="btn btn-secondary" disabled={busy} onClick={() => respond("ongoing")}>
                    Expected to continue
                  </button>
                </div>
                {picking ? (
                  <div className="stack">
                    <label className="field">
                      Which category is right?
                      <select value={category} onChange={(e) => setCategory(e.target.value)}>
                        <option value="">Choose a category</option>
                        {data.category_options.map((o) => (
                          <option key={o.value} value={o.value}>
                            {o.label}
                          </option>
                        ))}
                      </select>
                    </label>
                    <button
                      type="button"
                      className="btn btn-primary"
                      disabled={busy || !category}
                      onClick={() => respond("wrong_category", category)}
                    >
                      Save category
                    </button>
                  </div>
                ) : (
                  <div className="grid-2">
                    <button type="button" className="btn btn-ghost" disabled={busy} onClick={() => setPicking(true)}>
                      Category is incorrect
                    </button>
                    <button type="button" className="btn btn-ghost" disabled={busy} onClick={() => respond("dismissed")}>
                      Dismiss
                    </button>
                  </div>
                )}
                {message && <p className="error">{message}</p>}
              </div>
              <div className="actions">
                <Link className="btn btn-primary" to={`${path}/scenario`}>
                  See the impact
                </Link>
              </div>
            </>
          ) : (
            <div className="card stack">
              <p className="small">{data.question}</p>
              <div className="grid-2">
                {GOAL_KINDS.map((kind) => (
                  <button
                    key={kind}
                    type="button"
                    className="btn btn-secondary"
                    disabled={busy}
                    onClick={() => navigate(`/goals/new?kind=${kind}&from=${encodeURIComponent(key)}`)}
                  >
                    {GOAL_LABELS[kind]}
                  </button>
                ))}
              </div>
              <button type="button" className="btn btn-ghost" disabled={busy} onClick={() => respond("dismissed")}>
                No thanks
              </button>
              {message && <p className="error">{message}</p>}
            </div>
          )}

          </div>
          <div className="split-side">
          <details className="card">
            <summary>Why you're seeing this</summary>
            <ul>
              {data.evidence.map((line) => (
                <li key={line}>{line}</li>
              ))}
            </ul>
          </details>

          <div className="card">
            <h3 className="card-title">{isSpending ? "Payments behind this" : "Transfers to savings"}</h3>
            <ul className="list">
              {data.transactions.map((t) => (
                <li key={t.id}>
                  <span className="grow">
                    <span className="muted small">{dayMonth(t.booked_on)}</span> {t.counterparty}
                  </span>
                  <span className={`amount ${t.amount_cents > 0 && isSpending ? "pos" : ""}`}>{eur(t.amount_cents)}</span>
                </li>
              ))}
            </ul>
          </div>
          <p className="muted small">{data.coverage_note}</p>
          </div>
        </div>
      )}
    </Screen>
  );
}
