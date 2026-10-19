import { useState, useEffect } from "react";
import { getEnvironments, createEnvironment, updateEnvironmentFeatures } from "../api/api";

const ALL_FEATURES = [
    { id: "face_detection", label: "Face & Person Detection", icon: "👤", desc: "Localize people & faces in camera feeds" },
    { id: "face_recognition", label: "Face Recognition", icon: "🔍", desc: "Identity matching against enrolled database" },
    { id: "attendance", label: "Automated Attendance", icon: "🎓", desc: "Track presence duration & record check-ins" },
    { id: "dress_code", label: "Dress Code Monitoring", icon: "👔", desc: "Uniform, ID card & attire compliance check" },
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

    // Create environment form
    const [newName, setNewName] = useState("");
    const [newType, setNewType] = useState("School");
    const [newDesc, setNewDesc] = useState("");
    const [newLocation, setNewLocation] = useState("");
    const [loading, setLoading] = useState(true);

    const loadEnvironments = async () => {
        try {
            const res = await getEnvironments();
            const list = res.environments || [];
            setEnvironments(list);
            if (list.length > 0) {
                const first = list[0];
                setSelectedEnv(first);
                setEnabledFeatures(first.enabled_features || []);
            }
        } catch (err) {
            console.error("Failed to load environments", err);
        } finally {
            setLoading(false);
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

    const handleSaveAndEnter = async () => {
        if (!selectedEnv) return;
        try {
            await updateEnvironmentFeatures(selectedEnv.id, enabledFeatures);
            const updated = { ...selectedEnv, enabled_features: enabledFeatures };
            localStorage.setItem("sentronix_env", JSON.stringify(updated));
            onEnvironmentSelected(updated);
        } catch (err) {
            console.error("Failed to update features", err);
            // proceed anyway with local state
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
                enabled_features: enabledFeatures.length > 0 ? enabledFeatures : ["face_detection", "attendance", "alerts"]
            });
            if (res.success) {
                setShowCreateModal(false);
                setNewName("");
                setNewDesc("");
                setNewLocation("");
                await loadEnvironments();
            }
        } catch (err) {
            alert(err.response?.data?.detail || "Failed to create environment");
        }
    };

    return (
        <div className="env-select-container">
            <div className="env-select-card">
                <div className="env-select-header">
                    <div className="brand-logo-icon">
                        <div className="inner-radar"></div>
                    </div>
                    <div>
                        <h2>Operational Environment & Mode Selection</h2>
                        <p>Welcome, {user?.full_name || user?.username}. Select or configure your surveillance deployment mode.</p>
                    </div>
                </div>

                <div className="env-grid-section">
                    <div className="section-title-row">
                        <h3>1. Select Surveillance Environment</h3>
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
                                    <div className="env-card-badge">{env.type.toUpperCase()}</div>
                                    <h4>{env.name}</h4>
                                    <p>{env.description || "Active surveillance environment"}</p>
                                    <span className="env-loc">📍 {env.location || "On-Premises"}</span>
                                </div>
                            );
                        })}
                    </div>
                </div>

                <div className="features-section">
                    <div className="section-title-row">
                        <h3>2. Active Modules & Intelligence Capabilities</h3>
                        <span>{enabledFeatures.length} enabled</span>
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

                <div className="env-select-footer">
                    <button className="enter-command-btn" onClick={handleSaveAndEnter} disabled={!selectedEnv}>
                        Enter Surveillance Command Center →
                    </button>
                </div>
            </div>

            {/* Create Custom Environment Modal */}
            {showCreateModal && (
                <div className="modal-overlay">
                    <div className="modal-dialog">
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
                                    <option value="School">School</option>
                                    <option value="College">College</option>
                                    <option value="University">University</option>
                                    <option value="Hospital">Hospital</option>
                                    <option value="Industry">Industry / Factory</option>
                                    <option value="Office">Corporate Office</option>
                                    <option value="Custom">Custom Facility</option>
                                </select>
                            </div>
                            <div className="form-group">
                                <label>Location</label>
                                <input
                                    type="text"
                                    placeholder="e.g. North Wing / Main Building"
                                    value={newLocation}
                                    onChange={(e) => setNewLocation(e.target.value)}
                                />
                            </div>
                            <div className="form-group">
                                <label>Description</label>
                                <textarea
                                    placeholder="Purpose and operational objectives..."
                                    value={newDesc}
                                    onChange={(e) => setNewDesc(e.target.value)}
                                    rows={3}
                                />
                            </div>
                            <div className="modal-actions">
                                <button type="button" className="btn-secondary" onClick={() => setShowCreateModal(false)}>
                                    Cancel
                                </button>
                                <button type="submit" className="btn-primary">
                                    Create & Select
                                </button>
                            </div>
                        </form>
                    </div>
                </div>
            )}
        </div>
    );
}
