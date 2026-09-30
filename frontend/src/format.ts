import type { GoalKind } from "./types";

const money = new Intl.NumberFormat("en-IE", { style: "currency", currency: "EUR" });
const moneyWhole = new Intl.NumberFormat("en-IE", {
  style: "currency",
  currency: "EUR",
  minimumFractionDigits: 0,
  maximumFractionDigits: 0,
});

export const eur = (cents: number) => money.format(cents / 100);
export const eurWhole = (cents: number) => moneyWhole.format(cents / 100);
export const signedEur = (cents: number) => (cents > 0 ? "+" : "") + eurWhole(cents);

const SHORT = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
const LONG = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"];

// Accepts "2026-09" or "2026-09-30".
function parts(iso: string) {
  const [y, m, d] = iso.split("-").map(Number);
  return { y, m, d };
}

export const monthShort = (iso: string) => SHORT[parts(iso).m - 1] ?? iso;
export const monthLong = (iso: string) => {
  const { y, m } = parts(iso);
  return `${LONG[m - 1]} ${y}`;
};
export const dayMonth = (iso: string) => {
  const { m, d } = parts(iso);
  return `${d} ${SHORT[m - 1]}`;
};
export const longDate = (iso: string) => {
  const { y, m, d } = parts(iso);
  return `${d} ${LONG[m - 1]} ${y}`;
};

export const GOAL_LABELS: Record<GoalKind, string> = {
  car: "Car",
  home: "Home",
  emergency: "Emergency fund",
  other: "Another goal",
};

export const GOAL_DEFAULT_NAMES: Record<GoalKind, string> = {
  car: "New car",
  home: "New home",
  emergency: "Emergency fund",
  other: "My goal",
};
