import { useState, useEffect } from "react";
import { getEnvironments, createEnvironment, updateEnvironment, updateEnvironmentFeatures } from "../api/api";

const ALL_FEATURES = [
    { id: "face_detection", label: "Face & Person Detection", icon: "👤", desc: "Localize people & faces in camera feeds" },
    { id: "face_recognition", label: "Face Recognition", icon: "🔍", desc: "Identity matching against enrolled database" },
    { id: "attendance", label: "Automated Attendance", icon: "🎓", desc: "Track presence duration & record check-ins" },
    { id: "dress_code", label: "Dress Code Monitoring", icon: "👔", desc: "Formals & regular school dress compliance" },
    { id: "exam_monitor", label: "Exam Hall Proctoring", icon: "📝", desc: "Detects prohibited phones, notes & cheating" },
    { id: "restricted_area", label: "Restricted Area Access", icon: "⛔", desc: "Virtual tripwires & zone intrusion detection" },
    { id: "prohibited_activity", label: "Prohibited Activity", icon: "🚨", desc: "Weapons, smoke, fire & abnormal behavior" },
    { id: "alerts", label: "Incident Alerts & Triage", icon: "🔔", desc: "Operator notification & acknowledgment workflow" },
    { id: "reports", label: "Analytics & Reports", icon: "📊", desc: "Presence trends, event breakdown & PDF/CSV" },
];

export default function EnvironmentSelectPage({ user, onEnvironmentSelected }) {
    const [environments, setEnvironments] = useState([]);
    const [selectedEnv, setSelectedEnv] = useState(null);
    const [enabledFeatures, setEnabledFeatures] = useState([]);
    const [showCreateModal, setShowCreateModal] = useState(false);
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

    const toggleFeature = (featId) => {
        setEnabledFeatures((prev) =>
            prev.includes(featId) ? prev.filter((f) => f !== featId) : [...prev, featId]
        );
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

    const handleSaveAndEnter = async () => {
        if (!selectedEnv) return;
        try {
            await updateEnvironmentFeatures(selectedEnv.id, enabledFeatures);
            const updated = { ...selectedEnv, enabled_features: enabledFeatures };
            localStorage.setItem("sentronix_env", JSON.stringify(updated));
            onEnvironmentSelected(updated);
        } catch (err) {
            console.error("Failed to update features", err);
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
                enabled_features: enabledFeatures.length > 0 ? enabledFeatures : ["face_detection", "attendance", "dress_code", "alerts"],
            });
            if (res.success) {
                setShowCreateModal(false);
                setNewName("");
                setNewDesc("");
                setNewLocation("");
                setFeedback(`✓ Created new environment "${newName}"!`);
                setTimeout(() => setFeedback(""), 4000);
                await loadEnvironments();
            }
        } catch (err) {
            alert(err.response?.data?.detail || "Failed to create environment");
        }
    };

    return (
        <div className="env-select-container">
            <div className="env-select-card">
                {/* Header */}
                <div className="env-select-header">
                    <div className="brand-logo-icon">
                        <div className="inner-radar"></div>
                    </div>
                    <div>
                        <h2>Operational Environment & Mode Selection</h2>
                        <p>Welcome, {user?.full_name || user?.username}. Select or customize your surveillance deployment mode.</p>
                    </div>
                </div>

                {feedback && <div className="checkin-feedback-banner">{feedback}</div>}

                {/* Section 1: Environments Grid */}
                <div className="env-grid-section">
                    <div className="section-title-row">
                        <h3>1. Select or Rename Deployment Mode</h3>
                        <button className="btn-secondary small" onClick={() => setShowCreateModal(true)}>
                            + Custom Environment
                        </button>
                    </div>

                    <div className="env-cards-grid">
                        {environments.map((env) => {
                            const isSelected = selectedEnv?.id === env.id;
                            return (
                                <div
                                    key={env.id}
                                    className={`env-mode-card ${isSelected ? "selected" : ""}`}
                                    onClick={() => handleSelectEnv(env)}
                                >
                                    <div className="env-card-header-bar">
                                        <div className="env-card-badge">{env.type.toUpperCase()} MODE</div>
                                        <button
                                            type="button"
                                            className="btn-rename-pill"
                                            title="Rename or customize this mode"
                                            onClick={(e) => handleOpenEdit(e, env)}
                                        >
                                            ✏️ Rename
                                        </button>
                                    </div>
                                    <h4>{env.name}</h4>
                                    <p>{env.description || "Active surveillance environment"}</p>
                                    <span className="env-loc">📍 {env.location || "On-Premises Campus"}</span>
                                </div>
                            );
                        })}
                    </div>
                </div>

                {/* Section 2: Active Modules */}
                <div className="features-section">
                    <div className="section-title-row">
                        <h3>2. Active Modules & Intelligence Capabilities</h3>
                        <span className="badge-count">{enabledFeatures.length} enabled</span>
                    </div>

                    <div className="features-checklist-grid">
                        {ALL_FEATURES.map((f) => {
                            const isChecked = enabledFeatures.includes(f.id);
                            return (
                                <div
                                    key={f.id}
                                    className={`feature-toggle-card ${isChecked ? "active" : ""}`}
                                    onClick={() => toggleFeature(f.id)}
                                >
                                    <div className="feature-card-header">
                                        <span className="feature-icon">{f.icon}</span>
                                        <strong>{f.label}</strong>
                                        <input
                                            type="checkbox"
                                            checked={isChecked}
                                            onChange={() => {}}
                                        />
                                    </div>
                                    <p>{f.desc}</p>
                                </div>
                            );
                        })}
                    </div>
                </div>

                {/* Footer Action */}
                <div className="env-select-footer">
                    <button className="enter-command-btn" onClick={handleSaveAndEnter} disabled={!selectedEnv}>
                        Enter Surveillance Command Center ({selectedEnv?.type || "School"} Mode) →
                    </button>
                </div>
            </div>

            {/* ── Rename / Edit Mode Modal ── */}
            {editingEnv && (
                <div className="modal-overlay" onClick={() => setEditingEnv(null)}>
                    <div className="modal-dialog" onClick={(e) => e.stopPropagation()}>
                        <div className="modal-header">
                            <h3>Rename & Customize Environment Mode</h3>
                            <button className="close-btn" onClick={() => setEditingEnv(null)}>×</button>
                        </div>
                        <form onSubmit={handleSaveEnvRename} className="modal-form">
                            <div className="form-group">
                                <label>Environment / Mode Name (Editable)</label>
                                <input
                                    type="text"
                                    value={editName}
                                    onChange={(e) => setEditName(e.target.value)}
                                    placeholder="e.g. Apex International University"
                                    required
                                />
                            </div>
                            <div className="form-group">
                                <label>Environment Type</label>
                                <select value={editType} onChange={(e) => setEditType(e.target.value)}>
                                    <option value="School">School / College Campus</option>
                                    <option value="Military">Military Tactical Zone</option>
                                    <option value="Industry">Heavy Industry & Chemical</option>
                                    <option value="Hospital">Hospital & Healthcare</option>
                                    <option value="Corporate">Corporate Tech Park</option>
                                    <option value="Custom">Custom Deployment</option>
                                </select>
                            </div>
                            <div className="form-group">
                                <label>Description</label>
                                <input
                                    type="text"
                                    value={editDesc}
                                    onChange={(e) => setEditDesc(e.target.value)}
                                    placeholder="Description of the facility"
                                />
                            </div>
                            <div className="form-group">
                                <label>Facility Location</label>
                                <input
                                    type="text"
                                    value={editLoc}
                                    onChange={(e) => setEditLoc(e.target.value)}
                                    placeholder="e.g. North Gate Complex"
                                />
                            </div>
                            <div className="modal-actions">
                                <button type="button" className="btn-secondary" onClick={() => setEditingEnv(null)}>
                                    Cancel
                                </button>
                                <button type="submit" className="btn-primary">
                                    💾 Save Mode Name
                                </button>
                            </div>
                        </form>
                    </div>
                </div>
            )}

            {/* ── Create Custom Environment Modal ── */}
            {showCreateModal && (
                <div className="modal-overlay" onClick={() => setShowCreateModal(false)}>
                    <div className="modal-dialog" onClick={(e) => e.stopPropagation()}>
                        <div className="modal-header">
                            <h3>Create Custom Environment</h3>
                            <button className="close-btn" onClick={() => setShowCreateModal(false)}>×</button>
                        </div>
                        <form onSubmit={handleCreateNew} className="modal-form">
                            <div className="form-group">
                                <label>Environment Name</label>
                                <input
                                    type="text"
                                    placeholder="e.g. Apex High School Campus"
                                    value={newName}
                                    onChange={(e) => setNewName(e.target.value)}
                                    required
                                />
                            </div>
                            <div className="form-group">
                                <label>Environment Type</label>
                                <select value={newType} onChange={(e) => setNewType(e.target.value)}>
                                    <option value="School">School / University Campus</option>
                                    <option value="Military">Military Zone / Strategic Defense Base</option>
                                    <option value="Industry">Heavy Industry / Factory Plant</option>
                                    <option value="Hospital">Hospital & Emergency Center</option>
                                    <option value="Corporate">Corporate Tech Park</option>
                                    <option value="Custom">Custom Facility</option>
                                </select>
                            </div>
                            <div className="form-group">
                                <label>Description</label>
                                <input
                                    type="text"
                                    placeholder="Surveillance perimeter purpose"
                                    value={newDesc}
                                    onChange={(e) => setNewDesc(e.target.value)}
                                />
                            </div>
                            <div className="form-group">
                                <label>Location</label>
                                <input
                                    type="text"
                                    placeholder="Main City Campus"
                                    value={newLocation}
                                    onChange={(e) => setNewLocation(e.target.value)}
                                />
                            </div>
                            <div className="modal-actions">
                                <button type="button" className="btn-secondary" onClick={() => setShowCreateModal(false)}>
                                    Cancel
                                </button>
                                <button type="submit" className="btn-primary">
                                    Create Mode
                                </button>
                            </div>
                        </form>
                    </div>
                </div>
            )}
        </div>
    );
}
