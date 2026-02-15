import { Link, useLocation } from "react-router-dom";
import { motion } from "framer-motion";
import Logo from "./Logo";

const navLinks = [
  { to: "/", label: "Home" },
  { to: "/trace-viewer", label: "Traces" },
  { to: "/evaluator", label: "Evaluator" },
  { to: "/cost", label: "Cost" },
];

export default function Navbar() {
  const location = useLocation();

  return (
    <nav className="fixed top-0 left-0 right-0 z-50 bg-[#0a0a0a]/80 backdrop-blur-2xl">
      <div className="mx-auto flex h-16 max-w-6xl items-center justify-between px-6">
        {/* Logo */}
        <Link to="/" className="flex items-center gap-3 group">
          <Logo size={30} />
          <span className="text-[15px] font-semibold text-neutral-200 tracking-tight group-hover:text-white transition-colors duration-300">
            AgentProbe
          </span>
        </Link>

        {/* Navigation */}
        <div className="hidden md:flex items-center gap-1">
          {navLinks.map((link) => {
            const isActive = location.pathname === link.to;
            return (
              <Link
                key={link.to}
                to={link.to}
                className="relative px-4 py-2 text-[13px] font-medium transition-colors duration-300"
              >
                <span className={isActive ? "text-white" : "text-neutral-500 hover:text-neutral-300"}>
                  {link.label}
                </span>
                {isActive && (
                  <motion.div
                    layoutId="nav-indicator"
                    className="absolute bottom-0 left-2 right-2 h-px bg-gradient-to-r from-primary/0 via-primary to-primary/0"
                    transition={{ type: "spring", stiffness: 400, damping: 30 }}
                  />
                )}
              </Link>
            );
          })}
        </div>

        {/* GitHub */}
        <a
          href="https://github.com/dyrach1o/agentprobe-framework"
          target="_blank"
          rel="noopener noreferrer"
          className="flex items-center gap-2 rounded-full border border-white/[0.06] px-4 py-1.5 text-[13px] text-neutral-500 transition-all duration-300 hover:border-white/[0.12] hover:text-neutral-300"
        >
          <svg viewBox="0 0 16 16" fill="currentColor" className="h-4 w-4">
            <path d="M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17.55-.38 0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53.63-.01 1.08.58 1.23.82.72 1.21 1.87.87 2.33.66.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 0-.87.31-1.59.82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82.64-.18 1.32-.27 2-.27.68 0 1.36.09 2 .27 1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82 1.27.82 2.15 0 3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48 0 1.07-.01 1.93-.01 2.2 0 .21.15.46.55.38A8.013 8.013 0 0016 8c0-4.42-3.58-8-8-8z" />
          </svg>
          <span className="hidden sm:inline">GitHub</span>
        </a>
      </div>

      {/* Mobile nav */}
      <div className="flex md:hidden items-center gap-1 overflow-x-auto px-6 pb-3 scrollbar-none">
        {navLinks.map((link) => {
          const isActive = location.pathname === link.to;
          return (
            <Link
              key={link.to}
              to={link.to}
              className={`whitespace-nowrap rounded-full px-3 py-1 text-xs font-medium transition-all duration-300 ${
                isActive
                  ? "bg-white/[0.06] text-white"
                  : "text-neutral-500 hover:text-neutral-300"
              }`}
            >
              {link.label}
            </Link>
          );
        })}
      </div>

      {/* Bottom border */}
      <div className="divider-gradient" />
    </nav>
  );
}
