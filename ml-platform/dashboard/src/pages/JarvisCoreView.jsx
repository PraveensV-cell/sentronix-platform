import { useState, useEffect } from "react";
import {
    getAIBrainStatus,
    updateAIBrainConfig,
    getAIDailyLog,
    getAIDailyLogMarkdown,
    getAIActions,
    logAIAction,
} from "../api/api";

export default function JarvisCoreView({ environment }) {
    const [aiStatus, setAiStatus] = useState(null);
    const [dailyLog, setDailyLog] = useState(null);
    const [actions, setActions] = useState([]);
    const [loading, setLoading] = useState(true);

    // AI Configuration form
    const [aiName, setAiName] = useState("JARVIS PRIME");
    const [speedMode, setSpeedMode] = useState("HIGH_PRECISION");
    const [autonomyLevel, setAutonomyLevel] = useState("FULL_AUTONOMOUS");
    const [voiceEnabled, setVoiceEnabled] = useState(true);
    const [saveFeedback, setSaveFeedback] = useState("");
    const [activeTab, setActiveTab] = useState("telemetry"); // "telemetry" | "work_log" | "neural_stream"

    const loadAll = async () => {
        try {
            const [statusRes, logRes, actRes] = await Promise.all([
                getAIBrainStatus(),
                getAIDailyLog(),
                getAIActions(30),
            ]);
            setAiStatus(statusRes);
            setDailyLog(logRes);
            setActions(actRes.actions || []);
            if (statusRes.name) setAiName(statusRes.name);
            if (statusRes.speed_mode) setSpeedMode(statusRes.speed_mode);
            if (statusRes.autonomy_level) setAutonomyLevel(statusRes.autonomy_level);
            if (statusRes.voice_announcements !== undefined) setVoiceEnabled(statusRes.voice_announcements);
        } catch (err) {
            console.error("Error loading JARVIS brain data", err);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        loadAll();
        const interval = setInterval(loadAll, 3000);
        return () => clearInterval(interval);
    }, []);

    const handleSaveConfig = async (e) => {
        e.preventDefault();
        try {
            const res = await updateAIBrainConfig({
                name: aiName,
                speed_mode: speedMode,
                autonomy_level: autonomyLevel,
                voice_announcements: voiceEnabled,
            });
            if (res.success) {
                setSaveFeedback("✓ AI Configuration updated successfully!");
                setTimeout(() => setSaveFeedback(""), 3000);
                if (voiceEnabled && "speechSynthesis" in window) {
                    const utterance = new SpeechSynthesisUtterance(
                        `${aiName} configuration updated to ${speedMode.replace("_", " ")} mode with ${autonomyLevel.replace("_", " ")} autonomy.`
                    );
                    utterance.rate = 1.05;
                    window.speechSynthesis.speak(utterance);
                }
                loadAll();
            }
        } catch (err) {
            alert("Could not update AI brain configuration");
        }
    };

    const handleVoiceAnnouncement = () => {
        if ("speechSynthesis" in window) {
            const stats = aiStatus?.stats || {};
            const text = `Greetings Commander. I am ${aiName}. Systems are fully operational. Uptime is ${aiStatus?.uptime || "continuous"}. We are actively supervising ${stats.cameras_active || 80} institution cameras, ${stats.attendances_today || 0} attendances logged today, and zero unaddressed security breaches.`;
            const utterance = new SpeechSynthesisUtterance(text);
            utterance.rate = 1.0;
            utterance.pitch = 1.0;
            window.speechSynthesis.speak(utterance);
        } else {
            alert("Speech synthesis not supported on this browser.");
        }
    };

    const handleDownloadDailyReport = async () => {
        try {
            const md = await getAIDailyLogMarkdown();
            const blob = new Blob([md], { type: "text/markdown;charset=utf-8" });
            const url = URL.createObjectURL(blob);
            const a = document.createElement("a");
            a.href = url;
            a.download = `AI_DAILY_LOG_${new Date().toISOString().slice(0, 10)}.md`;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            URL.revokeObjectURL(url);
        } catch (err) {
            alert("Could not download report");
        }
    };

    return (
        <div className="surveillance-view" style={{ maxWidth: "1400px", margin: "0 auto" }}>
            {/* Royal Top Banner */}
            <div
                style={{
                    background: "linear-gradient(135deg, #0f172a 0%, #1e293b 100%)",
                    borderRadius: "12px",
                    padding: "24px 28px",
                    color: "#ffffff",
                    display: "flex",
                    justifyContent: "space-between",
                    alignItems: "center",
                    boxShadow: "0 4px 20px rgba(0,0,0,0.12)",
                    border: "1px solid rgba(255,255,255,0.1)",
                }}
            >
                <div style={{ display: "flex", alignItems: "center", gap: "20px" }}>
                    {/* Pulsing Arc Reactor Graphic */}
                    <div
                        style={{
                            width: "68px",
                            height: "68px",
                            borderRadius: "50%",
                            border: "3px solid #38bdf8",
                            boxShadow: "0 0 25px rgba(56, 189, 248, 0.6), inset 0 0 15px rgba(56, 189, 248, 0.4)",
                            display: "flex",
                            alignItems: "center",
                            justifyContent: "center",
                            position: "relative",
                            background: "radial-gradient(circle, #0284c7 0%, #0369a1 40%, #0f172a 100%)",
                        }}
                    >
                        <div
                            style={{
                                width: "24px",
                                height: "24px",
                                borderRadius: "50%",
                                background: "#ffffff",
                                boxShadow: "0 0 15px #ffffff",
                            }}
                        />
                    </div>

                    <div>
                        <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
                            <h2 style={{ margin: 0, fontSize: "22px", fontWeight: 800, letterSpacing: "1px", color: "#f8fafc" }}>
                                {aiStatus?.name || "JARVIS PRIME"} — 24/7 AUTONOMOUS COMMAND BRAIN
                            </h2>
                            <span style={{ fontSize: "11px", background: "#10b981", color: "#ffffff", padding: "2px 10px", borderRadius: "12px", fontWeight: 700 }}>
                                24/7 ONLINE
                            </span>
                        </div>
                        <p style={{ margin: "4px 0 0 0", fontSize: "13px", color: "#94a3b8" }}>
                            Master Artificial Intelligence Operations Commander • Institutional Surveillance &amp; Safety Hub
                        </p>
                    </div>
                </div>

                <div style={{ display: "flex", gap: "10px" }}>
                    <button
                        onClick={handleVoiceAnnouncement}
                        className="tool-btn btn-primary"
                        style={{ background: "#0ea5e9", display: "flex", alignItems: "center", gap: "8px", padding: "10px 18px", fontSize: "12px", fontWeight: 700 }}
                    >
                        🔊 Voice Status Briefing
                    </button>
                    <button
                        onClick={handleDownloadDailyReport}
                        className="tool-btn btn-secondary-mini"
                        style={{ background: "#ffffff", color: "#0f172a", padding: "10px 18px", fontSize: "12px", fontWeight: 700 }}
                    >
                        📥 Export Daily Work File (.MD)
                    </button>
                </div>
            </div>

            {/* Sub-navigation tabs */}
            <div style={{ display: "flex", gap: "8px", margin: "16px 0 8px 0" }}>
                {[
                    { id: "telemetry", label: "⚡ Neural Telemetry & Control" },
                    { id: "work_log", label: "📋 Daily Operations Work Log File" },
                    { id: "neural_stream", label: "🧠 Autonomous Stream of Thoughts" },
                ].map((t) => (
                    <button
                        key={t.id}
                        onClick={() => setActiveTab(t.id)}
                        className={`fleet-pill ${activeTab === t.id ? "active" : ""}`}
                        style={{ fontSize: "12px", padding: "8px 18px", fontWeight: 600 }}
                    >
                        {t.label}
                    </button>
                ))}
            </div>

            {/* TAB 1: Neural Telemetry & Control */}
            {activeTab === "telemetry" && (
                <div style={{ display: "grid", gridTemplateColumns: "1.2fr 1fr", gap: "18px", marginTop: "10px" }}>
                    {/* Left: AI Core KPI Metrics */}
                    <div style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
                        <div className="fleet-stats-row">
                            <div className="fleet-stat-card">
                                <div className="fleet-stat-label">AI System Uptime</div>
                                <div className="fleet-stat-val" style={{ color: "#0ea5e9" }}>{aiStatus?.uptime || "24h 00m"}</div>
                                <div style={{ fontSize: "10px", color: "var(--text-muted)", marginTop: "4px" }}>24/7 Non-stop monitoring</div>
                            </div>
                            <div className="fleet-stat-card">
                                <div className="fleet-stat-label">Inference Latency</div>
                                <div className="fleet-stat-val" style={{ color: "#10b981" }}>{aiStatus?.latency_ms || 16.4} ms</div>
                                <div style={{ fontSize: "10px", color: "var(--text-muted)", marginTop: "4px" }}>Ultra-fast perception</div>
                            </div>
                            <div className="fleet-stat-card">
                                <div className="fleet-stat-label">Neural Cores Active</div>
                                <div className="fleet-stat-val">{aiStatus?.neural_threads || 8} Threads</div>
                                <div style={{ fontSize: "10px", color: "var(--text-muted)", marginTop: "4px" }}>Multi-core acceleration</div>
                            </div>
                        </div>

                        {/* Current Thought / Live Consciousness Card */}
                        <div className="cam-card" style={{ padding: "18px", borderLeft: "4px solid #0ea5e9" }}>
                            <div style={{ display: "flex", alignItems: "center", gap: "8px", marginBottom: "8px" }}>
                                <span className="alert-pulse-red" style={{ background: "#0ea5e9" }}></span>
                                <h4 style={{ margin: 0, fontSize: "13px", textTransform: "uppercase", letterSpacing: "0.5px" }}>
                                    Active Stream of Consciousness
                                </h4>
                            </div>
                            <p style={{ margin: 0, fontSize: "14px", fontStyle: "italic", color: "var(--text-primary)" }}>
                                "{aiStatus?.current_thought || "Actively monitoring 80 operational sectors. Face biometric engine and uniform compliance running continuously."}"
                            </p>
                        </div>

                        {/* Daily Metrics Breakdown */}
                        <div className="detections-card" style={{ padding: "18px" }}>
                            <h4 style={{ margin: "0 0 12px 0", fontSize: "14px", fontWeight: 700 }}>
                                📊 Today's Cumulative Accomplishments
                            </h4>
                            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "12px" }}>
                                <div style={{ padding: "12px", background: "var(--bg-secondary)", borderRadius: "8px" }}>
                                    <div style={{ fontSize: "11px", color: "var(--text-muted)", textTransform: "uppercase" }}>Face Attendances Marked</div>
                                    <div style={{ fontSize: "20px", fontWeight: 700, color: "var(--success-color)", marginTop: "4px" }}>
                                        {aiStatus?.stats?.attendances_today || 0} Check-ins
                                    </div>
                                </div>
                                <div style={{ padding: "12px", background: "var(--bg-secondary)", borderRadius: "8px" }}>
                                    <div style={{ fontSize: "11px", color: "var(--text-muted)", textTransform: "uppercase" }}>Active Security Incidents</div>
                                    <div style={{ fontSize: "20px", fontWeight: 700, color: "#f59e0b", marginTop: "4px" }}>
                                        {aiStatus?.stats?.active_alerts || 0} Alerts
                                    </div>
                                </div>
                                <div style={{ padding: "12px", background: "var(--bg-secondary)", borderRadius: "8px" }}>
                                    <div style={{ fontSize: "11px", color: "var(--text-muted)", textTransform: "uppercase" }}>Active Cameras in Fleet</div>
                                    <div style={{ fontSize: "20px", fontWeight: 700, color: "#0ea5e9", marginTop: "4px" }}>
                                        {aiStatus?.stats?.cameras_active || 80} Cams
                                    </div>
                                </div>
                                <div style={{ padding: "12px", background: "var(--bg-secondary)", borderRadius: "8px" }}>
                                    <div style={{ fontSize: "11px", color: "var(--text-muted)", textTransform: "uppercase" }}>Registered Biometric Dossiers</div>
                                    <div style={{ fontSize: "20px", fontWeight: 700, marginTop: "4px" }}>
                                        {aiStatus?.stats?.people_registered || 0} Enrolled
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>

                    {/* Right: Personalization & Control Card */}
                    <div className="cam-card" style={{ padding: "20px" }}>
                        <h4 style={{ margin: "0 0 6px 0", fontSize: "15px", fontWeight: 700 }}>
                            ⚙️ AI Persona &amp; Operational Customization
                        </h4>
                        <p style={{ margin: "0 0 16px 0", fontSize: "12px", color: "var(--text-secondary)" }}>
                            Configure the AI main brain's persona, speed profile, and decision autonomy.
                        </p>

                        {saveFeedback && (
                            <div style={{ padding: "8px 12px", background: "#f0fdf4", border: "1px solid #bbf7d0", color: "#166534", borderRadius: "6px", fontSize: "12px", marginBottom: "14px" }}>
                                {saveFeedback}
                            </div>
                        )}

                        <form onSubmit={handleSaveConfig} style={{ display: "flex", flexDirection: "column", gap: "14px" }}>
                            <div>
                                <label className="fleet-stat-label">AI Brain Designated Name</label>
                                <input
                                    className="form-control"
                                    value={aiName}
                                    onChange={(e) => setAiName(e.target.value)}
                                    placeholder="e.g. JARVIS PRIME, ATHENA, SENTRONIX"
                                    style={{ width: "100%", padding: "10px 12px", fontSize: "13px", borderRadius: "6px", border: "1px solid var(--border-color)" }}
                                />
                            </div>

                            <div>
                                <label className="fleet-stat-label">Inference Speed Mode</label>
                                <select
                                    className="sector-select-box"
                                    value={speedMode}
                                    onChange={(e) => setSpeedMode(e.target.value)}
                                    style={{ width: "100%", padding: "10px 12px", fontSize: "13px" }}
                                >
                                    <option value="TURBO">⚡ TURBO (High-speed 60fps tracking)</option>
                                    <option value="BALANCED">⚖️ BALANCED (30fps Optimal Energy)</option>
                                    <option value="HIGH_PRECISION">🎯 HIGH PRECISION (Deep 128-pt facial biometrics)</option>
                                </select>
                            </div>

                            <div>
                                <label className="fleet-stat-label">Autonomous Decision Level</label>
                                <select
                                    className="sector-select-box"
                                    value={autonomyLevel}
                                    onChange={(e) => setAutonomyLevel(e.target.value)}
                                    style={{ width: "100%", padding: "10px 12px", fontSize: "13px" }}
                                >
                                    <option value="FULL_AUTONOMOUS">🤖 FULL AUTONOMOUS (Automatic check-ins &amp; alert dispatch)</option>
                                    <option value="SUPERVISED">👁️ SUPERVISED (Operator confirmation required)</option>
                                    <option value="ADVISORY">📊 ADVISORY ONLY (Silent telemetry logging)</option>
                                </select>
                            </div>

                            <div style={{ display: "flex", alignItems: "center", gap: "10px", marginTop: "4px" }}>
                                <input
                                    type="checkbox"
                                    id="voiceToggle"
                                    checked={voiceEnabled}
                                    onChange={(e) => setVoiceEnabled(e.target.checked)}
                                    style={{ width: "16px", height: "16px", cursor: "pointer" }}
                                />
                                <label htmlFor="voiceToggle" style={{ fontSize: "13px", cursor: "pointer", fontWeight: 600 }}>
                                    Enable Audio Voice Announcements (JARVIS Speech)
                                </label>
                            </div>

                            <button
                                type="submit"
                                className="tool-btn btn-primary"
                                style={{ marginTop: "10px", padding: "10px 20px", fontSize: "13px", fontWeight: 700 }}
                            >
                                Save AI Brain Persona
                            </button>
                        </form>
                    </div>
                </div>
            )}

            {/* TAB 2: Daily Work Log File Viewer */}
            {activeTab === "work_log" && (
                <div className="detections-card" style={{ padding: "24px", marginTop: "10px" }}>
                    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "16px", borderBottom: "1px solid var(--border-color)", paddingBottom: "12px" }}>
                        <div>
                            <h3 style={{ margin: 0, fontSize: "16px", fontWeight: 700 }}>
                                📁 AI Daily Surveillance Work File: <code>ai_work_log_{new Date().toISOString().slice(0, 10)}.json</code>
                            </h3>
                            <p style={{ margin: "4px 0 0 0", fontSize: "12px", color: "var(--text-secondary)" }}>
                                Automatically compiled, formatted, and persisted on disk by {aiStatus?.name || "JARVIS"}.
                            </p>
                        </div>
                        <button
                            onClick={handleDownloadDailyReport}
                            className="tool-btn btn-primary"
                            style={{ padding: "8px 16px", fontSize: "12px", fontWeight: 600 }}
                        >
                            📥 Download Markdown Report
                        </button>
                    </div>

                    <pre
                        style={{
                            background: "var(--bg-secondary)",
                            padding: "16px",
                            borderRadius: "8px",
                            border: "1px solid var(--border-color)",
                            fontSize: "12px",
                            fontFamily: "monospace",
                            maxHeight: "550px",
                            overflowY: "auto",
                            whiteSpace: "pre-wrap",
                        }}
                    >
                        {JSON.stringify(dailyLog, null, 2)}
                    </pre>
                </div>
            )}

            {/* TAB 3: Autonomous Stream of Thoughts */}
            {activeTab === "neural_stream" && (
                <div className="detections-card" style={{ padding: "24px", marginTop: "10px" }}>
                    <h3 style={{ margin: "0 0 6px 0", fontSize: "16px", fontWeight: 700 }}>
                        ⚡ Chronological Autonomous Decisions Stream
                    </h3>
                    <p style={{ margin: "0 0 16px 0", fontSize: "12px", color: "var(--text-secondary)" }}>
                        Real-time feed of perceptions, biometrics, uniform evaluations, and triage events executed by the AI.
                    </p>

                    <div style={{ display: "flex", flexDirection: "column", gap: "10px" }}>
                        {actions.map((act) => (
                            <div
                                key={act.id}
                                style={{
                                    padding: "12px 16px",
                                    borderRadius: "8px",
                                    background: "var(--bg-secondary)",
                                    borderLeft: `4px solid ${act.severity === "CRITICAL" ? "#ef4444" : "#0ea5e9"}`,
                                    display: "flex",
                                    justifyContent: "space-between",
                                    alignItems: "center",
                                }}
                            >
                                <div>
                                    <div style={{ fontSize: "10px", color: "var(--text-muted)", textTransform: "uppercase", fontWeight: 700 }}>
                                        [{act.module}] • {act.timestamp}
                                    </div>
                                    <div style={{ fontSize: "13px", marginTop: "2px", color: "var(--text-primary)" }}>
                                        {act.action}
                                    </div>
                                </div>
                                <span className={`cam-func-badge ${act.severity === "CRITICAL" ? "badge-danger" : "badge-primary"}`}>
                                    {act.severity || "INFO"}
                                </span>
                            </div>
                        ))}
                    </div>
                </div>
            )}
        </div>
    );
}
