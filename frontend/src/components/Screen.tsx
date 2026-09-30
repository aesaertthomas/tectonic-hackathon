import type { ReactNode } from "react";
import { Link } from "react-router-dom";
import logo from "../assets/logo.svg";

type Props = { title: string; back?: string; action?: ReactNode; children: ReactNode };

export function Screen({ title, back, action, children }: Props) {
  return (
    <div className="screen">
      <header className="topbar">
        {back ? (
          <Link to={back} className="icon-btn" aria-label="Back">
            ‹
          </Link>
        ) : (
          <img src={logo} alt="KBC" className="topbar-logo" />
        )}
        <h1>{title}</h1>
        {action}
      </header>
      <main className="content">{children}</main>
    </div>
  );
}
