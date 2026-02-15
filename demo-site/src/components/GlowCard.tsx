import { type ReactNode } from "react";
import { motion } from "framer-motion";

interface GlowCardProps {
  children: ReactNode;
  className?: string;
  delay?: number;
}

export default function GlowCard({
  children,
  className = "",
  delay = 0,
}: GlowCardProps) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 24 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true, margin: "-40px" }}
      transition={{ duration: 0.6, delay, ease: [0.22, 1, 0.36, 1] }}
      className={`group relative rounded-2xl border border-white/[0.06] bg-surface p-6 transition-all duration-500 hover:border-white/[0.1] hover:bg-surface-light ${className}`}
    >
      {/* Hover glow — warm gradient */}
      <div className="pointer-events-none absolute -inset-px rounded-2xl opacity-0 transition-opacity duration-500 group-hover:opacity-100">
        <div className="absolute inset-0 rounded-2xl bg-gradient-to-br from-primary/[0.08] via-transparent to-accent/[0.06]" />
      </div>

      <div className="relative z-10">{children}</div>
    </motion.div>
  );
}
