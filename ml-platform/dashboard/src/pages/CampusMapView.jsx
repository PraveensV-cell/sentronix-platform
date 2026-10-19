import { useState, useEffect } from "react";
import { getCameras, getAlerts } from "../api/api";

export default function CampusMapView() {
    const [cameras, setCameras] = useState([]);
    const [alerts, setAlerts] = useState([]);
    const [selectedZone, setSelectedZone] = useState("gate");
    const [viewMode, setViewMode] = useState("2D"); // '2D' | '3D'
    const [zoomLevel, setZoomLevel] = useState(100);

    const zones = [
        { id: "gate", name: "Main Gate & Entrance", totalCams: 2, activeCams: 2, status: "secure", coordinates: { top: "35%", left: "18%" } },
        { id: "academic", name: "Academic & Classroom Block", totalCams: 4, activeCams: 4, status: "secure", coordinates: { top: "25%", left: "48%" } },
        { id: "labs", name: "Science & Computer Labs", totalCams: 2, activeCams: 2, status: "secure", coordinates: { top: "45%", left: "68%" } },
        { id: "courtyard", name: "Central Walkway & Courtyard", totalCams: 3, activeCams: 3, status: "secure", coordinates: { top: "60%", left: "42%" } },
        { id: "lake", name: "Lake & Green Campus Area", totalCams: 2, activeCams: 2, status: "secure", coordinates: { top: "72%", left: "75%" } },
        { id: "parking", name: "Vehicle Parking & Perimeter", totalCams: 2, activeCams: 2, status: "alert", coordinates: { top: "80%", left: "20%" } },
    ];

    useEffect(() => {
        const load = async () => {
            try {
                const [camRes, altRes] = await Promise.all([getCameras(), getAlerts()]);
                setCameras(camRes.cameras || []);
                setAlerts(altRes.alerts || []);
            } catch (e) {
                console.error("Failed to load map data", e);
            }
        };
        load();
    }, []);

    const activeZone = zones.find((z) => z.id === selectedZone) || zones[0];
    const totalActiveCameras = zones.reduce((acc, z) => acc + z.activeCams, 0);

    return (
        <div className="campus-map-container">
            {/* Header info */}
            <div className="map-top-bar">
                <div>
                    <h2>Interactive Campus & Zone Tactical Map</h2>
                    <p>Real-time visual surveillance spatial telemetry and perimeter monitoring</p>
                </div>
                <div className="map-view-controls">
                    <div className="toggle-pill-group">
                        <button
                            className={`pill-btn ${viewMode === "2D" ? "active" : ""}`}
                            onClick={() => setViewMode("2D")}
                        >
                            2D Plan
                        </button>
                        <button
                            className={`pill-btn ${viewMode === "3D" ? "active" : ""}`}
                            onClick={() => setViewMode("3D")}
                        >
                            3D Aerial
                        </button>
                    </div>

                    <div className="zoom-controls">
                        <button onClick={() => setZoomLevel((z) => Math.max(70, z - 10))}>-</button>
                        <span>{zoomLevel}%</span>
                        <button onClick={() => setZoomLevel((z) => Math.min(150, z + 10))}>+</button>
                    </div>
                </div>
            </div>

            {/* Main Stage: Left Sidebar Zone Tree + Center Tactical Canvas */}
            <div className="campus-map-stage">
                {/* Left: Zone Tree Navigation */}
                <div className="map-zone-tree-sidebar">
                    <div className="tree-header">
                        <h4>Facility Sectors</h4>
                        <span className="total-cam-pill">{totalActiveCameras} Active Nodes</span>
                    </div>

                    <div className="tree-list">
                        {zones.map((zone) => {
                            const isSelected = selectedZone === zone.id;
                            const isAlert = zone.status === "alert";
                            return (
                                <div
                                    key={zone.id}
                                    className={`zone-tree-node ${isSelected ? "selected" : ""} ${isAlert ? "alert-state" : ""}`}
                                    onClick={() => setSelectedZone(zone.id)}
                                >
                                    <div className="node-title-row">
                                        <span className="node-indicator"></span>
                                        <strong>{zone.name}</strong>
                                    </div>
                                    <div className="node-meta-row">
                                        <span className={`cam-stat-tag ${isAlert ? "danger" : "normal"}`}>
                                            ● {zone.activeCams}/{zone.totalCams} active cameras
                                        </span>
                                        {isAlert && <span className="warning-pill">Threat Notice</span>}
                                    </div>
                                </div>
                            );
                        })}
                    </div>

                    <div className="operator-badge-card">
                        <div className="operator-avatar">👮</div>
                        <div className="operator-info">
                            <strong>Security Console #01</strong>
                            <span>Command Operator: Active</span>
                        </div>
                    </div>
                </div>

                {/* Center: Tactical Spatial Canvas */}
                <div className="map-canvas-wrapper">
                    <div
                        className={`map-blueprint-grid ${viewMode === "3D" ? "perspective-3d" : ""}`}
                        style={{ transform: `scale(${zoomLevel / 100})` }}
                    >
                        {/* Architectural Zone Blocks */}
                        <div className="building-block b-gate" onClick={() => setSelectedZone("gate")}>
                            <span>Main Entrance Gate</span>
                        </div>
                        <div className="building-block b-academic" onClick={() => setSelectedZone("academic")}>
                            <span>Classroom Complex A-B</span>
                        </div>
                        <div className="building-block b-labs" onClick={() => setSelectedZone("labs")}>
                            <span>Science & Tech Center</span>
                        </div>
                        <div className="building-block b-courtyard" onClick={() => setSelectedZone("courtyard")}>
                            <span>Central Courtyard</span>
                        </div>
                        <div className="building-block b-lake" onClick={() => setSelectedZone("lake")}>
                            <span>Campus Lake & Park</span>
                        </div>
                        <div className="building-block b-parking" onClick={() => setSelectedZone("parking")}>
                            <span>Perimeter & Parking</span>
                        </div>

                        {/* Interactive Zone Camera Pins */}
                        {zones.map((zone) => {
                            const isSelected = selectedZone === zone.id;
                            const isAlert = zone.status === "alert";
                            return (
                                <div
                                    key={zone.id}
                                    className={`map-pin-marker ${isSelected ? "selected-pin" : ""} ${isAlert ? "alert-pin" : ""}`}
                                    style={{ top: zone.coordinates.top, left: zone.coordinates.left }}
                                    onClick={() => setSelectedZone(zone.id)}
                                >
                                    <div className="pin-pulse-ring"></div>
                                    <div className="pin-core">
                                        <span>📹 {zone.activeCams}</span>
                                    </div>
                                    <div className="pin-tooltip">
                                        <strong>{zone.name}</strong>
                                        <span>{zone.activeCams} cameras online</span>
                                    </div>
                                </div>
                            );
                        })}

                        {/* Ground Compass & Scale HUD */}
                        <div className="map-hud-overlay">
                            <span className="scale-legend">━━━ 200 m</span>
                            <span className="grid-sub">SENTRONIX GEOSPATIAL ENGINE</span>
                        </div>
                    </div>

                    {/* Active Zone Detail Card Overlay */}
                    <div className="selected-zone-overlay-card">
                        <div className="zone-header">
                            <div>
                                <h3>{activeZone.name}</h3>
                                <span className="zone-telemetry">
                                    Status: {activeZone.status.toUpperCase()} • {activeZone.activeCams} Live Feeds Active
                                </span>
                            </div>
                            <span className={`status-pill ${activeZone.status}`}>
                                {activeZone.status === "alert" ? "Active Incident" : "Secure"}
                            </span>
                        </div>

                        <div className="zone-quick-streams">
                            <div className="mini-stream-box">
                                <div className="mini-stream-header">
                                    <span>CAM-01 • Sector View</span>
                                    <span className="live-dot-green">● LIVE</span>
                                </div>
                                <div className="mock-stream-display">
                                    <img
                                        src={`http://127.0.0.1:8000/stream/1`}
                                        alt="Stream Feed"
                                        className="stream-thumbnail"
                                    />
                                </div>
                            </div>
                            <div className="mini-stream-box">
                                <div className="mini-stream-header">
                                    <span>CAM-02 • Access Turnstile</span>
                                    <span className="live-dot-green">● LIVE</span>
                                </div>
                                <div className="mock-stream-display">
                                    <img
                                        src={`http://127.0.0.1:8000/stream/2`}
                                        alt="Stream Feed"
                                        className="stream-thumbnail"
                                    />
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}
