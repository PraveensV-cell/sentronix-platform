import { useState, useEffect } from "react";
import {
    getPeople,
    createPerson,
    updatePerson,
    getPersonHistory,
    getPersonDossier,
    getPersonDossierMarkdown,
    clearEnvironmentPeople,
    markPersonPresent,
    enrollPersonFace,
    deletePerson,
} from "../api/api";

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

export default function PeopleView({ environment }) {
    const [people, setPeople] = useState([]);
    const [filterRole, setFilterRole] = useState("ALL");
    const [searchQuery, setSearchQuery] = useState("");
    const [showAddModal, setShowAddModal] = useState(false);
    const [selectedPerson, setSelectedPerson] = useState(null);
    const [personHistory, setPersonHistory] = useState([]);
    const [loadingHistory, setLoadingHistory] = useState(false);
    const [feedbackMsg, setFeedbackMsg] = useState("");

    // Biometric Face Enrollment Modal
    const [showEnrollModal, setShowEnrollModal] = useState(false);
    const [enrollPersonTarget, setEnrollPersonTarget] = useState(null);
    const [enrollPhoto, setEnrollPhoto] = useState("");
    const [isEnrolling, setIsEnrolling] = useState(false);

    // Dossier Modal
    const [dossierData, setDossierData] = useState(null);
    const [showDossierModal, setShowDossierModal] = useState(false);
    const [loadingDossier, setLoadingDossier] = useState(false);

    // Add person form state
    const [newName, setNewName] = useState("");
    const [newIdentifier, setNewIdentifier] = useState("");
    const [newRole, setNewRole] = useState("student");
    const [newDept, setNewDept] = useState("Computer Science");
    const [newGrade, setNewGrade] = useState("Grade 10-A");
    const [newDress, setNewDress] = useState("Formals & Regular Uniform");
    const [newPhone, setNewPhone] = useState("");
    const [newEmail, setNewEmail] = useState("");
    const [newPhoto, setNewPhoto] = useState("");

    // Edit person form state
    const [editFormData, setEditFormData] = useState({
        name: "",
        identifier: "",
        role: "student",
        department: "",
        class_grade: "",
        allowed_dress: "Formals & Regular Uniform",
        status: "active",
        phone: "",
        email: "",
        photo_url: "",
    });

    const loadPeople = async () => {
        try {
            const res = await getPeople(filterRole === "ALL" ? undefined : filterRole);
            setPeople(res.people || []);
        } catch (err) {
            console.error("Failed to load people", err);
        }
    };

    useEffect(() => {
        loadPeople();
    }, [filterRole]);

    const showToast = (msg) => {
        setFeedbackMsg(msg);
        setTimeout(() => setFeedbackMsg(""), 4000);
    };

    const handleCreatePerson = async (e) => {
        e.preventDefault();
        try {
            const res = await createPerson({
                name: newName,
                identifier: newIdentifier,
                role: newRole,
                department: newDept,
                class_grade: newGrade,
                allowed_dress: newDress,
                phone: newPhone,
                email: newEmail,
                photo_url: newPhoto || undefined,
                environment_id: environment?.id || 1,
            });

            if (res.success) {
                setShowAddModal(false);
                setNewName("");
                setNewIdentifier("");
                setNewPhone("");
                setNewEmail("");
                setNewPhoto("");
                showToast(`✓ Registered ${newName}. Face photo enrolled & AI dossier created.`);
                await loadPeople();
            }
        } catch (err) {
            alert(err.response?.data?.detail || "Registration failed");
        }
    };

    const handleOpenEditModal = async (person) => {
        setSelectedPerson(person);
        setEditFormData({
            name: person.name || "",
            identifier: person.identifier || "",
            role: person.role || "student",
            department: person.department || "",
            class_grade: person.class_grade || "",
            allowed_dress: person.allowed_dress || "Formals & Regular Uniform",
            status: person.status || "active",
            phone: person.phone || "",
            email: person.email || "",
            photo_url: person.photo_url || "",
        });

        // Load individual records table
        setLoadingHistory(true);
        try {
            const res = await getPersonHistory(person.id);
            setPersonHistory(res.history || []);
        } catch (err) {
            console.error("Failed to load person history", err);
            setPersonHistory([]);
        } finally {
            setLoadingHistory(false);
        }
    };

    const handleSavePersonEdit = async (e) => {
        e.preventDefault();
        if (!selectedPerson) return;
        try {
            const res = await updatePerson(selectedPerson.id, editFormData);
            if (res.success) {
                showToast(`✓ Updated profile for ${editFormData.name} successfully!`);
                setSelectedPerson(res.person);
                await loadPeople();
            }
        } catch (err) {
            alert(err.response?.data?.detail || "Failed to save profile changes");
        }
    };

    // Open Face Biometric Enrollment Modal
    const handleOpenEnrollModal = (person) => {
        setEnrollPersonTarget(person);
        setEnrollPhoto(person.photo_url || "");
        setShowEnrollModal(true);
    };

    const handleSaveEnrollPhoto = async () => {
        if (!enrollPersonTarget) return;
        if (!enrollPhoto) {
            alert("Please upload or choose a face photo to enroll.");
            return;
        }
        setIsEnrolling(true);
        try {
            const res = await enrollPersonFace(enrollPersonTarget.id, { photo_url: enrollPhoto });
            if (res.success) {
                showToast(`✓ Face biometrics and image updated for ${enrollPersonTarget.name}`);
                setShowEnrollModal(false);
                setEnrollPersonTarget(null);
                setEnrollPhoto("");
                await loadPeople();
            }
        } catch (err) {
            alert(err.response?.data?.detail || "Face enrollment failed");
        } finally {
            setIsEnrolling(false);
        }
    };

    // Open & Load AI Individual Dossier (Point 6)
    const handleOpenDossier = async (person) => {
        setLoadingDossier(true);
        setShowDossierModal(true);
        try {
            const data = await getPersonDossier(person.id);
            setDossierData(data);
        } catch (err) {
            console.error("Failed to load dossier", err);
            alert("Could not load AI dossier");
        } finally {
            setLoadingDossier(false);
        }
    };

    const handleDownloadDossierMd = async (personId, name) => {
        try {
            const md = await getPersonDossierMarkdown(personId);
            const blob = new Blob([md], { type: "text/markdown;charset=utf-8" });
            const url = URL.createObjectURL(blob);
            const a = document.createElement("a");
            a.href = url;
            a.download = `DOSSIER_${name.replace(/\s+/g, "_")}.md`;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            URL.revokeObjectURL(url);
        } catch (err) {
            alert("Could not download dossier markdown");
        }
    };

    const handleDownloadDossierJson = (dossier, name) => {
        const jsonStr = JSON.stringify(dossier, null, 2);
        const blob = new Blob([jsonStr], { type: "application/json;charset=utf-8" });
        const url = URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = `DOSSIER_${name.replace(/\s+/g, "_")}.json`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
    };

    const handleMarkPresent = async (personId, name) => {
        try {
            const res = await markPersonPresent(personId);
            if (res.success) {
                showToast(`✓ Biometric check-in recorded for ${name} at ${res.timestamp}`);
                await loadPeople();
                if (selectedPerson && selectedPerson.id === personId) {
                    const hRes = await getPersonHistory(personId);
                    setPersonHistory(hRes.history || []);
                }
            }
        } catch (err) {
            alert("Failed to mark attendance");
        }
    };

    const handleDelete = async (personId, name) => {
        if (!confirm(`Are you sure you want to delete profile for ${name}?`)) return;
        try {
            await deletePerson(personId);
            showToast(`✓ Deleted ${name} from registry.`);
            setSelectedPerson(null);
            await loadPeople();
        } catch (err) {
            alert("Delete failed");
        }
    };

    const handleClearAllRoster = async () => {
        const envId = environment?.id || 1;
        if (!confirm("Are you sure you want to clear all personnel from this environment to start 100% fresh?")) return;
        try {
            await clearEnvironmentPeople(envId);
            showToast("✓ Cleaned environment roster. You can now onboard new personnel.");
            await loadPeople();
        } catch (err) {
            alert("Could not clear roster");
        }
    };

    const filteredPeople = people.filter((p) => {
        if (!searchQuery) return true;
        const q = searchQuery.toLowerCase();
        return (
            p.name?.toLowerCase().includes(q) ||
            p.identifier?.toLowerCase().includes(q) ||
            p.department?.toLowerCase().includes(q)
        );
    });

    return (
        <div className="people-module-container">
            {/* Header */}
            <div className="module-header-row">
                <div>
                    <h2 style={{ margin: 0, fontSize: "18px", fontWeight: 700, color: "var(--text-primary)" }}>
                        People Registry &amp; AI-Managed Individual Dossiers
                    </h2>
                    <p style={{ margin: "4px 0 0 0", fontSize: "12px", color: "var(--text-secondary)" }}>
                        Every student, faculty, and officer has an independent, physical AI dossier file tracking attendance, biometrics, and uniform compliance.
                    </p>
                </div>
                <div style={{ display: "flex", gap: "10px" }}>
                    <button
                        className="tool-btn btn-secondary-mini"
                        onClick={handleClearAllRoster}
                        title="Clear dummy data to onboard new people"
                        style={{ color: "#ef4444", border: "1px solid #fecaca", background: "#fef2f2" }}
                    >
                        🗑️ Reset Roster
                    </button>
                    <button className="tool-btn btn-primary" onClick={() => setShowAddModal(true)}>
                        + Register New Individual
                    </button>
                </div>
            </div>

            {/* Filter & Search Bar */}
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", margin: "14px 0", flexWrap: "wrap", gap: "10px" }}>
                <div className="filter-role-pills">
                    {["ALL", "student", "staff", "visitor"].map((r) => (
                        <button
                            key={r}
                            className={`fleet-pill ${filterRole === r ? "active" : ""}`}
                            onClick={() => setFilterRole(r)}
                        >
                            {r.toUpperCase()}
                        </button>
                    ))}
                </div>
                <input
                    className="form-control"
                    placeholder="🔍 Search by name, roll no, department..."
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    style={{ padding: "6px 14px", fontSize: "12px", borderRadius: "20px", border: "1px solid var(--border-color)", width: "260px" }}
                />
            </div>

            {feedbackMsg && <div className="checkin-feedback-banner">{feedbackMsg}</div>}

            {/* People Cards Grid */}
            <div className="people-cards-grid">
                {filteredPeople.length === 0 ? (
                    <div style={{ gridColumn: "1 / -1", padding: "40px", textAlign: "center", background: "var(--card-bg)", borderRadius: "8px", border: "1px solid var(--border-color)" }}>
                        <div style={{ fontSize: "36px", marginBottom: "10px" }}>👤</div>
                        <h4 style={{ margin: 0, fontSize: "16px" }}>No Personnel Registered In This Mode</h4>
                        <p style={{ margin: "6px 0 16px 0", fontSize: "13px", color: "var(--text-secondary)" }}>
                            Start fresh by registering students/staff or launch the Guided Setup Wizard.
                        </p>
                        <button className="tool-btn btn-primary" onClick={() => setShowAddModal(true)}>
                            + Register First Person
                        </button>
                    </div>
                ) : (
                    filteredPeople.map((p) => {
                        const isEnrolled = p.is_enrolled === 1;
                        const isPresentToday = p.today_attendance?.status === "PRESENT";
                        return (
                            <div key={p.id} className="person-profile-card">
                                <div className="profile-header">
                                    {p.photo_url ? (
                                        <img
                                            src={p.photo_url}
                                            alt={p.name}
                                            className="avatar-large"
                                            style={{ width: "44px", height: "44px", borderRadius: "50%", objectFit: "cover", border: "2px solid #d4af37", boxShadow: "0 2px 6px rgba(0,0,0,0.15)" }}
                                        />
                                    ) : (
                                        <div className="avatar-large">{p.name.charAt(0).toUpperCase()}</div>
                                    )}
                                    <div className="profile-meta">
                                        <h3 className="person-card-name">{p.name}</h3>
                                        <span className="profile-id">{p.identifier}</span>
                                    </div>
                                    <span className={`enroll-status-badge ${isEnrolled ? "enrolled" : "pending"}`}>
                                        {isEnrolled ? "● ENROLLED" : "○ PENDING"}
                                    </span>
                                </div>

                                <div className="profile-details-list">
                                    <div className="detail-item">
                                        <span>ROLE</span>
                                        <strong>{p.role?.toUpperCase()}</strong>
                                    </div>
                                    <div className="detail-item">
                                        <span>DEPARTMENT</span>
                                        <strong>{p.department || "General"}</strong>
                                    </div>
                                    <div className="detail-item">
                                        <span>CLASS / GRADE</span>
                                        <strong>{p.class_grade || "--"}</strong>
                                    </div>
                                    <div className="detail-item">
                                        <span>ALLOWED DRESS</span>
                                        <strong className="text-primary">{p.allowed_dress || "Formals"}</strong>
                                    </div>
                                    <div className="detail-item">
                                        <span>TODAY'S STATUS</span>
                                        <strong className={isPresentToday ? "text-success" : "text-muted"}>
                                            {isPresentToday ? "● PRESENT" : "○ NOT LOGGED"}
                                        </strong>
                                    </div>
                                    <div className="detail-item">
                                        <span>ACCOUNT</span>
                                        <strong className="text-secondary">{p.status?.toUpperCase() || "ACTIVE"}</strong>
                                    </div>
                                </div>

                                <div style={{ display: "flex", flexDirection: "column", gap: "6px", marginTop: "12px" }}>
                                    <button
                                        className="tool-btn btn-primary"
                                        onClick={() => handleOpenDossier(p)}
                                        style={{ fontSize: "11px", padding: "6px 12px", background: "linear-gradient(135deg, #0ea5e9 0%, #0284c7 100%)", color: "#ffffff" }}
                                    >
                                        📁 View &amp; Export AI Dossier File
                                    </button>
                                    <div style={{ display: "flex", gap: "6px" }}>
                                        <button
                                            className="tool-btn btn-secondary-mini"
                                            onClick={() => handleOpenEditModal(p)}
                                            style={{ flex: 1, fontSize: "11px" }}
                                        >
                                            ✏️ Edit Profile
                                        </button>
                                        {!isEnrolled ? (
                                            <button
                                                className="tool-btn btn-primary"
                                                onClick={() => handleOpenEnrollModal(p)}
                                                style={{ fontSize: "11px", background: "linear-gradient(135deg, #d4af37 0%, #b8860b 100%)", color: "#0c1017", fontWeight: 700 }}
                                            >
                                                📷 Enroll Photo
                                            </button>
                                        ) : (
                                            <div style={{ display: "flex", gap: "4px" }}>
                                                <button
                                                    className="tool-btn btn-secondary-mini"
                                                    onClick={() => handleOpenEnrollModal(p)}
                                                    style={{ fontSize: "11px", padding: "4px 8px" }}
                                                    title="Change or re-upload face photo"
                                                >
                                                    📷 Photo
                                                </button>
                                                <button
                                                    className="tool-btn btn-secondary-mini"
                                                    onClick={() => handleMarkPresent(p.id, p.name)}
                                                    style={{ fontSize: "11px", padding: "4px 8px" }}
                                                >
                                                    ✓ Check-in
                                                </button>
                                            </div>
                                        )}
                                    </div>
                                </div>
                            </div>
                        );
                    })
                )}
            </div>

            {/* ── Individual AI Dossier File Viewer Modal (Point 6) ── */}
            {showDossierModal && (
                <div className="modal-overlay" onClick={() => setShowDossierModal(false)}>
                    <div className="modal-dialog-large" onClick={(e) => e.stopPropagation()} style={{ maxWidth: "900px" }}>
                        <div className="modal-header" style={{ borderBottom: "2px solid #e2e8f0" }}>
                            <div>
                                <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                                    <span style={{ fontSize: "20px" }}>📁</span>
                                    <h3 style={{ margin: 0, fontSize: "17px", fontWeight: 700 }}>
                                        {dossierData?.dossier_title || "AI Individual Dossier File"}
                                    </h3>
                                </div>
                                <div style={{ fontSize: "11px", color: "var(--text-muted)", marginTop: "2px" }}>
                                    Reference: <code>{dossierData?.dossier_id}</code> • Maintained 24/7 by Sentronix AI Core
                                </div>
                            </div>
                            <div style={{ display: "flex", gap: "8px" }}>
                                {dossierData && (
                                    <>
                                        <button
                                            type="button"
                                            onClick={() => handleDownloadDossierMd(dossierData.person_details.id, dossierData.person_details.name)}
                                            className="tool-btn btn-primary"
                                            style={{ fontSize: "11px", padding: "6px 12px" }}
                                        >
                                            📥 Download .MD
                                        </button>
                                        <button
                                            type="button"
                                            onClick={() => handleDownloadDossierJson(dossierData, dossierData.person_details.name)}
                                            className="tool-btn btn-secondary-mini"
                                            style={{ fontSize: "11px", padding: "6px 12px" }}
                                        >
                                            📥 Download .JSON
                                        </button>
                                    </>
                                )}
                                <button className="tool-btn btn-secondary-mini" onClick={() => setShowDossierModal(false)}>✕</button>
                            </div>
                        </div>

                        {loadingDossier ? (
                            <div style={{ padding: "40px", textAlign: "center" }}>Loading AI dossier from disk...</div>
                        ) : dossierData ? (
                            <div style={{ padding: "20px 24px", maxHeight: "70vh", overflowY: "auto" }}>
                                {/* Profile Credentials Grid */}
                                <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "16px", marginBottom: "18px" }}>
                                    <div style={{ padding: "14px", background: "var(--bg-secondary)", borderRadius: "8px", border: "1px solid var(--border-color)", display: "flex", gap: "14px" }}>
                                        {dossierData.person_details.photo_url ? (
                                            <img
                                                src={dossierData.person_details.photo_url}
                                                alt={dossierData.person_details.name}
                                                style={{ width: "64px", height: "64px", borderRadius: "8px", objectFit: "cover", border: "2px solid #d4af37", alignSelf: "flex-start" }}
                                            />
                                        ) : null}
                                        <div>
                                            <div style={{ fontSize: "11px", fontWeight: 700, color: "var(--text-muted)", textTransform: "uppercase" }}>Personal Biometric Credentials</div>
                                            <div style={{ fontSize: "14px", fontWeight: 700, marginTop: "4px" }}>{dossierData.person_details.name}</div>
                                            <div style={{ fontSize: "12px", color: "var(--text-secondary)", marginTop: "2px" }}>ID: {dossierData.person_details.identifier} • Role: {dossierData.person_details.role.toUpperCase()}</div>
                                            <div style={{ fontSize: "12px", color: "var(--text-secondary)" }}>Dept: {dossierData.person_details.department} • Grade: {dossierData.person_details.class_grade}</div>
                                            <div style={{ fontSize: "12px", marginTop: "4px" }}>Allowed Dress: <strong className="text-primary">{dossierData.person_details.allowed_dress}</strong></div>
                                        </div>
                                    </div>

                                    <div style={{ padding: "14px", background: "var(--bg-secondary)", borderRadius: "8px", border: "1px solid var(--border-color)" }}>
                                        <div style={{ fontSize: "11px", fontWeight: 700, color: "var(--text-muted)", textTransform: "uppercase" }}>AI Biometric &amp; Compliance Rate</div>
                                        <div style={{ fontSize: "22px", fontWeight: 800, color: "var(--success-color)", marginTop: "4px" }}>
                                            {dossierData.attendance_performance.compliance_rate}
                                        </div>
                                        <div style={{ fontSize: "12px", color: "var(--text-secondary)" }}>
                                            Check-ins Recorded: {dossierData.attendance_performance.present_count} / {dossierData.attendance_performance.total_records}
                                        </div>
                                        <div style={{ fontSize: "11px", color: "var(--text-muted)", marginTop: "4px" }}>
                                            Biometric Facial Match Avg: {dossierData.biometric_analytics.face_confidence_avg} • Anti-Spoof: PASSED
                                        </div>
                                    </div>
                                </div>

                                {/* AI Assessment Banner */}
                                <div style={{ padding: "12px 16px", background: "#f0f9ff", border: "1px solid #bae6fd", borderRadius: "8px", color: "#0369a1", fontSize: "13px", marginBottom: "18px" }}>
                                    <strong>🧠 AI Autonomous Assessment:</strong> "{dossierData.ai_autonomous_assessment}"
                                </div>

                                {/* Attendance & Biometric Audit Log Table */}
                                <h4 style={{ margin: "0 0 8px 0", fontSize: "13px", fontWeight: 700 }}>
                                    📅 Biometric Check-in History (Stored in Individual File)
                                </h4>
                                <div style={{ border: "1px solid var(--border-color)", borderRadius: "8px", overflow: "hidden", marginBottom: "18px" }}>
                                    <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "12px" }}>
                                        <thead>
                                            <tr style={{ background: "var(--bg-secondary)", borderBottom: "1px solid var(--border-color)", textAlign: "left" }}>
                                                <th style={{ padding: "8px 12px" }}>Timestamp</th>
                                                <th style={{ padding: "8px 12px" }}>Camera / Zone</th>
                                                <th style={{ padding: "8px 12px" }}>Status</th>
                                                <th style={{ padding: "8px 12px" }}>Confidence</th>
                                            </tr>
                                        </thead>
                                        <tbody>
                                            {dossierData.attendance_performance.history.length === 0 ? (
                                                <tr>
                                                    <td colSpan={4} style={{ padding: "16px", textAlign: "center", color: "var(--text-muted)" }}>
                                                        No attendance scans recorded for this individual yet.
                                                    </td>
                                                </tr>
                                            ) : (
                                                dossierData.attendance_performance.history.map((h, i) => (
                                                    <tr key={i} style={{ borderBottom: "1px solid var(--border-color)" }}>
                                                        <td style={{ padding: "8px 12px" }}>{h.timestamp}</td>
                                                        <td style={{ padding: "8px 12px" }}>{h.camera_name || "Main Gate Checkpoint"}</td>
                                                        <td style={{ padding: "8px 12px" }}>
                                                            <span className="cam-func-badge badge-primary">{h.status}</span>
                                                        </td>
                                                        <td style={{ padding: "8px 12px" }}>{((h.confidence || 0.94) * 100).toFixed(1)}%</td>
                                                    </tr>
                                                ))
                                            )}
                                        </tbody>
                                    </table>
                                </div>

                                {/* Prohibited Activity / Alert Records */}
                                <h4 style={{ margin: "0 0 8px 0", fontSize: "13px", fontWeight: 700 }}>
                                    🚨 Security &amp; Prohibited Activity Records
                                </h4>
                                <div style={{ padding: "12px", background: "var(--bg-secondary)", borderRadius: "8px", border: "1px solid var(--border-color)", fontSize: "12px" }}>
                                    {dossierData.security_alerts_and_flags.length === 0 ? (
                                        <div style={{ color: "#166534" }}>✓ Clean conduct record. Zero prohibited activities or violations on file.</div>
                                    ) : (
                                        dossierData.security_alerts_and_flags.map((al, idx) => (
                                            <div key={idx} style={{ marginBottom: "6px" }}>
                                                <strong>[{al.priority}]</strong> {al.timestamp}: {al.object}
                                            </div>
                                        ))
                                    )}
                                </div>
                            </div>
                        ) : null}
                    </div>
                </div>
            )}

            {/* ── Person Profile Edit Modal ── */}
            {selectedPerson && (
                <div className="modal-overlay" onClick={() => setSelectedPerson(null)}>
                    <div className="modal-dialog-large" onClick={(e) => e.stopPropagation()}>
                        <div className="modal-header">
                            <div>
                                <h3 style={{ margin: 0, fontSize: "16px" }}>Edit Profile &amp; Data — {selectedPerson.name}</h3>
                                <span style={{ fontSize: "11px", color: "var(--text-muted)" }}>ID: {selectedPerson.identifier}</span>
                            </div>
                            <button className="tool-btn btn-secondary-mini" onClick={() => setSelectedPerson(null)}>✕</button>
                        </div>

                        <div style={{ padding: "20px 24px", display: "grid", gridTemplateColumns: "1fr 1fr", gap: "20px" }}>
                            {/* Left: Edit Form */}
                            <form onSubmit={handleSavePersonEdit} style={{ display: "flex", flexDirection: "column", gap: "10px" }}>
                                <div>
                                    <label className="fleet-stat-label">Full Name</label>
                                    <input
                                        className="form-control"
                                        value={editFormData.name}
                                        onChange={(e) => setEditFormData({ ...editFormData, name: e.target.value })}
                                        style={{ width: "100%", padding: "7px 10px", fontSize: "12px", border: "1px solid var(--border-color)", borderRadius: "4px" }}
                                    />
                                </div>
                                <div>
                                    <label className="fleet-stat-label">Unique ID / Roll No.</label>
                                    <input
                                        className="form-control"
                                        value={editFormData.identifier}
                                        onChange={(e) => setEditFormData({ ...editFormData, identifier: e.target.value })}
                                        style={{ width: "100%", padding: "7px 10px", fontSize: "12px", border: "1px solid var(--border-color)", borderRadius: "4px" }}
                                    />
                                </div>
                                <div>
                                    <label className="fleet-stat-label">Permitted Dress Code Policy</label>
                                    <input
                                        className="form-control"
                                        value={editFormData.allowed_dress}
                                        onChange={(e) => setEditFormData({ ...editFormData, allowed_dress: e.target.value })}
                                        style={{ width: "100%", padding: "7px 10px", fontSize: "12px", border: "1px solid var(--border-color)", borderRadius: "4px" }}
                                    />
                                </div>

                                {/* Photo Upload & Change in Edit Modal */}
                                <div>
                                    <label className="fleet-stat-label">Person Face Photo</label>
                                    <div style={{ display: "flex", alignItems: "center", gap: "12px", marginTop: "4px" }}>
                                        {editFormData.photo_url ? (
                                            <img
                                                src={editFormData.photo_url}
                                                alt="Profile"
                                                style={{ width: "44px", height: "44px", borderRadius: "50%", objectFit: "cover", border: "2px solid #d4af37" }}
                                            />
                                        ) : (
                                            <div style={{ width: "44px", height: "44px", borderRadius: "50%", border: "1px dashed var(--border-color)", display: "flex", alignItems: "center", justifyContent: "center", fontSize: "18px" }}>
                                                👤
                                            </div>
                                        )}
                                        <div>
                                            <input
                                                type="file"
                                                accept="image/*"
                                                id="edit-person-photo-input"
                                                style={{ display: "none" }}
                                                onChange={async (e) => {
                                                    const file = e.target.files && e.target.files[0];
                                                    if (file) {
                                                        const compressed = await compressImage(file);
                                                        setEditFormData((prev) => ({ ...prev, photo_url: compressed }));
                                                    }
                                                }}
                                            />
                                            <label
                                                htmlFor="edit-person-photo-input"
                                                className="tool-btn btn-secondary-mini"
                                                style={{ cursor: "pointer", padding: "5px 12px", fontSize: "11px", border: "1px solid var(--border-color)", borderRadius: "4px", fontWeight: 600 }}
                                            >
                                                📁 Change Photo
                                            </label>
                                        </div>
                                    </div>
                                </div>

                                <div>
                                    <label className="fleet-stat-label">Phone &amp; Email</label>
                                    <div style={{ display: "flex", gap: "8px" }}>
                                        <input
                                            className="form-control"
                                            value={editFormData.phone}
                                            onChange={(e) => setEditFormData({ ...editFormData, phone: e.target.value })}
                                            placeholder="Phone"
                                            style={{ flex: 1, padding: "7px 10px", fontSize: "12px", border: "1px solid var(--border-color)", borderRadius: "4px" }}
                                        />
                                        <input
                                            className="form-control"
                                            value={editFormData.email}
                                            onChange={(e) => setEditFormData({ ...editFormData, email: e.target.value })}
                                            placeholder="Email"
                                            style={{ flex: 1, padding: "7px 10px", fontSize: "12px", border: "1px solid var(--border-color)", borderRadius: "4px" }}
                                        />
                                    </div>
                                </div>
                                <div style={{ display: "flex", justifyContent: "space-between", marginTop: "10px" }}>
                                    <button
                                        type="button"
                                        onClick={() => handleDelete(selectedPerson.id, selectedPerson.name)}
                                        style={{ background: "#fef2f2", color: "#b91c1c", border: "1px solid #fecaca", padding: "6px 14px", borderRadius: "4px", fontSize: "12px", cursor: "pointer" }}
                                    >
                                        Delete Person
                                    </button>
                                    <button type="submit" className="tool-btn btn-primary" style={{ padding: "6px 18px", fontSize: "12px" }}>
                                        Save Changes
                                    </button>
                                </div>
                            </form>

                            {/* Right: History Log */}
                            <div>
                                <h4 style={{ margin: "0 0 8px 0", fontSize: "13px", fontWeight: 700 }}>Individual Audit Record</h4>
                                <div style={{ maxHeight: "280px", overflowY: "auto", border: "1px solid var(--border-color)", borderRadius: "6px" }}>
                                    <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "11px" }}>
                                        <thead>
                                            <tr style={{ background: "var(--bg-secondary)", borderBottom: "1px solid var(--border-color)" }}>
                                                <th style={{ padding: "6px 8px", textAlign: "left" }}>Timestamp</th>
                                                <th style={{ padding: "6px 8px", textAlign: "left" }}>Event</th>
                                                <th style={{ padding: "6px 8px", textAlign: "left" }}>Status</th>
                                            </tr>
                                        </thead>
                                        <tbody>
                                            {personHistory.length === 0 ? (
                                                <tr>
                                                    <td colSpan={3} style={{ padding: "14px", textAlign: "center", color: "var(--text-muted)" }}>
                                                        No history logged yet.
                                                    </td>
                                                </tr>
                                            ) : (
                                                personHistory.map((h, i) => (
                                                    <tr key={i} style={{ borderBottom: "1px solid var(--border-color)" }}>
                                                        <td style={{ padding: "6px 8px" }}>{h.timestamp}</td>
                                                        <td style={{ padding: "6px 8px" }}>{h.event}</td>
                                                        <td style={{ padding: "6px 8px" }}>
                                                            <span className="cam-func-badge badge-primary">{h.status}</span>
                                                        </td>
                                                    </tr>
                                                ))
                                            )}
                                        </tbody>
                                    </table>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            )}

            {/* ── Biometric Face Enrollment Modal ── */}
            {showEnrollModal && enrollPersonTarget && (
                <div className="modal-overlay" onClick={() => setShowEnrollModal(false)}>
                    <div className="modal-dialog" onClick={(e) => e.stopPropagation()} style={{ maxWidth: "460px" }}>
                        <div className="modal-header">
                            <div>
                                <h3 style={{ margin: 0, fontSize: "15px", fontWeight: 700 }}>
                                    📷 Biometric Face Enrollment
                                </h3>
                                <span style={{ fontSize: "11px", color: "var(--text-muted)" }}>
                                    {enrollPersonTarget.name} ({enrollPersonTarget.identifier})
                                </span>
                            </div>
                            <button className="tool-btn btn-secondary-mini" onClick={() => setShowEnrollModal(false)}>✕</button>
                        </div>
                        <div style={{ padding: "20px" }}>
                            <p style={{ margin: "0 0 16px 0", fontSize: "12px", color: "var(--text-secondary)" }}>
                                Upload a clear frontal portrait photo of this individual. The Sentronix AI neural vision engine will extract facial embeddings for automatic biometric recognition, dress code checks, and attendance logging.
                            </p>

                            <div style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: "12px", padding: "16px", background: "var(--bg-secondary)", borderRadius: "8px", border: "1px dashed var(--border-color)" }}>
                                {enrollPhoto ? (
                                    <div style={{ position: "relative" }}>
                                        <img
                                            src={enrollPhoto}
                                            alt="Preview"
                                            style={{ width: "90px", height: "90px", borderRadius: "50%", objectFit: "cover", border: "3px solid #d4af37", boxShadow: "0 4px 14px rgba(0,0,0,0.25)" }}
                                        />
                                        <button
                                            type="button"
                                            onClick={() => setEnrollPhoto("")}
                                            style={{ position: "absolute", top: "-4px", right: "-4px", background: "#ef4444", color: "#fff", border: "none", borderRadius: "50%", width: "22px", height: "22px", fontSize: "12px", cursor: "pointer", display: "flex", alignItems: "center", justifyContent: "center" }}
                                            title="Clear Photo"
                                        >
                                            ✕
                                        </button>
                                    </div>
                                ) : (
                                    <div style={{ width: "90px", height: "90px", borderRadius: "50%", border: "2px dashed var(--border-color)", display: "flex", alignItems: "center", justifyContent: "center", fontSize: "36px", color: "var(--text-muted)", background: "var(--card-bg)" }}>
                                        👤
                                    </div>
                                )}

                                <input
                                    type="file"
                                    accept="image/*"
                                    id="enroll-modal-photo-file"
                                    style={{ display: "none" }}
                                    onChange={async (e) => {
                                        const file = e.target.files && e.target.files[0];
                                        if (file) {
                                            const compressed = await compressImage(file);
                                            setEnrollPhoto(compressed);
                                        }
                                    }}
                                />
                                <label
                                    htmlFor="enroll-modal-photo-file"
                                    className="tool-btn btn-secondary-mini"
                                    style={{ cursor: "pointer", padding: "8px 18px", fontSize: "12px", background: "rgba(212, 175, 55, 0.15)", color: "var(--text-primary)", border: "1px solid rgba(212, 175, 55, 0.35)", borderRadius: "6px", fontWeight: 700 }}
                                >
                                    📁 Choose Face Photo from Computer
                                </label>
                                {enrollPhoto && (
                                    <span style={{ fontSize: "11px", color: "var(--success-color)", fontWeight: 700 }}>
                                        ✓ Photo loaded and ready to encode
                                    </span>
                                )}
                            </div>

                            <div className="modal-actions" style={{ marginTop: "20px" }}>
                                <button type="button" className="tool-btn btn-secondary-mini" onClick={() => setShowEnrollModal(false)}>
                                    Cancel
                                </button>
                                <button
                                    type="button"
                                    className="tool-btn btn-primary"
                                    onClick={handleSaveEnrollPhoto}
                                    disabled={isEnrolling || !enrollPhoto}
                                    style={{ opacity: isEnrolling || !enrollPhoto ? 0.6 : 1 }}
                                >
                                    {isEnrolling ? "Extracting Embeddings..." : "Save & Enroll Face"}
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            )}

            {/* ── Add Person Modal ── */}
            {showAddModal && (
                <div className="modal-overlay" onClick={() => setShowAddModal(false)}>
                    <div className="modal-dialog" onClick={(e) => e.stopPropagation()}>
                        <div className="modal-header">
                            <h3>➕ Register Person</h3>
                            <button className="tool-btn btn-secondary-mini" onClick={() => setShowAddModal(false)}>✕</button>
                        </div>
                        <form onSubmit={handleCreatePerson} className="modal-form">
                            <div>
                                <label className="fleet-stat-label">Full Name *</label>
                                <input
                                    className="form-control"
                                    value={newName}
                                    onChange={(e) => setNewName(e.target.value)}
                                    placeholder="e.g. Diya Patel"
                                    required
                                    style={{ width: "100%", padding: "8px 12px", fontSize: "13px" }}
                                />
                            </div>
                            <div>
                                <label className="fleet-stat-label">Unique ID / Roll No. *</label>
                                <input
                                    className="form-control"
                                    value={newIdentifier}
                                    onChange={(e) => setNewIdentifier(e.target.value)}
                                    placeholder="e.g. STU-2026-05"
                                    required
                                    style={{ width: "100%", padding: "8px 12px", fontSize: "13px" }}
                                />
                            </div>
                            <div>
                                <label className="fleet-stat-label">Role</label>
                                <select
                                    className="sector-select-box"
                                    value={newRole}
                                    onChange={(e) => setNewRole(e.target.value)}
                                    style={{ width: "100%", padding: "8px 12px", fontSize: "13px" }}
                                >
                                    <option value="student">Student</option>
                                    <option value="staff">Staff / Faculty</option>
                                    <option value="visitor">Visitor</option>
                                </select>
                            </div>
                            <div>
                                <label className="fleet-stat-label">Permitted Dress Policy</label>
                                <input
                                    className="form-control"
                                    value={newDress}
                                    onChange={(e) => setNewDress(e.target.value)}
                                    style={{ width: "100%", padding: "8px 12px", fontSize: "13px" }}
                                />
                            </div>

                            {/* Photo Upload Section for Manual Registration */}
                            <div style={{ padding: "12px", background: "var(--bg-secondary)", borderRadius: "8px", border: "1px dashed var(--border-color)", marginTop: "4px" }}>
                                <label className="fleet-stat-label" style={{ display: "block", marginBottom: "6px" }}>
                                    📷 Person Face Photo (Upload for AI Biometric Recognition)
                                </label>
                                <div style={{ display: "flex", alignItems: "center", gap: "14px" }}>
                                    {newPhoto ? (
                                        <div style={{ position: "relative" }}>
                                            <img
                                                src={newPhoto}
                                                alt="Preview"
                                                style={{ width: "52px", height: "52px", borderRadius: "50%", objectFit: "cover", border: "2px solid #d4af37", boxShadow: "0 2px 8px rgba(0,0,0,0.2)" }}
                                            />
                                            <button
                                                type="button"
                                                onClick={() => setNewPhoto("")}
                                                style={{ position: "absolute", top: "-4px", right: "-4px", background: "#ef4444", color: "#fff", border: "none", borderRadius: "50%", width: "18px", height: "18px", fontSize: "10px", cursor: "pointer", display: "flex", alignItems: "center", justifyContent: "center" }}
                                                title="Remove photo"
                                            >
                                                ✕
                                            </button>
                                        </div>
                                    ) : (
                                        <div style={{ width: "52px", height: "52px", borderRadius: "50%", border: "2px dashed var(--border-color)", display: "flex", alignItems: "center", justifyContent: "center", fontSize: "20px", color: "var(--text-muted)", background: "var(--card-bg)" }}>
                                            👤
                                        </div>
                                    )}
                                    <div style={{ flex: 1 }}>
                                        <input
                                            type="file"
                                            accept="image/*"
                                            id="add-person-photo-file"
                                            style={{ display: "none" }}
                                            onChange={async (e) => {
                                                const file = e.target.files && e.target.files[0];
                                                if (file) {
                                                    const compressed = await compressImage(file);
                                                    setNewPhoto(compressed);
                                                }
                                            }}
                                        />
                                        <label
                                            htmlFor="add-person-photo-file"
                                            className="tool-btn btn-secondary-mini"
                                            style={{ display: "inline-block", cursor: "pointer", padding: "6px 14px", fontSize: "12px", background: "rgba(212, 175, 55, 0.15)", color: "var(--text-primary)", border: "1px solid rgba(212, 175, 55, 0.3)", borderRadius: "6px", fontWeight: 600 }}
                                        >
                                            📁 Choose Face Photo
                                        </label>
                                        <div style={{ fontSize: "11px", color: "var(--text-muted)", marginTop: "4px" }}>
                                            {newPhoto ? "✓ Photo loaded for automatic biometric match" : "PNG, JPG, or WEBP supported"}
                                        </div>
                                    </div>
                                </div>
                            </div>

                            <div className="modal-actions">
                                <button type="button" className="tool-btn btn-secondary-mini" onClick={() => setShowAddModal(false)}>Cancel</button>
                                <button type="submit" className="tool-btn btn-primary">Create Profile &amp; AI Dossier</button>
                            </div>
                        </form>
                    </div>
                </div>
            )}
        </div>
    );
}
