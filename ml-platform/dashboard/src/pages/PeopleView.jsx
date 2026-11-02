import { useState, useEffect } from "react";
import {
    getPeople,
    createPerson,
    updatePerson,
    getPersonFolder,
    uploadFileToPersonFolder,
    deleteFileFromPersonFolder,
    getUnknownCaptures,
    getUnknownPhotoUrl,
    getPersonFileUrl,
    clearEnvironmentPeople,
    markPersonPresent,
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

export default function PeopleView({ environment }) {
    const [people, setPeople] = useState([]);
    const [filterRole, setFilterRole] = useState("ALL");
    const [searchQuery, setSearchQuery] = useState("");
    const [feedbackMsg, setFeedbackMsg] = useState("");

    // Registration Modal
    const [showAddModal, setShowAddModal] = useState(false);
    const [newName, setNewName] = useState("");
    const [newIdentifier, setNewIdentifier] = useState("");
    const [newRole, setNewRole] = useState("student");
    const [newDept, setNewDept] = useState("General");
    const [newGrade, setNewGrade] = useState("Standard");
    const [newDress, setNewDress] = useState("Formals & Regular Uniform");
    const [newPhone, setNewPhone] = useState("");
    const [newEmail, setNewEmail] = useState("");
    const [newPhoto, setNewPhoto] = useState("");
    const [isSubmitting, setIsSubmitting] = useState(false);

    // VANTEP AI Physical Folder & Dossier Explorer Modal
    const [showFolderModal, setShowFolderModal] = useState(false);
    const [selectedPerson, setSelectedPerson] = useState(null);
    const [folderData, setFolderData] = useState(null);
    const [folderTab, setFolderTab] = useState("profile"); // 'profile' | 'attendance' | 'violations' | 'files'
    const [loadingFolder, setLoadingFolder] = useState(false);

    // Edit Profile Modal
    const [showEditModal, setShowEditModal] = useState(false);
    const [editFormData, setEditFormData] = useState({});

    // Upload custom file state
    const [uploadCustomFile, setUploadCustomFile] = useState(null);
    const [isUploadingFile, setIsUploadingFile] = useState(false);

    // Unknown Captured Persons Modal
    const [showUnknownModal, setShowUnknownModal] = useState(false);
    const [unknownRecords, setUnknownRecords] = useState([]);
    const [loadingUnknowns, setLoadingUnknowns] = useState(false);

    // Snapshot Viewer Modal
    const [viewSnapshotUrl, setViewSnapshotUrl] = useState(null);

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
        setTimeout(() => setFeedbackMsg(""), 4500);
    };

    const handlePhotoFileChange = async (e) => {
        const file = e.target.files?.[0];
        if (file) {
            const compressed = await compressImage(file);
            setNewPhoto(compressed);
        }
    };

    const handleCreatePerson = async (e) => {
        e.preventDefault();
        if (!newName.trim() || !newIdentifier.trim()) {
            alert("Full Name and Unique ID are required.");
            return;
        }
        if (!newPhoto) {
            alert("High-resolution face photo is mandatory for biometric verification.");
            return;
        }

        setIsSubmitting(true);
        try {
            const res = await createPerson({
                name: newName.trim(),
                identifier: newIdentifier.trim(),
                role: newRole,
                department: newDept.trim() || "General",
                class_grade: newGrade.trim() || "Standard",
                allowed_dress: newDress.trim() || "Formals & Regular Uniform",
                phone: newPhone.trim(),
                email: newEmail.trim(),
                photo_url: newPhoto,
                environment_id: environment?.id || 1,
            });

            if (res.success) {
                setShowAddModal(false);
                setNewName("");
                setNewIdentifier("");
                setNewPhone("");
                setNewEmail("");
                setNewPhoto("");
                showToast(`✓ Registered ${newName}. VANTEP AI initialized physical folder & biometric profile.`);
                await loadPeople();
            }
        } catch (err) {
            alert(err.response?.data?.detail || "Registration failed");
        } finally {
            setIsSubmitting(false);
        }
    };

    const handleOpenFolderModal = async (person) => {
        setSelectedPerson(person);
        setShowFolderModal(true);
        setFolderTab("profile");
        setLoadingFolder(true);
        try {
            const res = await getPersonFolder(person.id);
            setFolderData(res);
        } catch (err) {
            alert("Could not load individual folder data");
            setShowFolderModal(false);
        } finally {
            setLoadingFolder(false);
        }
    };

    const handleUploadCustomDocument = async (e) => {
        e.preventDefault();
        if (!uploadCustomFile || !selectedPerson) return;
        setIsUploadingFile(true);
        try {
            await uploadFileToPersonFolder(selectedPerson.id, uploadCustomFile);
            setUploadCustomFile(null);
            showToast(`✓ Uploaded "${uploadCustomFile.name}" to ${selectedPerson.name}'s folder`);
            const refreshed = await getPersonFolder(selectedPerson.id);
            setFolderData(refreshed);
        } catch (err) {
            alert("Upload failed: " + (err.response?.data?.detail || err.message));
        } finally {
            setIsUploadingFile(false);
        }
    };

    const handleDeleteCustomFile = async (filename) => {
        if (!confirm(`Delete custom file "${filename}" from this person's folder?`)) return;
        try {
            await deleteFileFromPersonFolder(selectedPerson.id, filename);
            showToast(`✓ Deleted "${filename}"`);
            const refreshed = await getPersonFolder(selectedPerson.id);
            setFolderData(refreshed);
        } catch (err) {
            alert(err.response?.data?.detail || "Could not delete file");
        }
    };

    const handleOpenEditModal = (person) => {
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
        setShowEditModal(true);
    };

    const handleSaveEdit = async (e) => {
        e.preventDefault();
        try {
            const res = await updatePerson(selectedPerson.id, editFormData);
            if (res.success) {
                setShowEditModal(false);
                showToast(`✓ Updated profile for ${editFormData.name}`);
                await loadPeople();
                if (showFolderModal) {
                    const refreshed = await getPersonFolder(selectedPerson.id);
                    setFolderData(refreshed);
                }
            }
        } catch (err) {
            alert(err.response?.data?.detail || "Update failed");
        }
    };

    const handleDeletePerson = async (person) => {
        if (!confirm(`Permanently delete ${person.name} (${person.identifier}) and remove their physical dossier folder?`)) return;
        try {
            await deletePerson(person.id);
            showToast(`✓ Deleted ${person.name} and archived folder.`);
            if (showFolderModal && selectedPerson?.id === person.id) {
                setShowFolderModal(false);
            }
            await loadPeople();
        } catch (err) {
            alert("Failed to delete person");
        }
    };

    const handleOpenUnknowns = async () => {
        setShowUnknownModal(true);
        setLoadingUnknowns(true);
        try {
            const envId = environment?.id || 1;
            const res = await getUnknownCaptures(envId);
            setUnknownRecords(res.unknown_records || []);
        } catch (err) {
            console.error("Failed to load unknown captures", err);
        } finally {
            setLoadingUnknowns(false);
        }
    };

    const filteredPeople = people.filter((p) => {
        const q = searchQuery.toLowerCase();
        return (
            p.name?.toLowerCase().includes(q) ||
            p.identifier?.toLowerCase().includes(q) ||
            p.department?.toLowerCase().includes(q)
        );
    });

    return (
        <div className="people-view-container" style={{ padding: "20px 24px" }}>
            {/* Top Command Bar */}
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "18px", flexWrap: "wrap", gap: "12px" }}>
                <div>
                    <h2 style={{ margin: 0, fontSize: "20px", fontWeight: 700, color: "var(--text-primary)" }}>
                        Personnel Registry & VANTEP AI Dossiers
                    </h2>
                    <p style={{ margin: "3px 0 0 0", fontSize: "12px", color: "var(--text-muted)" }}>
                        Physical folder maintained for every individual: Profile, Attendance snapshot log, and Violations proof.
                    </p>
                </div>

                <div style={{ display: "flex", gap: "10px", alignItems: "center" }}>
                    <button
                        type="button"
                        onClick={handleOpenUnknowns}
                        style={{
                            background: "var(--bg-secondary)",
                            border: "1px solid var(--border-color)",
                            color: "var(--text-primary)",
                            borderRadius: "6px",
                            padding: "8px 14px",
                            fontSize: "12px",
                            fontWeight: 600,
                            display: "flex",
                            alignItems: "center",
                            gap: "6px",
                            boxShadow: "var(--card-shadow)",
                        }}
                    >
                        <span>⚠️</span> Unknown Persons Repository
                    </button>

                    <button
                        type="button"
                        onClick={() => setShowAddModal(true)}
                        style={{
                            background: "var(--primary-color)",
                            color: "#ffffff",
                            border: "none",
                            borderRadius: "6px",
                            padding: "8px 16px",
                            fontSize: "12px",
                            fontWeight: 700,
                            display: "flex",
                            alignItems: "center",
                            gap: "6px",
                            boxShadow: "0 2px 6px rgba(0,0,0,0.15)",
                        }}
                    >
                        <span>+</span> Enroll Individual
                    </button>
                </div>
            </div>

            {feedbackMsg && (
                <div style={{ background: "var(--primary-soft)", border: "1px solid var(--primary-color)", color: "var(--text-primary)", padding: "10px 14px", borderRadius: "6px", marginBottom: "16px", fontSize: "12px", fontWeight: 600 }}>
                    {feedbackMsg}
                </div>
            )}

            {/* Filter & Search Bar */}
            <div style={{ display: "flex", gap: "12px", marginBottom: "18px", flexWrap: "wrap" }}>
                <input
                    type="text"
                    placeholder="Search by name, ID (e.g. STU-101), or department..."
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    style={{
                        flex: 1,
                        minWidth: "240px",
                        padding: "8px 12px",
                        borderRadius: "6px",
                        border: "1px solid var(--border-color)",
                        background: "var(--card-bg)",
                        color: "var(--text-primary)",
                        fontSize: "13px",
                    }}
                />

                <div style={{ display: "flex", gap: "6px" }}>
                    {["ALL", "student", "staff", "worker", "officer"].map((r) => (
                        <button
                            key={r}
                            type="button"
                            onClick={() => setFilterRole(r)}
                            style={{
                                padding: "6px 12px",
                                borderRadius: "6px",
                                fontSize: "11px",
                                fontWeight: 700,
                                textTransform: "uppercase",
                                border: filterRole === r ? "1px solid var(--primary-color)" : "1px solid var(--border-color)",
                                background: filterRole === r ? "var(--primary-color)" : "var(--card-bg)",
                                color: filterRole === r ? "#ffffff" : "var(--text-secondary)",
                            }}
                        >
                            {r}
                        </button>
                    ))}
                </div>
            </div>

            {/* Personnel Grid */}
            {filteredPeople.length === 0 ? (
                <div style={{ padding: "48px 20px", textAlign: "center", background: "var(--card-bg)", borderRadius: "8px", border: "1px solid var(--border-color)" }}>
                    <div style={{ fontSize: "36px", marginBottom: "10px" }}>📁</div>
                    <h3 style={{ margin: "0 0 6px 0", fontSize: "16px", color: "var(--text-primary)" }}>No Individuals Enrolled Yet</h3>
                    <p style={{ margin: 0, fontSize: "12px", color: "var(--text-muted)", maxWidth: "480px", marginInline: "auto" }}>
                        Enroll staff, students, or workers above or through the setup wizard. Each individual will automatically receive a dedicated physical folder managed by VANTEP AI.
                    </p>
                </div>
            ) : (
                <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(280px, 1fr))", gap: "16px" }}>
                    {filteredPeople.map((person) => {
                        const todayAtt = person.today_attendance || {};
                        const isPresent = todayAtt.status === "PRESENT" || todayAtt.status === "LATE";
                        return (
                            <div
                                key={person.id}
                                style={{
                                    background: "var(--card-bg)",
                                    border: "1px solid var(--border-color)",
                                    borderRadius: "8px",
                                    padding: "16px",
                                    boxShadow: "var(--card-shadow)",
                                    display: "flex",
                                    flexDirection: "column",
                                    justifyContent: "space-between",
                                }}
                            >
                                <div>
                                    <div style={{ display: "flex", gap: "12px", alignItems: "center", marginBottom: "12px" }}>
                                        <img
                                            src={person.photo_url || "https://images.unsplash.com/photo-1535713875002-d1d0cf377fde?w=150&auto=format&fit=crop"}
                                            alt={person.name}
                                            style={{
                                                width: "52px",
                                                height: "52px",
                                                borderRadius: "6px",
                                                objectFit: "cover",
                                                border: "2px solid var(--primary-color)",
                                                background: "#1e293b",
                                            }}
                                        />
                                        <div style={{ overflow: "hidden" }}>
                                            <div style={{ fontSize: "14px", fontWeight: 700, color: "var(--text-primary)", whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}>
                                                {person.name}
                                            </div>
                                            <div style={{ fontSize: "11px", fontWeight: 600, color: "var(--primary-color)", marginTop: "1px" }}>
                                                {person.identifier} • {person.role?.toUpperCase()}
                                            </div>
                                            <div style={{ fontSize: "11px", color: "var(--text-muted)", marginTop: "1px" }}>
                                                {person.department || "General"}
                                            </div>
                                        </div>
                                    </div>

                                    <div style={{ background: "var(--bg-secondary)", borderRadius: "6px", padding: "8px 10px", fontSize: "11px", marginBottom: "12px" }}>
                                        <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "4px" }}>
                                            <span style={{ color: "var(--text-muted)" }}>Today Attendance:</span>
                                            <span style={{ fontWeight: 700, color: isPresent ? "var(--success-color)" : "var(--danger-color)" }}>
                                                {todayAtt.status || "ABSENT"}
                                            </span>
                                        </div>
                                        <div style={{ display: "flex", justifyContent: "space-between" }}>
                                            <span style={{ color: "var(--text-muted)" }}>Uniform Policy:</span>
                                            <span style={{ fontWeight: 600, color: "var(--text-primary)" }}>{person.allowed_dress || "Formals"}</span>
                                        </div>
                                    </div>
                                </div>

                                <div style={{ display: "flex", gap: "8px", borderTop: "1px solid var(--border-color)", paddingTop: "12px" }}>
                                    <button
                                        type="button"
                                        onClick={() => handleOpenFolderModal(person)}
                                        style={{
                                            flex: 1,
                                            background: "var(--primary-color)",
                                            color: "#ffffff",
                                            padding: "6px 10px",
                                            borderRadius: "4px",
                                            fontSize: "11px",
                                            fontWeight: 700,
                                        }}
                                    >
                                        📁 Open AI Folder
                                    </button>
                                    <button
                                        type="button"
                                        onClick={() => handleOpenEditModal(person)}
                                        style={{
                                            background: "var(--bg-secondary)",
                                            border: "1px solid var(--border-color)",
                                            color: "var(--text-primary)",
                                            padding: "6px 10px",
                                            borderRadius: "4px",
                                            fontSize: "11px",
                                            fontWeight: 600,
                                        }}
                                        title="Edit Profile"
                                    >
                                        ✏️ Edit
                                    </button>
                                    <button
                                        type="button"
                                        onClick={() => handleDeletePerson(person)}
                                        style={{
                                            background: "transparent",
                                            border: "1px solid var(--danger-color)",
                                            color: "var(--danger-color)",
                                            padding: "6px 10px",
                                            borderRadius: "4px",
                                            fontSize: "11px",
                                            fontWeight: 600,
                                        }}
                                        title="Delete Individual"
                                    >
                                        🗑️
                                    </button>
                                </div>
                            </div>
                        );
                    })}
                </div>
            )}

            {/* ─── MODAL 1: ENROLL INDIVIDUAL ────────────────────────────────────────── */}
            {showAddModal && (
                <div style={{ position: "fixed", inset: 0, background: "rgba(0,0,0,0.6)", zIndex: 10000, display: "flex", alignItems: "center", justifyContent: "center", padding: "16px" }}>
                    <div style={{ background: "var(--card-bg)", border: "1px solid var(--border-color)", borderRadius: "10px", padding: "22px", width: "100%", maxWidth: "520px", maxHeight: "90vh", overflowY: "auto", boxShadow: "0 10px 30px rgba(0,0,0,0.3)" }}>
                        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "16px" }}>
                            <h3 style={{ margin: 0, fontSize: "16px", fontWeight: 700, color: "var(--text-primary)" }}>
                                📋 Enroll Individual to VANTEP AI
                            </h3>
                            <button type="button" onClick={() => setShowAddModal(false)} style={{ background: "transparent", border: "none", fontSize: "18px", cursor: "pointer", color: "var(--text-muted)" }}>✕</button>
                        </div>

                        <form onSubmit={handleCreatePerson}>
                            {/* Mandatory Photo Upload */}
                            <div style={{ marginBottom: "14px" }}>
                                <label style={{ display: "block", fontSize: "12px", fontWeight: 700, color: "var(--text-primary)", marginBottom: "6px" }}>
                                    Face Photo (Mandatory with Clean Resolution) *
                                </label>
                                <div style={{ display: "flex", gap: "12px", alignItems: "center" }}>
                                    {newPhoto ? (
                                        <img src={newPhoto} alt="Preview" style={{ width: "64px", height: "64px", borderRadius: "6px", objectFit: "cover", border: "2px solid var(--success-color)" }} />
                                    ) : (
                                        <div style={{ width: "64px", height: "64px", borderRadius: "6px", border: "1px dashed var(--border-color)", display: "flex", alignItems: "center", justifyContent: "center", fontSize: "10px", color: "var(--text-muted)", textAlign: "center" }}>
                                            No Photo
                                        </div>
                                    )}
                                    <input
                                        type="file"
                                        accept="image/*"
                                        onChange={handlePhotoFileChange}
                                        required
                                        style={{ fontSize: "11px", color: "var(--text-primary)" }}
                                    />
                                </div>
                            </div>

                            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "12px", marginBottom: "12px" }}>
                                <div>
                                    <label style={{ display: "block", fontSize: "11px", fontWeight: 700, color: "var(--text-muted)", marginBottom: "4px" }}>Full Name *</label>
                                    <input type="text" value={newName} onChange={(e) => setNewName(e.target.value)} required placeholder="e.g. Johnathan Doe" style={{ width: "100%", padding: "7px 10px", borderRadius: "4px", border: "1px solid var(--border-color)", background: "var(--bg-secondary)", color: "var(--text-primary)" }} />
                                </div>
                                <div>
                                    <label style={{ display: "block", fontSize: "11px", fontWeight: 700, color: "var(--text-muted)", marginBottom: "4px" }}>Unique ID Number *</label>
                                    <input type="text" value={newIdentifier} onChange={(e) => setNewIdentifier(e.target.value)} required placeholder="e.g. STU-201" style={{ width: "100%", padding: "7px 10px", borderRadius: "4px", border: "1px solid var(--border-color)", background: "var(--bg-secondary)", color: "var(--text-primary)" }} />
                                </div>
                            </div>

                            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "12px", marginBottom: "12px" }}>
                                <div>
                                    <label style={{ display: "block", fontSize: "11px", fontWeight: 700, color: "var(--text-muted)", marginBottom: "4px" }}>Role</label>
                                    <select value={newRole} onChange={(e) => setNewRole(e.target.value)} style={{ width: "100%", padding: "7px 10px", borderRadius: "4px", border: "1px solid var(--border-color)", background: "var(--bg-secondary)", color: "var(--text-primary)" }}>
                                        <option value="student">Student</option>
                                        <option value="staff">Faculty / Staff</option>
                                        <option value="worker">Industrial Worker</option>
                                        <option value="officer">Security Officer</option>
                                        <option value="visitor">Visitor</option>
                                    </select>
                                </div>
                                <div>
                                    <label style={{ display: "block", fontSize: "11px", fontWeight: 700, color: "var(--text-muted)", marginBottom: "4px" }}>Department / Division</label>
                                    <input type="text" value={newDept} onChange={(e) => setNewDept(e.target.value)} placeholder="e.g. Physics Department" style={{ width: "100%", padding: "7px 10px", borderRadius: "4px", border: "1px solid var(--border-color)", background: "var(--bg-secondary)", color: "var(--text-primary)" }} />
                                </div>
                            </div>

                            <div style={{ marginBottom: "12px" }}>
                                <label style={{ display: "block", fontSize: "11px", fontWeight: 700, color: "var(--text-muted)", marginBottom: "4px" }}>Permitted Dress Code Standard</label>
                                <input type="text" value={newDress} onChange={(e) => setNewDress(e.target.value)} placeholder="Formals & Regular Uniform" style={{ width: "100%", padding: "7px 10px", borderRadius: "4px", border: "1px solid var(--border-color)", background: "var(--bg-secondary)", color: "var(--text-primary)" }} />
                            </div>

                            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "12px", marginBottom: "16px" }}>
                                <div>
                                    <label style={{ display: "block", fontSize: "11px", fontWeight: 700, color: "var(--text-muted)", marginBottom: "4px" }}>Contact Phone</label>
                                    <input type="text" value={newPhone} onChange={(e) => setNewPhone(e.target.value)} placeholder="+91 ..." style={{ width: "100%", padding: "7px 10px", borderRadius: "4px", border: "1px solid var(--border-color)", background: "var(--bg-secondary)", color: "var(--text-primary)" }} />
                                </div>
                                <div>
                                    <label style={{ display: "block", fontSize: "11px", fontWeight: 700, color: "var(--text-muted)", marginBottom: "4px" }}>Email Address</label>
                                    <input type="email" value={newEmail} onChange={(e) => setNewEmail(e.target.value)} placeholder="user@domain.com" style={{ width: "100%", padding: "7px 10px", borderRadius: "4px", border: "1px solid var(--border-color)", background: "var(--bg-secondary)", color: "var(--text-primary)" }} />
                                </div>
                            </div>

                            <div style={{ display: "flex", justifyContent: "flex-end", gap: "10px" }}>
                                <button type="button" onClick={() => setShowAddModal(false)} style={{ background: "transparent", border: "1px solid var(--border-color)", padding: "8px 14px", borderRadius: "4px", fontSize: "12px", color: "var(--text-primary)" }}>
                                    Cancel
                                </button>
                                <button type="submit" disabled={isSubmitting} style={{ background: "var(--primary-color)", color: "#ffffff", padding: "8px 18px", borderRadius: "4px", fontSize: "12px", fontWeight: 700 }}>
                                    {isSubmitting ? "Enrolling..." : "Complete Enrollment"}
                                </button>
                            </div>
                        </form>
                    </div>
                </div>
            )}

            {/* ─── MODAL 2: VANTEP AI PHYSICAL FOLDER & DOSSIER EXPLORER ────────────────── */}
            {showFolderModal && selectedPerson && (
                <div style={{ position: "fixed", inset: 0, background: "rgba(0,0,0,0.6)", zIndex: 10000, display: "flex", alignItems: "center", justifyContent: "center", padding: "16px" }}>
                    <div style={{ background: "var(--card-bg)", border: "1px solid var(--border-color)", borderRadius: "10px", padding: "20px", width: "100%", maxWidth: "840px", maxHeight: "90vh", overflowY: "auto", boxShadow: "0 12px 36px rgba(0,0,0,0.3)" }}>
                        {/* Folder Header */}
                        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: "14px", borderBottom: "1px solid var(--border-color)", paddingBottom: "12px" }}>
                            <div>
                                <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                                    <span style={{ fontSize: "20px" }}>📁</span>
                                    <h3 style={{ margin: 0, fontSize: "17px", fontWeight: 700, color: "var(--text-primary)" }}>
                                        {selectedPerson.name} ({selectedPerson.identifier})
                                    </h3>
                                    <span style={{ fontSize: "10px", background: "var(--primary-soft)", color: "var(--primary-color)", padding: "2px 8px", borderRadius: "4px", fontWeight: 700 }}>
                                        VANTEP AI MANAGED FOLDER
                                    </span>
                                </div>
                                <div style={{ fontSize: "11px", color: "var(--text-muted)", marginTop: "4px", fontFamily: "monospace" }}>
                                    Physical Path: {folderData?.folder_path || "ml-platform/dossiers/..."}
                                </div>
                            </div>
                            <button type="button" onClick={() => setShowFolderModal(false)} style={{ background: "transparent", border: "none", fontSize: "18px", cursor: "pointer", color: "var(--text-muted)" }}>✕</button>
                        </div>

                        {/* Folder Navigation Tabs */}
                        <div style={{ display: "flex", gap: "8px", marginBottom: "16px", borderBottom: "1px solid var(--border-color)", paddingBottom: "10px" }}>
                            {[
                                { id: "profile", label: "1. Profile & Photo (profile.json)", icon: "👤" },
                                { id: "attendance", label: "2. Attendance Log (attendance.json)", icon: "⏱️" },
                                { id: "violations", label: "3. Violations Log (violations.json)", icon: "🚨" },
                                { id: "files", label: "4. Folder Files & Uploads", icon: "📄" },
                            ].map((tab) => (
                                <button
                                    key={tab.id}
                                    type="button"
                                    onClick={() => setFolderTab(tab.id)}
                                    style={{
                                        padding: "6px 12px",
                                        borderRadius: "4px",
                                        fontSize: "11px",
                                        fontWeight: 700,
                                        border: folderTab === tab.id ? "1px solid var(--primary-color)" : "1px solid transparent",
                                        background: folderTab === tab.id ? "var(--primary-soft)" : "transparent",
                                        color: folderTab === tab.id ? "var(--primary-color)" : "var(--text-muted)",
                                    }}
                                >
                                    {tab.icon} {tab.label}
                                </button>
                            ))}
                        </div>

                        {loadingFolder ? (
                            <div style={{ padding: "30px", textAlign: "center", color: "var(--text-muted)" }}>Loading folder contents from disk...</div>
                        ) : (
                            <>
                                {/* TAB 1: PROFILE & PHOTO */}
                                {folderTab === "profile" && (
                                    <div style={{ display: "grid", gridTemplateColumns: "180px 1fr", gap: "20px" }}>
                                        <div>
                                            <img
                                                src={selectedPerson.photo_url || "https://images.unsplash.com/photo-1535713875002-d1d0cf377fde?w=200&auto=format&fit=crop"}
                                                alt="Subject Photo"
                                                style={{ width: "100%", height: "200px", objectFit: "cover", borderRadius: "6px", border: "2px solid var(--border-color)" }}
                                            />
                                            <div style={{ fontSize: "10px", color: "var(--text-muted)", marginTop: "6px", textAlign: "center" }}>
                                                Photo File: photo.jpg
                                            </div>
                                        </div>

                                        <div>
                                            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "10px", fontSize: "12px", marginBottom: "16px" }}>
                                                <div><strong>Name:</strong> {selectedPerson.name}</div>
                                                <div><strong>Unique ID:</strong> {selectedPerson.identifier}</div>
                                                <div><strong>Role:</strong> {selectedPerson.role?.toUpperCase()}</div>
                                                <div><strong>Department:</strong> {selectedPerson.department || "General"}</div>
                                                <div><strong>Allowed Dress:</strong> {selectedPerson.allowed_dress || "Formals"}</div>
                                                <div><strong>Contact Phone:</strong> {selectedPerson.phone || "N/A"}</div>
                                                <div><strong>Email:</strong> {selectedPerson.email || "N/A"}</div>
                                                <div><strong>Status:</strong> {selectedPerson.status?.toUpperCase() || "ACTIVE"}</div>
                                            </div>

                                            <div style={{ display: "flex", gap: "10px" }}>
                                                <button
                                                    type="button"
                                                    onClick={() => handleOpenEditModal(selectedPerson)}
                                                    style={{ background: "var(--primary-color)", color: "#ffffff", padding: "6px 14px", borderRadius: "4px", fontSize: "11px", fontWeight: 700 }}
                                                >
                                                    ✏️ Edit Profile Details
                                                </button>
                                                <button
                                                    type="button"
                                                    onClick={() => {
                                                        const pUrl = getPersonFileUrl(selectedPerson.id, "profile.json");
                                                        window.open(pUrl, "_blank");
                                                    }}
                                                    style={{ background: "var(--bg-secondary)", border: "1px solid var(--border-color)", color: "var(--text-primary)", padding: "6px 14px", borderRadius: "4px", fontSize: "11px", fontWeight: 600 }}
                                                >
                                                    View Raw profile.json
                                                </button>
                                            </div>
                                        </div>
                                    </div>
                                )}

                                {/* TAB 2: ATTENDANCE LOG */}
                                {folderTab === "attendance" && (
                                    <div>
                                        <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "10px", fontSize: "12px" }}>
                                            <span style={{ fontWeight: 700, color: "var(--text-primary)" }}>
                                                Total Check-in Records: {folderData?.attendance?.records?.length || 0}
                                            </span>
                                            <button
                                                type="button"
                                                onClick={async () => {
                                                    await markPersonPresent(selectedPerson.id);
                                                    showToast("✓ Marked present manually");
                                                    const res = await getPersonFolder(selectedPerson.id);
                                                    setFolderData(res);
                                                }}
                                                style={{ background: "var(--success-color)", color: "#ffffff", padding: "4px 10px", borderRadius: "4px", fontSize: "11px", fontWeight: 700 }}
                                            >
                                                + Mark Present Today
                                            </button>
                                        </div>

                                        {(!folderData?.attendance?.records || folderData.attendance.records.length === 0) ? (
                                            <div style={{ padding: "20px", textAlign: "center", color: "var(--text-muted)", fontSize: "12px" }}>
                                                No attendance check-ins recorded yet for this individual.
                                            </div>
                                        ) : (
                                            <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "11px" }}>
                                                <thead>
                                                    <tr style={{ background: "var(--bg-secondary)", textAlign: "left" }}>
                                                        <th style={{ padding: "8px", borderBottom: "1px solid var(--border-color)" }}>Date & Time</th>
                                                        <th style={{ padding: "8px", borderBottom: "1px solid var(--border-color)" }}>Status</th>
                                                        <th style={{ padding: "8px", borderBottom: "1px solid var(--border-color)" }}>Camera</th>
                                                        <th style={{ padding: "8px", borderBottom: "1px solid var(--border-color)" }}>Location</th>
                                                        <th style={{ padding: "8px", borderBottom: "1px solid var(--border-color)" }}>Snapshot Proof</th>
                                                    </tr>
                                                </thead>
                                                <tbody>
                                                    {folderData.attendance.records.map((r, i) => (
                                                        <tr key={i} style={{ borderBottom: "1px solid var(--border-color)" }}>
                                                            <td style={{ padding: "8px" }}>{r.timestamp}</td>
                                                            <td style={{ padding: "8px", fontWeight: 700, color: r.status === "PRESENT" ? "var(--success-color)" : "var(--warning-color)" }}>
                                                                {r.status}
                                                            </td>
                                                            <td style={{ padding: "8px" }}>{r.camera}</td>
                                                            <td style={{ padding: "8px" }}>{r.location}</td>
                                                            <td style={{ padding: "8px" }}>
                                                                {r.snapshot_file ? (
                                                                    <button
                                                                        type="button"
                                                                        onClick={() => setViewSnapshotUrl(getPersonFileUrl(selectedPerson.id, r.snapshot_file))}
                                                                        style={{ background: "var(--bg-secondary)", border: "1px solid var(--border-color)", padding: "2px 8px", borderRadius: "4px", fontSize: "10px", color: "var(--primary-color)", fontWeight: 700 }}
                                                                    >
                                                                        📷 View Proof
                                                                    </button>
                                                                ) : (
                                                                    <span style={{ color: "var(--text-muted)" }}>Verified</span>
                                                                )}
                                                            </td>
                                                        </tr>
                                                    ))}
                                                </tbody>
                                            </table>
                                        )}
                                    </div>
                                )}

                                {/* TAB 3: VIOLATIONS LOG */}
                                {folderTab === "violations" && (
                                    <div>
                                        <div style={{ marginBottom: "10px", fontSize: "12px", fontWeight: 700, color: "var(--text-primary)" }}>
                                            Total Logged Violations & Malpractice: {folderData?.violations?.violations?.length || 0}
                                        </div>

                                        {(!folderData?.violations?.violations || folderData.violations.violations.length === 0) ? (
                                            <div style={{ padding: "24px", textAlign: "center", color: "var(--success-color)", fontSize: "12px", background: "var(--bg-secondary)", borderRadius: "6px" }}>
                                                ✓ Clean Standing — No dress code violations, safety PPE infractions, or malpractice logged by VANTEP AI.
                                            </div>
                                        ) : (
                                            <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "11px" }}>
                                                <thead>
                                                    <tr style={{ background: "var(--bg-secondary)", textAlign: "left" }}>
                                                        <th style={{ padding: "8px", borderBottom: "1px solid var(--border-color)" }}>Timestamp</th>
                                                        <th style={{ padding: "8px", borderBottom: "1px solid var(--border-color)" }}>Type</th>
                                                        <th style={{ padding: "8px", borderBottom: "1px solid var(--border-color)" }}>Description</th>
                                                        <th style={{ padding: "8px", borderBottom: "1px solid var(--border-color)" }}>Camera</th>
                                                        <th style={{ padding: "8px", borderBottom: "1px solid var(--border-color)" }}>Proof Snapshot</th>
                                                    </tr>
                                                </thead>
                                                <tbody>
                                                    {folderData.violations.violations.map((v, i) => (
                                                        <tr key={i} style={{ borderBottom: "1px solid var(--border-color)" }}>
                                                            <td style={{ padding: "8px" }}>{v.timestamp}</td>
                                                            <td style={{ padding: "8px", fontWeight: 700, color: "var(--danger-color)" }}>{v.type}</td>
                                                            <td style={{ padding: "8px" }}>{v.description}</td>
                                                            <td style={{ padding: "8px" }}>{v.camera}</td>
                                                            <td style={{ padding: "8px" }}>
                                                                {v.proof_file ? (
                                                                    <button
                                                                        type="button"
                                                                        onClick={() => setViewSnapshotUrl(getPersonFileUrl(selectedPerson.id, v.proof_file))}
                                                                        style={{ background: "var(--danger-color)", color: "#ffffff", border: "none", padding: "2px 8px", borderRadius: "4px", fontSize: "10px", fontWeight: 700 }}
                                                                    >
                                                                        🚨 View Proof Photo
                                                                    </button>
                                                                ) : (
                                                                    <span style={{ color: "var(--text-muted)" }}>Flagged</span>
                                                                )}
                                                            </td>
                                                        </tr>
                                                    ))}
                                                </tbody>
                                            </table>
                                        )}
                                    </div>
                                )}

                                {/* TAB 4: FOLDER FILES & UPLOADS */}
                                {folderTab === "files" && (
                                    <div>
                                        {/* Upload Custom File Box */}
                                        <div style={{ background: "var(--bg-secondary)", border: "1px dashed var(--border-color)", padding: "12px", borderRadius: "6px", marginBottom: "16px" }}>
                                            <div style={{ fontSize: "11px", fontWeight: 700, color: "var(--text-primary)", marginBottom: "6px" }}>
                                                Upload Additional Document / File to this Person's Folder
                                            </div>
                                            <form onSubmit={handleUploadCustomDocument} style={{ display: "flex", gap: "10px", alignItems: "center" }}>
                                                <input
                                                    type="file"
                                                    onChange={(e) => setUploadCustomFile(e.target.files?.[0] || null)}
                                                    required
                                                    style={{ fontSize: "11px", color: "var(--text-primary)" }}
                                                />
                                                <button
                                                    type="submit"
                                                    disabled={!uploadCustomFile || isUploadingFile}
                                                    style={{ background: "var(--primary-color)", color: "#ffffff", padding: "6px 14px", borderRadius: "4px", fontSize: "11px", fontWeight: 700 }}
                                                >
                                                    {isUploadingFile ? "Uploading..." : "Upload File"}
                                                </button>
                                            </form>
                                        </div>

                                        <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "11px" }}>
                                            <thead>
                                                <tr style={{ background: "var(--bg-secondary)", textAlign: "left" }}>
                                                    <th style={{ padding: "8px", borderBottom: "1px solid var(--border-color)" }}>File Name</th>
                                                    <th style={{ padding: "8px", borderBottom: "1px solid var(--border-color)" }}>Size</th>
                                                    <th style={{ padding: "8px", borderBottom: "1px solid var(--border-color)" }}>Last Modified</th>
                                                    <th style={{ padding: "8px", borderBottom: "1px solid var(--border-color)", textAlign: "right" }}>Actions</th>
                                                </tr>
                                            </thead>
                                            <tbody>
                                                {(folderData?.files || []).map((file, i) => (
                                                    <tr key={i} style={{ borderBottom: "1px solid var(--border-color)" }}>
                                                        <td style={{ padding: "8px", fontWeight: file.is_core ? 700 : 500, color: file.is_core ? "var(--primary-color)" : "var(--text-primary)" }}>
                                                            {file.is_core ? "🔒 " : "📄 "} {file.filename}
                                                        </td>
                                                        <td style={{ padding: "8px" }}>{(file.size_bytes / 1024).toFixed(1)} KB</td>
                                                        <td style={{ padding: "8px" }}>{file.last_modified}</td>
                                                        <td style={{ padding: "8px", textAlign: "right" }}>
                                                            <a
                                                                href={getPersonFileUrl(selectedPerson.id, file.filename)}
                                                                target="_blank"
                                                                rel="noopener noreferrer"
                                                                style={{ marginRight: "8px", color: "var(--primary-color)", fontWeight: 600, textDecoration: "none" }}
                                                            >
                                                                Download
                                                            </a>
                                                            {!file.is_core && (
                                                                <button
                                                                    type="button"
                                                                    onClick={() => handleDeleteCustomFile(file.filename)}
                                                                    style={{ background: "transparent", border: "none", color: "var(--danger-color)", cursor: "pointer", fontSize: "11px", fontWeight: 600 }}
                                                                >
                                                                    Delete
                                                                </button>
                                                            )}
                                                        </td>
                                                    </tr>
                                                ))}
                                            </tbody>
                                        </table>
                                    </div>
                                )}
                            </>
                        )}
                    </div>
                </div>
            )}

            {/* ─── MODAL 3: EDIT PROFILE ────────────────────────────────────────────── */}
            {showEditModal && selectedPerson && (
                <div style={{ position: "fixed", inset: 0, background: "rgba(0,0,0,0.6)", zIndex: 10001, display: "flex", alignItems: "center", justifyContent: "center", padding: "16px" }}>
                    <div style={{ background: "var(--card-bg)", border: "1px solid var(--border-color)", borderRadius: "10px", padding: "20px", width: "100%", maxWidth: "480px", boxShadow: "0 10px 30px rgba(0,0,0,0.3)" }}>
                        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "14px" }}>
                            <h3 style={{ margin: 0, fontSize: "15px", fontWeight: 700, color: "var(--text-primary)" }}>
                                ✏️ Edit Profile: {selectedPerson.name}
                            </h3>
                            <button type="button" onClick={() => setShowEditModal(false)} style={{ background: "transparent", border: "none", fontSize: "18px", cursor: "pointer", color: "var(--text-muted)" }}>✕</button>
                        </div>

                        <form onSubmit={handleSaveEdit}>
                            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "10px", marginBottom: "10px" }}>
                                <div>
                                    <label style={{ display: "block", fontSize: "11px", fontWeight: 700, color: "var(--text-muted)", marginBottom: "4px" }}>Name</label>
                                    <input type="text" value={editFormData.name} onChange={(e) => setEditFormData({ ...editFormData, name: e.target.value })} required style={{ width: "100%", padding: "7px 10px", borderRadius: "4px", border: "1px solid var(--border-color)", background: "var(--bg-secondary)", color: "var(--text-primary)" }} />
                                </div>
                                <div>
                                    <label style={{ display: "block", fontSize: "11px", fontWeight: 700, color: "var(--text-muted)", marginBottom: "4px" }}>Unique ID</label>
                                    <input type="text" value={editFormData.identifier} onChange={(e) => setEditFormData({ ...editFormData, identifier: e.target.value })} required style={{ width: "100%", padding: "7px 10px", borderRadius: "4px", border: "1px solid var(--border-color)", background: "var(--bg-secondary)", color: "var(--text-primary)" }} />
                                </div>
                            </div>

                            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "10px", marginBottom: "10px" }}>
                                <div>
                                    <label style={{ display: "block", fontSize: "11px", fontWeight: 700, color: "var(--text-muted)", marginBottom: "4px" }}>Role</label>
                                    <select value={editFormData.role} onChange={(e) => setEditFormData({ ...editFormData, role: e.target.value })} style={{ width: "100%", padding: "7px 10px", borderRadius: "4px", border: "1px solid var(--border-color)", background: "var(--bg-secondary)", color: "var(--text-primary)" }}>
                                        <option value="student">Student</option>
                                        <option value="staff">Staff</option>
                                        <option value="worker">Worker</option>
                                        <option value="officer">Officer</option>
                                        <option value="visitor">Visitor</option>
                                    </select>
                                </div>
                                <div>
                                    <label style={{ display: "block", fontSize: "11px", fontWeight: 700, color: "var(--text-muted)", marginBottom: "4px" }}>Department</label>
                                    <input type="text" value={editFormData.department} onChange={(e) => setEditFormData({ ...editFormData, department: e.target.value })} style={{ width: "100%", padding: "7px 10px", borderRadius: "4px", border: "1px solid var(--border-color)", background: "var(--bg-secondary)", color: "var(--text-primary)" }} />
                                </div>
                            </div>

                            <div style={{ marginBottom: "10px" }}>
                                <label style={{ display: "block", fontSize: "11px", fontWeight: 700, color: "var(--text-muted)", marginBottom: "4px" }}>Allowed Dress Code</label>
                                <input type="text" value={editFormData.allowed_dress} onChange={(e) => setEditFormData({ ...editFormData, allowed_dress: e.target.value })} style={{ width: "100%", padding: "7px 10px", borderRadius: "4px", border: "1px solid var(--border-color)", background: "var(--bg-secondary)", color: "var(--text-primary)" }} />
                            </div>

                            <div style={{ display: "flex", justifyContent: "flex-end", gap: "8px", marginTop: "14px" }}>
                                <button type="button" onClick={() => setShowEditModal(false)} style={{ background: "transparent", border: "1px solid var(--border-color)", padding: "6px 12px", borderRadius: "4px", fontSize: "11px", color: "var(--text-primary)" }}>Cancel</button>
                                <button type="submit" style={{ background: "var(--primary-color)", color: "#ffffff", padding: "6px 14px", borderRadius: "4px", fontSize: "11px", fontWeight: 700 }}>Save Changes</button>
                            </div>
                        </form>
                    </div>
                </div>
            )}

            {/* ─── MODAL 4: UNKNOWN PERSONS REPOSITORY ──────────────────────────────── */}
            {showUnknownModal && (
                <div style={{ position: "fixed", inset: 0, background: "rgba(0,0,0,0.6)", zIndex: 10000, display: "flex", alignItems: "center", justifyContent: "center", padding: "16px" }}>
                    <div style={{ background: "var(--card-bg)", border: "1px solid var(--border-color)", borderRadius: "10px", padding: "20px", width: "100%", maxWidth: "800px", maxHeight: "88vh", overflowY: "auto", boxShadow: "0 12px 36px rgba(0,0,0,0.3)" }}>
                        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "14px", borderBottom: "1px solid var(--border-color)", paddingBottom: "10px" }}>
                            <div>
                                <h3 style={{ margin: 0, fontSize: "16px", fontWeight: 700, color: "var(--text-primary)" }}>
                                    ⚠️ Unidentified Persons Repository (VANTEP AI Capture)
                                </h3>
                                <p style={{ margin: "2px 0 0 0", fontSize: "11px", color: "var(--text-muted)" }}>
                                    Faces captured in attendance & surveillance mode that do not match registered records.
                                </p>
                            </div>
                            <button type="button" onClick={() => setShowUnknownModal(false)} style={{ background: "transparent", border: "none", fontSize: "18px", cursor: "pointer", color: "var(--text-muted)" }}>✕</button>
                        </div>

                        {loadingUnknowns ? (
                            <div style={{ padding: "30px", textAlign: "center", color: "var(--text-muted)" }}>Loading captured unknowns...</div>
                        ) : unknownRecords.length === 0 ? (
                            <div style={{ padding: "36px", textAlign: "center", color: "var(--text-muted)", fontSize: "12px" }}>
                                No unidentified individuals captured yet. When an unregistered face appears in front of an attendance camera, VANTEP AI will store their snapshot here automatically.
                            </div>
                        ) : (
                            <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(220px, 1fr))", gap: "14px" }}>
                                {unknownRecords.map((unk) => {
                                    const photoUrl = getUnknownPhotoUrl(environment?.id || 1, unk.photo_file);
                                    return (
                                        <div key={unk.id} style={{ background: "var(--bg-secondary)", borderRadius: "6px", border: "1px solid var(--border-color)", padding: "10px" }}>
                                            <img
                                                src={photoUrl}
                                                alt="Unknown Subject"
                                                style={{ width: "100%", height: "140px", objectFit: "cover", borderRadius: "4px", marginBottom: "8px", border: "1px solid var(--border-color)" }}
                                                onClick={() => setViewSnapshotUrl(photoUrl)}
                                            />
                                            <div style={{ fontSize: "11px", fontWeight: 700, color: "var(--warning-color)" }}>
                                                {unk.id} ({unk.estimated_gender?.toUpperCase()})
                                            </div>
                                            <div style={{ fontSize: "10px", color: "var(--text-muted)", marginTop: "2px" }}>
                                                {unk.timestamp}
                                            </div>
                                            <div style={{ fontSize: "10px", color: "var(--text-secondary)", marginTop: "2px" }}>
                                                Camera: {unk.camera_name}
                                            </div>
                                        </div>
                                    );
                                })}
                            </div>
                        )}
                    </div>
                </div>
            )}

            {/* ─── MODAL 5: SNAPSHOT VIEWER ────────────────────────────────────────── */}
            {viewSnapshotUrl && (
                <div style={{ position: "fixed", inset: 0, background: "rgba(0,0,0,0.85)", zIndex: 10002, display: "flex", alignItems: "center", justifyContent: "center", padding: "16px" }} onClick={() => setViewSnapshotUrl(null)}>
                    <div style={{ maxWidth: "90vw", maxHeight: "90vh", background: "var(--card-bg)", padding: "12px", borderRadius: "8px" }} onClick={(e) => e.stopPropagation()}>
                        <img src={viewSnapshotUrl} alt="Evidence Snapshot" style={{ maxWidth: "100%", maxHeight: "75vh", objectFit: "contain", borderRadius: "4px" }} />
                        <div style={{ display: "flex", justifyContent: "space-between", marginTop: "10px" }}>
                            <span style={{ fontSize: "11px", color: "var(--text-muted)" }}>VANTEP AI Evidence Capture</span>
                            <button type="button" onClick={() => setViewSnapshotUrl(null)} style={{ background: "var(--primary-color)", color: "#ffffff", padding: "4px 12px", borderRadius: "4px", fontSize: "11px", fontWeight: 700 }}>Close</button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}
