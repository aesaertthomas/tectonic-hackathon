import type { ReactNode } from "react";
import { Link } from "react-router-dom";
import { Icon } from "./Icons";

type Props = { title: string; subtitle?: string; back?: string; action?: ReactNode; children: ReactNode };

export function Screen({ title, subtitle, back, action, children }: Props) {
  return (
    <>
      <div className="page-heading">
        <div>
          {back && (
            <Link to={back} className="back"><Icon name="arrow" /> Back</Link>
          )}
          <h1>{title}</h1>
          {subtitle && <p>{subtitle}</p>}
        </div>
        {action}
      </div>
      {children}
    </>
  );
}
