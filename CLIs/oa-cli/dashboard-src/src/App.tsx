import { lazy, Suspense, useState } from "react";
import { MotionConfig, motion, AnimatePresence } from "framer-motion";
import { useOAData } from "./hooks/useOAData";
import { isVisualTestMode } from "./lib/runtimeFlags";

type Tab = "system-health" | "mechanism";

const SystemHealth = lazy(async () => {
  const module = await import("./components/SystemHealth");
  return { default: module.SystemHealth };
});

const MechanismView = lazy(async () => {
  const module = await import("./components/MechanismView");
  return { default: module.MechanismView };
});

function TabPanelFallback() {
  return (
    <div className="glass-card p-6">
      <div className="animate-pulse space-y-4">
        <div className="h-4 w-40 rounded-full bg-gray-100" />
        <div className="grid grid-cols-1 gap-4 lg:grid-cols-[280px_1fr]">
          <div className="rounded-2xl bg-white/70 p-5">
            <div className="h-4 w-32 rounded-full bg-gray-100" />
            <div className="mt-5 h-10 w-24 rounded-2xl bg-gray-100" />
            <div className="mt-4 h-20 rounded-2xl bg-gray-50" />
          </div>
          <div className="rounded-2xl bg-white/70 p-6">
            <div className="h-[200px] rounded-2xl bg-gray-50" />
            <div className="mt-4 grid grid-cols-2 gap-3 xl:grid-cols-4">
              {Array.from({ length: 4 }).map((_, index) => (
                <div key={index} className="h-24 rounded-2xl bg-gray-50" />
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default function App() {
  const [activeTab, setActiveTab] = useState<Tab>("system-health");
  const visualTestMode = isVisualTestMode();
  const { goals, health, traces, cronRuns, teamHealth, goalMetrics, isLoading, error } = useOAData(30_000);

  return (
    <MotionConfig reducedMotion={visualTestMode ? "always" : "user"}>
      <div className="min-h-screen">
        <div className="max-w-7xl mx-auto px-4 py-6">
          {/* Header */}
          <div className="flex items-center justify-between mb-6">
            <div>
              <h1 className="text-xl font-bold text-gray-900 tracking-tight">
                OA Dashboard
              </h1>
              <p className="text-xs text-gray-400 mt-0.5">
                Is our machine getting better?
              </p>
            </div>

            <nav className="flex gap-6">
              {([
                ["system-health", "System Health"],
                ["mechanism", "Mechanism"],
              ] as [Tab, string][]).map(([tab, label]) => (
                <button
                  key={tab}
                  onClick={() => setActiveTab(tab)}
                  className={`pb-1 text-sm transition-all ${
                    activeTab === tab ? "tab-active" : "tab-inactive"
                  }`}
                >
                  {label}
                </button>
              ))}
            </nav>
          </div>

          {/* Content */}
          <AnimatePresence mode="wait">
            {isLoading ? (
              <motion.div
                key="loading"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                className="flex items-center justify-center py-32"
              >
                <div className="text-center space-y-4">
                  <motion.div
                    className="w-8 h-8 rounded-full border-2 border-gray-200 mx-auto"
                    animate={{ rotate: 360 }}
                    transition={{ duration: 1.5, repeat: Infinity, ease: "linear" }}
                    style={{ borderTopColor: "#60A5FA" }}
                  />
                  <p className="text-[10px] text-gray-400 uppercase tracking-[0.3em] font-mono">
                    Loading
                  </p>
                </div>
              </motion.div>
            ) : error && !goals.length ? (
              <motion.div
                key="error"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                className="flex items-center justify-center py-32"
              >
                <div className="glass-card p-8 max-w-md text-center space-y-3">
                  <p className="text-sm text-gray-600">Connection Error</p>
                  <p className="text-xs text-gray-400 font-mono">{error}</p>
                  <p className="text-[10px] text-gray-400">
                    Ensure the API server is running: <code>oa serve</code>
                  </p>
                </div>
              </motion.div>
            ) : (
              <motion.div
                key={activeTab}
                initial={{ opacity: 0, y: 8 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -8 }}
                transition={{ duration: 0.3 }}
              >
                <Suspense fallback={<TabPanelFallback />}>
                  {activeTab === "system-health" ? (
                    <SystemHealth
                      goals={goals}
                      health={health}
                      goalMetrics={goalMetrics}
                      cronRuns={cronRuns}
                      teamHealth={teamHealth}
                    />
                  ) : activeTab === "mechanism" ? (
                    <MechanismView
                      goals={goals}
                      traces={traces}
                      cronRuns={cronRuns}
                    />
                  ) : null}
                </Suspense>
              </motion.div>
            )}
          </AnimatePresence>

          {/* Footer */}
          <motion.div
            className="text-center py-4 mt-8"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.8 }}
          >
            <span className="text-[10px] text-gray-300 font-mono tracking-wider uppercase">
              OA — Operational Analytics
            </span>
          </motion.div>
        </div>
      </div>
    </MotionConfig>
  );
}
