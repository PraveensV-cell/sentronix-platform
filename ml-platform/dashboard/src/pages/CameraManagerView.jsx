import { useState, useEffect } from "react";
import { getCameras, createCamera } from "../api/api";

export default function CameraManagerView() {
    const [cameras, setCameras] = useState([]);
    const [showModal, setShowModal] = useState(false);
    const [name, setName] = useState("");
    const [location, setLocation] = useState("");
    const [sourceType, setSourceType] = useState("webcam");
    const [sourceUrl, setSourceUrl] = useState("0");

    const loadCameras = async () => {
        try {
            const res = await getCameras();
            setCameras(res.cameras || []);
        } catch (err) {
            console.error("Failed to load cameras", err);
        }
    };

    useEffect(() => {
        loadCameras();
    }, []);

    const handleAddCamera = async (e) => {
        e.preventDefault();
        try {
            const res = await createCamera({
                camera_id: `cam_${Date.now()}`,
                name,
                source: sourceUrl,
                camera_type: sourceType.toUpperCase(),
            });

            if (res.success) {
                setShowModal(false);
                setName("");
                setLocation("");
                await loadCameras();
            }
        } catch (err) {
            alert(err.response?.data?.detail || "Failed to add camera");
        }
    };

    return (
        <div className="cameras-module-container">
            <div className="module-header-row">
                <div>
                    <h2>Surveillance Camera & Hardware Management</h2>
                    <p>Configure RTSP Feeds, USB Webcams, and Synthetic Test Streams</p>
                </div>
                <button className="btn-primary" onClick={() => setShowModal(true)}>
                    + Register Camera Feed
                </button>
            </div>

            <div className="camera-devices-grid">
                {cameras.map((c) => {
                    const isOnline = String(c.status).toLowerCase() === "online";
                    return (
                        <div key={c.id} className="camera-device-card">
                            <div className="card-top-row">
                                <span className="device-id-tag">ID: {c.id}</span>
                                <span className={`status-pill ${isOnline ? "online" : "offline"}`}>
                                    <span className="status-dot"></span>
                                    {c.status}
                                </span>
                            </div>
                            <h3>{c.camera_name || c.name}</h3>
                            <p className="device-loc">📍 {c.location || "Surveillance Point"}</p>

                            <div className="device-specs-list">
                                <div className="spec-row">
                                    <span>SOURCE TYPE</span>
                                    <strong>{c.source_type || c.camera_type || "USB / Webcam"}</strong>
                                </div>
                                <div className="spec-row">
                                    <span>STREAM PATH</span>
                                    <code>{c.source_url || c.source || "/stream/0"}</code>
                                </div>
                                <div className="spec-row">
                                    <span>AI DETECTION</span>
                                    <strong className="text-success">ACTIVE (YOLO)</strong>
                                </div>
                            </div>
                        </div>
                    );
                })}
            </div>

            {/* Add Camera Modal */}
            {showModal && (
                <div className="modal-overlay">
                    <div className="modal-dialog">
                        <div className="modal-header">
                            <h3>Register Camera Feed</h3>
                            <button className="close-btn" onClick={() => setShowModal(false)}>×</button>
                        </div>
                        <form onSubmit={handleAddCamera} className="modal-form">
                            <div className="form-group">
                                <label>Camera Name</label>
                                <input
                                    type="text"
                                    placeholder="e.g. Science Lab Gate Cam"
                                    value={name}
                                    onChange={(e) => setName(e.target.value)}
                                    required
                                />
                            </div>
                            <div className="form-group">
                                <label>Location</label>
                                <input
                                    type="text"
                                    placeholder="e.g. Science Block Floor 1"
                                    value={location}
                                    onChange={(e) => setLocation(e.target.value)}
                                    required
                                />
                            </div>
                            <div className="form-group">
                                <label>Source Type</label>
                                <select value={sourceType} onChange={(e) => setSourceType(e.target.value)}>
                                    <option value="webcam">Local USB / Integrated Webcam</option>
                                    <option value="test_stream">Synthetic Test Stream (No Camera Hardware Needed)</option>
                                    <option value="rtsp">Network RTSP Camera</option>
                                    <option value="video_file">Pre-recorded MP4 File</option>
                                </select>
                            </div>
                            <div className="form-group">
                                <label>Stream URL / Device Index</label>
                                <input
                                    type="text"
                                    placeholder="0 for default webcam, or rtsp://192.168.1.100:554/stream"
                                    value={sourceUrl}
                                    onChange={(e) => setSourceUrl(e.target.value)}
                                    required
                                />
                            </div>
                            <div className="modal-actions">
                                <button type="button" className="btn-secondary" onClick={() => setShowModal(false)}>
                                    Cancel
                                </button>
                                <button type="submit" className="btn-primary">
                                    Save & Connect Camera
                                </button>
                            </div>
                        </form>
                    </div>
                </div>
            )}
        </div>
    );
}
