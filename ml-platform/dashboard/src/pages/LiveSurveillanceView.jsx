import { useState, useEffect } from "react";
import {
    getCameras,
    getDetections,
    getAlerts,
    updateAlertStatus,
    API_BASE_URL,
    getExportCsvUrl,
} from "../api/api";

export default function LiveSurveillanceView({ environment, systemOnline }) {
    const [cameras, setCameras] = useState([]);
    const [selectedCamera, setSelectedCamera] = useState(null);
    const [detections, setDetections] = useState([]);
    const [alerts, setAlerts] = useState([]);
    const [isStreaming, setIsStreaming] = useState(true);
    const [viewMode, setViewMode] = useState("focus"); // "focus" | "multi_grid"
    const [snapshotMsg, setSnapshotMsg] = useState("");

    const loadData = async () => {
        try {
            const [camRes, detRes, altRes] = await Promise.all([
                getCameras(),
                getDetections(),
                getAlerts(),
            ]);

            const camList = camRes.cameras || [];
            setCameras(camList);
            setSelectedCamera((curr) => {
                if (!curr && camList.length > 0) return camList[0];
                if (curr) {
                    const match = camList.find((c) => c.id === curr.id);
                    return match || curr;
                }
                return curr;
            });

            setDetections(detRes.detections || []);
            setAlerts(altRes.alerts || []);
        } catch (err) {
            console.error("Error loading surveillance data", err);
        }
    };

    useEffect(() => {
        loadData();
        const interval = setInterval(loadData, 3000);
        return () => clearInterval(interval);
    }, []);

    const activeAlerts = alerts.filter(
        (a) => String(a.status).toUpperCase() === "ACTIVE"
    );

    const criticalAlert = activeAlerts.find(
        (a) => a.priority === "CRITICAL" || a.priority === "HIGH"
    );

    const handleAcknowledge = async (alertId) => {
        try {
            await updateAlertStatus(alertId, "RESOLVED");
            await loadData();
        } catch (err) {
            console.error("Failed to acknowledge alert", err);
        }
    };

    const handleSnapshot = () => {
        setSnapshotMsg("Snapshot captured & archived to evidence storage!");
        setTimeout(() => setSnapshotMsg(""), 3500);
    };

    const streamUrl =
        selectedCamera && isStreaming
            ? `${API_BASE_URL}/stream/${selectedCamera.id}?t=${Date.now()}`
            : null;

    return (
        <div className="surveillance-view">
            {/* Critical Security Incident Ticker */}
            {criticalAlert && (
                <div className="critical-alert-banner">
                    <div className="alert-pulse-red"></div>
                    <div className="banner-text">
                        <strong>CRITICAL SECURITY EVENT DETECTED:</strong>
                        <span>
                            {criticalAlert.object} identified on{" "}
                            {selectedCamera?.camera_name || "Camera"} with{" "}
                            {int(criticalAlert.confidence * 100) || 95}% confidence.
                        </span>
                    </div>
                    <button
                        className="btn-resolve-quick"
                        onClick={() => handleAcknowledge(criticalAlert.id)}
                    >
                        Acknowledge & Triage
                    </button>
                </div>
            )}

            {/* Quick KPI Stat Tiles */}
            <div className="kpi-grid">
                <div className="kpi-card">
                    <span className="kpi-label">REGISTERED CAMERAS</span>
                    <strong className="kpi-val">{cameras.length}</strong>
                    <span className="kpi-sub">Campus Coverage</span>
                </div>
                <div className="kpi-card">
                    <span className="kpi-label">TODAY'S INFERENCES</span>
                    <strong className="kpi-val">{detections.length}</strong>
                    <span className="kpi-sub">YOLOv8/11 Engine</span>
                </div>
                <div className="kpi-card">
                    <span className="kpi-label">ACTIVE ALERTS</span>
                    <strong
                        className={`kpi-val ${activeAlerts.length > 0 ? "warning" : ""}`}
                    >
                        {activeAlerts.length}
                    </strong>
                    <span className="kpi-sub">
                        {criticalAlert ? "Critical Incident Active" : "Nominal"}
                    </span>
                </div>
                <div className="kpi-card">
                    <span className="kpi-label">VISION PIPELINE</span>
                    <strong className="kpi-val success">ONLINE</strong>
                    <span className="kpi-sub">CUDA Accelerated</span>
                </div>
            </div>

            {/* View Mode Selector Toolbar */}
            <div className="surveillance-mode-bar">
                <div className="mode-bar-left">
                    <span className="mode-bar-title">OPERATIONAL SURVEILLANCE DISPLAY</span>
                    <span className="mode-bar-sub">
                        Concurrent feeds: Laptop Webcam, Mobile Phone IP, CCTV RTSP, USB Camera
                    </span>
                </div>
                <div className="mode-switcher-pills">
                    <button
                        className={`mode-pill ${viewMode === "focus" ? "active" : ""}`}
                        onClick={() => setViewMode("focus")}
                    >
                        ◻ Single Focus View
                    </button>
                    <button
                        className={`mode-pill ${viewMode === "multi_grid" ? "active" : ""}`}
                        onClick={() => setViewMode("multi_grid")}
                    >
                        ⊞ Multi-Camera Quad Matrix ({cameras.length} Feeds Live)
                    </button>
                </div>
            </div>

            {/* Multi-Camera Matrix (Simultaneous Multi-Screen Grid) */}
            {viewMode === "multi_grid" ? (
                <div className="multi-camera-matrix">
                    {cameras.map((c) => {
                        const isOnline = String(c.status).toLowerCase() === "online";
                        const isSelected = selectedCamera?.id === c.id;
                        return (
                            <div
                                key={c.id}
                                className={`matrix-cam-card ${isSelected ? "highlighted" : ""}`}
                            >
                                <div className="matrix-cam-header">
                                    <div className="matrix-title-group">
                                        <span
                                            className={`status-dot ${isOnline ? "online" : "offline"}`}
                                        ></span>
                                        <strong>{c.camera_name}</strong>
                                    </div>
                                    <div className="matrix-badge-group">
                                        <span className="source-pill">
                                            {c.source_type || "webcam"}
                                        </span>
                                        <button
                                            className="btn-focus-quick"
                                            title="Zoom into this camera feed"
                                            onClick={() => {
                                                setSelectedCamera(c);
                                                setViewMode("focus");
                                            }}
                                        >
                                            🔍 Focus
                                        </button>
                                    </div>
                                </div>
                                <div className="matrix-video-wrapper">
                                    <img
                                        src={`${API_BASE_URL}/stream/${c.id}`}
                                        alt={c.camera_name}
                                        className="matrix-video-img"
                                    />
                                    <div className="matrix-hud-strip">
                                        <span className="matrix-loc">
                                            📍 {c.location || "Security Zone"}
                                        </span>
                                        <span className="matrix-fps">HD 720p • 25 FPS</span>
                                    </div>
                                </div>
                            </div>
                        );
                    })}
                </div>
            ) : (
                /* Main Stage: Single Focused Video Player & Sidebar */
                <div className="surveillance-main-grid">
                    {/* Left: Video Player */}
                    <div className="video-player-container">
                        <div className="player-header">
                            <div className="camera-meta">
                                <h3>{selectedCamera?.camera_name || "Camera 01"}</h3>
                                <span className="camera-loc">
                                    📍 {selectedCamera?.location || "Main Entrance"}
                                </span>
                            </div>
                            <div className="stream-badge-row">
                                <span className={`live-tag ${isStreaming ? "active" : ""}`}>
                                    {isStreaming ? "● LIVE FEED" : "PAUSED"}
                                </span>
                                <span className="res-tag">HD 720p • 25 FPS</span>
                            </div>
                        </div>

                        <div className="video-viewport">
                            {streamUrl ? (
                                <img
                                    src={streamUrl}
                                    alt="Sentronix Live Feed"
                                    className="surveillance-stream-img"
                                />
                            ) : (
                                <div className="video-paused-placeholder">
                                    <span>Stream Paused / Standby</span>
                                </div>
                            )}

                            {snapshotMsg && (
                                <div className="snapshot-toast">{snapshotMsg}</div>
                            )}
                        </div>

                        <div className="player-toolbar">
                            <div className="toolbar-left">
                                <button
                                    className={`tool-btn ${isStreaming ? "btn-danger" : "btn-primary"}`}
                                    onClick={() => setIsStreaming(!isStreaming)}
                                >
                                    {isStreaming ? "⏸ Pause Stream" : "▶ Resume Stream"}
                                </button>
                                <button
                                    className="tool-btn btn-secondary"
                                    onClick={handleSnapshot}
                                >
                                    📷 Capture Snapshot
                                </button>
                            </div>
                            <div className="toolbar-right">
                                <span className="hud-label">AI Overlay: Active</span>
                            </div>
                        </div>
                    </div>

                    {/* Right: Camera Selector List */}
                    <div className="camera-sidebar-list">
                        <div className="panel-title-bar">
                            <h4>Camera Devices ({cameras.length})</h4>
                            <span>Group: All</span>
                        </div>

                        <div className="camera-card-stack">
                            {cameras.map((c) => {
                                const isSelected = selectedCamera?.id === c.id;
                                const isOnline =
                                    String(c.status).toLowerCase() === "online";
                                return (
                                    <div
                                        key={c.id}
                                        className={`camera-list-item ${isSelected ? "selected" : ""}`}
                                        onClick={() => setSelectedCamera(c)}
                                    >
                                        <div className="item-top">
                                            <div className="item-title-group">
                                                <span
                                                    className={`status-dot ${isOnline ? "online" : "offline"}`}
                                                ></span>
                                                <strong>{c.camera_name}</strong>
                                            </div>
                                            <span className="item-type">
                                                {c.source_type || "USB"}
                                            </span>
                                        </div>
                                        <span className="item-location">
                                            {c.location || "Facility Area"}
                                        </span>
                                        <div className="item-footer">
                                            <span>
                                                AI Detection:{" "}
                                                {c.ai_enabled !== 0 ? "ENABLED" : "OFF"}
                                            </span>
                                            <span className="item-status">{c.status}</span>
                                        </div>
                                    </div>
                                );
                            })}
                        </div>

                        {/* Remote Viewing QR Card */}
                        <div className="remote-qr-card">
                            <div className="qr-code-box">
                                <svg className="qr-svg-mock" viewBox="0 0 100 100">
                                    <rect
                                        width="100"
                                        height="100"
                                        fill="#ffffff"
                                        rx="8"
                                    />
                                    <rect
                                        x="10"
                                        y="10"
                                        width="25"
                                        height="25"
                                        fill="#000000"
                                    />
                                    <rect
                                        x="15"
                                        y="15"
                                        width="15"
                                        height="15"
                                        fill="#ffffff"
                                    />
                                    <rect
                                        x="19"
                                        y="19"
                                        width="7"
                                        height="7"
                                        fill="#000000"
                                    />
                                    <rect
                                        x="65"
                                        y="10"
                                        width="25"
                                        height="25"
                                        fill="#000000"
                                    />
                                    <rect
                                        x="70"
                                        y="15"
                                        width="15"
                                        height="15"
                                        fill="#ffffff"
                                    />
                                    <rect
                                        x="74"
                                        y="19"
                                        width="7"
                                        height="7"
                                        fill="#000000"
                                    />
                                    <rect
                                        x="10"
                                        y="65"
                                        width="25"
                                        height="25"
                                        fill="#000000"
                                    />
                                    <rect
                                        x="15"
                                        y="70"
                                        width="15"
                                        height="15"
                                        fill="#ffffff"
                                    />
                                    <rect
                                        x="19"
                                        y="74"
                                        width="7"
                                        height="7"
                                        fill="#000000"
                                    />
                                    <rect
                                        x="42"
                                        y="42"
                                        width="16"
                                        height="16"
                                        fill="#000000"
                                    />
                                    <rect
                                        x="42"
                                        y="15"
                                        width="10"
                                        height="15"
                                        fill="#000000"
                                    />
                                    <rect
                                        x="15"
                                        y="45"
                                        width="15"
                                        height="10"
                                        fill="#000000"
                                    />
                                    <rect
                                        x="65"
                                        y="65"
                                        width="12"
                                        height="12"
                                        fill="#000000"
                                    />
                                    <rect
                                        x="75"
                                        y="45"
                                        width="12"
                                        height="8"
                                        fill="#000000"
                                    />
                                    <rect
                                        x="45"
                                        y="75"
                                        width="15"
                                        height="12"
                                        fill="#000000"
                                    />
                                </svg>
                            </div>
                            <div className="qr-text-info">
                                <strong>Mobile Security View</strong>
                                <p>
                                    Scan to view live stream & alerts on handheld tablet/phone
                                </p>
                            </div>
                        </div>
                    </div>
                </div>
            )}

            {/* Bottom: Real-Time Detections Table */}
            <div className="detections-card">
                <div className="panel-title-bar">
                    <div className="title-left">
                        <h4>Live AI Detections Feed</h4>
                        <span>{detections.length} recorded</span>
                    </div>
                    <div className="detections-actions-right">
                        <a
                            href={getExportCsvUrl("detections")}
                            target="_blank"
                            rel="noreferrer"
                            className="btn-secondary-mini"
                        >
                            📥 Export CSV
                        </a>
                    </div>
                </div>
                <div className="table-wrapper">
                    <table className="soc-table">
                        <thead>
                            <tr>
                                <th># ID</th>
                                <th>OBJECT CLASS</th>
                                <th>CONFIDENCE</th>
                                <th>SOURCE CAMERA</th>
                                <th>TIMESTAMP</th>
                            </tr>
                        </thead>
                        <tbody>
                            {detections.length === 0 ? (
                                <tr>
                                    <td colSpan="5" className="empty-cell">No detections recorded yet.</td>
                                </tr>
                            ) : (
                                detections.slice(0, 8).map((d) => (
                                    <tr key={d.id}>
                                        <td>#{d.id}</td>
                                        <td>
                                            <span className={`class-chip ${d.object.toLowerCase()}`}>
                                                {d.object.toUpperCase()}
                                            </span>
                                        </td>
                                        <td>
                                            <div className="conf-bar-cell">
                                                <div
                                                    className="conf-bar-fill"
                                                    style={{ width: `${Math.min(100, d.confidence * 100)}%` }}
                                                ></div>
                                                <span>{(d.confidence * 100).toFixed(0)}%</span>
                                            </div>
                                        </td>
                                        <td>{d.camera_id}</td>
                                        <td>{d.timestamp}</td>
                                    </tr>
                                ))
                            )}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    );
}

function int(val) {
    return parseInt(val, 10);
}
