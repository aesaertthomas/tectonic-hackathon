import { Link } from "react-router-dom";
import { BarChart } from "../components/BarChart";
import { Icon, type IconName, Piggy } from "../components/Icons";
import { Screen } from "../components/Screen";
import { eur, eurWhole, longDate, monthLong, monthShort } from "../format";
import type { Budget, BudgetCategory, BudgetStatus, Overview } from "../types";
import { useLoad } from "../useLoad";
import "./budget.css";

const COLOUR: Record<BudgetStatus, "red" | "orange" | "green"> = { high: "red", above: "orange", ok: "green" };
const STATUS_TITLE: Record<BudgetStatus, string> = { high: "Unusual month", above: "Above your usual month", ok: "On track" };
const ICONS: Record<string, IconName> = {
  food: "cart", restaurants: "fork", transport: "car", clothing: "bag",
  housing_energy: "house", household_maintenance: "house", healthcare: "heart",
  subscriptions: "doc", communication: "doc", insurance_financial_services: "doc",
  leisure_culture: "trend", debt_repayment: "wallet",
};
const ACCOUNT_TYPES = { current: "Current account", savings: "Savings account", credit_card: "Credit card" } as const;

/** Share of the usual month, for the bar. Clamped so refunds and big spikes still draw sanely. */
export function barWidth(amount: number, typical: number): number {
  if (typical <= 0) return amount > 0 ? 100 : 0;
  return Math.min(100, Math.max(0, (amount / typical) * 100));
}

function percentLabel(amount: number, typical: number): string {
  return typical > 0 ? `${Math.round((amount / typical) * 100)}%` : "new";
}

function Progress({ amount, typical, label }: { amount: number; typical: number; label: string }) {
  const pct = percentLabel(amount, typical);
  return (
    <div className="progress-row">
      <div className="bar" role="img" aria-label={`${pct} of ${label}`}>
        <span style={{ width: `${barWidth(amount, typical)}%` }} />
      </div>
      <b className="percent">{pct}</b>
    </div>
  );
}

function CategoryCard({ c }: { c: BudgetCategory }) {
  return (
    <a href={`#cat-${c.category}`} className={`category ${COLOUR[c.status]}`}>
      <span className="tile-icon"><Icon name={ICONS[c.category] ?? "budget"} /></span>
      <h3>{c.label}</h3>
      <strong className="amount-big">{eurWhole(c.amount_cents)}</strong>
      <span className="of">usual {eurWhole(c.typical_cents)}</span>
      <Progress amount={c.amount_cents} typical={c.typical_cents} label="your usual month" />
      <div className="note">
        <span className="note-symbol" aria-hidden="true">{c.status === "ok" ? "✓" : "!"}</span>
        <p>{c.noted ? "Noted: you expect this to continue." : c.note}</p>
      </div>
    </a>
  );
}

function DetailRow({ c, open }: { c: BudgetCategory; open: boolean }) {
  return (
    <details className={`detail ${COLOUR[c.status]}`} id={`cat-${c.category}`} open={open}>
      <summary>
        <span className="detail-name">
          <span className="tile-icon"><Icon name={ICONS[c.category] ?? "budget"} /></span>
          <b>{c.label}</b>
          <span className="fold" aria-hidden="true">⌄</span>
        </span>
        <span className="detail-amount"><b>{eur(c.amount_cents)}</b> <span>usual {eur(c.typical_cents)}</span></span>
        <Progress amount={c.amount_cents} typical={c.typical_cents} label="your usual month" />
      </summary>
      <div className="detail-content">
        <section>
          <h4>Last {c.history.length} months</h4>
          <BarChart
            bars={c.history.map((h, i) => ({ label: monthShort(h.month), value: h.amount_cents, highlight: i === c.history.length - 1 }))}
            band={{ low: c.usual_low_cents, high: c.usual_high_cents }}
          />
          <p className="small muted">Shaded: your usual range</p>
        </section>
        <section className="tip">
          <h4>{STATUS_TITLE[c.status]}</h4>
          <p>{c.note}</p>
          {c.noted && <span className="chip">Noted: you expect this to continue</span>}
          {c.insight_key && (
            <Link className="btn btn-primary" to={`/insights/${encodeURIComponent(c.insight_key)}`}>
              Look at this change <Icon name="chevron" />
            </Link>
          )}
        </section>
        <section className="comparison">
          <h4>Your usual month</h4>
          <strong>{eurWhole(c.typical_cents)}</strong>
          <p>Usually between {eurWhole(c.usual_low_cents)} and {eurWhole(c.usual_high_cents)}.</p>
        </section>
      </div>
    </details>
  );
}

export function Home() {
  const budget = useLoad<Budget>("/budget");
  const overview = useLoad<Overview>("/overview");
  const error = budget.error ?? overview.error;
  const b = budget.data;
  const o = overview.data;
  const saving = o?.insights.find((i) => i.type === "saving");

  return (
    <Screen
      title="Budget & insights"
      subtitle="See where your money went this month compared with a usual month, and what it could mean."
      action={b && <span className="month-pill">{monthLong(b.month)}</span>}
    >
      {error && <p className="error">{error}</p>}
      {!error && (!b || !o) && <p className="muted">Loading…</p>}
      {b && o && (
        <>
          <div className="summary-row">
            <section className={`card month-summary ${COLOUR[b.status]}`} aria-label="This month">
              <div className="month-number">
                <h3>{monthLong(b.month)}</h3>
                <strong>{eur(b.total_cents)}</strong>
                <p>usual {eur(b.typical_total_cents)}</p>
              </div>
              <Progress amount={b.total_cents} typical={b.typical_total_cents} label="a usual month" />
              <div className="status-pill">
                <span className="dot" aria-hidden="true" />
                <div><strong>{STATUS_TITLE[b.status]}</strong><p>{b.note}</p></div>
              </div>
            </section>
            <section className="card accounts" aria-label="Accounts">
              {o.accounts.map((a) => (
                <div key={a.id} className="account">
                  <span className="small muted">{ACCOUNT_TYPES[a.type]}</span>
                  <b className={a.balance_cents < 0 ? "neg" : undefined}>{eur(a.balance_cents)}</b>
                </div>
              ))}
            </section>
          </div>

          {b.categories.length === 0 ? (
            <div className="card muted">{b.note}</div>
          ) : (
            <section aria-labelledby="categories-title">
              <div className="section-heading">
                <h2 id="categories-title">Spending by category</h2>
                <span className="unit-label">€ this month · % of your usual month</span>
              </div>
              <div className="categories">
                {b.categories.slice(0, 6).map((c) => <CategoryCard key={c.category} c={c} />)}
              </div>
            </section>
          )}

          <div className="advice-banner">
            <Piggy />
            <div className="banner-copy">
              <h2>{saving ? "You're saving more" : "Saving for something?"}</h2>
              <p>{saving ? saving.headline : "Set a goal and see when you could reach it."}</p>
            </div>
            <Link className="btn btn-primary banner-cta" to={saving ? `/insights/${encodeURIComponent(saving.key)}` : "/goals/new"}>
              {saving ? "Connect it to a goal" : "Set a goal"} <Icon name="arrow" />
            </Link>
          </div>

          {b.categories.length > 0 && (
            <section aria-labelledby="details-title">
              <div className="section-heading"><h2 id="details-title">Details per category</h2></div>
              {b.categories.map((c, i) => <DetailRow key={c.category} c={c} open={i === 0} />)}
            </section>
          )}

          <footer className="page-footer">
            <span>{b.coverage_note}</span>
            <span>Data up to {longDate(o.as_of)}</span>
          </footer>
        </>
      )}
    </Screen>
  );
}
