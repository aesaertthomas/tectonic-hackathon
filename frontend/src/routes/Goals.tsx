import { Link } from "react-router-dom";
import { Screen } from "../components/Screen";
import { GOAL_LABELS, eurWhole, monthLong } from "../format";
import type { GoalPlan, GoalsResponse } from "../types";
import { useLoad } from "../useLoad";

function eta(plan: GoalPlan): string {
  if (plan.months_needed === 0) return "Reached";
  if (!plan.estimated_completion) return "Set a monthly amount to see an estimate";
  return `around ${monthLong(plan.estimated_completion)}`;
}

export function Goals() {
  const { data, error } = useLoad<GoalsResponse>("/goals");

  return (
    <Screen
      title="My goals"
      action={
        data && (
          <Link to="/goals/new" className="btn btn-primary banner-cta">
            New goal
          </Link>
        )
      }
    >
      {error && <p className="error">{error}</p>}
      {!data && !error && <p className="muted">Loading…</p>}
      {data && (
        <>
          {data.goals.length === 0 && (
            <div className="card muted">No goals yet. A goal connects what you save to something you want.</div>
          )}
          <div className="goal-grid">
          {data.goals.map((g) => (
            <Link key={g.id} to={`/goals/${g.id}`} className="card card-link">
              <div className="stack-tight grow">
                <div className="row">
                  <span className="account-name">{g.name}</span>
                  <span className="tag">{GOAL_LABELS[g.kind]}</span>
                </div>
                <div className="progress" aria-label={`${g.plan.progress_pct}% earmarked`}>
                  <div style={{ width: `${g.plan.progress_pct}%` }} />
                </div>
                <span className="small muted">
                  {eurWhole(g.earmarked_cents)} of {eurWhole(g.target_cents)} · {eta(g.plan)}
                </span>
              </div>
              <span className="chevron" aria-hidden="true">
                ›
              </span>
            </Link>
          ))}
          </div>
        </>
      )}
    </Screen>
  );
}
