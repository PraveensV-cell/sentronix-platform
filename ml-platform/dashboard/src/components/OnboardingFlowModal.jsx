import { useState, useEffect } from "react";
import { createPeopleBatch, createCamera } from "../api/api";

const DATASET_TEMPLATES = {
    School: {
        category: "Academic & Campus Roster",
        desc: "Enroll students, faculty professors, and campus security staff.",
        defaultRoles: ["student", "staff", "visitor"],
        sampleSuggestions: [
            { name: "Pravin S.", identifier: "STU-001", role: "student", department: "Computer Science", class_grade: "Year 3", allowed_dress: "Regular School Uniform & Formals", phone: "+91 9876543210", email: "pravin@campus.edu" },
            { name: "Dr. A. Sharma", identifier: "FAC-102", role: "staff", department: "Artificial Intelligence", class_grade: "Professor", allowed_dress: "Academic Formals", phone: "+91 9876543211", email: "sharma@campus.edu" },
        ],
    },
    Military: {
        category: "Defense Personnel Roster",
        desc: "Enroll commanding officers, perimeter sentries, and clearance personnel.",
        defaultRoles: ["officer", "sentry", "commander"],
        sampleSuggestions: [
            { name: "Major K. Verma", identifier: "MIL-401", role: "officer", department: "Tactical Perimeter Command", class_grade: "Commandant", allowed_dress: "Service Dress Uniform", phone: "+91 9876543212", email: "verma@defense.mil" },
            { name: "Sgt. R. Nambiar", identifier: "MIL-402", role: "sentry", department: "Gate Alpha Security", class_grade: "Security Detail", allowed_dress: "Tactical Combat Dress", phone: "+91 9876543213", email: "nambiar@defense.mil" },
        ],
    },
    Industry: {
        category: "Plant Workers & Engineers Roster",
        desc: "Enroll machinery operators, chemical technicians, and safety auditors.",
        defaultRoles: ["worker", "engineer", "auditor"],
        sampleSuggestions: [
            { name: "Arun K. Singh", identifier: "IND-801", role: "worker", department: "Assembly Line 01", class_grade: "Lead Operator", allowed_dress: "High-Vis Vest & Hardhat", phone: "+91 9876543214", email: "arun@plant.com" },
            { name: "Priya Sundaram", identifier: "IND-802", role: "engineer", department: "Turbine Bay", class_grade: "Chief Engineer", allowed_dress: "Safety Overalls & Glasses", phone: "+91 9876543215", email: "priya@plant.com" },
        ],
    },
    Hospital: {
        category: "Healthcare & Public Facility Roster",
        desc: "Enroll surgical doctors, emergency ward nurses, and concourse guards.",
        defaultRoles: ["doctor", "nurse", "guard"],
        sampleSuggestions: [
            { name: "Dr. Meera Iyer", identifier: "MED-301", role: "doctor", department: "Trauma & Surgery", class_grade: "Attending Surgeon", allowed_dress: "Hospital Scrubs & ID", phone: "+91 9876543216", email: "meera@hospital.org" },
            { name: "Rajesh Guard", identifier: "SEC-101", role: "guard", department: "Concourse Patrol", class_grade: "Senior Guard", allowed_dress: "Security Uniform", phone: "+91 9876543217", email: "rajesh@hospital.org" },
        ],
    },
    Corporate: {
        category: "Enterprise Staff & Executive Roster",
        desc: "Enroll executives, software engineers, and facility administrators.",
        defaultRoles: ["employee", "executive", "visitor"],
        sampleSuggestions: [
            { name: "Siddharth Rao", identifier: "CORP-901", role: "employee", department: "Cloud Infrastructure", class_grade: "VP of Engineering", allowed_dress: "Business Casual & Formals", phone: "+91 9876543218", email: "sid@corp.com" },
        ],
    },
};

export default function OnboardingFlowModal({ environment, isOpen, onClose, onLaunchLive }) {
    const [step, setStep] = useState(1); // 1: Dataset, 2: Camera Name, 3: Stream Port, 4: Function, 5: Launch
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
    const [cameraName, setCameraName] = useState("Main Entrance Checkpoint Cam 01");
    const [cameraLocation, setCameraLocation] = useState("Turnstile Gate Alpha");
    const [streamType, setStreamType] = useState("laptop_webcam");
    const [externalDevices, setExternalDevices] = useState([]);
    const [selectedDeviceId, setSelectedDeviceId] = useState("");
    const [assignedFunction, setAssignedFunction] = useState("FACE_ATTENDANCE");
    const [isSubmitting, setIsSubmitting] = useState(false);
    const [errorMsg, setErrorMsg] = useState("");

    const modeType = environment?.type || "School";
    const template = DATASET_TEMPLATES[modeType] || DATASET_TEMPLATES.School;

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

    const handleAddPerson = (e) => {
        e.preventDefault();
        if (!name.trim() || !identifier.trim()) {
            setErrorMsg("Full Name and Unique ID are required to register an individual.");
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
            photo_url: photoUrl || "https://images.unsplash.com/photo-1535713875002-d1d0cf377fde?w=150&auto=format&fit=crop",
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

    const handleLoadSuggestions = () => {
        setPeopleList(template.sampleSuggestions);
    };

    const handleFinalLaunch = async () => {
        if (peopleList.length === 0) {
            setErrorMsg("Please add at least 1 person profile so the AI can verify identities.");
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
                zone: "Sector Alpha",
                source_type: streamType === "laptop_webcam" ? "webcam" : (streamType === "external_usb" ? "usb_port" : "mobile_ip"),
                source_url: selectedDeviceId || "0",
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
            setErrorMsg(err.response?.data?.detail || "Could not complete setup. Launching live view with defaults.");
            if (onLaunchLive) {
                onLaunchLive({
                    camera: { id: 1, camera_name: cameraName, assigned_function: assignedFunction },
                    streamType,
                });
            }
            onClose();
        } finally {
            setIsSubmitting(false);
        }
    };

    return (
        <div className="modal-overlay" style={{ zIndex: 9999 }}>
            <div className="modal-dialog-large" style={{ maxWidth: "880px", background: "#0e131b", border: "1px solid rgba(212, 175, 55, 0.3)", boxShadow: "0 10px 40px rgba(0,0,0,0.8)" }}>
                {/* Royal Header */}
                <div className="modal-header" style={{ borderBottom: "1px solid rgba(255,255,255,0.08)", padding: "18px 24px" }}>
                    <div>
                        <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
                            <span style={{ fontSize: "20px", color: "#d4af37" }}>⚜️</span>
                            <h3 style={{ margin: 0, fontSize: "17px", fontWeight: 700, color: "#f8fafc", letterSpacing: "0.5px" }}>
                                System Deployment &amp; Dataset Enrollment
                            </h3>
                        </div>
                        <p style={{ margin: "4px 0 0 0", fontSize: "12px", color: "#94a3b8" }}>
                            Mode: <strong style={{ color: "#d4af37" }}>{environment?.name || "Academic Campus"}</strong> • Step {step} of 4
                        </p>
                    </div>
                    <button className="tool-btn btn-secondary-mini" onClick={onClose} style={{ fontSize: "14px", color: "#94a3b8" }}>✕</button>
                </div>

                {/* Progress Strip */}
                <div style={{ display: "flex", padding: "10px 24px", background: "rgba(0,0,0,0.3)", gap: "8px", borderBottom: "1px solid rgba(255,255,255,0.06)" }}>
                    {[
                        { num: 1, label: "1. Dataset Input" },
                        { num: 2, label: "2. Camera Assign" },
                        { num: 3, label: "3. Stream Input Port" },
                        { num: 4, label: "4. Function & Launch" },
                    ].map((s) => (
                        <div
                            key={s.num}
                            onClick={() => s.num < step && setStep(s.num)}
                            style={{
                                flex: 1,
                                padding: "7px 10px",
                                borderRadius: "6px",
                                textAlign: "center",
                                fontSize: "11px",
                                fontWeight: 700,
                                textTransform: "uppercase",
                                letterSpacing: "0.5px",
                                cursor: s.num < step ? "pointer" : "default",
                                background: step === s.num ? "linear-gradient(135deg, #d4af37 0%, #b8860b 100%)" : (step > s.num ? "#10b981" : "rgba(255,255,255,0.05)"),
                                color: step >= s.num ? "#0c1017" : "#64748b",
                                border: "1px solid rgba(255,255,255,0.08)",
                                transition: "all 0.2s ease",
                            }}
                        >
                            {s.label}
                        </div>
                    ))}
                </div>

                {errorMsg && (
                    <div style={{ margin: "14px 24px 0 24px", padding: "10px 14px", background: "rgba(239, 68, 68, 0.15)", border: "1px solid rgba(239, 68, 68, 0.3)", borderRadius: "6px", color: "#f87171", fontSize: "12px" }}>
                        ⚠️ {errorMsg}
                    </div>
                )}

                {/* ── STEP 1: Dataset Enrollment ── */}
                {step === 1 && (
                    <div style={{ padding: "20px 24px", maxHeight: "65vh", overflowY: "auto" }}>
                        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "12px" }}>
                            <div>
                                <h4 style={{ margin: 0, fontSize: "14px", fontWeight: 700, color: "#f8fafc" }}>
                                    {template.category}
                                </h4>
                                <p style={{ margin: "2px 0 0 0", fontSize: "12px", color: "#94a3b8" }}>
                                    {template.desc} Add the individuals you want the AI to recognize and log.
                                </p>
                            </div>
                            <button
                                type="button"
                                className="tool-btn btn-secondary-mini"
                                onClick={handleLoadSuggestions}
                                style={{ background: "rgba(212, 175, 55, 0.12)", color: "#d4af37", border: "1px solid rgba(212, 175, 55, 0.3)", fontWeight: 700, fontSize: "11px" }}
                            >
                                ⚡ Load Clean Verified Dataset
                            </button>
                        </div>

                        {/* Roster Table */}
                        <div style={{ marginBottom: "18px", border: "1px solid rgba(255,255,255,0.08)", borderRadius: "8px", overflow: "hidden" }}>
                            <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "12px" }}>
                                <thead>
                                    <tr style={{ background: "rgba(255,255,255,0.04)", borderBottom: "1px solid rgba(255,255,255,0.08)", color: "#94a3b8", textAlign: "left" }}>
                                        <th style={{ padding: "8px 12px" }}>Name &amp; ID</th>
                                        <th style={{ padding: "8px 12px" }}>Role</th>
                                        <th style={{ padding: "8px 12px" }}>Department</th>
                                        <th style={{ padding: "8px 12px" }}>Allowed Uniform Policy</th>
                                        <th style={{ padding: "8px 12px", textAlign: "right" }}>Action</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {peopleList.length === 0 ? (
                                        <tr>
                                            <td colSpan={5} style={{ padding: "24px", textAlign: "center", color: "#64748b" }}>
                                                No individuals added to dataset yet. Fill the registration form below or click "Load Clean Verified Dataset".
                                            </td>
                                        </tr>
                                    ) : (
                                        peopleList.map((p, idx) => (
                                            <tr key={idx} style={{ borderBottom: "1px solid rgba(255,255,255,0.04)", color: "#f8fafc" }}>
                                                <td style={{ padding: "8px 12px" }}>
                                                    <strong>{p.name}</strong>
                                                    <div style={{ fontSize: "10px", color: "#94a3b8" }}>{p.identifier}</div>
                                                </td>
                                                <td style={{ padding: "8px 12px" }}>
                                                    <span style={{ fontSize: "10px", background: "rgba(212,175,55,0.15)", color: "#d4af37", padding: "2px 8px", borderRadius: "10px", fontWeight: 700 }}>
                                                        {p.role.toUpperCase()}
                                                    </span>
                                                </td>
                                                <td style={{ padding: "8px 12px" }}>{p.department}</td>
                                                <td style={{ padding: "8px 12px", fontSize: "11px", color: "#cbd5e1" }}>{p.allowed_dress}</td>
                                                <td style={{ padding: "8px 12px", textAlign: "right" }}>
                                                    <button
                                                        type="button"
                                                        onClick={() => handleRemovePerson(idx)}
                                                        style={{ background: "transparent", border: "none", color: "#f87171", cursor: "pointer", fontWeight: 700 }}
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

                        {/* Registration Form */}
                        <div style={{ padding: "14px", border: "1px solid rgba(255,255,255,0.08)", borderRadius: "8px", background: "rgba(255,255,255,0.02)" }}>
                            <div style={{ fontSize: "12px", fontWeight: 700, color: "#d4af37", marginBottom: "10px" }}>
                                ➕ Enroll Individual into Dataset
                            </div>
                            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: "10px", marginBottom: "10px" }}>
                                <div>
                                    <label style={{ fontSize: "10px", color: "#94a3b8", textTransform: "uppercase", fontWeight: 700 }}>Full Name *</label>
                                    <input
                                        placeholder="e.g. Aarav Sharma"
                                        value={name}
                                        onChange={(e) => setName(e.target.value)}
                                        style={{ width: "100%", padding: "8px 10px", fontSize: "12px", borderRadius: "6px", background: "#131a26", border: "1px solid rgba(255,255,255,0.1)", color: "#ffffff" }}
                                    />
                                </div>
                                <div>
                                    <label style={{ fontSize: "10px", color: "#94a3b8", textTransform: "uppercase", fontWeight: 700 }}>Unique ID / Roll No. *</label>
                                    <input
                                        placeholder="e.g. STU-101"
                                        value={identifier}
                                        onChange={(e) => setIdentifier(e.target.value)}
                                        style={{ width: "100%", padding: "8px 10px", fontSize: "12px", borderRadius: "6px", background: "#131a26", border: "1px solid rgba(255,255,255,0.1)", color: "#ffffff" }}
                                    />
                                </div>
                                <div>
                                    <label style={{ fontSize: "10px", color: "#94a3b8", textTransform: "uppercase", fontWeight: 700 }}>Designated Role</label>
                                    <select
                                        value={role}
                                        onChange={(e) => setRole(e.target.value)}
                                        style={{ width: "100%", padding: "8px 10px", fontSize: "12px", borderRadius: "6px", background: "#131a26", border: "1px solid rgba(255,255,255,0.1)", color: "#ffffff" }}
                                    >
                                        {template.defaultRoles.map((r) => (
                                            <option key={r} value={r}>{r.toUpperCase()}</option>
                                        ))}
                                    </select>
                                </div>
                            </div>

                            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: "10px", marginBottom: "10px" }}>
                                <div>
                                    <label style={{ fontSize: "10px", color: "#94a3b8", textTransform: "uppercase", fontWeight: 700 }}>Department / Branch</label>
                                    <input
                                        placeholder="e.g. Computer Science"
                                        value={department}
                                        onChange={(e) => setDepartment(e.target.value)}
                                        style={{ width: "100%", padding: "8px 10px", fontSize: "12px", borderRadius: "6px", background: "#131a26", border: "1px solid rgba(255,255,255,0.1)", color: "#ffffff" }}
                                    />
                                </div>
                                <div>
                                    <label style={{ fontSize: "10px", color: "#94a3b8", textTransform: "uppercase", fontWeight: 700 }}>Permitted Dress Code</label>
                                    <input
                                        placeholder="e.g. Regular School Uniform & Formals"
                                        value={allowedDress}
                                        onChange={(e) => setAllowedDress(e.target.value)}
                                        style={{ width: "100%", padding: "8px 10px", fontSize: "12px", borderRadius: "6px", background: "#131a26", border: "1px solid rgba(255,255,255,0.1)", color: "#ffffff" }}
                                    />
                                </div>
                                <div>
                                    <label style={{ fontSize: "10px", color: "#94a3b8", textTransform: "uppercase", fontWeight: 700 }}>Contact Phone</label>
                                    <input
                                        placeholder="+91 98765 43210"
                                        value={phone}
                                        onChange={(e) => setPhone(e.target.value)}
                                        style={{ width: "100%", padding: "8px 10px", fontSize: "12px", borderRadius: "6px", background: "#131a26", border: "1px solid rgba(255,255,255,0.1)", color: "#ffffff" }}
                                    />
                                </div>
                            </div>

                            <div style={{ display: "flex", justifyContent: "flex-end" }}>
                                <button
                                    type="button"
                                    onClick={handleAddPerson}
                                    style={{ padding: "8px 20px", fontSize: "12px", fontWeight: 700, background: "linear-gradient(135deg, #d4af37 0%, #b8860b 100%)", color: "#0c1017", borderRadius: "6px", cursor: "pointer", border: "none" }}
                                >
                                    + Add to Dataset Roster
                                </button>
                            </div>
                        </div>
                    </div>
                )}

                {/* ── STEP 2: Camera Assignment ── */}
                {step === 2 && (
                    <div style={{ padding: "28px 24px", minHeight: "300px" }}>
                        <h4 style={{ margin: 0, fontSize: "15px", fontWeight: 700, color: "#f8fafc" }}>
                            Step 2: Assign &amp; Name Surveillance Camera
                        </h4>
                        <p style={{ margin: "4px 0 18px 0", fontSize: "12px", color: "#94a3b8" }}>
                            Specify the identifier and tactical location for this live surveillance stream.
                        </p>

                        <div style={{ display: "flex", flexDirection: "column", gap: "14px", maxWidth: "600px" }}>
                            <div>
                                <label style={{ fontSize: "10px", color: "#94a3b8", textTransform: "uppercase", fontWeight: 700 }}>Camera Designated Name *</label>
                                <input
                                    value={cameraName}
                                    onChange={(e) => setCameraName(e.target.value)}
                                    placeholder="e.g. Main Gate Entrance Cam 01"
                                    style={{ width: "100%", padding: "10px 14px", fontSize: "13px", borderRadius: "6px", background: "#131a26", border: "1px solid rgba(255,255,255,0.1)", color: "#ffffff" }}
                                />
                            </div>

                            <div>
                                <label style={{ fontSize: "10px", color: "#94a3b8", textTransform: "uppercase", fontWeight: 700 }}>Physical Deployment Sector</label>
                                <input
                                    value={cameraLocation}
                                    onChange={(e) => setCameraLocation(e.target.value)}
                                    placeholder="e.g. North Gate Turnstiles"
                                    style={{ width: "100%", padding: "10px 14px", fontSize: "13px", borderRadius: "6px", background: "#131a26", border: "1px solid rgba(255,255,255,0.1)", color: "#ffffff" }}
                                />
                            </div>
                        </div>
                    </div>
                )}

                {/* ── STEP 3: Stream Input Port ── */}
                {step === 3 && (
                    <div style={{ padding: "28px 24px", minHeight: "300px" }}>
                        <h4 style={{ margin: 0, fontSize: "15px", fontWeight: 700, color: "#f8fafc" }}>
                            Step 3: Select Video Stream Input Port
                        </h4>
                        <p style={{ margin: "4px 0 18px 0", fontSize: "12px", color: "#94a3b8" }}>
                            Select the hardware input device. External USB ports are auto-detected upon connection.
                        </p>

                        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "12px", marginBottom: "16px" }}>
                            {[
                                { id: "laptop_webcam", icon: "💻", title: "Laptop Integrated Camera", desc: "Front-facing integrated laptop webcam." },
                                { id: "external_usb", icon: "🔌", title: "External USB Port Camera", desc: "Plug-and-play USB webcam or capture card." },
                                { id: "mobile_camera", icon: "📱", title: "Mobile Phone Camera", desc: "Direct browser rear lens or remote stream." },
                                { id: "rtsp", icon: "📡", title: "CCTV / Network IP Stream", desc: "RTSP or network IP surveillance stream." },
                            ].map((opt) => (
                                <div
                                    key={opt.id}
                                    onClick={() => setStreamType(opt.id)}
                                    style={{
                                        padding: "16px",
                                        borderRadius: "8px",
                                        border: `2px solid ${streamType === opt.id ? "#d4af37" : "rgba(255,255,255,0.08)"}`,
                                        background: streamType === opt.id ? "rgba(212, 175, 55, 0.12)" : "rgba(255,255,255,0.02)",
                                        cursor: "pointer",
                                    }}
                                >
                                    <div style={{ fontSize: "22px", marginBottom: "6px" }}>{opt.icon}</div>
                                    <div style={{ fontSize: "13px", fontWeight: 700, color: "#f8fafc" }}>{opt.title}</div>
                                    <div style={{ fontSize: "11px", color: "#94a3b8", marginTop: "4px" }}>{opt.desc}</div>
                                </div>
                            ))}
                        </div>

                        {streamType === "external_usb" && (
                            <div style={{ padding: "14px", background: "rgba(0,0,0,0.3)", borderRadius: "6px", border: "1px solid rgba(255,255,255,0.08)" }}>
                                <label style={{ fontSize: "10px", color: "#94a3b8", textTransform: "uppercase", fontWeight: 700 }}>Detected USB Hardware Ports</label>
                                {externalDevices.length > 0 ? (
                                    <select
                                        value={selectedDeviceId}
                                        onChange={(e) => setSelectedDeviceId(e.target.value)}
                                        style={{ width: "100%", padding: "8px 12px", marginTop: "6px", background: "#131a26", border: "1px solid rgba(255,255,255,0.1)", color: "#ffffff", borderRadius: "6px" }}
                                    >
                                        {externalDevices.map((d, i) => (
                                            <option key={d.deviceId || i} value={d.deviceId}>
                                                {d.label || `USB Video Device Port #${i + 1}`}
                                            </option>
                                        ))}
                                    </select>
                                ) : (
                                    <div style={{ fontSize: "12px", color: "#fbbf24", marginTop: "4px" }}>
                                        🔍 Listening for hardware plug-in... (Connect your USB camera; permission prompt will appear upon launch).
                                    </div>
                                )}
                            </div>
                        )}
                    </div>
                )}

                {/* ── STEP 4: Assign Function & Launch ── */}
                {step === 4 && (
                    <div style={{ padding: "28px 24px", minHeight: "300px" }}>
                        <h4 style={{ margin: 0, fontSize: "15px", fontWeight: 700, color: "#f8fafc" }}>
                            Step 4: Assign Primary AI Operational Function
                        </h4>
                        <p style={{ margin: "4px 0 18px 0", fontSize: "12px", color: "#94a3b8" }}>
                            Select the automated perception and rule evaluation engine for this stream.
                        </p>

                        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "12px" }}>
                            {[
                                { id: "FACE_ATTENDANCE", icon: "🎓", title: "Face Biometric Attendance", desc: "Automated scan, timestamping, deduplication, and mark PRESENT/LATE." },
                                { id: "DRESS_CODE", icon: "👔", title: "Dress Code & Uniform Check", desc: "Formals and regular uniform compliance; flags casual attire & violations." },
                                { id: "EXAM_MONITOR", icon: "📝", title: "Exam Hall Proctoring", desc: "Detects prohibited cell phones, notes, laptops, and cheating postures." },
                                { id: "PERIMETER_INTRUSION", icon: "🛡️", title: "Perimeter & Safety Defense", desc: "Virtual tripwires, unauthorized zone breach alerts, and intruder tracking." },
                            ].map((f) => (
                                <div
                                    key={f.id}
                                    onClick={() => setAssignedFunction(f.id)}
                                    style={{
                                        padding: "16px",
                                        borderRadius: "8px",
                                        border: `2px solid ${assignedFunction === f.id ? "#d4af37" : "rgba(255,255,255,0.08)"}`,
                                        background: assignedFunction === f.id ? "rgba(212, 175, 55, 0.12)" : "rgba(255,255,255,0.02)",
                                        cursor: "pointer",
                                    }}
                                >
                                    <div style={{ fontSize: "22px", marginBottom: "6px" }}>{f.icon}</div>
                                    <div style={{ fontSize: "13px", fontWeight: 700, color: "#f8fafc" }}>{f.title}</div>
                                    <div style={{ fontSize: "11px", color: "#94a3b8", marginTop: "4px" }}>{f.desc}</div>
                                </div>
                            ))}
                        </div>
                    </div>
                )}

                {/* Footer Controls */}
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", padding: "16px 24px", borderTop: "1px solid rgba(255,255,255,0.08)", background: "rgba(0,0,0,0.3)" }}>
                    <div>
                        {step > 1 && (
                            <button
                                type="button"
                                className="tool-btn btn-secondary-mini"
                                onClick={() => setStep(step - 1)}
                                style={{ padding: "8px 16px", fontSize: "12px", color: "#cbd5e1" }}
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
                            style={{ padding: "8px 16px", fontSize: "12px", color: "#cbd5e1" }}
                        >
                            Cancel
                        </button>
                        {step < 4 ? (
                            <button
                                type="button"
                                onClick={() => {
                                    if (step === 1 && peopleList.length === 0) {
                                        setErrorMsg("Please add at least 1 person profile or load the verified dataset.");
                                        return;
                                    }
                                    setErrorMsg("");
                                    setStep(step + 1);
                                }}
                                style={{ padding: "8px 24px", fontSize: "12px", fontWeight: 700, background: "linear-gradient(135deg, #d4af37 0%, #b8860b 100%)", color: "#0c1017", borderRadius: "6px", cursor: "pointer", border: "none" }}
                            >
                                Next Step →
                            </button>
                        ) : (
                            <button
                                type="button"
                                onClick={handleFinalLaunch}
                                disabled={isSubmitting}
                                style={{ padding: "8px 28px", fontSize: "12px", fontWeight: 800, background: "linear-gradient(135deg, #10b981 0%, #059669 100%)", color: "#ffffff", borderRadius: "6px", cursor: "pointer", border: "none", boxShadow: "0 4px 15px rgba(16, 185, 129, 0.3)" }}
                            >
                                {isSubmitting ? "🚀 Initializing..." : "🚀 Launch Live Surveillance"}
                            </button>
                        )}
                    </div>
                </div>
            </div>
        </div>
    );
}
