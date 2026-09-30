export type Me = { display_name: string };

export type Account = {
  id: number;
  name: string;
  number: string;
  type: "current" | "savings" | "credit_card";
  balance_cents: number;
};

export type InsightCard = { key: string; type: "spending" | "saving"; headline: string; noted: boolean };

export type Overview = {
  display_name: string;
  as_of: string;
  accounts: Account[];
  insights: InsightCard[];
  coverage_note: string;
};

export type MonthAmount = { month: string; amount_cents: number };
export type Txn = { id: number; booked_on: string; counterparty: string; amount_cents: number; category: string };
export type CategoryOption = { value: string; label: string };

export type InsightDetail = {
  key: string;
  type: "spending" | "saving";
  headline: string;
  question: string;
  category: string | null;
  history: MonthAmount[];
  this_month_cents: number;
  typical_cents: number;
  usual_low_cents: number | null;
  usual_high_cents: number | null;
  transactions: Txn[];
  evidence: string[];
  feedback: string | null;
  category_options: CategoryOption[];
  coverage_note: string;
};

export type FeedbackResponse = "one_off" | "ongoing" | "wrong_category" | "dismissed";

export type ForecastLine = { label: string; amount_cents: number; confirmed: boolean };
export type MonthProjection = {
  month: string;
  start_balance_cents: number;
  net_cents: number;
  end_balance_cents: number;
  lines: ForecastLine[];
};
export type Scenario = {
  name: "one_off" | "continues";
  months: MonthProjection[];
  cumulative_net_cents: number;
  min_balance_cents: number;
  below_buffer: boolean;
  savings_transfer_may_be_needed: boolean;
};
export type ScenarioResponse = {
  key: string;
  months: number;
  cash_buffer_cents: number;
  one_off: Scenario;
  continues: Scenario;
  assumptions: string[];
  coverage_note: string;
};

export type GoalKind = "car" | "home" | "emergency" | "other";
export type GoalPlan = {
  remaining_cents: number;
  months_needed: number | null;
  estimated_completion: string | null;
  required_monthly_cents: number | null;
  on_track: boolean | null;
  progress_pct: number;
};
export type NextStep = { title: string; reason: string };
export type Goal = {
  id: number;
  kind: GoalKind;
  name: string;
  target_cents: number;
  target_date: string | null;
  earmarked_cents: number;
  monthly_contribution_cents: number;
  plan: GoalPlan;
  next_steps: NextStep[];
};
export type GoalsResponse = {
  goals: Goal[];
  available_to_earmark_cents: number;
  suggested_monthly_cents: number;
  verify_note: string;
};
export type GoalEstimate = { plan: GoalPlan; next_steps: NextStep[]; verify_note: string };
