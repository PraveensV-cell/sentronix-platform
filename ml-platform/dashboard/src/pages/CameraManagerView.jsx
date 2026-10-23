import { useState, useEffect, useRef } from "react";
import {
    getCameras,
    createCamera,
    assignCameraFunction,
    assignCameraSource,
    toggleCameraAi,
    getNetworkInfo,
    uploadCameraFrame,
    API_BASE_URL,
} from "../api/api";

const SECTORS = [
    { id: "all", label: "All Sectors (80)" },
    { id: 1, label: "Sector 1: Perimeter Fences" },
    { id: 2, label: "Sector 2: Main Gates & Turnstiles" },
    { id: 3, label: "Sector 3: Corridors & Walkways" },
    { id: 4, label: "Sector 4: Vaults & Laboratories" },
    { id: 5, label: "Sector 5: Operational Plants" },
    { id: 6, label: "Sector 6: Public Plazas" },
    { id: 7, label: "Sector 7: Logistics & Parking" },
];

const FUNCTIONS_CATALOG = [
    { id: "all", label: "All Functions", icon: "🌐" },
    { id: "FACE_ATTENDANCE", label: "Face Attendance", icon: "🎓", desc: "Face matching and student/staff attendance check-in" },
    { id: "DRESS_CODE", label: "Dress Code (Formals)", icon: "👔", desc: "School uniform & regular formals dress compliance check" },
    { id: "EXAM_MONITOR", label: "Exam Hall Proctoring", icon: "📝", desc: "Monitors exam halls, detects smartphones & cheating" },
    { id: "PERIMETER_INTRUSION", label: "Perimeter Intrusion", icon: "⛔", desc: "Boundary fence tripwire and sterile zone alerts" },
    { id: "DRESS_CODE_PPE", label: "Industrial PPE & Safety", icon: "🦺", desc: "Hardhat, high-vis vest & safety eyewear verification" },
    { id: "FIRE_SMOKE_HAZARD", label: "Fire & Hazard", icon: "🔥", desc: "Thermal heat, flame, smoke and chemical hazard alert" },
    { id: "CROWD_LOITERING", label: "Crowd & Loitering", icon: "👥", desc: "Congestion monitoring and dwell stagnation threshold" },
    { id: "WEAPON_VIOLENCE", label: "Weapon & Violence", icon: "🚨", desc: "Firearm, knife brandish and physical brawl alerts" },
    { id: "ANPR_VEHICLES", label: "Vehicle / ANPR", icon: "🚗", desc: "Vehicle license plate recognition and boom barrier gate" },
];

export default function CameraManagerView() {
    const [cameras, setCameras] = useState([]);
    const [filteredCameras, setFilteredCameras] = useState([]);
    const [selectedSector, setSelectedSector] = useState("all");
    const [selectedFunction, setSelectedFunction] = useState("all");
    const [searchQuery, setSearchQuery] = useState("");

    // Modals
    const [showRegisterModal, setShowRegisterModal] = useState(false);
    const [showMobileModal, setShowMobileModal] = useState(false);
    const [activeFunctionCam, setActiveFunctionCam] = useState(null);
    const [activeSourceCam, setActiveSourceCam] = useState(null);

    // Network & Broadcaster State
    const [networkInfo, setNetworkInfo] = useState(null);
    const [isBroadcasting, setIsBroadcasting] = useState(false);
    const [broadcastStatus, setBroadcastStatus] = useState("");
    const videoRef = useRef(null);
    const canvasRef = useRef(null);
    const streamIntervalRef = useRef(null);

    // Form inputs for modals
    const [targetFunction, setTargetFunction] = useState("FACE_ATTENDANCE");
    const [sourceType, setSourceType] = useState("webcam");
    const [sourceUrl, setSourceUrl] = useState("0");
    const [newLocation, setNewLocation] = useState("");

    // Register Form
    const [regName, setRegName] = useState("");
    const [regLoc, setRegLoc] = useState("");
    const [regGroup, setRegGroup] = useState(1);
    const [regFunc, setRegFunc] = useState("FACE_ATTENDANCE");
    const [regSrcType, setRegSrcType] = useState("webcam");
    const [regSrcUrl, setRegSrcUrl] = useState("0");

    const loadData = async () => {
        try {
            const [camRes, netRes] = await Promise.all([
                getCameras({ limit: 120 }),
                getNetworkInfo().catch(() => null),
            ]);
            setCameras(camRes.cameras || []);
            if (netRes) setNetworkInfo(netRes);
        } catch (err) {
            console.error("Failed to load camera fleet data", err);
        }
    };

    useEffect(() => {
        loadData();
        return () => stopBroadcasting();
    }, []);

    // Filter cameras based on Sector, Function, and Search
    useEffect(() => {
        let result = [...cameras];

        if (selectedSector !== "all") {
            result = result.filter((c) => Number(c.group_id) === Number(selectedSector));
        }

        if (selectedFunction !== "all") {
            result = result.filter(
                (c) => String(c.assigned_function).toUpperCase() === String(selectedFunction).toUpperCase()
            );
        }

        if (searchQuery.trim()) {
            const q = searchQuery.toLowerCase();
            result = result.filter(
                (c) =>
                    c.camera_name.toLowerCase().includes(q) ||
                    (c.location && c.location.toLowerCase().includes(q)) ||
                    (c.zone && c.zone.toLowerCase().includes(q)) ||
                    String(c.id).includes(q)
            );
        }

        setFilteredCameras(result);
    }, [cameras, selectedSector, selectedFunction, searchQuery]);

    // Assign Function Handler
    const handleSaveFunction = async () => {
        if (!activeFunctionCam) return;
        try {
            await assignCameraFunction(activeFunctionCam.id, targetFunction);
            setActiveFunctionCam(null);
            await loadData();
        } catch (err) {
            alert(err.response?.data?.detail || "Failed to update camera function");
        }
    };

    // Assign Source Handler
    const handleSaveSource = async () => {
        if (!activeSourceCam) return;
        try {
            await assignCameraSource(activeSourceCam.id, {
                source_type: sourceType,
                source_url: sourceUrl,
                location: newLocation || activeSourceCam.location,
            });
            setActiveSourceCam(null);
            await loadData();
        } catch (err) {
            alert(err.response?.data?.detail || "Failed to update camera source");
        }
    };

    // Toggle AI
    const handleToggleAi = async (camId) => {
        try {
            await toggleCameraAi(camId);
            await loadData();
        } catch (err) {
            alert("Failed to toggle AI processing");
        }
    };

    // Add New Camera
    const handleAddCamera = async (e) => {
        e.preventDefault();
        try {
            const res = await createCamera({
                name: regName,
                location: regLoc,
                group_id: Number(regGroup),
                assigned_function: regFunc,
                source_type: regSrcType,
                source_url: regSrcUrl,
            });
            if (res.success) {
                setShowRegisterModal(false);
                setRegName("");
                setRegLoc("");
                await loadData();
            }
        } catch (err) {
            alert(err.response?.data?.detail || "Failed to add camera");
        }
    };

    // In-browser broadacaster
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
                                // silent
                            }
                        }
                    },
                    "image/jpeg",
                    0.7
                );
            }, 66);
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

    const getFuncMeta = (funcId) => {
        return (
            FUNCTIONS_CATALOG.find(
                (f) => String(f.id).toUpperCase() === String(funcId).toUpperCase()
            ) || { label: funcId, icon: "🎯" }
        );
    };

    return (
        <div className="cameras-module-container">
            {/* Header */}
            <div className="module-header-row">
                <div>
                    <h2>Surveillance Fleet & Function Assignment (80 Cameras)</h2>
                    <p>Assign tactical operational functions and hardware video sources to every camera across 7 sectors.</p>
                </div>
                <div className="camera-header-actions">
                    <button className="btn-secondary" onClick={() => setShowMobileModal(true)}>
                        📱 Connect Mobile Camera
                    </button>
                    <button
                        className="btn-secondary"
                        onClick={() => {
                            // Assign Cam 1 to Laptop Webcam 0
                            assignCameraSource(1, { source_type: "webcam", source_url: "0", location: "Main Gate Alpha" });
                            alert("Camera #1 set to Laptop Built-In Camera (Index 0)!");
                            loadData();
                        }}
                    >
                        💻 Hook Laptop Cam (CAM-001)
                    </button>
                    <button className="btn-primary" onClick={() => setShowRegisterModal(true)}>
                        + Register Camera
                    </button>
                </div>
            </div>

            {/* Quick Fleet Telemetry Counters */}
            <div className="kpi-grid">
                <div className="kpi-card">
                    <span className="kpi-label">TOTAL FLEET</span>
                    <strong className="kpi-val">{cameras.length}</strong>
                    <span className="kpi-sub">Cameras Online</span>
                </div>
                <div className="kpi-card">
                    <span className="kpi-label">FILTERED RESULTS</span>
                    <strong className="kpi-val">{filteredCameras.length}</strong>
                    <span className="kpi-sub">Active Selection</span>
                </div>
                <div className="kpi-card">
                    <span className="kpi-label">TACTICAL SECTORS</span>
                    <strong className="kpi-val">7 Sectors</strong>
                    <span className="kpi-sub">Perimeter to Core</span>
                </div>
                <div className="kpi-card">
                    <span className="kpi-label">AI ENGINE ASSIGNMENTS</span>
                    <strong className="kpi-val success">100% ASSIGNED</strong>
                    <span className="kpi-sub">Neural Multi-Pipeline</span>
                </div>
            </div>

            {/* Sector Filtering Bar */}
            <div className="fleet-filter-card">
                <div className="filter-row-header">
                    <span>1. FILTER BY TACTICAL SECTOR / ZONE:</span>
                </div>
                <div className="filter-pills-row">
                    {SECTORS.map((s) => (
                        <button
                            key={s.id}
                            className={`filter-pill-btn ${selectedSector === s.id ? "active" : ""}`}
                            onClick={() => setSelectedSector(s.id)}
                        >
                            {s.label}
                        </button>
                    ))}
                </div>
            </div>

            {/* Function Filtering Bar & Search */}
            <div className="fleet-filter-card">
                <div className="filter-row-header space-between">
                    <span>2. FILTER BY ASSIGNED FUNCTION:</span>
                    <input
                        type="text"
                        placeholder="🔍 Search camera by ID, name, or room..."
                        className="fleet-search-input"
                        value={searchQuery}
                        onChange={(e) => setSearchQuery(e.target.value)}
                    />
                </div>
                <div className="filter-pills-row">
                    {FUNCTIONS_CATALOG.map((f) => (
                        <button
                            key={f.id}
                            className={`filter-pill-btn ${selectedFunction === f.id ? "active" : ""}`}
                            onClick={() => setSelectedFunction(f.id)}
                        >
                            <span>{f.icon}</span> {f.label}
                        </button>
                    ))}
                </div>
            </div>

            {/* Camera Cards Grid (80 Cameras Fleet) */}
            <div className="camera-devices-grid">
                {filteredCameras.map((c) => {
                    const isOnline = String(c.status).toLowerCase() === "online";
                    const funcMeta = getFuncMeta(c.assigned_function);
                    const isAiOn = c.ai_enabled !== 0;

                    return (
                        <div key={c.id} className="camera-device-card">
                            <div className="card-top-row">
                                <span className="device-id-tag">CAM #{String(c.id).padStart(3, "0")}</span>
                                <span className={`status-pill ${isOnline ? "online" : "offline"}`}>
                                    <span className="status-dot"></span>
                                    {c.status.toUpperCase()}
                                </span>
                            </div>

                            <h3 className="camera-card-title">{c.camera_name}</h3>
                            <p className="device-loc">
                                📍 {c.location || "Facility Zone"} • <strong>{c.group_name || `Sector ${c.group_id}`}</strong>
                            </p>

                            {/* Assigned Function Badge */}
                            <div className="assigned-func-banner">
                                <span className="func-icon">{funcMeta.icon}</span>
                                <div className="func-text">
                                    <span className="func-tag-label">ASSIGNED FUNCTION:</span>
                                    <strong>{funcMeta.label}</strong>
                                </div>
                            </div>

                            <div className="device-specs-list">
                                <div className="spec-row">
                                    <span>SOURCE TYPE</span>
                                    <strong>{c.source_type?.toUpperCase() || "WEBCAM"}</strong>
                                </div>
                                <div className="spec-row">
                                    <span>STREAM / DEVICE</span>
                                    <code>{c.source_url || "0"}</code>
                                </div>
                                <div className="spec-row">
                                    <span>AI PERCEPTION</span>
                                    <strong className={isAiOn ? "text-success" : "text-muted"}>
                                        {isAiOn ? "● ENABLED (Active)" : "○ DISABLED"}
                                    </strong>
                                </div>
                            </div>

                            {/* Operational Action Controls */}
                            <div className="camera-card-footer-buttons">
                                <button
                                    className="btn-action-pill func-btn"
                                    onClick={() => {
                                        setActiveFunctionCam(c);
                                        setTargetFunction(c.assigned_function || "FACE_ATTENDANCE");
                                    }}
                                >
                                    🎯 Reassign Function
                                </button>
                                <button
                                    className="btn-action-pill source-btn"
                                    onClick={() => {
                                        setActiveSourceCam(c);
                                        setSourceType(c.source_type || "webcam");
                                        setSourceUrl(c.source_url || "0");
                                        setNewLocation(c.location || "");
                                    }}
                                >
                                    ⚙️ Assign Source
                                </button>
                                <button
                                    className={`btn-action-pill ${isAiOn ? "ai-on" : "ai-off"}`}
                                    onClick={() => handleToggleAi(c.id)}
                                >
                                    {isAiOn ? "AI: ON" : "AI: OFF"}
                                </button>
                                <a
                                    href={`${API_BASE_URL}/stream/${c.id}`}
                                    target="_blank"
                                    rel="noreferrer"
                                    className="btn-action-pill view-btn"
                                >
                                    Feed ↗
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

            {/* Modal: Reassign Camera Function */}
            {activeFunctionCam && (
                <div className="modal-backdrop" onClick={() => setActiveFunctionCam(null)}>
                    <div className="modal-content function-assign-modal" onClick={(e) => e.stopPropagation()}>
                        <div className="modal-header">
                            <div>
                                <h3>Assign Tactical Function to {activeFunctionCam.camera_name}</h3>
                                <p>Select which AI perception model and safety rule pipeline executes on this camera stream.</p>
                            </div>
                            <button className="modal-close-btn" onClick={() => setActiveFunctionCam(null)}>✕</button>
                        </div>
                        <div className="function-picker-grid">
                            {FUNCTIONS_CATALOG.filter((f) => f.id !== "all").map((f) => {
                                const isSelected = targetFunction === f.id;
                                return (
                                    <div
                                        key={f.id}
                                        className={`func-option-card ${isSelected ? "selected" : ""}`}
                                        onClick={() => setTargetFunction(f.id)}
                                    >
                                        <div className="func-opt-header">
                                            <span className="opt-icon">{f.icon}</span>
                                            <strong>{f.label}</strong>
                                            <input type="radio" checked={isSelected} onChange={() => {}} />
                                        </div>
                                        <p>{f.desc}</p>
                                    </div>
                                );
                            })}
                        </div>
                        <div className="modal-actions-bar">
                            <button className="btn-secondary" onClick={() => setActiveFunctionCam(null)}>
                                Cancel
                            </button>
                            <button className="btn-primary" onClick={handleSaveFunction}>
                                Confirm Function Assignment
                            </button>
                        </div>
                    </div>
                </div>
            )}

            {/* Modal: Assign Video Source */}
            {activeSourceCam && (
                <div className="modal-backdrop" onClick={() => setActiveSourceCam(null)}>
                    <div className="modal-content" onClick={(e) => e.stopPropagation()}>
                        <div className="modal-header">
                            <div>
                                <h3>Assign Hardware Source to {activeSourceCam.camera_name}</h3>
                                <p>Map this camera to your Laptop Built-In Camera, Mobile Phone stream, or RTSP feed.</p>
                            </div>
                            <button className="modal-close-btn" onClick={() => setActiveSourceCam(null)}>✕</button>
                        </div>
                        <div className="modal-form">
                            <div className="quick-source-buttons">
                                <span>Quick 1-Click Source Presets:</span>
                                <div className="preset-row">
                                    <button
                                        type="button"
                                        className="btn-secondary small"
                                        onClick={() => { setSourceType("webcam"); setSourceUrl("0"); }}
                                    >
                                        💻 Built-In Laptop Webcam (0)
                                    </button>
                                    <button
                                        type="button"
                                        className="btn-secondary small"
                                        onClick={() => { setSourceType("webcam"); setSourceUrl("1"); }}
                                    >
                                        🔌 External USB Webcam (1)
                                    </button>
                                    <button
                                        type="button"
                                        className="btn-secondary small"
                                        onClick={() => { setSourceType("mobile_ip"); setSourceUrl("http://192.168.1.50:8080/video"); }}
                                    >
                                        📱 Phone IP Webcam
                                    </button>
                                </div>
                            </div>

                            <div className="form-group">
                                <label>Hardware / Stream Type</label>
                                <select value={sourceType} onChange={(e) => setSourceType(e.target.value)}>
                                    <option value="webcam">Integrated Laptop / USB Camera (Index 0, 1, 2)</option>
                                    <option value="mobile_ip">Mobile Phone IP Webcam (http://...)</option>
                                    <option value="rtsp">Network RTSP CCTV Stream (rtsp://...)</option>
                                    <option value="test_stream">Synthetic Test Simulation Feed</option>
                                </select>
                            </div>
                            <div className="form-group">
                                <label>Device Index / Stream URL</label>
                                <input
                                    type="text"
                                    value={sourceUrl}
                                    onChange={(e) => setSourceUrl(e.target.value)}
                                    placeholder="0 for laptop webcam, or http://192.168.x.x:8080/video"
                                    required
                                />
                            </div>
                            <div className="form-group">
                                <label>Location Description</label>
                                <input
                                    type="text"
                                    value={newLocation}
                                    onChange={(e) => setNewLocation(e.target.value)}
                                    placeholder="e.g. Science Lab Checkpoint"
                                />
                            </div>
                            <div className="modal-actions-bar">
                                <button className="btn-secondary" onClick={() => setActiveSourceCam(null)}>
                                    Cancel
                                </button>
                                <button className="btn-primary" onClick={handleSaveSource}>
                                    Save & Connect Hardware
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            )}

            {/* Modal: Connect Mobile Phone Camera Guide */}
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
                                    <li>Click <strong>"⚙️ Assign Source"</strong> on any camera and paste that URL!</li>
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

            {/* Modal: Register Custom Camera */}
            {showRegisterModal && (
                <div className="modal-backdrop" onClick={() => setShowRegisterModal(false)}>
                    <div className="modal-content" onClick={(e) => e.stopPropagation()}>
                        <div className="modal-header">
                            <h3>Register Surveillance Camera Feed</h3>
                            <button className="modal-close-btn" onClick={() => setShowRegisterModal(false)}>✕</button>
                        </div>
                        <form onSubmit={handleAddCamera} className="modal-form">
                            <div className="form-group">
                                <label>Camera Name</label>
                                <input
                                    type="text"
                                    placeholder="e.g. CAM-081 [West Perimeter Sentry]"
                                    value={regName}
                                    onChange={(e) => setRegName(e.target.value)}
                                    required
                                />
                            </div>
                            <div className="form-group">
                                <label>Facility Location</label>
                                <input
                                    type="text"
                                    placeholder="e.g. Perimeter Gate West"
                                    value={regLoc}
                                    onChange={(e) => setRegLoc(e.target.value)}
                                    required
                                />
                            </div>
                            <div className="form-group">
                                <label>Tactical Sector</label>
                                <select value={regGroup} onChange={(e) => setRegGroup(e.target.value)}>
                                    <option value={1}>Sector 1: Perimeter Fences</option>
                                    <option value={2}>Sector 2: Main Gates & Turnstiles</option>
                                    <option value={3}>Sector 3: Corridors & Walkways</option>
                                    <option value={4}>Sector 4: Vaults & Laboratories</option>
                                    <option value={5}>Sector 5: Operational Plants</option>
                                    <option value={6}>Sector 6: Public Plazas</option>
                                    <option value={7}>Sector 7: Logistics & Parking</option>
                                </select>
                            </div>
                            <div className="form-group">
                                <label>Assigned Tactical Function</label>
                                <select value={regFunc} onChange={(e) => setRegFunc(e.target.value)}>
                                    <option value="FACE_ATTENDANCE">Face Attendance</option>
                                    <option value="PERIMETER_INTRUSION">Perimeter Intrusion</option>
                                    <option value="DRESS_CODE_PPE">Dress Code & PPE Compliance</option>
                                    <option value="FIRE_SMOKE_HAZARD">Fire & Smoke Hazard</option>
                                    <option value="CROWD_LOITERING">Crowd & Loitering Alert</option>
                                    <option value="WEAPON_VIOLENCE">Weapon & Violence Alert</option>
                                    <option value="ANPR_VEHICLES">Vehicle / ANPR Access</option>
                                </select>
                            </div>
                            <div className="form-group">
                                <label>Source Hardware / Stream Type</label>
                                <select value={regSrcType} onChange={(e) => setRegSrcType(e.target.value)}>
                                    <option value="webcam">Integrated Laptop / USB Camera (Index 0, 1)</option>
                                    <option value="mobile_ip">Mobile Phone IP Webcam</option>
                                    <option value="rtsp">Network IP / RTSP Camera</option>
                                    <option value="test_stream">Synthetic Test Simulation Stream</option>
                                </select>
                            </div>
                            <div className="form-group">
                                <label>Stream Path / Device Index</label>
                                <input
                                    type="text"
                                    placeholder="0 for laptop webcam, or http://192.168.1.15:8080/video"
                                    value={regSrcUrl}
                                    onChange={(e) => setRegSrcUrl(e.target.value)}
                                    required
                                />
                            </div>
                            <div className="modal-actions-bar">
                                <button type="button" className="btn-secondary" onClick={() => setShowRegisterModal(false)}>
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
