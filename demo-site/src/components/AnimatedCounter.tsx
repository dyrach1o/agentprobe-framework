import { useEffect, useRef } from "react";
import {
  useInView,
  useMotionValue,
  useSpring,
  motion,
} from "framer-motion";

interface AnimatedCounterProps {
  target: number;
  suffix?: string;
  label: string;
  duration?: number;
}

export default function AnimatedCounter({
  target,
  suffix = "",
  label,
  duration = 2,
}: AnimatedCounterProps) {
  const ref = useRef<HTMLDivElement>(null);
  const isInView = useInView(ref, { once: true, margin: "-80px" });

  const motionValue = useMotionValue(0);
  const springValue = useSpring(motionValue, {
    damping: 50,
    stiffness: 80,
    duration: duration * 1000,
  });

  const displayRef = useRef<HTMLSpanElement>(null);

  useEffect(() => {
    if (isInView) {
      motionValue.set(target);
    }
  }, [isInView, motionValue, target]);

  useEffect(() => {
    const unsubscribe = springValue.on("change", (latest) => {
      if (displayRef.current) {
        displayRef.current.textContent =
          Math.round(latest).toLocaleString() + suffix;
      }
    });
    return unsubscribe;
  }, [springValue, suffix]);

  return (
    <motion.div
      ref={ref}
      initial={{ opacity: 0, y: 16 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true }}
      transition={{ duration: 0.6, ease: [0.22, 1, 0.36, 1] }}
      className="flex flex-col items-center gap-3"
    >
      <span
        ref={displayRef}
        className="font-display text-5xl text-white md:text-6xl"
      >
        0{suffix}
      </span>
      <span className="text-[13px] text-neutral-500 uppercase tracking-[0.15em] font-medium">
        {label}
      </span>
    </motion.div>
  );
}
