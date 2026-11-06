import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { useOAData } from "./hooks/useOAData";
import { SystemHealth } from "./components/SystemHealth";
import { MechanismView } from "./components/MechanismView";
import { useI18n } from "./i18n";
type Tab = "system-health" | "mechanism";

export default function App() {
  const [activeTab, setActiveTab] = useState<Tab>("system-health");
  const { goals, health, traces, cronRuns, teamHealth, goalMetrics, isLoading, error } = useOAData(30_000);
  const { lang, setLang, t } = useI18n();

  return (
    <div className="min-h-screen">
      <div className="max-w-7xl mx-auto px-4 py-6">
        {/* Header */}
        <div className="flex items-center justify-between mb-6">
          <div>
            <h1 className="text-xl font-bold text-gray-900 tracking-tight">
              {t("app.title")}
            </h1>
            <p className="text-xs text-gray-400 mt-0.5">
              {t("app.subtitle")}
            </p>
          </div>

          <div className="flex items-center gap-5">
            <div className="inline-flex rounded-full border border-gray-200 bg-white/70 p-1">
              {(["zh", "en"] as const).map((nextLang) => (
                <button
                  key={nextLang}
                  onClick={() => setLang(nextLang)}
                  className={`px-3 py-1 text-xs rounded-full transition-colors ${
                    lang === nextLang
                      ? "bg-gray-900 text-white"
                      : "text-gray-500 hover:text-gray-800"
                  }`}
                >
                  {t(`app.lang.${nextLang}`)}
                </button>
              ))}
            </div>

            <nav className="flex gap-6">
              {([
                ["system-health", t("app.tabs.systemHealth")],
                ["mechanism", t("app.tabs.mechanism")],
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
                  {t("app.loading")}
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
                <p className="text-sm text-gray-600">{t("app.connectionError")}</p>
                <p className="text-xs text-gray-400 font-mono">{error}</p>
                <p className="text-[10px] text-gray-400">
                  {t("app.ensureServer")} <code>oa serve</code>
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
            {t("app.footer")}
          </span>
        </motion.div>
      </div>
    </div>
  );
}
