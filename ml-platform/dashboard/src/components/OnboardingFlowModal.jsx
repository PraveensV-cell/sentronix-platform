import { useState, useEffect } from "react";
import { createPeopleBatch, createCamera } from "../api/api";

const compressImage = (file) => {
    return new Promise((resolve) => {
        const reader = new FileReader();
        reader.readAsDataURL(file);
        reader.onload = (e) => {
            const img = new Image();
            img.src = e.target.result;
            img.onload = () => {
                const canvas = document.createElement("canvas");
                let w = img.width;
                let h = img.height;
                const maxDim = 640;
                if (w > h && w > maxDim) {
                    h = Math.round((h * maxDim) / w);
                    w = maxDim;
                } else if (h > maxDim) {
                    w = Math.round((w * maxDim) / h);
                    h = maxDim;
                }
                canvas.width = w;
                canvas.height = h;
                const ctx = canvas.getContext("2d");
                ctx.drawImage(img, 0, 0, w, h);
                resolve(canvas.toDataURL("image/jpeg", 0.92));
            };
            img.onerror = () => resolve(e.target.result);
        };
        reader.onerror = () => resolve("");
    });
};

const MODE_LABELS = {
    School: { rosterTitle: "Students & Academic Faculty Dataset", defaultRole: "student", roles: ["student", "staff", "visitor"] },
    Military: { rosterTitle: "Tactical Officers & Sentry Personals Dataset", defaultRole: "officer", roles: ["officer", "sentry", "commander"] },
    Industry: { rosterTitle: "Plant Workers & Machinery Operators Dataset", defaultRole: "worker", roles: ["worker", "engineer", "auditor"] },
    Hospital: { rosterTitle: "Public Staff, Responders & Medical Dataset", defaultRole: "staff", roles: ["doctor", "nurse", "guard", "staff"] },
    Corporate: { rosterTitle: "Enterprise Staff & Associates Dataset", defaultRole: "employee", roles: ["employee", "executive", "visitor"] },
};

export default function OnboardingFlowModal({ environment, isOpen, onClose, onLaunchLive }) {
    const [step, setStep] = useState(1); // 1: Dataset, 2: Camera Name & Location, 3: Stream Source, 4: Function Assignment & Launch
    const [peopleList, setPeopleList] = useState([]);

    // Single person form state
    const [name, setName] = useState("");
    const [identifier, setIdentifier] = useState("");
    const [role, setRole] = useState("student");
    const [department, setDepartment] = useState("");
    const [allowedDress, setAllowedDress] = useState("Regular School Uniform & Formals");
    const [phone, setPhone] = useState("");
    const [email, setEmail] = useState("");
    const [photoUrl, setPhotoUrl] = useState("");

    // Camera settings
    const [cameraName, setCameraName] = useState("Sector Entrance Checkpoint Cam 01");
    const [cameraLocation, setCameraLocation] = useState("Main Gate Checkpoint");
    const [streamType, setStreamType] = useState("laptop_webcam");
    const [externalDevices, setExternalDevices] = useState([]);
    const [selectedDeviceId, setSelectedDeviceId] = useState("");
    const [networkUrl, setNetworkUrl] = useState("rtsp://192.168.1.100:554/stream1");
    const [assignedFunction, setAssignedFunction] = useState("FACE_ATTENDANCE");
    const [isSubmitting, setIsSubmitting] = useState(false);
    const [errorMsg, setErrorMsg] = useState("");

    const modeType = environment?.type || "School";
    const modeMeta = MODE_LABELS[modeType] || MODE_LABELS.School;

    useEffect(() => {
        setRole(modeMeta.defaultRole);
    }, [modeType]);

    // Scan external video ports
    useEffect(() => {
        if (navigator.mediaDevices && navigator.mediaDevices.enumerateDevices) {
            navigator.mediaDevices.enumerateDevices().then((devices) => {
                const videoInputs = devices.filter((d) => d.kind === "videoinput");
                setExternalDevices(videoInputs);
                if (videoInputs.length > 0 && !selectedDeviceId) {
                    setSelectedDeviceId(videoInputs[0].deviceId);
                }
            }).catch(() => {});
        }
    }, [streamType]);

    if (!isOpen) return null;

    const handlePhotoUpload = async (e) => {
        const file = e.target.files?.[0];
        if (file) {
            const compressed = await compressImage(file);
            setPhotoUrl(compressed);
        }
    };

    const handleAddPerson = (e) => {
        e.preventDefault();
        if (!name.trim() || !identifier.trim()) {
            setErrorMsg("Full Name and Unique ID are required to register an individual.");
            return;
        }
        if (!photoUrl) {
            setErrorMsg("High-resolution face photo is mandatory for biometric verification.");
            return;
        }

        setErrorMsg("");
        const newPerson = {
            name: name.trim(),
            identifier: identifier.trim(),
            role,
            department: department.trim() || "General",
            class_grade: "Verified Member",
            allowed_dress: allowedDress.trim() || "Formals",
            phone: phone.trim(),
            email: email.trim(),
            photo_url: photoUrl,
        };

        setPeopleList([...peopleList, newPerson]);
        setName("");
        setIdentifier("");
        setDepartment("");
        setPhone("");
        setEmail("");
        setPhotoUrl("");
    };

    const handleRemovePerson = (idx) => {
        setPeopleList(peopleList.filter((_, i) => i !== idx));
    };

    const handleFinalLaunch = async () => {
        if (peopleList.length < 3) {
            setErrorMsg(`Please add at least 3 individual profiles with photos (currently added: ${peopleList.length}).`);
            return;
        }
        setIsSubmitting(true);
        setErrorMsg("");
        try {
            const envId = environment?.id || 1;
            // 1. Batch save people and initialize physical folders
            await createPeopleBatch(peopleList, envId);

            // 2. Create the assigned camera
            const sourceUrl = streamType === "laptop_webcam" ? "0" : (streamType === "external_usb" ? (selectedDeviceId || "1") : networkUrl);
            const sourceType = streamType === "laptop_webcam" ? "webcam" : (streamType === "external_usb" ? "usb_port" : "mobile_ip");

            const camRes = await createCamera({
                environment_id: envId,
                camera_name: cameraName,
                location: cameraLocation,
                zone: "Sector Alpha",
                source_type: sourceType,
                source_url: sourceUrl,
                assigned_function: assignedFunction,
                ai_enabled: 1,
            });

            if (onLaunchLive) {
                onLaunchLive({
                    camera: camRes.camera || { id: 1, camera_name: cameraName, assigned_function: assignedFunction },
                    streamType,
                    selectedDeviceId,
                });
            }
            onClose();
        } catch (err) {
            console.error("Onboarding error:", err);
            setErrorMsg(err.response?.data?.detail || "Could not complete setup.");
        } finally {
            setIsSubmitting(false);
        }
    };

    return (
        <div style={{ position: "fixed", inset: 0, background: "rgba(0,0,0,0.75)", zIndex: 10000, display: "flex", alignItems: "center", justifyContent: "center", padding: "16px" }}>
            <div style={{ background: "var(--card-bg)", border: "1px solid var(--border-color)", borderRadius: "10px", width: "100%", maxWidth: "860px", maxHeight: "90vh", overflowY: "auto", boxShadow: "0 14px 40px rgba(0,0,0,0.5)" }}>
                {/* Header */}
                <div style={{ padding: "18px 24px", borderBottom: "1px solid var(--border-color)", display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                    <div>
                        <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                            <span style={{ fontSize: "20px" }}>🛡️</span>
                            <h3 style={{ margin: 0, fontSize: "17px", fontWeight: 700, color: "var(--text-primary)" }}>
                                VANTEP AI Setup &amp; Dataset Deployment
                            </h3>
                        </div>
                        <p style={{ margin: "3px 0 0 0", fontSize: "12px", color: "var(--text-muted)" }}>
                            Selected Mode: <strong style={{ color: "var(--primary-color)" }}>{environment?.name || "Surveillance Mode"}</strong> • Step {step} of 4
                        </p>
                    </div>
                    <button type="button" onClick={onClose} style={{ background: "transparent", border: "none", fontSize: "18px", cursor: "pointer", color: "var(--text-muted)" }}>✕</button>
                </div>

                {/* Step Indicator Strip */}
                <div style={{ display: "flex", padding: "10px 24px", background: "var(--bg-secondary)", gap: "8px", borderBottom: "1px solid var(--border-color)" }}>
                    {[
                        { num: 1, label: "1. Dataset Input (Min 3)" },
                        { num: 2, label: "2. Camera Identity" },
                        { num: 3, label: "3. Video Source (USB/IP)" },
                        { num: 4, label: "4. Function Assignment" },
                    ].map((s) => (
                        <div
                            key={s.num}
                            style={{
                                flex: 1,
                                padding: "6px 10px",
                                borderRadius: "4px",
                                fontSize: "11px",
                                fontWeight: 700,
                                textAlign: "center",
                                background: step === s.num ? "var(--primary-color)" : (step > s.num ? "var(--bg-panel)" : "transparent"),
                                color: step === s.num ? "#ffffff" : (step > s.num ? "var(--success-color)" : "var(--text-muted)"),
                                border: step === s.num ? "none" : "1px solid var(--border-color)",
                            }}
                        >
                            {step > s.num ? "✓ " : ""}{s.label}
                        </div>
                    ))}
                </div>

                {errorMsg && (
                    <div style={{ margin: "16px 24px 0 24px", padding: "10px 14px", borderRadius: "6px", background: "rgba(220, 38, 38, 0.12)", border: "1px solid var(--danger-color)", color: "var(--danger-color)", fontSize: "12px", fontWeight: 600 }}>
                        {errorMsg}
                    </div>
                )}

                <div style={{ padding: "20px 24px" }}>
                    {/* ─── STEP 1: DATASET INPUT ─────────────────────────────────────── */}
                    {step === 1 && (
                        <div>
                            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "14px" }}>
                                <div>
                                    <h4 style={{ margin: 0, fontSize: "14px", fontWeight: 700, color: "var(--text-primary)" }}>
                                        {modeMeta.rosterTitle}
                                    </h4>
                                    <p style={{ margin: "2px 0 0 0", fontSize: "11px", color: "var(--text-muted)" }}>
                                        Add at least 3 individuals with clean resolution face photos. VANTEP AI will create a dedicated physical folder for each individual.
                                    </p>
                                </div>
                                <span style={{ fontSize: "11px", fontWeight: 700, color: peopleList.length >= 3 ? "var(--success-color)" : "var(--warning-color)", background: "var(--bg-secondary)", padding: "4px 10px", borderRadius: "4px" }}>
                                    {peopleList.length} of 3 Enrolled (Minimum 3 required)
                                </span>
                            </div>

                            {/* Person Form */}
                            <form onSubmit={handleAddPerson} style={{ background: "var(--bg-secondary)", padding: "14px", borderRadius: "8px", border: "1px solid var(--border-color)", marginBottom: "16px" }}>
                                <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "10px", marginBottom: "10px" }}>
                                    <div>
                                        <label style={{ display: "block", fontSize: "11px", fontWeight: 700, color: "var(--text-muted)", marginBottom: "3px" }}>Full Name *</label>
                                        <input type="text" value={name} onChange={(e) => setName(e.target.value)} placeholder="Full Name" style={{ width: "100%", padding: "6px 10px", borderRadius: "4px", border: "1px solid var(--border-color)", background: "var(--card-bg)", color: "var(--text-primary)", fontSize: "12px" }} />
                                    </div>
                                    <div>
                                        <label style={{ display: "block", fontSize: "11px", fontWeight: 700, color: "var(--text-muted)", marginBottom: "3px" }}>Unique ID (Student / Staff / Worker ID) *</label>
                                        <input type="text" value={identifier} onChange={(e) => setIdentifier(e.target.value)} placeholder="e.g. STU-101" style={{ width: "100%", padding: "6px 10px", borderRadius: "4px", border: "1px solid var(--border-color)", background: "var(--card-bg)", color: "var(--text-primary)", fontSize: "12px" }} />
                                    </div>
                                </div>

                                <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "10px", marginBottom: "10px" }}>
                                    <div>
                                        <label style={{ display: "block", fontSize: "11px", fontWeight: 700, color: "var(--text-muted)", marginBottom: "3px" }}>Role</label>
                                        <select value={role} onChange={(e) => setRole(e.target.value)} style={{ width: "100%", padding: "6px 10px", borderRadius: "4px", border: "1px solid var(--border-color)", background: "var(--card-bg)", color: "var(--text-primary)", fontSize: "12px" }}>
                                            {modeMeta.roles.map((r) => (
                                                <option key={r} value={r}>{r.toUpperCase()}</option>
                                            ))}
                                        </select>
                                    </div>
                                    <div>
                                        <label style={{ display: "block", fontSize: "11px", fontWeight: 700, color: "var(--text-muted)", marginBottom: "3px" }}>Department / Class</label>
                                        <input type="text" value={department} onChange={(e) => setDepartment(e.target.value)} placeholder="e.g. Computer Science" style={{ width: "100%", padding: "6px 10px", borderRadius: "4px", border: "1px solid var(--border-color)", background: "var(--card-bg)", color: "var(--text-primary)", fontSize: "12px" }} />
                                    </div>
                                </div>

                                <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "10px", marginBottom: "12px" }}>
                                    <div>
                                        <label style={{ display: "block", fontSize: "11px", fontWeight: 700, color: "var(--text-muted)", marginBottom: "3px" }}>Allowed Dress Code</label>
                                        <input type="text" value={allowedDress} onChange={(e) => setAllowedDress(e.target.value)} placeholder="Regular School Uniform & Formals" style={{ width: "100%", padding: "6px 10px", borderRadius: "4px", border: "1px solid var(--border-color)", background: "var(--card-bg)", color: "var(--text-primary)", fontSize: "12px" }} />
                                    </div>
                                    <div>
                                        <label style={{ display: "block", fontSize: "11px", fontWeight: 700, color: "var(--text-muted)", marginBottom: "3px" }}>Clean Face Photo * (Mandatory)</label>
                                        <div style={{ display: "flex", gap: "8px", alignItems: "center" }}>
                                            {photoUrl && <img src={photoUrl} alt="Thumb" style={{ width: "32px", height: "32px", borderRadius: "4px", objectFit: "cover", border: "1px solid var(--success-color)" }} />}
                                            <input type="file" accept="image/*" onChange={handlePhotoUpload} style={{ fontSize: "11px", color: "var(--text-primary)" }} />
                                        </div>
                                    </div>
                                </div>

                                <button type="submit" style={{ background: "var(--primary-color)", color: "#ffffff", padding: "7px 16px", borderRadius: "4px", fontSize: "12px", fontWeight: 700 }}>
                                    + Add Person to Dataset
                                </button>
                            </form>

                            {/* Enrolled People Table */}
                            {peopleList.length > 0 && (
                                <div style={{ marginBottom: "16px" }}>
                                    <div style={{ fontSize: "12px", fontWeight: 700, color: "var(--text-primary)", marginBottom: "6px" }}>
                                        Enrolled Profiles for Upload ({peopleList.length})
                                    </div>
                                    <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(220px, 1fr))", gap: "8px" }}>
                                        {peopleList.map((p, idx) => (
                                            <div key={idx} style={{ background: "var(--card-bg)", border: "1px solid var(--border-color)", borderRadius: "6px", padding: "8px 10px", display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                                                <div style={{ display: "flex", gap: "8px", alignItems: "center" }}>
                                                    <img src={p.photo_url} alt="" style={{ width: "34px", height: "34px", borderRadius: "4px", objectFit: "cover", border: "1px solid var(--border-color)" }} />
                                                    <div>
                                                        <div style={{ fontSize: "12px", fontWeight: 700, color: "var(--text-primary)" }}>{p.name}</div>
                                                        <div style={{ fontSize: "10px", color: "var(--text-muted)" }}>{p.identifier} • {p.role}</div>
                                                    </div>
                                                </div>
                                                <button type="button" onClick={() => handleRemovePerson(idx)} style={{ background: "transparent", border: "none", color: "var(--danger-color)", cursor: "pointer", fontSize: "14px" }}>✕</button>
                                            </div>
                                        ))}
                                    </div>
                                </div>
                            )}

                            <div style={{ display: "flex", justifyContent: "flex-end" }}>
                                <button
                                    type="button"
                                    disabled={peopleList.length < 3}
                                    onClick={() => { setErrorMsg(""); setStep(2); }}
                                    style={{
                                        background: peopleList.length >= 3 ? "var(--primary-color)" : "var(--bg-secondary)",
                                        color: peopleList.length >= 3 ? "#ffffff" : "var(--text-muted)",
                                        padding: "8px 20px",
                                        borderRadius: "4px",
                                        fontSize: "12px",
                                        fontWeight: 700,
                                        cursor: peopleList.length >= 3 ? "pointer" : "not-allowed",
                                    }}
                                >
                                    Proceed to Camera Assignment →
                                </button>
                            </div>
                        </div>
                    )}

                    {/* ─── STEP 2: CAMERA IDENTITY ──────────────────────────────────── */}
                    {step === 2 && (
                        <div>
                            <h4 style={{ margin: "0 0 6px 0", fontSize: "14px", fontWeight: 700, color: "var(--text-primary)" }}>
                                Camera Naming &amp; Sector Assignment
                            </h4>
                            <p style={{ margin: "0 0 16px 0", fontSize: "11px", color: "var(--text-muted)" }}>
                                Assign a name and location to this primary camera. You can assign up to 80–100 independent cameras in this mode.
                            </p>

                            <div style={{ marginBottom: "14px" }}>
                                <label style={{ display: "block", fontSize: "11px", fontWeight: 700, color: "var(--text-muted)", marginBottom: "4px" }}>Camera Name *</label>
                                <input type="text" value={cameraName} onChange={(e) => setCameraName(e.target.value)} required placeholder="e.g. Main Entrance Checkpoint Cam 01" style={{ width: "100%", padding: "8px 12px", borderRadius: "4px", border: "1px solid var(--border-color)", background: "var(--bg-secondary)", color: "var(--text-primary)", fontSize: "13px" }} />
                            </div>

                            <div style={{ marginBottom: "18px" }}>
                                <label style={{ display: "block", fontSize: "11px", fontWeight: 700, color: "var(--text-muted)", marginBottom: "4px" }}>Surveillance Location / Zone *</label>
                                <input type="text" value={cameraLocation} onChange={(e) => setCameraLocation(e.target.value)} required placeholder="e.g. Turnstile Gate Alpha" style={{ width: "100%", padding: "8px 12px", borderRadius: "4px", border: "1px solid var(--border-color)", background: "var(--bg-secondary)", color: "var(--text-primary)", fontSize: "13px" }} />
                            </div>

                            <div style={{ display: "flex", justifyContent: "space-between" }}>
                                <button type="button" onClick={() => setStep(1)} style={{ background: "transparent", border: "1px solid var(--border-color)", padding: "8px 16px", borderRadius: "4px", fontSize: "12px", color: "var(--text-primary)" }}>
                                    ← Back
                                </button>
                                <button type="button" onClick={() => setStep(3)} style={{ background: "var(--primary-color)", color: "#ffffff", padding: "8px 20px", borderRadius: "4px", fontSize: "12px", fontWeight: 700 }}>
                                    Next: Select Video Stream →
                                </button>
                            </div>
                        </div>
                    )}

                    {/* ─── STEP 3: VIDEO SOURCE ─────────────────────────────────────── */}
                    {step === 3 && (
                        <div>
                            <h4 style={{ margin: "0 0 6px 0", fontSize: "14px", fontWeight: 700, color: "var(--text-primary)" }}>
                                Select Video Input Source
                            </h4>
                            <p style={{ margin: "0 0 16px 0", fontSize: "11px", color: "var(--text-muted)" }}>
                                Choose whether to use your laptop webcam, an external USB optical sensor, or an IP / network stream.
                            </p>

                            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: "12px", marginBottom: "16px" }}>
                                {[
                                    { id: "laptop_webcam", title: "Laptop Webcam", desc: "Built-in primary optical sensor (Index 0)" },
                                    { id: "external_usb", title: "External USB Cam", desc: "Plugged-in USB HD webcam or optical hub" },
                                    { id: "network_ip", title: "IP / RTSP Stream", desc: "Network IP surveillance stream or mobile camera" },
                                ].map((type) => (
                                    <div
                                        key={type.id}
                                        onClick={() => setStreamType(type.id)}
                                        style={{
                                            padding: "14px",
                                            borderRadius: "8px",
                                            border: streamType === type.id ? "2px solid var(--primary-color)" : "1px solid var(--border-color)",
                                            background: streamType === type.id ? "var(--primary-soft)" : "var(--bg-secondary)",
                                            cursor: "pointer",
                                        }}
                                    >
                                        <div style={{ fontSize: "13px", fontWeight: 700, color: "var(--text-primary)" }}>{type.title}</div>
                                        <div style={{ fontSize: "11px", color: "var(--text-muted)", marginTop: "4px" }}>{type.desc}</div>
                                    </div>
                                ))}
                            </div>

                            {streamType === "external_usb" && (
                                <div style={{ marginBottom: "16px", background: "var(--bg-secondary)", padding: "12px", borderRadius: "6px" }}>
                                    <label style={{ display: "block", fontSize: "11px", fontWeight: 700, color: "var(--text-muted)", marginBottom: "4px" }}>Detected USB Video Devices</label>
                                    <select value={selectedDeviceId} onChange={(e) => setSelectedDeviceId(e.target.value)} style={{ width: "100%", padding: "7px 10px", borderRadius: "4px", border: "1px solid var(--border-color)", background: "var(--card-bg)", color: "var(--text-primary)", fontSize: "12px" }}>
                                        {externalDevices.map((d, i) => (
                                            <option key={d.deviceId || i} value={d.deviceId}>{d.label || `USB Video Device #${i + 1}`}</option>
                                        ))}
                                    </select>
                                </div>
                            )}

                            {streamType === "network_ip" && (
                                <div style={{ marginBottom: "16px", background: "var(--bg-secondary)", padding: "12px", borderRadius: "6px" }}>
                                    <label style={{ display: "block", fontSize: "11px", fontWeight: 700, color: "var(--text-muted)", marginBottom: "4px" }}>RTSP / HTTP Stream URL</label>
                                    <input type="text" value={networkUrl} onChange={(e) => setNetworkUrl(e.target.value)} placeholder="rtsp://192.168.1.100:554/live" style={{ width: "100%", padding: "7px 10px", borderRadius: "4px", border: "1px solid var(--border-color)", background: "var(--card-bg)", color: "var(--text-primary)", fontSize: "12px" }} />
                                </div>
                            )}

                            <div style={{ display: "flex", justifyContent: "space-between" }}>
                                <button type="button" onClick={() => setStep(2)} style={{ background: "transparent", border: "1px solid var(--border-color)", padding: "8px 16px", borderRadius: "4px", fontSize: "12px", color: "var(--text-primary)" }}>
                                    ← Back
                                </button>
                                <button type="button" onClick={() => setStep(4)} style={{ background: "var(--primary-color)", color: "#ffffff", padding: "8px 20px", borderRadius: "4px", fontSize: "12px", fontWeight: 700 }}>
                                    Next: Assign Camera Function →
                                </button>
                            </div>
                        </div>
                    )}

                    {/* ─── STEP 4: FUNCTION ASSIGNMENT & LAUNCH ──────────────────────── */}
                    {step === 4 && (
                        <div>
                            <h4 style={{ margin: "0 0 6px 0", fontSize: "14px", fontWeight: 700, color: "var(--text-primary)" }}>
                                Assign Specific Function to this Camera
                            </h4>
                            <p style={{ margin: "0 0 16px 0", fontSize: "11px", color: "var(--text-muted)" }}>
                                Select the perception task for this camera. Each camera in your fleet operates its assigned function independently under VANTEP AI.
                            </p>

                            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "10px", marginBottom: "20px" }}>
                                {[
                                    { id: "DRESS_CODE", label: "👔 Dress Code & Uniform Verification", desc: "Flags casual clothes, verifies regular uniforms & checks ID card badges" },
                                    { id: "FACE_ATTENDANCE", label: "⏱️ Automated Face Attendance", desc: "Scans faces, logs attendance timestamps, captures unknown visitor photos" },
                                    { id: "SAFETY", label: "🦺 OSHA Safety & PPE Monitoring", desc: "Monitors hardhats/helmets, high-visibility vests & safety gear before accidents" },
                                    { id: "EXAM_MONITOR", label: "📝 Exam Hall Malpractice Proctoring", desc: "Detects prohibited cell phones, cheat sheets, unauthorized devices" },
                                    { id: "WEAPON_VIOLENCE", label: "⚔️ Threat, Weapon & Violence Triage", desc: "Detects physical fights, firearms, edged weapons & aggression" },
                                    { id: "PERIMETER_INTRUSION", label: "🚨 Sentry Perimeter Intrusion Watch", desc: "Tripwire perimeter breaches & restricted zone unauthorized entry" },
                                ].map((func) => (
                                    <div
                                        key={func.id}
                                        onClick={() => setAssignedFunction(func.id)}
                                        style={{
                                            padding: "12px",
                                            borderRadius: "6px",
                                            border: assignedFunction === func.id ? "2px solid var(--primary-color)" : "1px solid var(--border-color)",
                                            background: assignedFunction === func.id ? "var(--primary-soft)" : "var(--bg-secondary)",
                                            cursor: "pointer",
                                        }}
                                    >
                                        <div style={{ fontSize: "12px", fontWeight: 700, color: "var(--text-primary)" }}>{func.label}</div>
                                        <div style={{ fontSize: "10px", color: "var(--text-muted)", marginTop: "3px" }}>{func.desc}</div>
                                    </div>
                                ))}
                            </div>

                            <div style={{ display: "flex", justifyContent: "space-between" }}>
                                <button type="button" onClick={() => setStep(3)} style={{ background: "transparent", border: "1px solid var(--border-color)", padding: "8px 16px", borderRadius: "4px", fontSize: "12px", color: "var(--text-primary)" }}>
                                    ← Back
                                </button>
                                <button
                                    type="button"
                                    disabled={isSubmitting}
                                    onClick={handleFinalLaunch}
                                    style={{
                                        background: "var(--primary-color)",
                                        color: "#ffffff",
                                        padding: "8px 24px",
                                        borderRadius: "4px",
                                        fontSize: "12px",
                                        fontWeight: 700,
                                        boxShadow: "0 2px 8px rgba(0,0,0,0.2)",
                                    }}
                                >
                                    {isSubmitting ? "Deploying VANTEP AI..." : "🚀 Launch Surveillance Operations"}
                                </button>
                            </div>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}
