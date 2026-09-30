const PATHS = {
  home: <><path d="m3 10 9-7 9 7v10H3Z" /><path d="M9 20v-7h6v7" /></>,
  wallet: <><path d="M20 7H5a2 2 0 0 1 0-4h13v4M4 5v14a2 2 0 0 0 2 2h14V7" /><path d="M20 11h-6v5h6M16 13.5h.01" /></>,
  arrow: <path d="M4 12h16m-6-6 6 6-6 6" />,
  pig: <path d="M7 7a8 8 0 0 1 10 0l4 1v7l-3 1-1 4h-3v-3H9v3H6l-1-5-3-2V9h3l1-5 4 2M15 10h.01" />,
  trend: <path d="m3 17 6-6 4 4 8-10m-6 0h6v6" />,
  budget: <><rect x="3" y="13" width="4" height="8" rx="1" /><rect x="10" y="8" width="4" height="13" rx="1" /><rect x="17" y="3" width="4" height="18" rx="1" /></>,
  doc: <path d="M6 3h8l4 4v14H6Zm8 0v5h4M9 12h6m-6 4h6" />,
  gear: <><path d="m9 3-1 3-3 1-2 4 2 2v4l4 2 3-1 3 1 4-2v-4l2-2-2-4-3-1-1-3Z" /><circle cx="12" cy="11" r="3" /></>,
  cart: <><path d="M2 3h3l3 12h11l3-9H6" /><circle cx="9" cy="20" r="1" /><circle cx="18" cy="20" r="1" /></>,
  fork: <path d="M4 3v6c0 3 6 3 6 0V3M7 3v18M20 21V3c-5 2-5 10 0 10" />,
  car: <path d="m5 8 2-5h10l2 5M3 9h18v9H3Zm2 9v3m14-3v3M6 13h2m8 0h2" />,
  bag: <path d="M5 8h14l2 13H3ZM9 9V6a3 3 0 0 1 6 0v3" />,
  house: <><path d="m3 10 9-7 9 7v10H3Z" /><path d="M9 20v-7h6v7" /></>,
  heart: <path d="M12 20s-7-4.5-7-10a4 4 0 0 1 7-2.6A4 4 0 0 1 19 10c0 5.5-7 10-7 10Z" />,
  chevron: <path d="m9 5 7 7-7 7" />,
};

export type IconName = keyof typeof PATHS;

export function Icon({ name, className = "" }: { name: IconName; className?: string }) {
  return (
    <svg className={`icon ${className}`} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.7} strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      {PATHS[name]}
    </svg>
  );
}

export function BrandMark() {
  return (
    <svg className="brand-logo" viewBox="0 0 80 64" role="img" aria-label="KBC">
      <circle cx="40" cy="12" r="10" fill="currentColor" />
      <path d="M10 28Q40 20 70 25V34H10Z" fill="currentColor" />
      <text x="8" y="58" fill="#003b71" fontFamily="Arial,sans-serif" fontWeight="900" fontSize="33" letterSpacing="-2">KBC</text>
    </svg>
  );
}

export function Piggy({ className }: { className?: string }) {
  return (
    <svg className={`pig ${className ?? ""}`} viewBox="0 0 190 100" aria-hidden="true">
      <defs><radialGradient id="piggy-blue" cx="35%" cy="25%" r="80%"><stop stopColor="#9edbff"/><stop offset=".55" stopColor="#55b4fa"/><stop offset="1" stopColor="#1680df"/></radialGradient><linearGradient id="piggy-gold" x2="1" y2="1"><stop stopColor="#ffe190"/><stop offset="1" stopColor="#edaa23"/></linearGradient></defs><path d="M8 98a86 86 0 0 1 172 0" fill="#deefff"/><ellipse cx="99" cy="91" rx="57" ry="6" fill="#bedefa"/><path d="M142 47q20-14 17 1t-14 4" fill="none" stroke="#248ded" strokeWidth="5"/><path d="M70 75v17h12l5-15m32-2v17h12l3-23" fill="#238ae5"/><ellipse cx="101" cy="56" rx="45" ry="33" fill="url(#piggy-blue)"/><path d="M75 33 70 14q18 0 21 16" fill="#55aefa"/><path d="m76 28-2-9 10 10" fill="#1b82d8"/><ellipse cx="59" cy="58" rx="13" ry="15" fill="#72c2fc"/><ellipse cx="54" cy="57" rx="2" ry="4" fill="#2986d6"/><ellipse cx="62" cy="57" rx="2" ry="4" fill="#2986d6"/><circle cx="78" cy="43" r="3" fill="#074d91"/><path d="m97 27 18 1" stroke="#0e75c3" strokeWidth="4" strokeLinecap="round"/><circle cx="108" cy="11" r="9" fill="url(#piggy-gold)"/><text x="108" y="15" fontSize="12" textAnchor="middle" fill="#c08822">€</text><ellipse cx="49" cy="92" rx="11" ry="3" fill="url(#piggy-gold)"/><ellipse cx="65" cy="95" rx="10" ry="3" fill="url(#piggy-gold)"/>
    </svg>
  );
}
