import { useState, useEffect } from "react";
import { getAlerts, updateAlertStatus } from "../api/api";

export default function AlertsView() {
    const [alerts, setAlerts] = useState([]);
    const [filter, setFilter] = useState("ALL");
    const [selectedAlert, setSelectedAlert] = useState(null);
    const [resolutionNotes, setResolutionNotes] = useState("");
    const [showResolveModal, setShowResolveModal] = useState(false);

    const loadAlerts = async () => {
        try {
            const res = await getAlerts();
            setAlerts(res.alerts || []);
        } catch (err) {
            console.error("Failed to load alerts", err);
        }
    };

    useEffect(() => {
        loadAlerts();
        const interval = setInterval(loadAlerts, 4000);
        return () => clearInterval(interval);
    }, []);

    const filteredAlerts = alerts.filter((a) => {
        if (filter === "ALL") return true;
        if (filter === "ACTIVE") return a.status.toUpperCase() === "ACTIVE";
        if (filter === "RESOLVED") return a.status.toUpperCase() === "RESOLVED";
        return a.priority.toUpperCase() === filter;
    });

    const handleAcknowledge = async (alertId) => {
        try {
            await updateAlertStatus(alertId, "ACKNOWLEDGED");
            await loadAlerts();
        } catch (err) {
            console.error("Failed to acknowledge", err);
        }
    };

    const handleOpenResolve = (alert) => {
        setSelectedAlert(alert);
        setResolutionNotes("Incident inspected by duty operator. Confirmed false alarm / normalized.");
        setShowResolveModal(true);
    };

    const handleConfirmResolve = async () => {
        if (!selectedAlert) return;
        try {
            await updateAlertStatus(selectedAlert.id, "RESOLVED");
            setShowResolveModal(false);
            await loadAlerts();
        } catch (err) {
            console.error("Failed to resolve alert", err);
        }
    };

    const counts = {
        critical: alerts.filter((a) => a.priority === "CRITICAL" && a.status === "ACTIVE").length,
        high: alerts.filter((a) => a.priority === "HIGH" && a.status === "ACTIVE").length,
        active: alerts.filter((a) => a.status === "ACTIVE").length,
        resolved: alerts.filter((a) => a.status === "RESOLVED").length,
    };

    return (
        <div className="alerts-module-container">
            <div className="module-header-row">
                <div>
                    <h2>Incident & Alert Triage Center</h2>
                    <p>Automated Hazard, Weapon & Restricted Area Incident Monitoring</p>
                </div>
                <div className="alert-filter-tabs">
                    {["ALL", "ACTIVE", "CRITICAL", "HIGH", "RESOLVED"].map((f) => (
                        <button
                            key={f}
                            className={`filter-tab ${filter === f ? "active" : ""}`}
                            onClick={() => setFilter(f)}
                        >
                            {f}
                        </button>
                    ))}
                </div>
            </div>

            {/* Severity Counter Row */}
            <div className="kpi-grid">
                <div className="kpi-card">
                    <span className="kpi-label">CRITICAL HAZARDS</span>
                    <strong className="kpi-val danger">{counts.critical}</strong>
                    <span className="kpi-sub">Immediate Action Required</span>
                </div>
                <div className="kpi-card">
                    <span className="kpi-label">HIGH PRIORITY</span>
                    <strong className="kpi-val warning">{counts.high}</strong>
                    <span className="kpi-sub">Restricted Area / Weapons</span>
                </div>
                <div className="kpi-card">
                    <span className="kpi-label">ACTIVE UNRESOLVED</span>
                    <strong className="kpi-val">{counts.active}</strong>
                    <span className="kpi-sub">Awaiting Operator Triage</span>
                </div>
                <div className="kpi-card">
                    <span className="kpi-label">RESOLVED TODAY</span>
                    <strong className="kpi-val success">{counts.resolved}</strong>
                    <span className="kpi-sub">Cleared & Documented</span>
                </div>
            </div>

            {/* Alerts List Grid */}
            <div className="alerts-feed-grid">
                {filteredAlerts.length === 0 ? (
                    <div className="empty-state-card">
                        <h3>No alerts found matching filter '{filter}'</h3>
                        <p>All monitored surveillance zones operating under normal conditions.</p>
                    </div>
                ) : (
                    filteredAlerts.map((a) => {
                        const isCritical = a.priority === "CRITICAL";
                        const isResolved = a.status.toUpperCase() === "RESOLVED";

                        return (
                            <div
                                key={a.id}
                                className={`alert-triage-card ${isCritical ? "critical-border" : ""} ${isResolved ? "resolved-card" : ""}`}
                            >
                                <div className="card-top-row">
                                    <div className="alert-type-badge-group">
                                        <span className={`priority-pill ${a.priority.toLowerCase()}`}>
                                            {a.priority}
                                        </span>
                                        <span className="alert-id-tag">Incident #{a.id}</span>
                                    </div>
                                    <span className={`status-text-pill ${a.status.toLowerCase()}`}>
                                        {a.status}
                                    </span>
                                </div>

                                <div className="alert-content">
                                    <h3>{a.object}</h3>
                                    <p className="alert-desc">
                                        Potential safety violation or security hazard detected by AI vision pipeline.
                                    </p>
                                    <div className="alert-metrics">
                                        <span>Confidence: <strong>{(a.confidence * 100).toFixed(0)}%</strong></span>
                                        <span>Camera: <strong>{a.camera_id || "Entrance Cam 01"}</strong></span>
                                        <span>Time: <strong>{a.timestamp}</strong></span>
                                    </div>
                                </div>

                                <div className="card-actions-row">
                                    {!isResolved && (
                                        <>
                                            <button
                                                className="btn-secondary small"
                                                onClick={() => handleAcknowledge(a.id)}
                                            >
                                                ✓ Acknowledge
                                            </button>
                                            <button
                                                className="btn-primary small"
                                                onClick={() => handleOpenResolve(a)}
                                            >
                                                Resolve Incident
                                            </button>
                                        </>
                                    )}
                                    {isResolved && (
                                        <span className="resolved-check-text">
                                            ✓ Cleared by Security Operator
                                        </span>
                                    )}
                                </div>
                            </div>
                        );
                    })
                )}
            </div>

            {/* Resolve Incident Modal */}
            {showResolveModal && (
                <div className="modal-overlay">
                    <div className="modal-dialog">
                        <div className="modal-header">
                            <h3>Resolve Incident #{selectedAlert?.id}</h3>
                            <button className="close-btn" onClick={() => setShowResolveModal(false)}>×</button>
                        </div>
                        <div className="modal-form">
                            <p>Enter operator investigation notes before closing this alert:</p>
                            <div className="form-group">
                                <label>Operator Notes</label>
                                <textarea
                                    value={resolutionNotes}
                                    onChange={(e) => setResolutionNotes(e.target.value)}
                                    rows={4}
                                />
                            </div>
                            <div className="modal-actions">
                                <button
                                    className="btn-secondary"
                                    onClick={() => setShowResolveModal(false)}
                                >
                                    Cancel
                                </button>
                                <button className="btn-primary" onClick={handleConfirmResolve}>
                                    Confirm Resolution & Archive
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}
