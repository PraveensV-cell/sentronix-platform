import { useState, useEffect } from "react";
import { getEnvironments, createEnvironment, updateEnvironment, updateEnvironmentFeatures } from "../api/api";
import SetupWizardModal from "../components/SetupWizardModal";

const MODE_CAPABILITIES = {
    School: {
        title: "🏛️ Academic Campus & School Safety",
        tagline: "Educational Campus Surveillance • Uniform Standards • Biometric Attendance",
        themeClass: "mode-campus",
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
    const [enabledFeatures, setEnabledFeatures] = useState([]);
    const [showCreateModal, setShowCreateModal] = useState(false);
    const [showWizardModal, setShowWizardModal] = useState(false);
    const [editingEnv, setEditingEnv] = useState(null);

    // Create environment form
    const [newName, setNewName] = useState("");
    const [newType, setNewType] = useState("School");
    const [newDesc, setNewDesc] = useState("");
    const [newLocation, setNewLocation] = useState("");

    // Edit / Rename environment form
    const [editName, setEditName] = useState("");
    const [editType, setEditType] = useState("");
    const [editDesc, setEditDesc] = useState("");
    const [editLoc, setEditLoc] = useState("");
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
                setEnabledFeatures(first.enabled_features || []);
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
        setEnabledFeatures(env.enabled_features || []);
    };

    const handleOpenEdit = (e, env) => {
        e.stopPropagation();
        setEditingEnv(env);
        setEditName(env.name || "");
        setEditType(env.type || "School");
        setEditDesc(env.description || "");
        setEditLoc(env.location || "");
    };

    const handleSaveEnvRename = async (e) => {
        e.preventDefault();
        if (!editingEnv) return;
        try {
            const res = await updateEnvironment(editingEnv.id, {
                name: editName,
                type: editType,
                description: editDesc,
                location: editLoc,
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

    const handleDirectEnter = async () => {
        if (!selectedEnv) return;
        try {
            await updateEnvironmentFeatures(selectedEnv.id, enabledFeatures);
            const updated = { ...selectedEnv, enabled_features: enabledFeatures };
            localStorage.setItem("sentronix_env", JSON.stringify(updated));
            onEnvironmentSelected(updated);
        } catch (err) {
            const updated = { ...selectedEnv, enabled_features: enabledFeatures };
            localStorage.setItem("sentronix_env", JSON.stringify(updated));
            onEnvironmentSelected(updated);
        }
    };

    const handleCreateNew = async (e) => {
        e.preventDefault();
        try {
            const res = await createEnvironment({
                name: newName,
                type: newType,
                description: newDesc,
                location: newLocation,
                enabled_features: ["face_detection", "attendance", "dress_code", "alerts"],
            });
            if (res.success) {
                setShowCreateModal(false);
                setNewName("");
                setNewDesc("");
                setNewLocation("");
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
        <div className="env-select-container" style={{ minHeight: "100vh", padding: "40px 20px" }}>
            <div className="env-select-card" style={{ maxWidth: "1200px", margin: "0 auto", padding: "32px", borderRadius: "12px", border: "1px solid var(--border-color)", background: "var(--card-bg)" }}>
                {/* Header */}
                <div className="env-select-header" style={{ marginBottom: "24px", borderBottom: "1px solid var(--border-color)", paddingBottom: "18px" }}>
                    <div style={{ display: "flex", alignItems: "center", gap: "16px" }}>
                        <div className="brand-logo-icon large" style={{ width: "48px", height: "48px" }}>
                            <div className="inner-radar"></div>
                        </div>
                        <div>
                            <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
                                <h2 style={{ margin: 0, fontSize: "22px", fontWeight: 800 }}>
                                    Operational Mode Selection &amp; Setup
                                </h2>
                                <span style={{ fontSize: "11px", background: "var(--primary-color)", color: "#ffffff", padding: "2px 10px", borderRadius: "12px", fontWeight: 700 }}>
                                    24/7 AI READY
                                </span>
                            </div>
                            <p style={{ margin: "4px 0 0 0", fontSize: "13px", color: "var(--text-secondary)" }}>
                                Welcome, <strong>{user?.name || user?.full_name || user?.username}</strong>. Choose or customize your surveillance domain below.
                            </p>
                        </div>
                    </div>
                </div>

                {feedback && <div className="checkin-feedback-banner" style={{ marginBottom: "16px" }}>{feedback}</div>}

                {/* Section 1: Modes Grid */}
                <div style={{ marginBottom: "24px" }}>
                    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "12px" }}>
                        <h3 style={{ margin: 0, fontSize: "15px", fontWeight: 700 }}>
                            1. Select Deployment Mode
                        </h3>
                        <button
                            className="tool-btn btn-secondary-mini"
                            onClick={() => setShowCreateModal(true)}
                            style={{ fontSize: "12px", fontWeight: 600 }}
                        >
                            + Add Custom Mode
                        </button>
                    </div>

                    <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))", gap: "14px" }}>
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
                                        border: `2px solid ${isSelected ? "var(--primary-color)" : "var(--border-color)"}`,
                                        background: isSelected ? "var(--primary-soft)" : "var(--bg-secondary)",
                                        cursor: "pointer",
                                        transition: "all 0.15s ease",
                                        display: "flex",
                                        flexDirection: "column",
                                        justifyContent: "space-between",
                                        minHeight: "130px",
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
                                                style={{ background: "transparent", border: "none", fontSize: "12px", cursor: "pointer", color: "var(--text-secondary)" }}
                                                title="Rename this mode"
                                            >
                                                ✏️ Rename
                                            </button>
                                        </div>
                                        <div style={{ fontSize: "14px", fontWeight: 700, marginTop: "8px", color: "var(--text-primary)" }}>
                                            {env.name}
                                        </div>
                                    </div>
                                    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginTop: "10px" }}>
                                        <span className="cam-func-badge badge-primary" style={{ fontSize: "10px" }}>
                                            {env.type.toUpperCase()}
                                        </span>
                                        {isSelected && (
                                            <span style={{ fontSize: "11px", color: "var(--primary-color)", fontWeight: 700 }}>
                                                ✓ ACTIVE
                                            </span>
                                        )}
                                    </div>
                                </div>
                            );
                        })}
                    </div>
                </div>

                {/* Section 2: Mode-Specific Capabilities Box (Points 2 & 3) */}
                {selectedEnv && (
                    <div style={{ padding: "20px", borderRadius: "10px", background: "var(--bg-secondary)", border: "1px solid var(--border-color)", marginBottom: "24px" }}>
                        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "14px" }}>
                            <div>
                                <h3 style={{ margin: 0, fontSize: "16px", fontWeight: 700 }}>
                                    {currentCap.title}
                                </h3>
                                <p style={{ margin: "2px 0 0 0", fontSize: "12px", color: "var(--text-secondary)" }}>
                                    {currentCap.tagline}
                                </p>
                            </div>
                            <span style={{ fontSize: "11px", background: "var(--primary-color)", color: "#ffffff", padding: "3px 10px", borderRadius: "6px", fontWeight: 700 }}>
                                {currentCap.functions.length} SPECIALIZED AI FUNCTIONS
                            </span>
                        </div>

                        {/* Functions List Grid */}
                        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(280px, 1fr))", gap: "12px" }}>
                            {currentCap.functions.map((fn) => (
                                <div
                                    key={fn.id}
                                    style={{
                                        padding: "12px 14px",
                                        background: "var(--card-bg)",
                                        borderRadius: "8px",
                                        border: "1px solid var(--border-color)",
                                        display: "flex",
                                        alignItems: "flex-start",
                                        gap: "10px",
                                    }}
                                >
                                    <span style={{ fontSize: "20px" }}>{fn.icon}</span>
                                    <div>
                                        <div style={{ fontSize: "12px", fontWeight: 700, color: "var(--text-primary)" }}>{fn.name}</div>
                                        <div style={{ fontSize: "11px", color: "var(--text-secondary)", marginTop: "2px" }}>{fn.desc}</div>
                                    </div>
                                </div>
                            ))}
                        </div>
                    </div>
                )}

                {/* Action Buttons: Guided Setup vs Direct Enter */}
                <div style={{ display: "flex", justifyContent: "flex-end", gap: "14px", borderTop: "1px solid var(--border-color)", paddingTop: "20px" }}>
                    <button
                        type="button"
                        className="tool-btn btn-secondary-mini"
                        onClick={handleDirectEnter}
                        style={{ padding: "10px 22px", fontSize: "13px", fontWeight: 600 }}
                    >
                        ⚡ Enter Direct Command Center
                    </button>
                    <button
                        type="button"
                        className="tool-btn btn-primary"
                        onClick={() => setShowWizardModal(true)}
                        style={{
                            padding: "10px 28px",
                            fontSize: "13px",
                            fontWeight: 700,
                            background: "linear-gradient(135deg, #0ea5e9 0%, #0284c7 100%)",
                            boxShadow: "0 2px 8px rgba(14,165,233,0.3)",
                        }}
                    >
                        🚀 Start Guided Setup Flow (Enroll People &amp; Camera)
                    </button>
                </div>
            </div>

            {/* Guided Setup Wizard Modal (Step 1 to 5) */}
            <SetupWizardModal
                environment={selectedEnv}
                isOpen={showWizardModal}
                onClose={() => setShowWizardModal(false)}
                onComplete={() => handleDirectEnter()}
            />

            {/* Rename Modal */}
            {editingEnv && (
                <div className="modal-overlay">
                    <div className="modal-dialog">
                        <div className="modal-header">
                            <h3>✏️ Rename Deployment Mode</h3>
                            <button className="tool-btn btn-secondary-mini" onClick={() => setEditingEnv(null)}>✕</button>
                        </div>
                        <form onSubmit={handleSaveEnvRename} className="modal-form">
                            <div>
                                <label className="fleet-stat-label">Mode Name</label>
                                <input
                                    className="form-control"
                                    value={editName}
                                    onChange={(e) => setEditName(e.target.value)}
                                    style={{ width: "100%", padding: "8px 12px", fontSize: "13px" }}
                                />
                            </div>
                            <div>
                                <label className="fleet-stat-label">Domain Category</label>
                                <select
                                    className="sector-select-box"
                                    value={editType}
                                    onChange={(e) => setEditType(e.target.value)}
                                    style={{ width: "100%", padding: "8px 12px", fontSize: "13px" }}
                                >
                                    <option value="School">School / Campus</option>
                                    <option value="Military">Military / Strategic Defense</option>
                                    <option value="Industry">Heavy Industry &amp; Plants</option>
                                    <option value="Hospital">Hospital &amp; Public Transit</option>
                                    <option value="Corporate">Corporate Campus</option>
                                </select>
                            </div>
                            <div className="modal-actions">
                                <button type="button" className="tool-btn btn-secondary-mini" onClick={() => setEditingEnv(null)}>Cancel</button>
                                <button type="submit" className="tool-btn btn-primary">Save Changes</button>
                            </div>
                        </form>
                    </div>
                </div>
            )}

            {/* Create New Mode Modal */}
            {showCreateModal && (
                <div className="modal-overlay">
                    <div className="modal-dialog">
                        <div className="modal-header">
                            <h3>➕ Add Custom Operational Mode</h3>
                            <button className="tool-btn btn-secondary-mini" onClick={() => setShowCreateModal(false)}>✕</button>
                        </div>
                        <form onSubmit={handleCreateNew} className="modal-form">
                            <div>
                                <label className="fleet-stat-label">Mode Name *</label>
                                <input
                                    className="form-control"
                                    value={newName}
                                    onChange={(e) => setNewName(e.target.value)}
                                    placeholder="e.g. Apex Strategic Research Compound"
                                    required
                                    style={{ width: "100%", padding: "8px 12px", fontSize: "13px" }}
                                />
                            </div>
                            <div>
                                <label className="fleet-stat-label">Domain Classification</label>
                                <select
                                    className="sector-select-box"
                                    value={newType}
                                    onChange={(e) => setNewType(e.target.value)}
                                    style={{ width: "100%", padding: "8px 12px", fontSize: "13px" }}
                                >
                                    <option value="School">School / Campus</option>
                                    <option value="Military">Military / Defense</option>
                                    <option value="Industry">Industry &amp; Manufacturing</option>
                                    <option value="Hospital">Hospital / Healthcare</option>
                                    <option value="Corporate">Corporate Tech Hub</option>
                                </select>
                            </div>
                            <div className="modal-actions">
                                <button type="button" className="tool-btn btn-secondary-mini" onClick={() => setShowCreateModal(false)}>Cancel</button>
                                <button type="submit" className="tool-btn btn-primary">Create Mode</button>
                            </div>
                        </form>
                    </div>
                </div>
            )}
        </div>
    );
}
