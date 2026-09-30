import type { ReactNode } from "react";
import { Link, useLocation } from "react-router-dom";
import { useAuth } from "../auth";
import "../shell.css";
import { BrandMark, Icon, type IconName } from "./Icons";

const INERT: [IconName, string][] = [
  ["home", "Overview"], ["wallet", "Accounts"], ["arrow", "Payments"], ["trend", "Investments"],
];

function initials(name: string) {
  return name.split(/[\s&]+/).filter(Boolean).map((w) => w[0]!.toUpperCase()).slice(0, 2).join("");
}

export function AppShell({ children }: { children: ReactNode }) {
  const { me, logout } = useAuth();
  const { pathname } = useLocation();
  const onGoals = pathname.startsWith("/goals");
  const links = [
    { to: "/", icon: "budget" as const, label: "Budget & insights", active: !onGoals },
    { to: "/goals", icon: "pig" as const, label: "Goals", active: onGoals },
  ];

  return (
    <>
      <header className="topbar">
        <Link className="brand" to="/" aria-label="Budget & insights"><BrandMark /></Link>
        <span className="profile">
          <span className="avatar" aria-hidden="true">{initials(me.display_name)}</span>
          <b>{me.display_name}</b>
          <button type="button" className="logout" onClick={logout}>Log out</button>
        </span>
      </header>
      <aside className="sidebar">
        <nav aria-label="Main navigation">
          {INERT.map(([icon, label]) => (
            <span key={label} className="nav" aria-disabled="true"><Icon name={icon} /><span>{label}</span></span>
          ))}
          {links.map((l) => (
            <Link key={l.to} to={l.to} className={`nav${l.active ? " active" : ""}`} aria-current={l.active ? "page" : undefined}>
              <Icon name={l.icon} /><span>{l.label}</span>
            </Link>
          ))}
        </nav>
        <span className="nav settings" aria-disabled="true"><Icon name="gear" /><span>Settings</span></span>
      </aside>
      <nav className="tabs" aria-label="Main navigation">
        {links.map((l) => (
          <Link key={l.to} to={l.to} className={l.active ? "active" : undefined} aria-current={l.active ? "page" : undefined}>
            <Icon name={l.icon} /><span>{l.label}</span>
          </Link>
        ))}
      </nav>
      <main className="page"><div className="page-inner">{children}</div></main>
    </>
  );
}
