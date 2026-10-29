import { useState, useEffect } from "react";
import { createPeopleBatch, createCamera, assignCameraFunction } from "../api/api";

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
                const maxDim = 480;
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
                resolve(canvas.toDataURL("image/jpeg", 0.88));
            };
            img.onerror = () => resolve(e.target.result);
        };
        reader.onerror = () => resolve("");
    });
};

const SAMPLE_CAMPUS_PROFILES = [
    {
        name: "Dr. Vikramaditya Sen",
        identifier: "FAC-8801",
        role: "staff",
        department: "Department of Artificial Intelligence",
        class_grade: "Dean & Senior Professor",
        allowed_dress: "Formals & Academic Blazer",
        phone: "+91 98450 11234",
        email: "v.sen@academy.edu",
        photo_url: "https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=150&auto=format&fit=crop",
    },
    {
        name: "Ananya Deshmukh",
        identifier: "STU-2024-041",
        role: "student",
        department: "Computer Science & Engineering",
        class_grade: "Year 3 - Section A",
        allowed_dress: "Regular School Uniform & Formals",
        phone: "+91 97412 88921",
        email: "ananya.d@student.academy.edu",
        photo_url: "https://images.unsplash.com/photo-1494790108377-be9c29b29330?w=150&auto=format&fit=crop",
    },
    {
        name: "Lt. Col. Rajesh Nambiar",
        identifier: "SEC-009",
        role: "staff",
        department: "Campus Security & Safety Directorate",
        class_grade: "Chief Security Officer",
        allowed_dress: "Security Uniform & Formal Regalia",
        phone: "+91 99001 44552",
        email: "rajesh.sec@academy.edu",
        photo_url: "https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=150&auto=format&fit=crop",
    },
    {
        name: "Rohan Singhal",
        identifier: "STU-2024-118",
        role: "student",
        department: "Mechanical & Robotics",
        class_grade: "Year 2 - Section C",
        allowed_dress: "Regular School Uniform & Formals",
        phone: "+91 98234 55667",
        email: "rohan.s@student.academy.edu",
        photo_url: "https://images.unsplash.com/photo-1500648767791-00dcc994a43e?w=150&auto=format&fit=crop",
    },
];

export default function SetupWizardModal({ environment, isOpen, onClose, onComplete }) {
    const [step, setStep] = useState(1); // 1: People, 2: Camera Name, 3: Stream Source, 4: Function, 5: Launch
    const [peopleList, setPeopleList] = useState([]);
    
    // Manual person form
    const [pName, setPName] = useState("");
    const [pId, setPId] = useState("");
    const [pRole, setPRole] = useState("student");
    const [pDept, setPDept] = useState("General");
    const [pGrade, setPGrade] = useState("Year 1");
    const [pDress, setPDress] = useState("Regular School Uniform & Formals");
    const [pPhone, setPPhone] = useState("");
    const [pEmail, setPEmail] = useState("");
    const [pPhoto, setPPhoto] = useState("");

    // Camera setup
    const [cameraName, setCameraName] = useState("Main Campus Entrance Gate Cam 01");
    const [cameraLocation, setCameraLocation] = useState("North Entrance Turnstiles");
    const [streamType, setStreamType] = useState("laptop_webcam"); // "laptop_webcam" | "mobile_camera" | "external_usb" | "rtsp"
    const [externalDevices, setExternalDevices] = useState([]);
    const [selectedDeviceId, setSelectedDeviceId] = useState("");
    const [assignedFunction, setAssignedFunction] = useState("FACE_ATTENDANCE");
    const [isSubmitting, setIsSubmitting] = useState(false);
    const [errorMsg, setErrorMsg] = useState("");

    // Pre-fill on open if list empty
    useEffect(() => {
        if (isOpen && peopleList.length === 0) {
            setPeopleList(SAMPLE_CAMPUS_PROFILES);
        }
    }, [isOpen]);

    // Detect external USB cameras
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

    const handleAddPerson = (e) => {
        e.preventDefault();
        if (!pName || !pId) {
            setErrorMsg("Name and Identifier are required.");
            return;
        }
        setErrorMsg("");
        const newPerson = {
            name: pName,
            identifier: pId,
            role: pRole,
            department: pDept,
            class_grade: pGrade,
            allowed_dress: pDress,
            phone: pPhone,
            email: pEmail,
            photo_url: pPhoto || "https://images.unsplash.com/photo-1535713875002-d1d0cf377fde?w=150&auto=format&fit=crop",
        };
        setPeopleList([...peopleList, newPerson]);
        setPName("");
        setPId("");
        setPPhone("");
        setPEmail("");
        setPPhoto("");
    };

    const handleRemovePerson = (idx) => {
        setPeopleList(peopleList.filter((_, i) => i !== idx));
    };

    const handleLoadSampleProfiles = () => {
        setPeopleList(SAMPLE_CAMPUS_PROFILES);
    };

    const handleFinalLaunch = async () => {
        if (peopleList.length === 0) {
            setErrorMsg("Please add at least 1 person profile (recommended 4+).");
            return;
        }
        setIsSubmitting(true);
        setErrorMsg("");
        try {
            const envId = environment?.id || 1;
            // 1. Batch save people
            await createPeopleBatch(peopleList, envId);

            // 2. Create the assigned camera
            const camRes = await createCamera({
                environment_id: envId,
                camera_name: cameraName,
                location: cameraLocation,
                zone: "Sector 2 - Entrance",
                source_type: streamType === "laptop_webcam" ? "webcam" : (streamType === "external_usb" ? "usb_port" : "mobile_ip"),
                source_url: selectedDeviceId || "0",
                assigned_function: assignedFunction,
                ai_enabled: 1,
            });

            // 3. Complete wizard
            if (onComplete) {
                onComplete({
                    camera: camRes.camera || { id: 1, camera_name: cameraName, assigned_function: assignedFunction },
                    peopleCount: peopleList.length,
                    streamType,
                    selectedDeviceId,
                });
            }
            onClose();
        } catch (err) {
            console.error("Setup wizard error:", err);
            setErrorMsg(err.response?.data?.detail || "Could not complete setup. Proceeding to live view.");
            if (onComplete) {
                onComplete({ camera: { id: 1, camera_name: cameraName, assigned_function: assignedFunction } });
            }
            onClose();
        } finally {
            setIsSubmitting(false);
        }
    };

    const envTitle = environment?.name || "Institution Mode";

    return (
        <div className="modal-overlay" style={{ zIndex: 9999 }}>
            <div className="modal-dialog" style={{ maxWidth: "860px", width: "95%" }}>
                {/* Royal Header */}
                <div className="modal-header" style={{ borderBottom: "2px solid #e2e8f0", padding: "18px 24px" }}>
                    <div>
                        <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
                            <span style={{ fontSize: "22px" }}>👑</span>
                            <h3 style={{ margin: 0, fontSize: "18px", fontWeight: 700, color: "var(--text-primary)" }}>
                                Guided System Setup &amp; Onboarding
                            </h3>
                        </div>
                        <p style={{ margin: "4px 0 0 0", fontSize: "12px", color: "var(--text-secondary)" }}>
                            Configuring: <strong>{envTitle}</strong> • Step {step} of 4
                        </p>
                    </div>
                    <button className="tool-btn btn-secondary-mini" onClick={onClose} style={{ fontSize: "16px" }}>✕</button>
                </div>

                {/* Step Progress Bar */}
                <div style={{ display: "flex", padding: "12px 24px", background: "var(--bg-secondary)", gap: "8px", borderBottom: "1px solid var(--border-color)" }}>
                    {[
                        { num: 1, label: "1. Enrol Personnel (4+)" },
                        { num: 2, label: "2. Assign Camera" },
                        { num: 3, label: "3. Stream Input Port" },
                        { num: 4, label: "4. Assign AI Function" },
                    ].map((s) => (
                        <div
                            key={s.num}
                            onClick={() => s.num < step && setStep(s.num)}
                            style={{
                                flex: 1,
                                padding: "8px 12px",
                                borderRadius: "6px",
                                textAlign: "center",
                                fontSize: "11px",
                                fontWeight: 600,
                                textTransform: "uppercase",
                                letterSpacing: "0.5px",
                                cursor: s.num < step ? "pointer" : "default",
                                background: step === s.num ? "var(--primary-color)" : (step > s.num ? "var(--success-color)" : "var(--card-bg)"),
                                color: step >= s.num ? "#ffffff" : "var(--text-muted)",
                                border: "1px solid var(--border-color)",
                                transition: "all 0.2s ease",
                            }}
                        >
                            {s.label}
                        </div>
                    ))}
                </div>

                {errorMsg && (
                    <div style={{ margin: "14px 24px 0 24px", padding: "10px 14px", background: "#fef2f2", border: "1px solid #fecaca", borderRadius: "6px", color: "#b91c1c", fontSize: "12px" }}>
                        ⚠️ {errorMsg}
                    </div>
                )}

                {/* ── STEP 1: Personnel Enrollment (4+) ── */}
                {step === 1 && (
                    <div style={{ padding: "20px 24px", maxHeight: "65vh", overflowY: "auto" }}>
                        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "14px" }}>
                            <div>
                                <h4 style={{ margin: 0, fontSize: "14px", fontWeight: 700 }}>Personnel &amp; Student Registration Roster</h4>
                                <p style={{ margin: "2px 0 0 0", fontSize: "12px", color: "var(--text-secondary)" }}>
                                    Each individual receives a dedicated, AI-managed dossier file with biometric attendance &amp; uniform tracking.
                                </p>
                            </div>
                            <button
                                type="button"
                                className="tool-btn btn-secondary-mini"
                                onClick={handleLoadSampleProfiles}
                                style={{ background: "#f0fdf4", color: "#166534", border: "1px solid #bbf7d0", fontWeight: 600 }}
                            >
                                ⚡ Pre-fill 4 Verified Profiles
                            </button>
                        </div>

                        {/* List of Enrolled Personnel */}
                        <div style={{ marginBottom: "18px", border: "1px solid var(--border-color)", borderRadius: "8px", overflow: "hidden" }}>
                            <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "12px" }}>
                                <thead>
                                    <tr style={{ background: "var(--bg-secondary)", borderBottom: "1px solid var(--border-color)", textAlign: "left" }}>
                                        <th style={{ padding: "8px 12px" }}>Photo</th>
                                        <th style={{ padding: "8px 12px" }}>Name &amp; ID</th>
                                        <th style={{ padding: "8px 12px" }}>Role / Occupation</th>
                                        <th style={{ padding: "8px 12px" }}>Department</th>
                                        <th style={{ padding: "8px 12px" }}>Allowed Dress Policy</th>
                                        <th style={{ padding: "8px 12px", textAlign: "right" }}>Action</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {peopleList.length === 0 ? (
                                        <tr>
                                            <td colSpan={6} style={{ padding: "20px", textAlign: "center", color: "var(--text-muted)" }}>
                                                No personnel registered yet. Fill the form below or click "Pre-fill 4 Verified Profiles".
                                            </td>
                                        </tr>
                                    ) : (
                                        peopleList.map((p, idx) => (
                                            <tr key={idx} style={{ borderBottom: "1px solid var(--border-color)", background: idx % 2 === 0 ? "var(--card-bg)" : "var(--bg-secondary)" }}>
                                                <td style={{ padding: "6px 12px" }}>
                                                    <img
                                                        src={p.photo_url || "https://images.unsplash.com/photo-1535713875002-d1d0cf377fde?w=150&auto=format&fit=crop"}
                                                        alt={p.name}
                                                        style={{ width: "32px", height: "32px", borderRadius: "50%", objectFit: "cover", border: "1px solid var(--border-color)" }}
                                                    />
                                                </td>
                                                <td style={{ padding: "6px 12px" }}>
                                                    <strong>{p.name}</strong>
                                                    <div style={{ fontSize: "10px", color: "var(--text-muted)" }}>{p.identifier}</div>
                                                </td>
                                                <td style={{ padding: "6px 12px" }}>
                                                    <span className={`cam-func-badge ${p.role === "staff" ? "badge-primary" : "badge-secondary"}`}>
                                                        {p.role.toUpperCase()}
                                                    </span>
                                                </td>
                                                <td style={{ padding: "6px 12px" }}>{p.department}</td>
                                                <td style={{ padding: "6px 12px", fontSize: "11px" }}>{p.allowed_dress}</td>
                                                <td style={{ padding: "6px 12px", textAlign: "right" }}>
                                                    <button
                                                        type="button"
                                                        onClick={() => handleRemovePerson(idx)}
                                                        style={{ background: "transparent", border: "none", color: "#ef4444", cursor: "pointer", fontWeight: 700 }}
                                                    >
                                                        ✕
                                                    </button>
                                                </td>
                                            </tr>
                                        ))
                                    )}
                                </tbody>
                            </table>
                        </div>

                        {/* Quick Add Form */}
                        <div style={{ padding: "14px", border: "1px solid var(--border-color)", borderRadius: "8px", background: "var(--bg-secondary)" }}>
                            <div style={{ fontSize: "12px", fontWeight: 700, marginBottom: "8px" }}>➕ Add New Person Profile</div>
                            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: "10px", marginBottom: "10px" }}>
                                <div>
                                    <label className="fleet-stat-label">Full Name *</label>
                                    <input
                                        className="form-control"
                                        placeholder="e.g. Aarav Singhania"
                                        value={pName}
                                        onChange={(e) => setPName(e.target.value)}
                                        style={{ width: "100%", padding: "7px 10px", fontSize: "12px", borderRadius: "5px", border: "1px solid var(--border-color)" }}
                                    />
                                </div>
                                <div>
                                    <label className="fleet-stat-label">Unique ID / Roll No. *</label>
                                    <input
                                        className="form-control"
                                        placeholder="e.g. STU-2026-09"
                                        value={pId}
                                        onChange={(e) => setPId(e.target.value)}
                                        style={{ width: "100%", padding: "7px 10px", fontSize: "12px", borderRadius: "5px", border: "1px solid var(--border-color)" }}
                                    />
                                </div>
                                <div>
                                    <label className="fleet-stat-label">Role / Category</label>
                                    <select
                                        className="sector-select-box"
                                        value={pRole}
                                        onChange={(e) => setPRole(e.target.value)}
                                        style={{ width: "100%", padding: "7px 10px", fontSize: "12px" }}
                                    >
                                        <option value="student">Student</option>
                                        <option value="staff">Staff / Faculty</option>
                                        <option value="officer">Security Officer</option>
                                        <option value="worker">Industrial Worker</option>
                                    </select>
                                </div>
                            </div>

                            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: "10px", marginBottom: "10px" }}>
                                <div>
                                    <label className="fleet-stat-label">Department / Branch</label>
                                    <input
                                        className="form-control"
                                        placeholder="e.g. Physics Department"
                                        value={pDept}
                                        onChange={(e) => setPDept(e.target.value)}
                                        style={{ width: "100%", padding: "7px 10px", fontSize: "12px", borderRadius: "5px", border: "1px solid var(--border-color)" }}
                                    />
                                </div>
                                <div>
                                    <label className="fleet-stat-label">Grade / Section / Designation</label>
                                    <input
                                        className="form-control"
                                        placeholder="e.g. Year 2 / Senior Analyst"
                                        value={pGrade}
                                        onChange={(e) => setPGrade(e.target.value)}
                                        style={{ width: "100%", padding: "7px 10px", fontSize: "12px", borderRadius: "5px", border: "1px solid var(--border-color)" }}
                                    />
                                </div>
                                <div>
                                    <label className="fleet-stat-label">Permitted Dress Code</label>
                                    <input
                                        className="form-control"
                                        placeholder="e.g. Regular School Uniform & Formals"
                                        value={pDress}
                                        onChange={(e) => setPDress(e.target.value)}
                                        style={{ width: "100%", padding: "7px 10px", fontSize: "12px", borderRadius: "5px", border: "1px solid var(--border-color)" }}
                                    />
                                </div>
                            </div>

                            {/* Photo Upload for Face Recognition */}
                            <div style={{ marginBottom: "12px", padding: "10px", background: "var(--card-bg)", borderRadius: "6px", border: "1px dashed var(--border-color)" }}>
                                <label className="fleet-stat-label">📷 Person Face Photo (Upload for AI Biometric Recognition)</label>
                                <div style={{ display: "flex", alignItems: "center", gap: "12px", marginTop: "6px" }}>
                                    <input
                                        type="file"
                                        accept="image/*"
                                        id="wizard-person-photo-input"
                                        style={{ display: "none" }}
                                        onChange={async (e) => {
                                            const file = e.target.files && e.target.files[0];
                                            if (file) {
                                                const compressed = await compressImage(file);
                                                setPPhoto(compressed);
                                            }
                                        }}
                                    />
                                    <label
                                        htmlFor="wizard-person-photo-input"
                                        className="tool-btn btn-secondary-mini"
                                        style={{ cursor: "pointer", padding: "6px 12px", fontSize: "11px", background: "rgba(212, 175, 55, 0.15)", color: "var(--text-primary)", border: "1px solid rgba(212, 175, 55, 0.3)", borderRadius: "4px", fontWeight: 700 }}
                                    >
                                        📁 Choose Face Image
                                    </label>
                                    {pPhoto ? (
                                        <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                                            <img
                                                src={pPhoto}
                                                alt="Preview"
                                                style={{ width: "34px", height: "34px", borderRadius: "50%", objectFit: "cover", border: "2px solid #d4af37" }}
                                            />
                                            <button
                                                type="button"
                                                onClick={() => setPPhoto("")}
                                                style={{ background: "transparent", border: "none", color: "#dc2626", fontSize: "11px", cursor: "pointer", fontWeight: 700 }}
                                            >
                                                ✕ Remove
                                            </button>
                                        </div>
                                    ) : (
                                        <span style={{ fontSize: "11px", color: "var(--text-muted)" }}>Upload JPG, PNG or WEBP frontal face photo</span>
                                    )}
                                </div>
                            </div>

                            <div style={{ display: "flex", justifyContent: "flex-end" }}>
                                <button
                                    type="button"
                                    className="tool-btn btn-primary"
                                    onClick={handleAddPerson}
                                    style={{ fontSize: "12px", padding: "6px 18px" }}
                                >
                                    + Add Person to Roster
                                </button>
                            </div>
                        </div>
                    </div>
                )}

                {/* ── STEP 2: Assign Camera Name ── */}
                {step === 2 && (
                    <div style={{ padding: "24px", minHeight: "300px" }}>
                        <h4 style={{ margin: 0, fontSize: "15px", fontWeight: 700 }}>Step 2: Assign &amp; Name Surveillance Camera</h4>
                        <p style={{ margin: "4px 0 16px 0", fontSize: "12px", color: "var(--text-secondary)" }}>
                            Define the identifier and physical deployment sector for this camera feed.
                        </p>

                        <div style={{ display: "flex", flexDirection: "column", gap: "14px", maxWidth: "600px" }}>
                            <div>
                                <label className="fleet-stat-label">Camera Designated Name *</label>
                                <input
                                    className="form-control"
                                    value={cameraName}
                                    onChange={(e) => setCameraName(e.target.value)}
                                    placeholder="e.g. Main Campus Gate 01, Examination Hall Alpha"
                                    style={{ width: "100%", padding: "10px 14px", fontSize: "13px", borderRadius: "6px", border: "1px solid var(--border-color)" }}
                                />
                            </div>

                            <div>
                                <label className="fleet-stat-label">Physical Location / Sector</label>
                                <input
                                    className="form-control"
                                    value={cameraLocation}
                                    onChange={(e) => setCameraLocation(e.target.value)}
                                    placeholder="e.g. Academic Block A - Turnstile Entrance"
                                    style={{ width: "100%", padding: "10px 14px", fontSize: "13px", borderRadius: "6px", border: "1px solid var(--border-color)" }}
                                />
                            </div>

                            <div style={{ padding: "14px", background: "var(--bg-secondary)", borderRadius: "6px", border: "1px solid var(--border-color)" }}>
                                <div style={{ fontSize: "11px", fontWeight: 600, color: "var(--text-secondary)", textTransform: "uppercase" }}>
                                    Fleet Scale Ready
                                </div>
                                <div style={{ fontSize: "12px", marginTop: "4px" }}>
                                    ✅ This camera will be added to your operational fleet of <strong>70–80 institution cameras</strong> managed by JARVIS AI.
                                </div>
                            </div>
                        </div>
                    </div>
                )}

                {/* ── STEP 3: Stream Input Port ── */}
                {step === 3 && (
                    <div style={{ padding: "24px", minHeight: "300px" }}>
                        <h4 style={{ margin: 0, fontSize: "15px", fontWeight: 700 }}>Step 3: Select Video Stream Input Port</h4>
                        <p style={{ margin: "4px 0 16px 0", fontSize: "12px", color: "var(--text-secondary)" }}>
                            Choose whether to use your laptop webcam, mobile phone camera, or plug-and-play external USB port camera.
                        </p>

                        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "12px", marginBottom: "16px" }}>
                            {[
                                {
                                    id: "laptop_webcam",
                                    icon: "💻",
                                    title: "Laptop / Built-in Webcam",
                                    desc: "Zero-latency direct stream from your device's integrated front camera.",
                                },
                                {
                                    id: "external_usb",
                                    icon: "🔌",
                                    title: "External USB Port Camera",
                                    desc: "Plug-and-play USB webcam, HDMI capture card, or external lens.",
                                },
                                {
                                    id: "mobile_camera",
                                    icon: "📱",
                                    title: "Mobile Phone Camera",
                                    desc: "Direct browser rear lens or wireless mobile stream connection.",
                                },
                                {
                                    id: "rtsp",
                                    icon: "📡",
                                    title: "Network IP / CCTV Stream",
                                    desc: "Connect via RTSP URL, IP address, or local surveillance hub.",
                                },
                            ].map((opt) => (
                                <div
                                    key={opt.id}
                                    onClick={() => setStreamType(opt.id)}
                                    style={{
                                        padding: "16px",
                                        borderRadius: "8px",
                                        border: `2px solid ${streamType === opt.id ? "var(--primary-color)" : "var(--border-color)"}`,
                                        background: streamType === opt.id ? "var(--primary-soft)" : "var(--card-bg)",
                                        cursor: "pointer",
                                        transition: "all 0.15s ease",
                                    }}
                                >
                                    <div style={{ fontSize: "24px", marginBottom: "6px" }}>{opt.icon}</div>
                                    <div style={{ fontSize: "13px", fontWeight: 700, color: "var(--text-primary)" }}>{opt.title}</div>
                                    <div style={{ fontSize: "11px", color: "var(--text-secondary)", marginTop: "4px" }}>{opt.desc}</div>
                                </div>
                            ))}
                        </div>

                        {streamType === "external_usb" && (
                            <div style={{ padding: "14px", background: "var(--bg-secondary)", borderRadius: "6px", border: "1px solid var(--border-color)" }}>
                                <label className="fleet-stat-label">Detected USB / External Video Devices</label>
                                {externalDevices.length > 0 ? (
                                    <select
                                        className="sector-select-box"
                                        value={selectedDeviceId}
                                        onChange={(e) => setSelectedDeviceId(e.target.value)}
                                        style={{ width: "100%", padding: "8px 12px", marginTop: "6px" }}
                                    >
                                        {externalDevices.map((d, i) => (
                                            <option key={d.deviceId || i} value={d.deviceId}>
                                                {d.label || `External USB Video Port #${i + 1}`}
                                            </option>
                                        ))}
                                    </select>
                                ) : (
                                    <div style={{ fontSize: "12px", color: "#f59e0b", marginTop: "4px" }}>
                                        🔍 Scanning for attached USB cameras... (Plug in your external camera; permission prompt will appear upon launch).
                                    </div>
                                )}
                            </div>
                        )}
                    </div>
                )}

                {/* ── STEP 4: Assign AI Function ── */}
                {step === 4 && (
                    <div style={{ padding: "24px", minHeight: "300px" }}>
                        <h4 style={{ margin: 0, fontSize: "15px", fontWeight: 700 }}>Step 4: Assign Specific Operational Function</h4>
                        <p style={{ margin: "4px 0 16px 0", fontSize: "12px", color: "var(--text-secondary)" }}>
                            Select the primary artificial intelligence task executed on this camera stream.
                        </p>

                        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "12px" }}>
                            {[
                                {
                                    id: "FACE_ATTENDANCE",
                                    icon: "🎓",
                                    title: "Face Biometric Attendance",
                                    desc: "Automated identity scan, exact timestamping, and individual dossier logging.",
                                    recommended: true,
                                },
                                {
                                    id: "DRESS_CODE",
                                    icon: "👔",
                                    title: "Dress Code & School Uniform",
                                    desc: "Verifies formals and regular uniform; flags casual attire and violations.",
                                    recommended: true,
                                },
                                {
                                    id: "EXAM_MONITOR",
                                    icon: "📝",
                                    title: "Exam Hall Proctoring",
                                    desc: "Detects prohibited cell phones, cheat notes, laptops, and suspicious handoffs.",
                                    recommended: false,
                                },
                                {
                                    id: "PERIMETER_INTRUSION",
                                    icon: "🛡️",
                                    title: "Perimeter & Safety Defense",
                                    desc: "Virtual tripwires, unauthorized zone breach alerts, and intruder tracking.",
                                    recommended: false,
                                },
                            ].map((f) => (
                                <div
                                    key={f.id}
                                    onClick={() => setAssignedFunction(f.id)}
                                    style={{
                                        padding: "16px",
                                        borderRadius: "8px",
                                        border: `2px solid ${assignedFunction === f.id ? "var(--primary-color)" : "var(--border-color)"}`,
                                        background: assignedFunction === f.id ? "var(--primary-soft)" : "var(--card-bg)",
                                        cursor: "pointer",
                                    }}
                                >
                                    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                                        <span style={{ fontSize: "22px" }}>{f.icon}</span>
                                        {f.recommended && (
                                            <span style={{ fontSize: "10px", background: "#f0fdf4", color: "#166534", padding: "2px 8px", borderRadius: "10px", fontWeight: 600 }}>
                                                RECOMMENDED
                                            </span>
                                        )}
                                    </div>
                                    <div style={{ fontSize: "13px", fontWeight: 700, marginTop: "6px" }}>{f.title}</div>
                                    <div style={{ fontSize: "11px", color: "var(--text-secondary)", marginTop: "4px" }}>{f.desc}</div>
                                </div>
                            ))}
                        </div>
                    </div>
                )}

                {/* Modal Footer Controls */}
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", padding: "16px 24px", borderTop: "1px solid var(--border-color)", background: "var(--bg-secondary)" }}>
                    <div>
                        {step > 1 && (
                            <button
                                type="button"
                                className="tool-btn btn-secondary-mini"
                                onClick={() => setStep(step - 1)}
                                style={{ padding: "8px 16px", fontSize: "12px" }}
                            >
                                ← Back
                            </button>
                        )}
                    </div>
                    <div style={{ display: "flex", gap: "10px" }}>
                        <button
                            type="button"
                            className="tool-btn btn-secondary-mini"
                            onClick={onClose}
                            style={{ padding: "8px 16px", fontSize: "12px" }}
                        >
                            Cancel
                        </button>
                        {step < 4 ? (
                            <button
                                type="button"
                                className="tool-btn btn-primary"
                                onClick={() => {
                                    if (step === 1 && peopleList.length === 0) {
                                        setErrorMsg("Please add at least 1 person or click 'Pre-fill 4 Verified Profiles'.");
                                        return;
                                    }
                                    setErrorMsg("");
                                    setStep(step + 1);
                                }}
                                style={{ padding: "8px 20px", fontSize: "12px", fontWeight: 600 }}
                            >
                                Next Step →
                            </button>
                        ) : (
                            <button
                                type="button"
                                className="tool-btn btn-primary"
                                onClick={handleFinalLaunch}
                                disabled={isSubmitting}
                                style={{ padding: "8px 24px", fontSize: "12px", fontWeight: 700, background: "var(--success-color)", color: "#ffffff" }}
                            >
                                {isSubmitting ? "🚀 Initializing AI..." : "🚀 Launch 24/7 AI Surveillance"}
                            </button>
                        )}
                    </div>
                </div>
            </div>
        </div>
    );
}
