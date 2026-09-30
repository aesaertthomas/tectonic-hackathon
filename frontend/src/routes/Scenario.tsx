import { useState } from "react";
import { useParams } from "react-router-dom";
import { Screen } from "../components/Screen";
import { eurWhole, monthLong, signedEur } from "../format";
import type { Scenario as ScenarioData, ScenarioResponse } from "../types";
import { useLoad } from "../useLoad";

const LENGTHS = [1, 2, 3];

function monthsLabel(n: number) {
  return `${n} ${n === 1 ? "month" : "months"}`;
}

function ScenarioCard({ title, scenario }: { title: string; scenario: ScenarioData }) {
  const last = scenario.months[scenario.months.length - 1];
  return (
    <div className="card stack-tight">
      <span className="small muted">{title}</span>
      <span className="amount big estimate">{eurWhole(last.end_balance_cents)}</span>
      <span className="small muted">estimated balance after {monthsLabel(scenario.months.length)}</span>
      <span className={`small ${scenario.cumulative_net_cents < 0 ? "neg" : "pos"}`}>
        {signedEur(scenario.cumulative_net_cents)} in total
      </span>
    </div>
  );
}

export function Scenario() {
  const { key = "" } = useParams();
  const base = `/insights/${encodeURIComponent(key)}`;
  const [months, setMonths] = useState(3);
  const { data, error } = useLoad<ScenarioResponse>(`${base}/scenario?months=${months}`);
  const firstBelow = data?.continues.months.find((m) => m.end_balance_cents < data.cash_buffer_cents);

  return (
    <Screen title="See the impact" back={base}>
      <div className="segmented" role="group" aria-label="Forecast length">
        {LENGTHS.map((n) => (
          <button key={n} type="button" aria-pressed={months === n} onClick={() => setMonths(n)}>
            {monthsLabel(n)}
          </button>
        ))}
      </div>
      {error && <p className="error">{error}</p>}
      {!data && !error && <p className="muted">Loading…</p>}
      {data && (
        <>
          <div className="grid-2">
            <ScenarioCard title="If it's a one-off" scenario={data.one_off} />
            <ScenarioCard title="If it continues" scenario={data.continues} />
          </div>

          {data.continues.below_buffer && firstBelow && (
            <div className="warning" role="status">
              If it continues, your current account could drop below your {eurWhole(data.cash_buffer_cents)} buffer by the end of{" "}
              {monthLong(firstBelow.month)}.
              {data.continues.savings_transfer_may_be_needed && " A transfer from your savings may be needed to cover your payments."}
            </div>
          )}

          <div className="card">
            <h3 className="card-title">Estimated month-end balance</h3>
            <table className="balances">
              <thead>
                <tr>
                  <th>Month</th>
                  <th>One-off</th>
                  <th>Continues</th>
                </tr>
              </thead>
              <tbody>
                {data.one_off.months.map((m, i) => {
                  const cont = data.continues.months[i];
                  return (
                    <tr key={m.month}>
                      <td>{monthLong(m.month)}</td>
                      <td>{eurWhole(m.end_balance_cents)}</td>
                      <td className={cont.end_balance_cents < data.cash_buffer_cents ? "neg" : ""}>{eurWhole(cont.end_balance_cents)}</td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>

          <div className="card stack">
            <h3 className="card-title">What's included if it continues</h3>
            <div className="legend">
              <span>Confirmed payment</span>
              <span className="estimate">Estimate</span>
            </div>
            {data.continues.months.map((m) => (
              <details key={m.month}>
                <summary>
                  {monthLong(m.month)} · {signedEur(m.net_cents)}
                </summary>
                <ul className="list">
                  {m.lines.map((line, i) => (
                    <li key={`${line.label}-${i}`}>
                      <span className={line.confirmed ? "" : "estimate"}>{line.label}</span>
                      <span className="amount">{signedEur(line.amount_cents)}</span>
                    </li>
                  ))}
                </ul>
              </details>
            ))}
          </div>

          <details className="card">
            <summary>Assumptions</summary>
            <ul>
              {data.assumptions.map((a) => (
                <li key={a}>{a}</li>
              ))}
            </ul>
          </details>
        </>
      )}
    </Screen>
  );
}
