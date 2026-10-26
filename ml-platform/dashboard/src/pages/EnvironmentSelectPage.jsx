import { useState, useEffect } from "react";
import { getEnvironments, createEnvironment, updateEnvironment, updateEnvironmentFeatures } from "../api/api";
import OnboardingFlowModal from "../components/OnboardingFlowModal";

const MODE_CAPABILITIES = {
    School: {
        title: "🏛️ Academic Campus & School Safety",
        tagline: "Educational Campus Surveillance • Uniform Standards • Biometric Attendance",
        themeClass: "mode-campus",
        bgImg: "https://images.unsplash.com/photo-1541339907198-e08756dedf3f?w=1920&q=80",
        functions: [
            { id: "attendance", name: "Face Biometric Attendance", icon: "🎓", desc: "Automated scan, timestamping, deduplication, and mark PRESENT/LATE in real-time." },
            { id: "dress_code", name: "Dress Code & School Uniform", icon: "👔", desc: "Permits formals and regular uniform; flags casual clothes & non-compliant attire." },
            { id: "exam_monitor", name: "Exam Hall Proctoring", icon: "📝", desc: "Detects prohibited cell phones, cheat notes, laptops, and suspicious postures." },
            { id: "safety", name: "Anti-Ragging & Campus Safety", icon: "🛡️", desc: "Crowd gathering, corridor aggression, and unauthorized perimeter presence." },
            { id: "dossier", name: "Individual Student/Staff Dossiers", icon: "📁", desc: "Dedicated physical dossier file updated in real-time by AI for every individual." },
        ],
    },
    Military: {
        title: "🛡️ Military & Strategic Defense Command",
        tagline: "High-Security Perimeter Watch • Tactical Defense • Sentry Enforcement",
        themeClass: "mode-military",
        bgImg: "https://images.unsplash.com/photo-1508873696983-2df570464756?w=1920&q=80",
        functions: [
            { id: "perimeter", name: "Sentry Perimeter & Intrusion Defense", icon: "🚨", desc: "Tripwire border breach, infrared motion, and unauthorized intruder interception." },
            { id: "weapon", name: "Weapon & Tactical Threat Intercept", icon: "⚔️", desc: "Real-time recognition of firearms, edged weapons, and suspicious payloads." },
            { id: "clearance", name: "Authorized Personnel Biometrics", icon: "🎖️", desc: "Security clearance verification (Tier 1–4) with facial biometrics." },
            { id: "alertness", name: "Guard Alertness & Watch Monitoring", icon: "👁️", desc: "Detects sleeping on watch, abandoned sentry posts, and perimeter lapses." },
            { id: "dossier", name: "Personnel Security Dossier", icon: "📁", desc: "Mission clearance, access history, and violation dossiers maintained 24/7." },
        ],
    },
    Industry: {
        title: "🏭 Heavy Industry, Chemical & Plant Safety",
        tagline: "OSHA Safety Compliance • Hazard Mitigation • Restricted Machinery Zones",
        themeClass: "mode-industry",
        bgImg: "https://images.unsplash.com/photo-1581091226825-a6a2a5aee158?w=1920&q=80",
        functions: [
            { id: "ppe", name: "OSHA & PPE Safety Gear Compliance", icon: "🦺", desc: "Verifies mandatory hardhats, high-visibility vests, safety goggles, and masks." },
            { id: "hazard", name: "Fire, Smoke & Chemical Hazard Warning", icon: "🔥", desc: "Deep optical smoke and flame detection with instant safety klaxon dispatch." },
            { id: "machinery", name: "Restricted Machinery Safety Zone", icon: "⚙️", desc: "Tripwires around robotic cells, conveyor pinch points, and boiler units." },
            { id: "worker_att", name: "Shift Clock-in & Labor Biometrics", icon: "⏱️", desc: "Exact biometric shift tracking and overtime timestamping." },
            { id: "dossier", name: "Plant Worker Safety Dossier", icon: "📁", desc: "Safety audit compliance, violation flags, and worker cert records." },
        ],
    },
    Hospital: {
        title: "🏥 Public Places, Transit & Healthcare Hub",
        tagline: "Civic Surveillance • Crowd Density • Public Safety & Transit Thoroughfares",
        themeClass: "mode-public",
        bgImg: "https://images.unsplash.com/photo-1519501025264-65ba15a82390?w=1920&q=80",
        functions: [
            { id: "crowd", name: "Crowd Density & Stampede Warning", icon: "👥", desc: "Monitors concourse density, detects bottleneck panics and stampedes." },
            { id: "abandoned", name: "Abandoned Object & Bag Detection", icon: "🧳", desc: "Detects stationary unattended luggage or packages in public thoroughfares." },
            { id: "violence", name: "Public Violence & Altercation Triage", icon: "⚠️", desc: "Recognizes physical fighting, sudden falls, and distress gestures." },
            { id: "authorized", name: "Restricted Ward & Pharmacy Vault Access", icon: "🔒", desc: "Biometric access gates to operating theaters, narcotics, and neonatal ICU." },
            { id: "dossier", name: "Staff & Responders Dossier", icon: "📁", desc: "Access badges, biometric check-ins, and shift records." },
        ],
    },
    Corporate: {
        title: "🌐 Corporate Campus & Enterprise Hub",
        tagline: "Enterprise Security • Executive Turnstiles • Server Room Biometrics",
        themeClass: "mode-campus",
        bgImg: "https://images.unsplash.com/photo-1486406146926-c627a92ad1ab?w=1920&q=80",
        functions: [
            { id: "executive_att", name: "Executive Face Attendance", icon: "🏢", desc: "Touchless turnstile check-in with millisecond biometric matching." },
            { id: "tailgating", name: "Anti-Tailgating & Badge Piggybacking", icon: "🚫", desc: "Detects unauthorized individuals following behind an authorized badge scan." },
            { id: "server_room", name: "High-Security Data Center Access", icon: "🖥️", desc: "Biometric dual-factor authentication for mission-critical IT infrastructure." },
            { id: "visitor", name: "Visitor Pass & Escort Tracking", icon: "🪪", desc: "Monitors guest roaming and flags unescorted entry to private executive suites." },
            { id: "dossier", name: "Employee Enterprise Dossier", icon: "📁", desc: "Full personnel dossier with attendance, dress code, and access history." },
        ],
    },
};

export default function EnvironmentSelectPage({ user, onEnvironmentSelected }) {
    const [environments, setEnvironments] = useState([]);
    const [selectedEnv, setSelectedEnv] = useState(null);
    const [showCreateModal, setShowCreateModal] = useState(false);
    const [showOnboardingModal, setShowOnboardingModal] = useState(false);
    const [editingEnv, setEditingEnv] = useState(null);

    // Create environment form
    const [newName, setNewName] = useState("");
    const [newType, setNewType] = useState("School");
    const [newDesc, setNewDesc] = useState("");

    // Edit / Rename environment form
    const [editName, setEditName] = useState("");
    const [editType, setEditType] = useState("");
    const [feedback, setFeedback] = useState("");

    const loadEnvironments = async () => {
        try {
            const res = await getEnvironments();
            const list = res.environments || [];
            setEnvironments(list);
            if (list.length > 0) {
                const first = list[0];
                setSelectedEnv((prev) => {
                    if (prev) {
                        const found = list.find((e) => e.id === prev.id);
                        return found || first;
                    }
                    return first;
                });
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
        setEditType(env.type || "School");
    };

    const handleSaveEnvRename = async (e) => {
        e.preventDefault();
        if (!editingEnv) return;
        try {
            const res = await updateEnvironment(editingEnv.id, {
                name: editName,
                type: editType,
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

    const handleCreateNew = async (e) => {
        e.preventDefault();
        try {
            const res = await createEnvironment({
                name: newName,
                type: newType,
                description: newDesc,
                enabled_features: ["face_detection", "attendance", "dress_code", "alerts"],
            });
            if (res.success) {
                setShowCreateModal(false);
                setNewName("");
                setNewDesc("");
                setFeedback(`✓ Created new mode "${newName}"!`);
                setTimeout(() => setFeedback(""), 4000);
                await loadEnvironments();
            }
        } catch (err) {
            alert(err.response?.data?.detail || "Failed to create environment");
        }
    };

    const currentCap = selectedEnv ? (MODE_CAPABILITIES[selectedEnv.type] || MODE_CAPABILITIES.School) : MODE_CAPABILITIES.School;

    return (
        <div
            className="env-select-container"
            style={{
                minHeight: "100vh",
                padding: "36px 20px",
                backgroundImage: `linear-gradient(180deg, rgba(10, 15, 24, 0.88) 0%, rgba(10, 15, 24, 0.96) 100%), url(${currentCap.bgImg})`,
                backgroundSize: "cover",
                backgroundPosition: "center",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
            }}
        >
            <div
                className="env-select-card"
                style={{
                    maxWidth: "1200px",
                    width: "100%",
                    padding: "36px",
                    borderRadius: "14px",
                    border: "1px solid rgba(212, 175, 55, 0.25)",
                    background: "rgba(14, 20, 31, 0.94)",
                    backdropFilter: "blur(20px)",
                    boxShadow: "0 20px 50px rgba(0, 0, 0, 0.7), inset 0 1px 0 rgba(255, 255, 255, 0.08)",
                }}
            >
                {/* Executive Brand Header */}
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "26px", borderBottom: "1px solid rgba(255, 255, 255, 0.08)", paddingBottom: "20px" }}>
                    <div style={{ display: "flex", alignItems: "center", gap: "16px" }}>
                        <div
                            style={{
                                width: "50px",
                                height: "50px",
                                borderRadius: "50%",
                                background: "linear-gradient(135deg, #d4af37 0%, #b8860b 100%)",
                                display: "flex",
                                alignItems: "center",
                                justifyContent: "center",
                                boxShadow: "0 0 20px rgba(212, 175, 55, 0.4)",
                                color: "#0c1017",
                                fontSize: "22px",
                                fontWeight: 800,
                            }}
                        >
                            ⚜️
                        </div>
                        <div>
                            <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
                                <h2 style={{ margin: 0, fontSize: "22px", fontWeight: 800, color: "#f8fafc", letterSpacing: "0.5px" }}>
                                    Operational Deployment Mode
                                </h2>
                                <span style={{ fontSize: "10px", background: "rgba(212, 175, 55, 0.2)", color: "#d4af37", border: "1px solid rgba(212, 175, 55, 0.4)", padding: "2px 8px", borderRadius: "10px", fontWeight: 700 }}>
                                    ENTERPRISE 3.0
                                </span>
                            </div>
                            <p style={{ margin: "4px 0 0 0", fontSize: "13px", color: "#94a3b8" }}>
                                Welcome, <strong>{user?.name || user?.full_name || user?.username}</strong>. Select your domain to configure datasets and cameras.
                            </p>
                        </div>
                    </div>

                    <button
                        type="button"
                        onClick={() => setShowCreateModal(true)}
                        className="tool-btn btn-secondary-mini"
                        style={{ border: "1px solid rgba(255,255,255,0.15)", background: "rgba(255,255,255,0.05)", color: "#cbd5e1", padding: "8px 16px", fontSize: "12px", fontWeight: 600 }}
                    >
                        + Create Custom Domain
                    </button>
                </div>

                {feedback && <div className="checkin-feedback-banner" style={{ marginBottom: "18px" }}>{feedback}</div>}

                {/* Section 1: Modes Grid */}
                <div style={{ marginBottom: "26px" }}>
                    <div style={{ fontSize: "12px", fontWeight: 700, color: "#94a3b8", textTransform: "uppercase", letterSpacing: "0.5px", marginBottom: "12px" }}>
                        1. Select Surveillance Domain
                    </div>

                    <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(210px, 1fr))", gap: "14px" }}>
                        {environments.map((env) => {
                            const isSelected = selectedEnv?.id === env.id;
                            const cap = MODE_CAPABILITIES[env.type] || MODE_CAPABILITIES.School;
                            return (
                                <div
                                    key={env.id}
                                    onClick={() => handleSelectEnv(env)}
                                    style={{
                                        padding: "16px",
                                        borderRadius: "10px",
                                        border: isSelected ? "2px solid #d4af37" : "1px solid rgba(255, 255, 255, 0.08)",
                                        background: isSelected ? "rgba(212, 175, 55, 0.12)" : "rgba(255, 255, 255, 0.02)",
                                        cursor: "pointer",
                                        transition: "all 0.15s ease",
                                        display: "flex",
                                        flexDirection: "column",
                                        justifyContent: "space-between",
                                        minHeight: "125px",
                                        boxShadow: isSelected ? "0 4px 20px rgba(212, 175, 55, 0.15)" : "none",
                                    }}
                                >
                                    <div>
                                        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
                                            <span style={{ fontSize: "24px" }}>
                                                {env.type === "School" ? "🏛️" : (env.type === "Military" ? "🛡️" : (env.type === "Industry" ? "🏭" : "🏥"))}
                                            </span>
                                            <button
                                                type="button"
                                                onClick={(e) => handleOpenEdit(e, env)}
                                                style={{ background: "transparent", border: "none", fontSize: "11px", cursor: "pointer", color: "#94a3b8" }}
                                                title="Rename mode"
                                            >
                                                ✏️ Rename
                                            </button>
                                        </div>
                                        <div style={{ fontSize: "14px", fontWeight: 700, marginTop: "8px", color: "#f8fafc" }}>
                                            {env.name}
                                        </div>
                                    </div>
                                    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginTop: "10px" }}>
                                        <span style={{ fontSize: "10px", color: isSelected ? "#d4af37" : "#94a3b8", fontWeight: 700, textTransform: "uppercase" }}>
                                            {env.type}
                                        </span>
                                        {isSelected && (
                                            <span style={{ fontSize: "10px", color: "#d4af37", fontWeight: 800 }}>
                                                ● ACTIVE
                                            </span>
                                        )}
                                    </div>
                                </div>
                            );
                        })}
                    </div>
                </div>

                {/* Section 2: Mode-Specific Capabilities Showcase */}
                {selectedEnv && (
                    <div style={{ padding: "20px 24px", borderRadius: "10px", background: "rgba(0, 0, 0, 0.35)", border: "1px solid rgba(255, 255, 255, 0.08)", marginBottom: "26px" }}>
                        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "14px" }}>
                            <div>
                                <h3 style={{ margin: 0, fontSize: "16px", fontWeight: 700, color: "#f8fafc" }}>
                                    {currentCap.title}
                                </h3>
                                <p style={{ margin: "2px 0 0 0", fontSize: "12px", color: "#94a3b8" }}>
                                    {currentCap.tagline}
                                </p>
                            </div>
                            <span style={{ fontSize: "10px", background: "rgba(212, 175, 55, 0.2)", color: "#d4af37", border: "1px solid rgba(212, 175, 55, 0.4)", padding: "3px 10px", borderRadius: "8px", fontWeight: 700 }}>
                                {currentCap.functions.length} AI SPECIALIZED FUNCTIONS
                            </span>
                        </div>

                        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(280px, 1fr))", gap: "10px" }}>
                            {currentCap.functions.map((fn) => (
                                <div
                                    key={fn.id}
                                    style={{
                                        padding: "12px 14px",
                                        background: "rgba(255, 255, 255, 0.03)",
                                        borderRadius: "8px",
                                        border: "1px solid rgba(255, 255, 255, 0.06)",
                                        display: "flex",
                                        alignItems: "flex-start",
                                        gap: "10px",
                                    }}
                                >
                                    <span style={{ fontSize: "20px" }}>{fn.icon}</span>
                                    <div>
                                        <div style={{ fontSize: "12px", fontWeight: 700, color: "#f8fafc" }}>{fn.name}</div>
                                        <div style={{ fontSize: "11px", color: "#94a3b8", marginTop: "2px" }}>{fn.desc}</div>
                                    </div>
                                </div>
                            ))}
                        </div>
                    </div>
                )}

                {/* Section 3: Action Controls */}
                <div style={{ display: "flex", justifyContent: "flex-end", gap: "14px", borderTop: "1px solid rgba(255, 255, 255, 0.08)", paddingTop: "20px" }}>
                    <button
                        type="button"
                        onClick={() => handleDirectEnter()}
                        className="tool-btn btn-secondary-mini"
                        style={{ padding: "10px 22px", fontSize: "13px", color: "#cbd5e1", border: "1px solid rgba(255,255,255,0.15)", background: "rgba(255,255,255,0.04)" }}
                    >
                        ⚡ Direct Command Center
                    </button>
                    <button
                        type="button"
                        onClick={() => setShowOnboardingModal(true)}
                        style={{
                            padding: "10px 28px",
                            fontSize: "13px",
                            fontWeight: 700,
                            background: "linear-gradient(135deg, #d4af37 0%, #b8860b 100%)",
                            color: "#0c1017",
                            border: "none",
                            borderRadius: "6px",
                            cursor: "pointer",
                            boxShadow: "0 4px 16px rgba(212, 175, 55, 0.35)",
                        }}
                    >
                        🚀 Initialize Mode &amp; Dataset (Guided Setup)
                    </button>
                </div>
            </div>

            {/* Step-by-Step Onboarding Wizard Modal */}
            <OnboardingFlowModal
                environment={selectedEnv}
                isOpen={showOnboardingModal}
                onClose={() => setShowOnboardingModal(false)}
                onLaunchLive={(config) => handleDirectEnter()}
            />

            {/* Rename Modal */}
            {editingEnv && (
                <div className="modal-overlay">
                    <div className="modal-dialog" style={{ background: "#0e131b", border: "1px solid rgba(212, 175, 55, 0.3)" }}>
                        <div className="modal-header">
                            <h3 style={{ color: "#f8fafc" }}>✏️ Rename Deployment Mode</h3>
                            <button className="tool-btn btn-secondary-mini" onClick={() => setEditingEnv(null)}>✕</button>
                        </div>
                        <form onSubmit={handleSaveEnvRename} className="modal-form">
                            <div>
                                <label style={{ fontSize: "11px", color: "#94a3b8" }}>Mode Name</label>
                                <input
                                    className="form-control"
                                    value={editName}
                                    onChange={(e) => setEditName(e.target.value)}
                                    style={{ width: "100%", padding: "8px 12px", fontSize: "13px", background: "#131a26", color: "#ffffff", border: "1px solid rgba(255,255,255,0.1)" }}
                                />
                            </div>
                            <div className="modal-actions">
                                <button type="button" className="tool-btn btn-secondary-mini" onClick={() => setEditingEnv(null)}>Cancel</button>
                                <button type="submit" className="tool-btn btn-primary" style={{ background: "#d4af37", color: "#0c1017" }}>Save Changes</button>
                            </div>
                        </form>
                    </div>
                </div>
            )}

            {/* Create Custom Mode Modal */}
            {showCreateModal && (
                <div className="modal-overlay">
                    <div className="modal-dialog" style={{ background: "#0e131b", border: "1px solid rgba(212, 175, 55, 0.3)" }}>
                        <div className="modal-header">
                            <h3 style={{ color: "#f8fafc" }}>➕ Add Custom Operational Domain</h3>
                            <button className="tool-btn btn-secondary-mini" onClick={() => setShowCreateModal(false)}>✕</button>
                        </div>
                        <form onSubmit={handleCreateNew} className="modal-form">
                            <div>
                                <label style={{ fontSize: "11px", color: "#94a3b8" }}>Mode Name *</label>
                                <input
                                    className="form-control"
                                    value={newName}
                                    onChange={(e) => setNewName(e.target.value)}
                                    placeholder="e.g. Apex Strategic Compound"
                                    required
                                    style={{ width: "100%", padding: "8px 12px", fontSize: "13px", background: "#131a26", color: "#ffffff", border: "1px solid rgba(255,255,255,0.1)" }}
                                />
                            </div>
                            <div>
                                <label style={{ fontSize: "11px", color: "#94a3b8" }}>Domain Category</label>
                                <select
                                    value={newType}
                                    onChange={(e) => setNewType(e.target.value)}
                                    style={{ width: "100%", padding: "8px 12px", fontSize: "13px", background: "#131a26", color: "#ffffff", border: "1px solid rgba(255,255,255,0.1)" }}
                                >
                                    <option value="School">School / Campus</option>
                                    <option value="Military">Military / Defense</option>
                                    <option value="Industry">Industry &amp; Manufacturing</option>
                                    <option value="Hospital">Hospital / Public Places</option>
                                    <option value="Corporate">Corporate Tech Hub</option>
                                </select>
                            </div>
                            <div className="modal-actions">
                                <button type="button" className="tool-btn btn-secondary-mini" onClick={() => setShowCreateModal(false)}>Cancel</button>
                                <button type="submit" className="tool-btn btn-primary" style={{ background: "#d4af37", color: "#0c1017" }}>Create Mode</button>
                            </div>
                        </form>
                    </div>
                </div>
            )}
        </div>
    );
}
