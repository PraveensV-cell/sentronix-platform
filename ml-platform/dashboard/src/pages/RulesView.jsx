import { useState, useEffect } from "react";
import { getRules, createRule, toggleRule } from "../api/api";

export default function RulesView() {
    const [rules, setRules] = useState([]);
    const [showAddModal, setShowAddModal] = useState(false);
    const [newName, setNewName] = useState("");
    const [newType, setNewType] = useState("prohibited_activity");
    const [newSeverity, setNewSeverity] = useState("HIGH");
    const [newCooldown, setNewCooldown] = useState(30);
    const [newTarget, setNewTarget] = useState("person");

    const loadRules = async () => {
        try {
            const res = await getRules();
            setRules(res.rules || []);
        } catch (err) {
            console.error("Failed to load rules", err);
        }
    };

    useEffect(() => {
        loadRules();
    }, []);

    const handleToggle = async (ruleId) => {
        try {
            await toggleRule(ruleId);
            await loadRules();
        } catch (err) {
            console.error("Failed to toggle rule", err);
        }
    };

    const handleCreate = async (e) => {
        e.preventDefault();
        try {
            const res = await createRule({
                name: newName,
                rule_type: newType,
                severity: newSeverity,
                cooldown_seconds: parseInt(newCooldown, 10),
                conditions: {
                    target: newTarget,
                    min_confidence: 0.70
                }
            });
            if (res.success) {
                setShowAddModal(false);
                setNewName("");
                await loadRules();
            }
        } catch (err) {
            alert(err.response?.data?.detail || "Rule creation failed");
        }
    };

    return (
        <div className="rules-module-container">
            <div className="module-header-row">
                <div>
                    <h2>Surveillance Rule & Policy Engine</h2>
                    <p>Configurable Policies for Safety Hazards, Restricted Zones & Dress Code</p>
                </div>
                <button className="btn-primary" onClick={() => setShowAddModal(true)}>
                    + Create Security Policy
                </button>
            </div>

            {/* Rules Cards Stack */}
            <div className="rules-stack">
                {rules.map((r) => {
                    const isEnabled = r.is_enabled === 1;
                    const isDressCode = r.rule_type === "dress_code";

                    return (
                        <div key={r.id} className={`rule-card ${isEnabled ? "active" : "disabled"}`}>
                            <div className="rule-card-left">
                                <div className="rule-type-badge-row">
                                    <span className="rule-type-tag">{r.rule_type.toUpperCase()}</span>
                                    <span className={`severity-pill ${r.severity.toLowerCase()}`}>
                                        {r.severity}
                                    </span>
                                    {isDressCode && (
                                        <span className="model-required-pill">
                                            ⚠️ Custom Model Required (Fine-Tuned YOLOv8/11)
                                        </span>
                                    )}
                                </div>
                                <h3>{r.name}</h3>
                                <div className="rule-conditions-snippet">
                                    <span>Conditions:</span>
                                    <code>{JSON.stringify(r.conditions)}</code>
                                </div>
                                <span className="cooldown-tag">Cooldown: {r.cooldown_seconds}s</span>
                            </div>

                            <div className="rule-card-right">
                                <label className="switch-toggle-label">
                                    <input
                                        type="checkbox"
                                        checked={isEnabled}
                                        onChange={() => handleToggle(r.id)}
                                    />
                                    <span className="slider"></span>
                                </label>
                                <span className="toggle-status-text">
                                    {isEnabled ? "ACTIVE POLICY" : "DISABLED"}
                                </span>
                            </div>
                        </div>
                    );
                })}
            </div>

            {/* Add Rule Modal */}
            {showAddModal && (
                <div className="modal-overlay">
                    <div className="modal-dialog">
                        <div className="modal-header">
                            <h3>Create Surveillance Policy</h3>
                            <button className="close-btn" onClick={() => setShowAddModal(false)}>×</button>
                        </div>
                        <form onSubmit={handleCreate} className="modal-form">
                            <div className="form-group">
                                <label>Policy Name</label>
                                <input
                                    type="text"
                                    placeholder="e.g. Science Lab After-Hours Intrusion"
                                    value={newName}
                                    onChange={(e) => setNewName(e.target.value)}
                                    required
                                />
                            </div>
                            <div className="form-group">
                                <label>Policy Category</label>
                                <select value={newType} onChange={(e) => setNewType(e.target.value)}>
                                    <option value="restricted_zone">Restricted Zone Access</option>
                                    <option value="prohibited_activity">Prohibited Activity / Hazard</option>
                                    <option value="dress_code">Dress Code Compliance</option>
                                    <option value="attendance">Attendance Rule</option>
                                    <option value="crowd_detection">Crowd Formation</option>
                                </select>
                            </div>
                            <div className="form-group">
                                <label>Trigger Target Object</label>
                                <select value={newTarget} onChange={(e) => setNewTarget(e.target.value)}>
                                    <option value="person">Person</option>
                                    <option value="fire">Fire / Flame</option>
                                    <option value="smoke">Smoke</option>
                                    <option value="weapon">Weapon / Sharp Object</option>
                                    <option value="vehicle">Unauthorized Vehicle</option>
                                    <option value="uniform">School Uniform</option>
                                </select>
                            </div>
                            <div className="form-group">
                                <label>Severity Level</label>
                                <select value={newSeverity} onChange={(e) => setNewSeverity(e.target.value)}>
                                    <option value="CRITICAL">CRITICAL (Immediate Alarm)</option>
                                    <option value="HIGH">HIGH (Security Dispatch)</option>
                                    <option value="MEDIUM">MEDIUM (Operator Triage)</option>
                                    <option value="LOW">LOW (Log Event Only)</option>
                                </select>
                            </div>
                            <div className="form-group">
                                <label>Alert Cooldown (Seconds)</label>
                                <input
                                    type="number"
                                    value={newCooldown}
                                    onChange={(e) => setNewCooldown(e.target.value)}
                                    min={5}
                                    max={600}
                                />
                            </div>
                            <div className="modal-actions">
                                <button type="button" className="btn-secondary" onClick={() => setShowAddModal(false)}>
                                    Cancel
                                </button>
                                <button type="submit" className="btn-primary">
                                    Save & Activate Policy
                                </button>
                            </div>
                        </form>
                    </div>
                </div>
            )}
        </div>
    );
}
