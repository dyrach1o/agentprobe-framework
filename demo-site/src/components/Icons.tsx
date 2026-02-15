/**
 * Custom SVG icons matching the AgentProbe logo style:
 * Gold-to-violet gradient, line art with circuit nodes.
 */

interface IconProps {
  size?: number;
  className?: string;
}

/* Shared gradient definition — include once in SVG */
function GradientDefs({ id }: { id: string }) {
  return (
    <defs>
      <linearGradient id={id} x1="0%" y1="0%" x2="100%" y2="100%">
        <stop offset="0%" stopColor="#e2a04f" />
        <stop offset="50%" stopColor="#c76a4a" />
        <stop offset="100%" stopColor="#8b5cf6" />
      </linearGradient>
    </defs>
  );
}

/* ------------------------------------------------------------------ */
/*  Feature / Landing page icons                                       */
/* ------------------------------------------------------------------ */

export function TraceIcon({ size = 24, className }: IconProps) {
  const id = "grad-trace";
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" className={className}>
      <GradientDefs id={id} />
      <path
        d="M3 12h4l3-8 4 16 3-8h4"
        stroke={`url(#${id})`}
        strokeWidth="1.8"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
      <circle cx="21" cy="12" r="1.5" fill="#8b5cf6" />
      <circle cx="3" cy="12" r="1.5" fill="#e2a04f" />
    </svg>
  );
}

export function EvalIcon({ size = 24, className }: IconProps) {
  const id = "grad-eval";
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" className={className}>
      <GradientDefs id={id} />
      <path
        d="M12 2L3 7v6c0 5.25 3.85 10.15 9 11.25C17.15 23.15 21 18.25 21 13V7l-9-5z"
        stroke={`url(#${id})`}
        strokeWidth="1.8"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
      <path
        d="M9 12l2 2 4-4"
        stroke={`url(#${id})`}
        strokeWidth="1.8"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}

export function CostIcon({ size = 24, className }: IconProps) {
  const id = "grad-cost";
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" className={className}>
      <GradientDefs id={id} />
      <circle cx="12" cy="12" r="9.5" stroke={`url(#${id})`} strokeWidth="1.8" />
      <path
        d="M12 6v12M15 9.5c0-1.38-1.34-2.5-3-2.5s-3 1.12-3 2.5 1.34 2.5 3 2.5 3 1.12 3 2.5-1.34 2.5-3 2.5"
        stroke={`url(#${id})`}
        strokeWidth="1.8"
        strokeLinecap="round"
      />
    </svg>
  );
}

export function SafetyIcon({ size = 24, className }: IconProps) {
  const id = "grad-safety";
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" className={className}>
      <GradientDefs id={id} />
      <path
        d="M12 2L4 5v6.09c0 5.05 3.41 9.76 8 10.91 4.59-1.15 8-5.86 8-10.91V5l-8-3z"
        stroke={`url(#${id})`}
        strokeWidth="1.8"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
      <path
        d="M12 9v4M12 16h.01"
        stroke={`url(#${id})`}
        strokeWidth="1.8"
        strokeLinecap="round"
      />
    </svg>
  );
}

/* ------------------------------------------------------------------ */
/*  Demo card / page icons                                             */
/* ------------------------------------------------------------------ */

export function ProbeEyeIcon({ size = 24, className }: IconProps) {
  const id = "grad-eye";
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" className={className}>
      <GradientDefs id={id} />
      <path
        d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8S1 12 1 12z"
        stroke={`url(#${id})`}
        strokeWidth="1.8"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
      <circle cx="12" cy="12" r="3" stroke={`url(#${id})`} strokeWidth="1.8" />
      <circle cx="12" cy="12" r="1" fill="#8b5cf6" />
      {/* Circuit nodes radiating out */}
      <line x1="17" y1="7" x2="20" y2="4" stroke="#8b5cf6" strokeWidth="1.2" strokeLinecap="round" />
      <rect x="19" y="3" width="2" height="2" rx="0.5" stroke="#8b5cf6" strokeWidth="1" fill="none" />
    </svg>
  );
}

export function FlaskIcon({ size = 24, className }: IconProps) {
  const id = "grad-flask";
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" className={className}>
      <GradientDefs id={id} />
      <path
        d="M9 3h6M10 3v6.5L4.5 19.5a1.5 1.5 0 001.3 2.2h12.4a1.5 1.5 0 001.3-2.2L14 9.5V3"
        stroke={`url(#${id})`}
        strokeWidth="1.8"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
      <path
        d="M7 15h10"
        stroke={`url(#${id})`}
        strokeWidth="1.5"
        strokeLinecap="round"
        strokeDasharray="2 2"
      />
      {/* Bubbles */}
      <circle cx="10" cy="18" r="1" fill="#e2a04f" opacity="0.6" />
      <circle cx="14" cy="17" r="0.7" fill="#8b5cf6" opacity="0.6" />
    </svg>
  );
}

export function ChartIcon({ size = 24, className }: IconProps) {
  const id = "grad-chart";
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" className={className}>
      <GradientDefs id={id} />
      <rect x="3" y="13" width="4" height="8" rx="1" stroke={`url(#${id})`} strokeWidth="1.8" />
      <rect x="10" y="8" width="4" height="13" rx="1" stroke={`url(#${id})`} strokeWidth="1.8" />
      <rect x="17" y="3" width="4" height="18" rx="1" stroke={`url(#${id})`} strokeWidth="1.8" />
      {/* Connecting trend line with nodes */}
      <path d="M5 11l5-3.5L17 5" stroke="#8b5cf6" strokeWidth="1.2" strokeLinecap="round" strokeDasharray="2 2" />
      <circle cx="5" cy="11" r="1.2" fill="#e2a04f" />
      <circle cx="12" cy="6.5" r="1.2" fill="#c76a4a" />
      <circle cx="19" cy="3" r="1.2" fill="#8b5cf6" />
    </svg>
  );
}

/* ------------------------------------------------------------------ */
/*  Trace timeline icons                                               */
/* ------------------------------------------------------------------ */

export function BrainIcon({ size = 24, className }: IconProps) {
  const id = "grad-brain";
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" className={className}>
      <GradientDefs id={id} />
      <path
        d="M12 2a5 5 0 00-4.8 3.6A4 4 0 004 9.5a4 4 0 001.2 7.2A5 5 0 0012 22a5 5 0 006.8-5.3A4 4 0 0020 9.5a4 4 0 00-3.2-3.9A5 5 0 0012 2z"
        stroke={`url(#${id})`}
        strokeWidth="1.8"
        strokeLinecap="round"
      />
      <path d="M12 2v20" stroke={`url(#${id})`} strokeWidth="1" strokeDasharray="2 2" />
      <circle cx="9" cy="9" r="1" fill="#e2a04f" />
      <circle cx="15" cy="9" r="1" fill="#8b5cf6" />
      <circle cx="9" cy="15" r="1" fill="#c76a4a" />
      <circle cx="15" cy="15" r="1" fill="#8b5cf6" />
    </svg>
  );
}

export function WrenchIcon({ size = 24, className }: IconProps) {
  const id = "grad-wrench";
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" className={className}>
      <GradientDefs id={id} />
      <path
        d="M14.7 6.3a1 1 0 000 1.4l1.6 1.6a1 1 0 001.4 0l3.77-3.77a6 6 0 01-7.94 7.94l-6.91 6.91a2.12 2.12 0 01-3-3l6.91-6.91a6 6 0 017.94-7.94l-3.77 3.77z"
        stroke={`url(#${id})`}
        strokeWidth="1.8"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}

export function TerminalIcon({ size = 24, className }: IconProps) {
  const id = "grad-terminal";
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" className={className}>
      <GradientDefs id={id} />
      <rect x="2" y="4" width="20" height="16" rx="2" stroke={`url(#${id})`} strokeWidth="1.8" />
      <path
        d="M6 10l4 2-4 2"
        stroke={`url(#${id})`}
        strokeWidth="1.8"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
      <path d="M12 16h6" stroke={`url(#${id})`} strokeWidth="1.8" strokeLinecap="round" />
    </svg>
  );
}

/* ------------------------------------------------------------------ */
/*  Stats / data icons                                                 */
/* ------------------------------------------------------------------ */

export function TokenIcon({ size = 24, className }: IconProps) {
  const id = "grad-token";
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" className={className}>
      <GradientDefs id={id} />
      <rect x="3" y="3" width="18" height="18" rx="3" stroke={`url(#${id})`} strokeWidth="1.8" />
      <path d="M7 8h10M7 12h7M7 16h4" stroke={`url(#${id})`} strokeWidth="1.5" strokeLinecap="round" />
      <circle cx="17" cy="14" r="1" fill="#8b5cf6" />
    </svg>
  );
}

export function ClockIcon({ size = 24, className }: IconProps) {
  const id = "grad-clock";
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" className={className}>
      <GradientDefs id={id} />
      <circle cx="12" cy="12" r="9.5" stroke={`url(#${id})`} strokeWidth="1.8" />
      <path d="M12 7v5l3.5 2" stroke={`url(#${id})`} strokeWidth="1.8" strokeLinecap="round" />
      <circle cx="12" cy="12" r="1.5" fill="#c76a4a" />
    </svg>
  );
}

export function SpeedIcon({ size = 24, className }: IconProps) {
  const id = "grad-speed";
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" className={className}>
      <GradientDefs id={id} />
      <path d="M13 2L3 14h9l-1 8 10-12h-9l1-8z" stroke={`url(#${id})`} strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

export function GaugeIcon({ size = 24, className }: IconProps) {
  const id = "grad-gauge";
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" className={className}>
      <GradientDefs id={id} />
      <path
        d="M12 2a10 10 0 100 20 10 10 0 000-20z"
        stroke={`url(#${id})`}
        strokeWidth="1.8"
      />
      <path d="M12 12l4-6" stroke={`url(#${id})`} strokeWidth="2" strokeLinecap="round" />
      <circle cx="12" cy="12" r="2" fill="#c76a4a" />
      <path d="M4.5 16.5h2M17.5 16.5h2M6 8l1.5 1M16.5 9L18 8" stroke={`url(#${id})`} strokeWidth="1.2" strokeLinecap="round" />
    </svg>
  );
}

export function TrendIcon({ size = 24, className }: IconProps) {
  const id = "grad-trend";
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" className={className}>
      <GradientDefs id={id} />
      <path d="M3 20L9 14l4 4L21 6" stroke={`url(#${id})`} strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" />
      <path d="M16 6h5v5" stroke={`url(#${id})`} strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" />
      <circle cx="9" cy="14" r="1.5" fill="#e2a04f" />
      <circle cx="13" cy="18" r="1.2" fill="#c76a4a" />
    </svg>
  );
}

export function FileIcon({ size = 24, className }: IconProps) {
  const id = "grad-file";
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" className={className}>
      <GradientDefs id={id} />
      <path
        d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8l-6-6z"
        stroke={`url(#${id})`}
        strokeWidth="1.8"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
      <path d="M14 2v6h6" stroke={`url(#${id})`} strokeWidth="1.8" strokeLinecap="round" />
      <path d="M8 13h8M8 17h5" stroke={`url(#${id})`} strokeWidth="1.5" strokeLinecap="round" />
    </svg>
  );
}

export function SettingsIcon({ size = 24, className }: IconProps) {
  const id = "grad-settings";
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" className={className}>
      <GradientDefs id={id} />
      <circle cx="12" cy="12" r="3" stroke={`url(#${id})`} strokeWidth="1.8" />
      <path
        d="M19.4 15a1.65 1.65 0 00.33 1.82l.06.06a2 2 0 010 2.83 2 2 0 01-2.83 0l-.06-.06a1.65 1.65 0 00-1.82-.33 1.65 1.65 0 00-1 1.51V21a2 2 0 01-4 0v-.09A1.65 1.65 0 009 19.4a1.65 1.65 0 00-1.82.33l-.06.06a2 2 0 01-2.83 0 2 2 0 010-2.83l.06-.06A1.65 1.65 0 004.68 15a1.65 1.65 0 00-1.51-1H3a2 2 0 010-4h.09A1.65 1.65 0 004.6 9a1.65 1.65 0 00-.33-1.82l-.06-.06a2 2 0 010-2.83 2 2 0 012.83 0l.06.06A1.65 1.65 0 009 4.68a1.65 1.65 0 001-1.51V3a2 2 0 014 0v.09a1.65 1.65 0 001 1.51 1.65 1.65 0 001.82-.33l.06-.06a2 2 0 012.83 0 2 2 0 010 2.83l-.06.06A1.65 1.65 0 0019.4 9a1.65 1.65 0 001.51 1H21a2 2 0 010 4h-.09a1.65 1.65 0 00-1.51 1z"
        stroke={`url(#${id})`}
        strokeWidth="1.5"
        strokeLinecap="round"
      />
    </svg>
  );
}

/* ------------------------------------------------------------------ */
/*  Utility icons (keep simple, still with gradient)                   */
/* ------------------------------------------------------------------ */

export function CheckIcon({ size = 24, className }: IconProps) {
  const id = "grad-check";
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" className={className}>
      <GradientDefs id={id} />
      <path d="M5 12l5 5L20 7" stroke={`url(#${id})`} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

export function CrossIcon({ size = 24, className }: IconProps) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" className={className}>
      <path d="M6 6l12 12M18 6L6 18" stroke="#ef4444" strokeWidth="2" strokeLinecap="round" />
    </svg>
  );
}

export function ChevronDownIcon({ size = 24, className }: IconProps) {
  const id = "grad-chevron";
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" className={className}>
      <GradientDefs id={id} />
      <path d="M6 9l6 6 6-6" stroke={`url(#${id})`} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

export function ArrowRightIcon({ size = 24, className }: IconProps) {
  const id = "grad-arrow";
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" className={className}>
      <GradientDefs id={id} />
      <path d="M5 12h14M13 5l7 7-7 7" stroke={`url(#${id})`} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

export function SuccessCircleIcon({ size = 24, className }: IconProps) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" className={className}>
      <circle cx="12" cy="12" r="10" stroke="#22c55e" strokeWidth="1.8" />
      <path d="M8 12l3 3 5-5" stroke="#22c55e" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

export function FailCircleIcon({ size = 24, className }: IconProps) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" className={className}>
      <circle cx="12" cy="12" r="10" stroke="#ef4444" strokeWidth="1.8" />
      <path d="M9 9l6 6M15 9l-6 6" stroke="#ef4444" strokeWidth="2" strokeLinecap="round" />
    </svg>
  );
}
