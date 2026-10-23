import { useState, useEffect } from "react";
import {
    getPeople,
    createPerson,
    updatePerson,
    getPersonHistory,
    markPersonPresent,
    enrollPersonFace,
    deletePerson,
} from "../api/api";

export default function PeopleView() {
    const [people, setPeople] = useState([]);
    const [filterRole, setFilterRole] = useState("ALL");
    const [searchQuery, setSearchQuery] = useState("");
    const [showAddModal, setShowAddModal] = useState(false);
    const [selectedPerson, setSelectedPerson] = useState(null);
    const [personHistory, setPersonHistory] = useState([]);
    const [loadingHistory, setLoadingHistory] = useState(false);
    const [feedbackMsg, setFeedbackMsg] = useState("");

    // Add person form state
    const [newName, setNewName] = useState("");
    const [newIdentifier, setNewIdentifier] = useState("");
    const [newRole, setNewRole] = useState("student");
    const [newDept, setNewDept] = useState("Computer Science");
    const [newGrade, setNewGrade] = useState("Grade 10-A");
    const [newDress, setNewDress] = useState("Formals & Regular Uniform");
    const [newPhone, setNewPhone] = useState("");
    const [newEmail, setNewEmail] = useState("");

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
            });

            if (res.success) {
                setShowAddModal(false);
                setNewName("");
                setNewIdentifier("");
                setNewPhone("");
                setNewEmail("");
                showToast(`✓ Registered ${newName}. Profile created successfully.`);
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
            alert(err.response?.data?.detail || "Failed to update person");
        }
    };

    const handleMarkPresentNow = async () => {
        if (!selectedPerson) return;
        try {
            const res = await markPersonPresent(selectedPerson.id);
            if (res.success) {
                showToast(`✓ Marked ${selectedPerson.name} as PRESENT for today!`);
                const histRes = await getPersonHistory(selectedPerson.id);
                setPersonHistory(histRes.history || []);
                await loadPeople();
            }
        } catch (err) {
            alert("Could not mark present");
        }
    };

    const handleEnrollFace = async (person) => {
        try {
            const res = await enrollPersonFace(person.id);
            if (res.success) {
                showToast(`✓ Face enrolled & neural vector generated for ${person.name}!`);
                await loadPeople();
            }
        } catch (err) {
            alert(err.response?.data?.detail || "Face enrollment failed");
        }
    };

    const handleDeletePerson = async (personId) => {
        if (!window.confirm("Are you sure you want to delete this person profile and their records?")) return;
        try {
            await deletePerson(personId);
            setSelectedPerson(null);
            showToast("Profile removed from registry.");
            await loadPeople();
        } catch (err) {
            alert("Delete failed");
        }
    };

    const showToast = (msg) => {
        setFeedbackMsg(msg);
        setTimeout(() => setFeedbackMsg(""), 4500);
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
            {/* Header Row */}
            <div className="module-header-row">
                <div>
                    <h2>People & Identity Registry</h2>
                    <p>Enrolled Student, Staff & Personnel Database • Profile & Records Management</p>
                </div>
                <div className="attendance-action-group">
                    <input
                        type="text"
                        placeholder="🔍 Search by name or ID..."
                        className="table-search-field"
                        value={searchQuery}
                        onChange={(e) => setSearchQuery(e.target.value)}
                    />
                    <div className="filter-role-pills">
                        {["ALL", "student", "staff", "visitor"].map((r) => (
                            <button
                                key={r}
                                className={`filter-tab ${filterRole === r ? "active" : ""}`}
                                onClick={() => setFilterRole(r)}
                            >
                                {r.toUpperCase()}
                            </button>
                        ))}
                    </div>
                    <button className="btn-primary" onClick={() => setShowAddModal(true)}>
                        + Register Person
                    </button>
                </div>
            </div>

            {feedbackMsg && <div className="checkin-feedback-banner">{feedbackMsg}</div>}

            {/* People Cards Grid */}
            <div className="people-cards-grid">
                {filteredPeople.map((p) => {
                    const isEnrolled = p.is_enrolled === 1;
                    const isPresentToday = p.today_attendance?.status === "PRESENT";
                    return (
                        <div key={p.id} className="person-profile-card">
                            <div className="profile-header">
                                <div className="avatar-large">{p.name.charAt(0)}</div>
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

                            <div className="profile-card-actions-row">
                                <button
                                    className="btn-inspect-mini full-width"
                                    onClick={() => handleOpenEditModal(p)}
                                >
                                    📝 Edit Profile & Records Table
                                </button>
                                {!isEnrolled ? (
                                    <button
                                        className="btn-primary-mini"
                                        onClick={() => handleEnrollFace(p)}
                                    >
                                        📷 Enroll Face
                                    </button>
                                ) : (
                                    <button
                                        className="btn-secondary-mini"
                                        onClick={() => handleEnrollFace(p)}
                                        title="Re-scan face vector"
                                    >
                                        🔄 Re-enroll
                                    </button>
                                )}
                            </div>
                        </div>
                    );
                })}
            </div>

            {/* ── Person Data Modification Window (Profile Editor & Individual Table) ── */}
            {selectedPerson && (
                <div className="modal-overlay" onClick={() => setSelectedPerson(null)}>
                    <div className="modal-dialog-large" onClick={(e) => e.stopPropagation()}>
                        <div className="modal-header">
                            <div className="modal-title-group">
                                <h3>Data Modification Window — {selectedPerson.name}</h3>
                                <span className="profile-id-chip">ID: {selectedPerson.identifier}</span>
                            </div>
                            <button className="close-btn" onClick={() => setSelectedPerson(null)}>
                                ×
                            </button>
                        </div>

                        <div className="modal-two-column-body">
                            {/* Left Column: Editable Profile Data Form */}
                            <div className="modal-column-left">
                                <h4 className="section-subtitle">👤 Modify Individual Profile Data</h4>
                                <form onSubmit={handleSavePersonEdit} className="person-edit-form">
                                    <div className="form-group">
                                        <label>Full Name (Editable)</label>
                                        <input
                                            type="text"
                                            value={editFormData.name}
                                            onChange={(e) =>
                                                setEditFormData({ ...editFormData, name: e.target.value })
                                            }
                                            required
                                        />
                                    </div>

                                    <div className="form-row">
                                        <div className="form-group">
                                            <label>Identifier (Student / Staff ID)</label>
                                            <input
                                                type="text"
                                                value={editFormData.identifier}
                                                onChange={(e) =>
                                                    setEditFormData({ ...editFormData, identifier: e.target.value })
                                                }
                                                required
                                            />
                                        </div>
                                        <div className="form-group">
                                            <label>Role</label>
                                            <select
                                                value={editFormData.role}
                                                onChange={(e) =>
                                                    setEditFormData({ ...editFormData, role: e.target.value })
                                                }
                                            >
                                                <option value="student">Student</option>
                                                <option value="staff">Staff / Faculty</option>
                                                <option value="visitor">Visitor</option>
                                            </select>
                                        </div>
                                    </div>

                                    <div className="form-row">
                                        <div className="form-group">
                                            <label>Department</label>
                                            <input
                                                type="text"
                                                value={editFormData.department}
                                                onChange={(e) =>
                                                    setEditFormData({ ...editFormData, department: e.target.value })
                                                }
                                            />
                                        </div>
                                        <div className="form-group">
                                            <label>Class / Grade</label>
                                            <input
                                                type="text"
                                                value={editFormData.class_grade}
                                                onChange={(e) =>
                                                    setEditFormData({ ...editFormData, class_grade: e.target.value })
                                                }
                                            />
                                        </div>
                                    </div>

                                    <div className="form-row">
                                        <div className="form-group">
                                            <label>Allowed Dress Code Policy</label>
                                            <select
                                                value={editFormData.allowed_dress}
                                                onChange={(e) =>
                                                    setEditFormData({ ...editFormData, allowed_dress: e.target.value })
                                                }
                                            >
                                                <option value="Formals & Regular Uniform">
                                                    Formals & Regular School Dress (Only Allowed)
                                                </option>
                                                <option value="Formal Business Attire">
                                                    Formal Business Attire
                                                </option>
                                                <option value="Lab Coat & Uniform">
                                                    Lab Coat & Formal Uniform
                                                </option>
                                                <option value="Casual Permitted">Casual Permitted</option>
                                            </select>
                                        </div>
                                        <div className="form-group">
                                            <label>Account Status</label>
                                            <select
                                                value={editFormData.status}
                                                onChange={(e) =>
                                                    setEditFormData({ ...editFormData, status: e.target.value })
                                                }
                                            >
                                                <option value="active">Active</option>
                                                <option value="on_leave">On Leave</option>
                                                <option value="suspended">Suspended</option>
                                                <option value="graduated">Graduated</option>
                                            </select>
                                        </div>
                                    </div>

                                    <div className="form-row">
                                        <div className="form-group">
                                            <label>Contact Phone</label>
                                            <input
                                                type="text"
                                                placeholder="+91 98765 43210"
                                                value={editFormData.phone}
                                                onChange={(e) =>
                                                    setEditFormData({ ...editFormData, phone: e.target.value })
                                                }
                                            />
                                        </div>
                                        <div className="form-group">
                                            <label>Email Address</label>
                                            <input
                                                type="email"
                                                placeholder="student@school.edu"
                                                value={editFormData.email}
                                                onChange={(e) =>
                                                    setEditFormData({ ...editFormData, email: e.target.value })
                                                }
                                            />
                                        </div>
                                    </div>

                                    <div className="form-actions-bar">
                                        <button type="submit" className="btn-primary">
                                            💾 Save Profile Changes
                                        </button>
                                        <button
                                            type="button"
                                            className="btn-success"
                                            onClick={handleMarkPresentNow}
                                        >
                                            ✓ Mark Present Today
                                        </button>
                                        <button
                                            type="button"
                                            className="btn-danger-ghost"
                                            onClick={() => handleDeletePerson(selectedPerson.id)}
                                        >
                                            🗑 Delete Profile
                                        </button>
                                    </div>
                                </form>
                            </div>

                            {/* Right Column: Individual Records & Activity Table */}
                            <div className="modal-column-right">
                                <div className="history-table-header">
                                    <h4 className="section-subtitle">
                                        📋 Individual Records Table ({personHistory.length} logs)
                                    </h4>
                                    <span className="live-log-tag">REAL-TIME BIOMETRIC AUDIT</span>
                                </div>

                                <div className="individual-table-wrapper">
                                    <table className="soc-table individual-records-table">
                                        <thead>
                                            <tr>
                                                <th>TIMESTAMP</th>
                                                <th>EVENT TYPE</th>
                                                <th>CAMERA</th>
                                                <th>STATUS</th>
                                                <th>CONFIDENCE</th>
                                                <th>NOTES</th>
                                            </tr>
                                        </thead>
                                        <tbody>
                                            {loadingHistory ? (
                                                <tr>
                                                    <td colSpan="6" className="empty-cell">
                                                        Loading records table...
                                                    </td>
                                                </tr>
                                            ) : personHistory.length === 0 ? (
                                                <tr>
                                                    <td colSpan="6" className="empty-cell">
                                                        No activity logs recorded for this individual yet.
                                                    </td>
                                                </tr>
                                            ) : (
                                                personHistory.map((rec) => (
                                                    <tr key={rec.id}>
                                                        <td className="timestamp-cell">{rec.timestamp}</td>
                                                        <td>
                                                            <span className={`event-type-chip ${rec.type?.toLowerCase()}`}>
                                                                {rec.event}
                                                            </span>
                                                        </td>
                                                        <td>{rec.camera}</td>
                                                        <td>
                                                            <span
                                                                className={`status-badge-chip ${
                                                                    rec.status === "PRESENT"
                                                                        ? "success"
                                                                        : rec.status === "LATE"
                                                                        ? "warning"
                                                                        : "danger"
                                                                }`}
                                                            >
                                                                {rec.status}
                                                            </span>
                                                        </td>
                                                        <td>{Math.round((rec.confidence || 0.95) * 100)}%</td>
                                                        <td className="notes-cell">{rec.notes}</td>
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

            {/* ── Register New Person Modal ── */}
            {showAddModal && (
                <div className="modal-overlay" onClick={() => setShowAddModal(false)}>
                    <div className="modal-dialog" onClick={(e) => e.stopPropagation()}>
                        <div className="modal-header">
                            <h3>Register Person</h3>
                            <button className="close-btn" onClick={() => setShowAddModal(false)}>
                                ×
                            </button>
                        </div>
                        <form onSubmit={handleCreatePerson} className="modal-form">
                            <div className="form-group">
                                <label>Full Name</label>
                                <input
                                    type="text"
                                    placeholder="e.g. Priya Sharma"
                                    value={newName}
                                    onChange={(e) => setNewName(e.target.value)}
                                    required
                                />
                            </div>
                            <div className="form-group">
                                <label>Identifier (Student / Staff ID)</label>
                                <input
                                    type="text"
                                    placeholder="e.g. STU-105"
                                    value={newIdentifier}
                                    onChange={(e) => setNewIdentifier(e.target.value)}
                                    required
                                />
                            </div>
                            <div className="form-row">
                                <div className="form-group">
                                    <label>Role</label>
                                    <select value={newRole} onChange={(e) => setNewRole(e.target.value)}>
                                        <option value="student">Student</option>
                                        <option value="staff">Staff / Faculty</option>
                                        <option value="visitor">Visitor</option>
                                    </select>
                                </div>
                                <div className="form-group">
                                    <label>Allowed Dress Policy</label>
                                    <select value={newDress} onChange={(e) => setNewDress(e.target.value)}>
                                        <option value="Formals & Regular Uniform">Formals & Regular School Dress</option>
                                        <option value="Formal Business Attire">Formal Business Attire</option>
                                        <option value="Casual Permitted">Casual Permitted</option>
                                    </select>
                                </div>
                            </div>
                            <div className="form-row">
                                <div className="form-group">
                                    <label>Department</label>
                                    <input
                                        type="text"
                                        placeholder="e.g. Computer Science"
                                        value={newDept}
                                        onChange={(e) => setNewDept(e.target.value)}
                                    />
                                </div>
                                <div className="form-group">
                                    <label>Class / Grade</label>
                                    <input
                                        type="text"
                                        placeholder="e.g. Grade 11-B"
                                        value={newGrade}
                                        onChange={(e) => setNewGrade(e.target.value)}
                                    />
                                </div>
                            </div>
                            <div className="form-row">
                                <div className="form-group">
                                    <label>Contact Phone</label>
                                    <input
                                        type="text"
                                        placeholder="+91 98765 43210"
                                        value={newPhone}
                                        onChange={(e) => setNewPhone(e.target.value)}
                                    />
                                </div>
                                <div className="form-group">
                                    <label>Email Address</label>
                                    <input
                                        type="email"
                                        placeholder="student@school.edu"
                                        value={newEmail}
                                        onChange={(e) => setNewEmail(e.target.value)}
                                    />
                                </div>
                            </div>
                            <div className="modal-actions">
                                <button
                                    type="button"
                                    className="btn-secondary"
                                    onClick={() => setShowAddModal(false)}
                                >
                                    Cancel
                                </button>
                                <button type="submit" className="btn-primary">
                                    Register Profile
                                </button>
                            </div>
                        </form>
                    </div>
                </div>
            )}
        </div>
    );
}
