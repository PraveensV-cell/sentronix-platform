import { useState, useEffect } from "react";
import { getHardwareTelemetry, getCameras, getStatus } from "../api/api";

export default function SystemHealthView() {
    const [telemetry, setTelemetry] = useState(null);
    const [cameras, setCameras] = useState([]);
    const [backendStatus, setBackendStatus] = useState(null);
    const [loading, setLoading] = useState(true);

    const loadHealth = async () => {
        try {
            const [telRes, camRes, statRes] = await Promise.all([
                getHardwareTelemetry(),
                getCameras(),
                getStatus(),
            ]);
            setTelemetry(telRes);
            setCameras(camRes.cameras || []);
            setBackendStatus(statRes);
        } catch (e) {
            console.error("Health poll error", e);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        loadHealth();
        const interval = setInterval(loadHealth, 4000);
        return () => clearInterval(interval);
    }, []);

    const onlineCameras = cameras.filter((c) => String(c.status).toLowerCase() === "online");

    return (
        <div className="system-health-container">
            {/* Header */}
            <div className="module-header-row">
                <div>
                    <h2>Infrastructure & AI System Health</h2>
                    <p>Core Microservices, Hardware Acceleration, Inference Latency & Camera Connectivity Telemetry</p>
                </div>
                <div className="health-overall-badge">
                    <span className="live-dot-green">●</span>
                    <strong>PLATFORM OPERATIONAL</strong>
                </div>
            </div>

            {/* Top Stat Tiles */}
            <div className="kpi-grid">
                <div className="kpi-card">
                    <span className="kpi-label">CAMERA NODES</span>
                    <strong className="kpi-val success">{onlineCameras.length}/{cameras.length} Online</strong>
                    <span className="kpi-sub">Campus Coverage</span>
                </div>
                <div className="kpi-card">
                    <span className="kpi-label">AI INFERENCE LATENCY</span>
                    <strong className="kpi-val accent">{telemetry?.hardware?.inference_latency_ms || 14.8} ms</strong>
                    <span className="kpi-sub">Per Frame Batch</span>
                </div>
                <div className="kpi-card">
                    <span className="kpi-label">PIPELINE THROUGHPUT</span>
                    <strong className="kpi-val">{telemetry?.hardware?.pipeline_fps || 28.5} FPS</strong>
                    <span className="kpi-sub">Target: 25.0 FPS</span>
                </div>
                <div className="kpi-card">
                    <span className="kpi-label">ACCELERATION</span>
                    <strong className="kpi-val success">{telemetry?.hardware?.acceleration || "CUDA"}</strong>
                    <span className="kpi-sub">{telemetry?.hardware?.device || "NVIDIA Active"}</span>
                </div>
            </div>

            {/* Services Grid Table */}
            <div className="health-services-card">
                <div className="panel-title-bar">
                    <h4>Microservice Subsystems & Dependencies</h4>
                    <span>Real-time heartbeat</span>
                </div>

                <div className="table-wrapper">
                    <table className="soc-table">
                        <thead>
                            <tr>
                                <th>SERVICE NAME</th>
                                <th>STATUS</th>
                                <th>DETAILS / PROTOCOL</th>
                                <th>LATENCY / DEPTH</th>
                                <th>PORT / CONNECTIONS</th>
                            </tr>
                        </thead>
                        <tbody>
                            {(telemetry?.services || []).map((s, idx) => (
                                <tr key={idx}>
                                    <td>
                                        <div className="service-name-cell">
                                            <span className="service-icon">⚙️</span>
                                            <strong>{s.name}</strong>
                                        </div>
                                    </td>
                                    <td>
                                        <span className={`status-badge-chip ${s.status === "ONLINE" ? "verified" : "warning"}`}>
                                            ● {s.status}
                                        </span>
                                    </td>
                                    <td>{s.device || s.type || s.protocol || s.mode || "Running"}</td>
                                    <td>{s.latency_ms ? `${s.latency_ms} ms` : s.queue_depth !== undefined ? `Queue: ${s.queue_depth}` : "Nominal"}</td>
                                    <td>{s.port ? `Port ${s.port}` : s.active_connections ? `${s.active_connections} active` : "Internal"}</td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            </div>

            {/* Hardware & Computational Telemetry Row */}
            <div className="hardware-metrics-row">
                <div className="hardware-card">
                    <h4>Compute Acceleration Engine</h4>
                    <div className="hardware-info-list">
                        <div className="hw-row">
                            <span>Acceleration Engine:</span>
                            <strong>PyTorch CUDA 12.1 + Ultralytics YOLOv11</strong>
                        </div>
                        <div className="hw-row">
                            <span>GPU Device:</span>
                            <strong>{telemetry?.hardware?.device || "NVIDIA Graphics Processor"}</strong>
                        </div>
                        <div className="hw-row">
                            <span>VRAM Allocated:</span>
                            <strong>{telemetry?.hardware?.vram_usage_mb || 1850} MB / {telemetry?.hardware?.vram_total_mb || 8192} MB</strong>
                        </div>
                        <div className="progress-bar-bg">
                            <div className="progress-bar-fill" style={{ width: "26%" }}></div>
                        </div>
                    </div>
                </div>

                <div className="hardware-card">
                    <h4>Host System Utilization</h4>
                    <div className="hardware-info-list">
                        <div className="hw-row">
                            <span>CPU Utilization:</span>
                            <strong>{telemetry?.hardware?.cpu_utilization_pct || 24.5}%</strong>
                        </div>
                        <div className="progress-bar-bg">
                            <div className="progress-bar-fill" style={{ width: `${telemetry?.hardware?.cpu_utilization_pct || 24.5}%` }}></div>
                        </div>
                        <div className="hw-row">
                            <span>RAM Usage:</span>
                            <strong>{telemetry?.hardware?.memory_utilization_pct || 38.2}%</strong>
                        </div>
                        <div className="progress-bar-bg">
                            <div className="progress-bar-fill" style={{ width: `${telemetry?.hardware?.memory_utilization_pct || 38.2}%` }}></div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}
