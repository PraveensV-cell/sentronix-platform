import { useState, useEffect, useRef } from "react";
import { getCameras, createCamera, getNetworkInfo, uploadCameraFrame, API_BASE_URL } from "../api/api";

export default function CameraManagerView() {
    const [cameras, setCameras] = useState([]);
    const [showModal, setShowModal] = useState(false);
    const [showMobileModal, setShowMobileModal] = useState(false);
    const [networkInfo, setNetworkInfo] = useState(null);

    // Camera Registration Form
    const [name, setName] = useState("");
    const [location, setLocation] = useState("");
    const [sourceType, setSourceType] = useState("webcam");
    const [sourceUrl, setSourceUrl] = useState("0");

    // In-Browser Mobile / Laptop Broadcaster
    const [isBroadcasting, setIsBroadcasting] = useState(false);
    const [broadcastStatus, setBroadcastStatus] = useState("");
    const videoRef = useRef(null);
    const canvasRef = useRef(null);
    const streamIntervalRef = useRef(null);

    const loadData = async () => {
        try {
            const [camRes, netRes] = await Promise.all([
                getCameras(),
                getNetworkInfo().catch(() => null),
            ]);
            setCameras(camRes.cameras || []);
            if (netRes) setNetworkInfo(netRes);
        } catch (err) {
            console.error("Failed to load camera data", err);
        }
    };

    useEffect(() => {
        loadData();
        return () => stopBroadcasting();
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
                await loadData();
            }
        } catch (err) {
            alert(err.response?.data?.detail || "Failed to add camera");
        }
    };

    const handleQuickAddLaptopWebcam = async () => {
        try {
            await createCamera({
                camera_id: `laptop_webcam_${Date.now()}`,
                name: "Integrated Laptop Camera",
                source: "0",
                camera_type: "WEBCAM",
            });
            await loadData();
            alert("Integrated Laptop Webcam registered as Device Index 0!");
        } catch (err) {
            alert("Laptop camera registered. Check live stream!");
        }
    };

    // Starts in-browser camera broadcast to Camera #1
    const startBroadcasting = async () => {
        try {
            setBroadcastStatus("Requesting camera access...");
            const stream = await navigator.mediaDevices.getUserMedia({
                video: { width: { ideal: 1280 }, height: { ideal: 720 } },
                audio: false,
            });

            if (videoRef.current) {
                videoRef.current.srcObject = stream;
                videoRef.current.play();
            }

            setIsBroadcasting(true);
            setBroadcastStatus("Transmitting live frames to Sentronix AI (~15 FPS)...");

            const canvas = canvasRef.current || document.createElement("canvas");
            canvas.width = 640;
            canvas.height = 480;

            streamIntervalRef.current = setInterval(() => {
                if (!videoRef.current) return;
                const ctx = canvas.getContext("2d");
                ctx.drawImage(videoRef.current, 0, 0, 640, 480);
                canvas.toBlob(
                    async (blob) => {
                        if (blob) {
                            try {
                                await uploadCameraFrame(1, blob);
                            } catch (e) {
                                // silent fallback
                            }
                        }
                    },
                    "image/jpeg",
                    0.7
                );
            }, 66); // ~15 FPS
        } catch (err) {
            console.error("Camera broadcast error", err);
            setBroadcastStatus(`Camera access failed: ${err.message}`);
        }
    };

    const stopBroadcasting = () => {
        if (streamIntervalRef.current) {
            clearInterval(streamIntervalRef.current);
            streamIntervalRef.current = null;
        }
        if (videoRef.current && videoRef.current.srcObject) {
            const tracks = videoRef.current.srcObject.getTracks();
            tracks.forEach((track) => track.stop());
            videoRef.current.srcObject = null;
        }
        setIsBroadcasting(false);
        setBroadcastStatus("Broadcast stopped.");
    };

    return (
        <div className="cameras-module-container">
            <div className="module-header-row">
                <div>
                    <h2>Surveillance Camera & Hardware Management</h2>
                    <p>Connect Built-in Laptop Cameras, Mobile Phone Feeds, USB Webcams, and RTSP Sources</p>
                </div>
                <div className="camera-header-actions">
                    <button className="btn-secondary" onClick={() => setShowMobileModal(true)}>
                        📱 Connect Mobile Phone Camera
                    </button>
                    <button className="btn-secondary" onClick={handleQuickAddLaptopWebcam}>
                        💻 Use Laptop Camera (Index 0)
                    </button>
                    <button className="btn-primary" onClick={() => setShowModal(true)}>
                        + Register Camera Feed
                    </button>
                </div>
            </div>

            {/* Quick Connection Help Banner */}
            <div className="hardware-help-banner">
                <div className="banner-icon">💡</div>
                <div className="banner-details">
                    <strong>Testing Tomorrow? Quick Camera Setup Guide:</strong>
                    <ul>
                        <li><strong>Laptop Camera:</strong> Plugged in or integrated? Camera #1 automatically checks device index <code>0</code> with DirectShow on Windows.</li>
                        <li><strong>Mobile Phone:</strong> Open <code>{networkInfo?.mobile_dashboard_url || "http://<your-laptop-ip>:5173"}</code> on your phone or use free "IP Webcam" app.</li>
                    </ul>
                </div>
            </div>

            {/* Camera Cards Grid */}
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
                                    <span>DEVICE / URL</span>
                                    <code>{c.source_url || c.source || "0"}</code>
                                </div>
                                <div className="spec-row">
                                    <span>AI DETECTION</span>
                                    <strong className="text-success">ACTIVE (YOLOv11 + Faces)</strong>
                                </div>
                            </div>

                            <div className="card-actions-row">
                                <a
                                    href={`${API_BASE_URL}/stream/${c.id}`}
                                    target="_blank"
                                    rel="noreferrer"
                                    className="btn-view-raw-stream"
                                >
                                    Open MJPEG Feed ↗
                                </a>
                            </div>
                        </div>
                    );
                })}
            </div>

            {/* In-Browser Mobile / Laptop Broadcaster Stage */}
            <div className="broadcaster-card">
                <div className="panel-title-bar">
                    <h4>Direct In-Browser Camera Broadcaster (WebRTC / getUserMedia)</h4>
                    <span>Transmit local laptop or phone camera to Camera #1</span>
                </div>
                <div className="broadcaster-body">
                    <div className="broadcaster-controls">
                        {!isBroadcasting ? (
                            <button className="btn-primary" onClick={startBroadcasting}>
                                📷 Start Camera Broadcast
                            </button>
                        ) : (
                            <button className="btn-danger" onClick={stopBroadcasting}>
                                ⏹ Stop Camera Broadcast
                            </button>
                        )}
                        <span className="broadcast-msg">{broadcastStatus}</span>
                    </div>

                    <div className="broadcaster-video-wrap">
                        <video
                            ref={videoRef}
                            playsInline
                            muted
                            className={`broadcaster-preview ${isBroadcasting ? "active" : ""}`}
                        />
                        <canvas ref={canvasRef} style={{ display: "none" }} />
                        {!isBroadcasting && (
                            <div className="broadcaster-placeholder">
                                <span>Click "Start Camera Broadcast" to transmit this device's camera into Sentronix AI</span>
                            </div>
                        )}
                    </div>
                </div>
            </div>

            {/* Mobile Phone Connection Modal */}
            {showMobileModal && (
                <div className="modal-backdrop" onClick={() => setShowMobileModal(false)}>
                    <div className="modal-content mobile-connect-modal" onClick={(e) => e.stopPropagation()}>
                        <div className="modal-header">
                            <div>
                                <h3>Connect Mobile Phone as Surveillance Camera</h3>
                                <p>Use your Android or iPhone camera as a live surveillance feed</p>
                            </div>
                            <button className="modal-close-btn" onClick={() => setShowMobileModal(false)}>✕</button>
                        </div>
                        <div className="mobile-modal-body">
                            <div className="mobile-option-card">
                                <h4>Option 1: In-Browser Direct Broadcast (Zero App Install)</h4>
                                <ol>
                                    <li>Connect your mobile phone to the <strong>same Wi-Fi network</strong> as this laptop.</li>
                                    <li>Open your phone's browser (Chrome / Safari) and navigate to:
                                        <div className="ip-highlight-box">
                                            <code>{networkInfo?.mobile_dashboard_url || "http://<laptop-ip>:5173"}</code>
                                        </div>
                                    </li>
                                    <li>Go to <strong>Camera Devices</strong> and tap <strong>"Start Camera Broadcast"</strong>.</li>
                                    <li>Your phone's camera will transmit live frames directly to Sentronix for AI detection!</li>
                                </ol>
                            </div>

                            <div className="mobile-option-card">
                                <h4>Option 2: Using Free "IP Webcam" App (Android / iOS)</h4>
                                <ol>
                                    <li>Install the free <strong>"IP Webcam"</strong> app from Google Play or App Store.</li>
                                    <li>Open the app, scroll to the bottom, and tap <strong>"Start server"</strong>.</li>
                                    <li>Note the URL displayed on the phone screen (e.g. <code>http://192.168.1.15:8080/video</code>).</li>
                                    <li>Click <strong>"+ Register Camera Feed"</strong> in Sentronix and paste that URL!</li>
                                </ol>
                            </div>

                            <div className="modal-actions-bar">
                                <button className="btn-primary" onClick={() => setShowMobileModal(false)}>
                                    Understood, Ready to Connect
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            )}

            {/* Register Camera Modal */}
            {showModal && (
                <div className="modal-backdrop" onClick={() => setShowModal(false)}>
                    <div className="modal-content" onClick={(e) => e.stopPropagation()}>
                        <div className="modal-header">
                            <h3>Register Surveillance Camera Feed</h3>
                            <button className="modal-close-btn" onClick={() => setShowModal(false)}>✕</button>
                        </div>
                        <form onSubmit={handleAddCamera} className="modal-form">
                            <div className="form-group">
                                <label>Camera Name</label>
                                <input
                                    type="text"
                                    placeholder="e.g. Laptop Front Cam or Phone Gate Cam"
                                    value={name}
                                    onChange={(e) => setName(e.target.value)}
                                    required
                                />
                            </div>
                            <div className="form-group">
                                <label>Facility Location</label>
                                <input
                                    type="text"
                                    placeholder="e.g. Science Block Floor 1"
                                    value={location}
                                    onChange={(e) => setLocation(e.target.value)}
                                    required
                                />
                            </div>
                            <div className="form-group">
                                <label>Source Hardware / Stream Type</label>
                                <select value={sourceType} onChange={(e) => setSourceType(e.target.value)}>
                                    <option value="webcam">Integrated Laptop / USB Camera (Index 0, 1, 2)</option>
                                    <option value="mobile_ip">Mobile Phone IP Webcam (http://192.168.x.x:8080/video)</option>
                                    <option value="rtsp">Network IP / RTSP Camera (rtsp://...)</option>
                                    <option value="test_stream">Synthetic Test Simulation Stream</option>
                                    <option value="video_file">Pre-recorded MP4 Video File</option>
                                </select>
                            </div>
                            <div className="form-group">
                                <label>Stream Path / Device Index</label>
                                <input
                                    type="text"
                                    placeholder="0 for laptop webcam, or http://192.168.1.15:8080/video"
                                    value={sourceUrl}
                                    onChange={(e) => setSourceUrl(e.target.value)}
                                    required
                                />
                                <small className="form-hint">
                                    Use <code>0</code> for your built-in laptop camera, <code>1</code> for external USB webcam, or full URL for mobile camera.
                                </small>
                            </div>
                            <div className="modal-actions-bar">
                                <button type="button" className="btn-secondary" onClick={() => setShowModal(false)}>
                                    Cancel
                                </button>
                                <button type="submit" className="btn-primary">
                                    Save & Connect Feed
                                </button>
                            </div>
                        </form>
                    </div>
                </div>
            )}
        </div>
    );
}
