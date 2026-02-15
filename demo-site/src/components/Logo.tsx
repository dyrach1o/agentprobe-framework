/**
 * AgentProbe logo — magnifying glass with circuit trace nodes.
 * Inline SVG: no loading issues, scales to any size, gradient always renders.
 */

interface LogoProps {
  size?: number;
  className?: string;
}

export default function Logo({ size = 32, className }: LogoProps) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 64 64"
      fill="none"
      className={className}
    >
      <defs>
        <linearGradient id="logo-grad" x1="0%" y1="100%" x2="100%" y2="0%">
          <stop offset="0%" stopColor="#e2a04f" />
          <stop offset="45%" stopColor="#c76a4a" />
          <stop offset="100%" stopColor="#8b5cf6" />
        </linearGradient>
      </defs>

      {/* Magnifying glass — circle */}
      <circle
        cx="26"
        cy="24"
        r="12"
        stroke="url(#logo-grad)"
        strokeWidth="3.5"
        fill="none"
      />

      {/* Magnifying glass — handle */}
      <line
        x1="17"
        y1="33"
        x2="8"
        y2="52"
        stroke="#e2a04f"
        strokeWidth="3.5"
        strokeLinecap="round"
      />

      {/* Circuit trace — main horizontal from glass */}
      <path
        d="M38 24 L44 24 L48 18"
        stroke="#c76a4a"
        strokeWidth="2.5"
        strokeLinecap="round"
        strokeLinejoin="round"
        fill="none"
      />

      {/* Circuit trace — branch down */}
      <path
        d="M44 24 L48 30"
        stroke="#9b6ddb"
        strokeWidth="2.5"
        strokeLinecap="round"
        strokeLinejoin="round"
        fill="none"
      />

      {/* Circuit trace — lower branch */}
      <path
        d="M34 30 L40 36 L48 36"
        stroke="#8b5cf6"
        strokeWidth="2.5"
        strokeLinecap="round"
        strokeLinejoin="round"
        fill="none"
      />

      {/* Node squares */}
      <rect x="46" y="14" width="6" height="6" rx="1.5" stroke="#c76a4a" strokeWidth="2" fill="none" />
      <rect x="46" y="27" width="6" height="6" rx="1.5" stroke="#9b6ddb" strokeWidth="2" fill="none" />
      <rect x="48" y="33" width="6" height="6" rx="1.5" stroke="#8b5cf6" strokeWidth="2" fill="none" />

      {/* Inner dot in magnifying glass */}
      <circle cx="26" cy="24" r="4" fill="url(#logo-grad)" opacity="0.15" />
    </svg>
  );
}
