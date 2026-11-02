import { useState, useEffect } from "react";
import { getEnvironments, createEnvironment, updateEnvironment } from "../api/api";
import OnboardingFlowModal from "../components/OnboardingFlowModal";

const FOUR_MODES = [
    {
        type: "School",
        title: "Campus & School Mode",
        tagline: "Academic Surveillance • Uniform Standards • Biometric Attendance",
        icon: "🎓",
        themeClass: "mode-campus",
        bgImg: "https://images.unsplash.com/photo-1541339907198-e08756dedf3f?w=1920&q=80",
        functions: [
            { name: "Face Biometric Attendance", icon: "⏱️", desc: "Automated facial recognition, exact timestamping, and present/late deduplication." },
            { name: "Dress Code & School Uniform", icon: "👔", desc: "Enforces formal dress & regular school uniform; flags casual clothes & checks ID badge." },
            { name: "Exam Hall Proctoring", icon: "📝", desc: "Detects prohibited cell phones, cheat sheets/notes, unauthorized devices & malpractice." },
            { name: "Anti-Ragging & Campus Safety", icon: "🛡️", desc: "Monitors aggressive clustering, hallway scuffles, and unauthorized perimeter presence." },
        ],
    },
    {
        type: "Military",
        title: "Military & Defence Mode",
        tagline: "Strategic Perimeter Watch • Tactical Defense • Sentry Enforcement",
        icon: "🎖️",
        themeClass: "mode-military",
        bgImg: "https://images.unsplash.com/photo-1508873696983-2df570464756?w=1920&q=80",
        functions: [
            { name: "Sentry Perimeter & Intrusion", icon: "🚨", desc: "Tripwire border breaches, optical tripwires, and unauthorized intruder detection." },
            { name: "Tactical Threat & Weapon Intercept", icon: "⚔️", desc: "Real-time recognition of firearms, blades, and suspicious payloads." },
            { name: "Authorized Personnel Biometrics", icon: "🪪", desc: "Security clearance verification and biometric facial credential auditing." },
            { name: "Guard Alertness Watch", icon: "👁️", desc: "Detects sleeping on watch, abandoned sentry stations, and perimeter lapses." },
        ],
    },
    {
        type: "Hospital",
        title: "Public Places & Government Mode",
        tagline: "Civic Surveillance • Crowd Density • Transit Thoroughfares",
        icon: "🏛️",
        themeClass: "mode-public",
        bgImg: "https://images.unsplash.com/photo-1519501025264-65ba15a82390?w=1920&q=80",
        functions: [
            { name: "Crowd Density & Stampede Warning", icon: "👥", desc: "Monitors concourse density, detects bottleneck panics and stampede risks." },
            { name: "Abandoned Object & Bag Detection", icon: "🧳", desc: "Detects stationary unattended bags and luggage in civic corridors." },
            { name: "Public Violence & Altercation Triage", icon: "⚠️", desc: "Recognizes physical fighting, sudden falls, and distress gestures." },
            { name: "Restricted Vault & Pharmacy Access", icon: "🔒", desc: "Biometric access gates to restricted vaults, archives, and high-security rooms." },
        ],
    },
    {
        type: "Industry",
        title: "Office & Industries Mode",
        tagline: "OSHA Safety Compliance • Hazard Mitigation • Machinery Zones",
        icon: "🏭",
        themeClass: "mode-industry",
        bgImg: "https://images.unsplash.com/photo-1581091226825-a6a2a5aee158?w=1920&q=80",
        functions: [
            { name: "OSHA & PPE Safety Gear Compliance", icon: "🦺", desc: "Verifies mandatory hardhats/helmets, high-vis vests, goggles, and gloves before accidents." },
            { name: "Fire, Smoke & Chemical Hazard Warning", icon: "🔥", desc: "Optical smoke and flame detection with instant safety klaxon dispatch." },
            { name: "Restricted Machinery Safety Tripwire", icon: "⚙️", desc: "Tripwires around robotic cells, conveyor pinch points, and boiler units." },
            { name: "Worker Shift Clock-in Biometrics", icon: "⏱️", desc: "Touchless biometric shift tracking and overtime timestamping." },
        ],
    },
];

export default function EnvironmentSelectPage({ user, onEnvironmentSelected }) {
    const [environments, setEnvironments] = useState([]);
    const [selectedEnv, setSelectedEnv] = useState(null);
    const [hoveredMode, setHoveredMode] = useState(null);
    const [showOnboardingModal, setShowOnboardingModal] = useState(false);
    const [editingEnv, setEditingEnv] = useState(null);
    const [editName, setEditName] = useState("");
    const [feedback, setFeedback] = useState("");

    const loadEnvironments = async () => {
        try {
            const res = await getEnvironments();
            const list = res.environments || [];
            setEnvironments(list);
            if (list.length > 0 && !selectedEnv) {
                setSelectedEnv(list[0]);
            }
        } catch (err) {
            console.error("Failed to load environments", err);
        }
    };

    useEffect(() => {
        loadEnvironments();
    }, []);

    const handleSelectEnv = (env) => {
        setSelectedEnv(env);
    };

    const handleOpenEdit = (e, env) => {
        e.stopPropagation();
        setEditingEnv(env);
        setEditName(env.name || "");
    };

    const handleSaveEnvRename = async (e) => {
        e.preventDefault();
        if (!editingEnv) return;
        try {
            const res = await updateEnvironment(editingEnv.id, {
                name: editName,
                type: editingEnv.type,
            });
            if (res.success) {
                setEditingEnv(null);
                setFeedback(`✓ Mode renamed to "${editName}" successfully!`);
                setTimeout(() => setFeedback(""), 4000);
                await loadEnvironments();
            }
        } catch (err) {
            alert("Could not update mode name");
        }
    };

    const handleDirectEnter = (customEnv) => {
        const env = customEnv || selectedEnv;
        if (!env) return;
        localStorage.setItem("sentronix_env", JSON.stringify(env));
        onEnvironmentSelected(env);
    };

    const activeModeMeta = FOUR_MODES.find((m) => m.type === selectedEnv?.type) || FOUR_MODES[0];
    const previewModeMeta = hoveredMode ? (FOUR_MODES.find((m) => m.type === hoveredMode.type) || activeModeMeta) : activeModeMeta;

    return (
        <div
            style={{
                minHeight: "100vh",
                padding: "36px 20px",
                backgroundImage: `linear-gradient(180deg, rgba(10, 15, 24, 0.90) 0%, rgba(10, 15, 24, 0.98) 100%), url(${previewModeMeta.bgImg})`,
                backgroundSize: "cover",
                backgroundPosition: "center",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
            }}
        >
            <div
                style={{
                    width: "100%",
                    maxWidth: "1080px",
                    background: "#0d1420",
                    border: "1px solid rgba(212, 175, 55, 0.35)",
                    borderRadius: "12px",
                    padding: "32px",
                    boxShadow: "0 16px 48px rgba(0,0,0,0.7)",
                }}
            >
                {/* Header */}
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "24px", borderBottom: "1px solid rgba(255, 255, 255, 0.08)", paddingBottom: "18px" }}>
                    <div>
                        <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
                            <span style={{ fontSize: "24px" }}>🛡️</span>
                            <h2 style={{ margin: 0, fontSize: "22px", fontWeight: 700, color: "#ffffff", letterSpacing: "0.5px" }}>
                                SENTRONIX SURVEILLANCE MODES
                            </h2>
                        </div>
                        <p style={{ margin: "4px 0 0 0", fontSize: "12px", color: "#94a3b8" }}>
                            Select your operational domain. Place your cursor on any mode to inspect its core detection functions. Managed by <strong style={{ color: "#d4af37" }}>VANTEP AI</strong>.
                        </p>
                    </div>

                    <div style={{ fontSize: "12px", color: "#cbd5e1" }}>
                        Operator: <strong style={{ color: "#d4af37" }}>{user?.full_name || user?.username || "Commander"}</strong>
                    </div>
                </div>

                {feedback && (
                    <div style={{ background: "rgba(16, 185, 129, 0.15)", border: "1px solid #10b981", color: "#10b981", padding: "10px 14px", borderRadius: "6px", marginBottom: "18px", fontSize: "12px", fontWeight: 600 }}>
                        {feedback}
                    </div>
                )}

                {/* 4 Main Modes Grid */}
                <div style={{ marginBottom: "26px" }}>
                    <div style={{ fontSize: "11px", fontWeight: 700, color: "#94a3b8", textTransform: "uppercase", letterSpacing: "0.6px", marginBottom: "12px" }}>
                        Select Operational Mode (Hover to Inspect Core Capabilities)
                    </div>

                    <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(240px, 1fr))", gap: "14px" }}>
                        {FOUR_MODES.map((mode) => {
                            const matchedEnv = environments.find((e) => e.type === mode.type) || { id: 1, name: mode.title, type: mode.type };
                            const isSelected = selectedEnv?.type === mode.type;
                            const isHovered = hoveredMode?.type === mode.type;

                            return (
                                <div
                                    key={mode.type}
                                    onClick={() => handleSelectEnv(matchedEnv)}
                                    onMouseEnter={() => setHoveredMode(matchedEnv)}
                                    onMouseLeave={() => setHoveredMode(null)}
                                    style={{
                                        padding: "18px",
                                        borderRadius: "10px",
                                        border: isSelected ? "2px solid #d4af37" : (isHovered ? "1px solid #cbd5e1" : "1px solid rgba(255, 255, 255, 0.10)"),
                                        background: isSelected ? "rgba(212, 175, 55, 0.14)" : (isHovered ? "rgba(255, 255, 255, 0.05)" : "rgba(255, 255, 255, 0.02)"),
                                        cursor: "pointer",
                                        transition: "all 0.15s ease",
                                        display: "flex",
                                        flexDirection: "column",
                                        justifyContent: "space-between",
                                        minHeight: "140px",
                                        boxShadow: isSelected ? "2px 2px 0px rgba(212, 175, 55, 0.3)" : "none",
                                    }}
                                >
                                    <div>
                                        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
                                            <span style={{ fontSize: "28px" }}>{mode.icon}</span>
                                            <button
                                                type="button"
                                                onClick={(e) => handleOpenEdit(e, matchedEnv)}
                                                style={{ background: "transparent", border: "none", fontSize: "11px", cursor: "pointer", color: "#94a3b8" }}
                                                title="Rename mode"
                                            >
                                                ✏️ Rename
                                            </button>
                                        </div>

                                        <div style={{ fontSize: "15px", fontWeight: 700, marginTop: "10px", color: isSelected ? "#d4af37" : "#ffffff" }}>
                                            {matchedEnv.name || mode.title}
                                        </div>
                                        <div style={{ fontSize: "11px", color: "#94a3b8", marginTop: "4px" }}>
                                            {mode.tagline}
                                        </div>
                                    </div>

                                    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginTop: "12px", borderTop: "1px solid rgba(255,255,255,0.06)", paddingTop: "8px" }}>
                                        <span style={{ fontSize: "10px", color: isSelected ? "#d4af37" : "#64748b", fontWeight: 700, textTransform: "uppercase" }}>
                                            {mode.type} MODE
                                        </span>
                                        {isSelected && (
                                            <span style={{ fontSize: "10px", color: "#d4af37", fontWeight: 800 }}>
                                                ● ACTIVE SELECTION
                                            </span>
                                        )}
                                    </div>
                                </div>
                            );
                        })}
                    </div>
                </div>

                {/* Interactive Mode Capabilities Showcase on Cursor Hover / Selection */}
                <div style={{ padding: "20px 24px", borderRadius: "10px", background: "rgba(0, 0, 0, 0.45)", border: "1px solid rgba(255, 255, 255, 0.10)", marginBottom: "26px" }}>
                    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "16px" }}>
                        <div>
                            <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                                <span style={{ fontSize: "20px" }}>{previewModeMeta.icon}</span>
                                <h3 style={{ margin: 0, fontSize: "16px", fontWeight: 700, color: "#ffffff" }}>
                                    {previewModeMeta.title} — Core Detection Capabilities
                                </h3>
                            </div>
                            <p style={{ margin: "2px 0 0 0", fontSize: "12px", color: "#94a3b8" }}>
                                {previewModeMeta.tagline}
                            </p>
                        </div>
                        <span style={{ fontSize: "11px", color: "#d4af37", fontWeight: 700, background: "rgba(212, 175, 55, 0.12)", padding: "4px 10px", borderRadius: "4px" }}>
                            VANTEP AI AUTO-TRIAGE
                        </span>
                    </div>

                    <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))", gap: "12px" }}>
                        {previewModeMeta.functions.map((fn, idx) => (
                            <div key={idx} style={{ padding: "12px 14px", borderRadius: "8px", background: "rgba(255, 255, 255, 0.03)", border: "1px solid rgba(255, 255, 255, 0.06)" }}>
                                <div style={{ display: "flex", alignItems: "center", gap: "6px", marginBottom: "4px" }}>
                                    <span>{fn.icon}</span>
                                    <span style={{ fontSize: "12px", fontWeight: 700, color: "#f8fafc" }}>{fn.name}</span>
                                </div>
                                <div style={{ fontSize: "11px", color: "#94a3b8", lineHeight: "1.4" }}>{fn.desc}</div>
                            </div>
                        ))}
                    </div>
                </div>

                {/* Action Launch Bar */}
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", borderTop: "1px solid rgba(255,255,255,0.08)", paddingTop: "20px" }}>
                    <div style={{ fontSize: "12px", color: "#94a3b8" }}>
                        Selected: <strong style={{ color: "#d4af37" }}>{selectedEnv?.name || "Campus Mode"}</strong>
                    </div>

                    <div style={{ display: "flex", gap: "12px" }}>
                        <button
                            type="button"
                            onClick={() => setShowOnboardingModal(true)}
                            style={{
                                background: "rgba(212, 175, 55, 0.15)",
                                border: "1px solid #d4af37",
                                color: "#d4af37",
                                padding: "10px 18px",
                                borderRadius: "6px",
                                fontSize: "13px",
                                fontWeight: 700,
                                cursor: "pointer",
                            }}
                        >
                            ⚙️ Setup Dataset &amp; Camera Wizard
                        </button>

                        <button
                            type="button"
                            onClick={() => handleDirectEnter()}
                            style={{
                                background: "#d4af37",
                                color: "#000000",
                                border: "none",
                                padding: "10px 24px",
                                borderRadius: "6px",
                                fontSize: "13px",
                                fontWeight: 800,
                                cursor: "pointer",
                                boxShadow: "0 4px 16px rgba(212, 175, 55, 0.35)",
                            }}
                        >
                            🚀 Launch Operational Dashboard →
                        </button>
                    </div>
                </div>
            </div>

            {/* Rename Modal */}
            {editingEnv && (
                <div style={{ position: "fixed", inset: 0, background: "rgba(0,0,0,0.7)", zIndex: 10001, display: "flex", alignItems: "center", justifyContent: "center", padding: "16px" }}>
                    <div style={{ background: "#0e131b", border: "1px solid #d4af37", borderRadius: "8px", padding: "20px", width: "100%", maxWidth: "400px" }}>
                        <h3 style={{ margin: "0 0 12px 0", fontSize: "15px", color: "#ffffff" }}>Rename Operational Mode</h3>
                        <form onSubmit={handleSaveEnvRename}>
                            <input
                                type="text"
                                value={editName}
                                onChange={(e) => setEditName(e.target.value)}
                                required
                                style={{ width: "100%", padding: "8px 10px", borderRadius: "4px", border: "1px solid rgba(255,255,255,0.2)", background: "#151c27", color: "#ffffff", fontSize: "13px", marginBottom: "14px" }}
                            />
                            <div style={{ display: "flex", justifyContent: "flex-end", gap: "8px" }}>
                                <button type="button" onClick={() => setEditingEnv(null)} style={{ background: "transparent", border: "1px solid rgba(255,255,255,0.2)", padding: "6px 12px", borderRadius: "4px", fontSize: "11px", color: "#cbd5e1" }}>Cancel</button>
                                <button type="submit" style={{ background: "#d4af37", color: "#000000", padding: "6px 14px", borderRadius: "4px", fontSize: "11px", fontWeight: 700 }}>Save</button>
                            </div>
                        </form>
                    </div>
                </div>
            )}

            {/* Setup Wizard */}
            {showOnboardingModal && (
                <OnboardingFlowModal
                    environment={selectedEnv}
                    isOpen={showOnboardingModal}
                    onClose={() => setShowOnboardingModal(false)}
                    onLaunchLive={() => handleDirectEnter()}
                />
            )}
        </div>
    );
}
