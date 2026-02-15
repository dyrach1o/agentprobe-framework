import { BrowserRouter, Routes, Route, useLocation } from "react-router-dom";
import { AnimatePresence, motion } from "framer-motion";
import Navbar from "./components/Navbar";
import Landing from "./pages/Landing";
import TraceViewer from "./pages/TraceViewer";
import Evaluator from "./pages/Evaluator";
import CostDashboard from "./pages/CostDashboard";

function AnimatedRoutes() {
  const location = useLocation();

  return (
    <AnimatePresence mode="wait">
      <motion.div
        key={location.pathname}
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        transition={{ duration: 0.4, ease: [0.22, 1, 0.36, 1] }}
      >
        <Routes location={location}>
          <Route path="/" element={<Landing />} />
          <Route path="/trace-viewer" element={<TraceViewer />} />
          <Route path="/evaluator" element={<Evaluator />} />
          <Route path="/cost" element={<CostDashboard />} />
        </Routes>
      </motion.div>
    </AnimatePresence>
  );
}

export default function App() {
  return (
    <BrowserRouter basename="/agentprobe-framework/demo/">
      <div className="grain min-h-screen">
        <Navbar />
        <main className="pt-20">
          <AnimatedRoutes />
        </main>
      </div>
    </BrowserRouter>
  );
}
