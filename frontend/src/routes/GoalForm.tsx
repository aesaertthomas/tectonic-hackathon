import { useEffect, useState } from "react";
import { useNavigate, useParams, useSearchParams } from "react-router-dom";
import { ApiError, api, errorMessage } from "../api";
import { useAuth } from "../auth";
import { Screen } from "../components/Screen";
import { GOAL_DEFAULT_NAMES, GOAL_LABELS, eurWhole, monthLong } from "../format";
import type { GoalEstimate, GoalKind, GoalsResponse } from "../types";
import { useLoad } from "../useLoad";

const KINDS: GoalKind[] = ["car", "home", "emergency", "other"];
const STEP_CENTS = 1000;

type Form = { kind: GoalKind; name: string; target: string; date: string; earmarked: string; monthly: number };

/** "1500" or "1500,50" -> cents; empty or invalid -> null. */
function toCents(value: string): number | null {
  const n = Number(value.trim().replace(",", "."));
  return value.trim() !== "" && Number.isFinite(n) && n >= 0 ? Math.round(n * 100) : null;
}

function isKind(value: string | null): value is GoalKind {
  return value !== null && (KINDS as string[]).includes(value);
}

export function GoalForm() {
  const { id } = useParams();
  const [params] = useSearchParams();
  const navigate = useNavigate();
  const { expire } = useAuth();
  const { data, error } = useLoad<GoalsResponse>("/goals");
  const editing = id !== undefined ? data?.goals.find((g) => g.id === Number(id)) : undefined;
  const fromInsight = params.get("from");
  const kindParam = params.get("kind");

  const [form, setForm] = useState<Form | null>(null);
  const [estimate, setEstimate] = useState<GoalEstimate | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [confirmDelete, setConfirmDelete] = useState(false);

  useEffect(() => {
    if (!data || form) return;
    if (id !== undefined) {
      const g = data.goals.find((x) => x.id === Number(id));
      if (!g) return;
      setForm({
        kind: g.kind,
        name: g.name,
        target: String(g.target_cents / 100),
        date: g.target_date ?? "",
        earmarked: String(g.earmarked_cents / 100),
        monthly: g.monthly_contribution_cents,
      });
    } else {
      const kind = isKind(kindParam) ? kindParam : "car";
      setForm({ kind, name: GOAL_DEFAULT_NAMES[kind], target: "", date: "", earmarked: "0", monthly: data.suggested_monthly_cents || 10000 });
    }
  }, [data, form, id, kindParam]);

  const target = form ? toCents(form.target) : null;
  const earmarked = form ? toCents(form.earmarked) : null;
  const valid = form !== null && form.name.trim() !== "" && target !== null && target > 0 && earmarked !== null;

  useEffect(() => {
    if (!form || !valid) {
      setEstimate(null);
      return;
    }
    let cancelled = false;
    const body = {
      kind: form.kind,
      target_cents: target,
      earmarked_cents: earmarked,
      monthly_contribution_cents: form.monthly,
      target_date: form.date || null,
      goal_id: editing?.id ?? null,
    };
    const timer = setTimeout(() => {
      api.post<GoalEstimate>("/goals/estimate", body).then(
        (result) => {
          if (cancelled) return;
          setEstimate(result);
          setMessage(null);
        },
        (e: unknown) => {
          if (cancelled) return;
          if (e instanceof ApiError && e.status === 401) return expire();
          setEstimate(null);
          setMessage(errorMessage(e));
        },
      );
    }, 250);
    return () => {
      cancelled = true;
      clearTimeout(timer);
    };
  }, [form?.kind, form?.date, form?.monthly, target, earmarked, valid, editing?.id, expire]); // eslint-disable-line react-hooks/exhaustive-deps

  async function save() {
    if (!form || !valid) return;
    setBusy(true);
    setMessage(null);
    const body = {
      name: form.name.trim(),
      target_cents: target,
      target_date: form.date || null,
      earmarked_cents: earmarked,
      monthly_contribution_cents: form.monthly,
    };
    try {
      if (editing) await api.patch(`/goals/${editing.id}`, body);
      else await api.post("/goals", { ...body, kind: form.kind, ...(fromInsight ? { from_insight: fromInsight } : {}) });
      navigate("/goals");
    } catch (e) {
      if (e instanceof ApiError && e.status === 401) return expire();
      setMessage(errorMessage(e));
      setBusy(false);
    }
  }

  async function remove() {
    if (!editing) return;
    if (!confirmDelete) {
      setConfirmDelete(true);
      return;
    }
    setBusy(true);
    try {
      await api.del(`/goals/${editing.id}`);
      navigate("/goals");
    } catch (e) {
      if (e instanceof ApiError && e.status === 401) return expire();
      setMessage(errorMessage(e));
      setBusy(false);
    }
  }

  const title = id !== undefined ? "Edit goal" : "New goal";
  if (error) return <Screen title={title} back="/goals"><p className="error">{error}</p></Screen>;
  if (data && id !== undefined && !editing) return <Screen title={title} back="/goals"><p className="muted">Goal not found.</p></Screen>;
  if (!data || !form) return <Screen title={title} back="/goals"><p className="muted">Loading…</p></Screen>;

  const available = data.available_to_earmark_cents + (editing?.earmarked_cents ?? 0);
  const sliderMax = Math.max(200_000, form.monthly, data.suggested_monthly_cents * 2);
  const update = (patch: Partial<Form>) => setForm({ ...form, ...patch });
  const plan = estimate?.plan;

  return (
    <Screen title={title} back="/goals">
      {!editing && (
        <div className="segmented" role="group" aria-label="Goal type">
          {KINDS.map((k) => (
            <button
              key={k}
              type="button"
              aria-pressed={form.kind === k}
              onClick={() => update({ kind: k, name: form.name === GOAL_DEFAULT_NAMES[form.kind] ? GOAL_DEFAULT_NAMES[k] : form.name })}
            >
              {GOAL_LABELS[k]}
            </button>
          ))}
        </div>
      )}

      <div className="split">
      <div className="split-main">
      <div className="card stack">
        <label className="field">
          Name
          <input value={form.name} maxLength={60} onChange={(e) => update({ name: e.target.value })} />
        </label>
        <label className="field">
          Amount you want to save (€)
          <input inputMode="decimal" value={form.target} placeholder="15000" onChange={(e) => update({ target: e.target.value })} />
        </label>
        <label className="field">
          Target date (optional)
          <input type="date" value={form.date} onChange={(e) => update({ date: e.target.value })} />
        </label>
        <label className="field">
          Already set aside from savings (€)
          <input inputMode="decimal" value={form.earmarked} onChange={(e) => update({ earmarked: e.target.value })} />
          <span className="small muted">Available to earmark: {eurWhole(available)}</span>
        </label>
        <label className="field">
          Monthly contribution: <strong>{eurWhole(form.monthly)}</strong>
          <input
            type="range"
            min={0}
            max={sliderMax}
            step={STEP_CENTS}
            value={form.monthly}
            onChange={(e) => update({ monthly: Number(e.target.value) })}
          />
          {data.suggested_monthly_cents > 0 && (
            <span className="small muted">You've recently been saving about {eurWhole(data.suggested_monthly_cents)} a month.</span>
          )}
        </label>
      </div>

      <div className="actions">
      <button type="button" className="btn btn-primary" disabled={busy || !valid} onClick={save}>
        {editing ? "Save changes" : "Create goal"}
      </button>
      {editing && (
        <button type="button" className="btn btn-ghost" disabled={busy} onClick={remove}>
          {confirmDelete ? "Tap again to delete" : "Delete goal"}
        </button>
      )}
      </div>
      </div>

      <div className="split-side">
      {plan && target !== null && (
        <div className="card stack-tight">
          <span className="tag">Estimate</span>
          {plan.months_needed === 0 && <p className="headline">You've already set aside enough for this goal.</p>}
          {plan.months_needed === null && <p>Choose a monthly amount to see when you could reach this goal.</p>}
          {plan.months_needed !== null && plan.months_needed > 0 && plan.estimated_completion && (
            <p className="headline">
              You could reach {eurWhole(target)} around {monthLong(plan.estimated_completion)} ({plan.months_needed} months).
            </p>
          )}
          {plan.required_monthly_cents !== null && form.date && (
            <p className={plan.on_track ? "pos" : "small"}>
              {plan.on_track
                ? "On track for your target date."
                : `To reach it by ${monthLong(form.date)} you'd need about ${eurWhole(plan.required_monthly_cents)} a month.`}
            </p>
          )}
          <span className="small muted">Remaining: {eurWhole(plan.remaining_cents)}. An estimate, assuming you keep this up.</span>
        </div>
      )}

      {estimate && estimate.next_steps.length > 0 && (
        <div className="card stack">
          <h3 className="card-title">Next steps</h3>
          {estimate.next_steps.map((s) => (
            <div key={s.title} className="stack-tight">
              <strong>{s.title}</strong>
              <span className="small muted">{s.reason}</span>
            </div>
          ))}
          <span className="small muted">{estimate.verify_note}</span>
        </div>
      )}

      {message && <p className="error">{message}</p>}
      </div>
      </div>
    </Screen>
  );
}
