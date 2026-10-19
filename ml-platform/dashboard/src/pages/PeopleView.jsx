import { useState, useEffect } from "react";
import { getPeople, createPerson, enrollPersonFace } from "../api/api";

export default function PeopleView() {
    const [people, setPeople] = useState([]);
    const [filterRole, setFilterRole] = useState("ALL");
    const [showAddModal, setShowAddModal] = useState(false);

    // Add person form fields
    const [newName, setNewName] = useState("");
    const [newIdentifier, setNewIdentifier] = useState("");
    const [newRole, setNewRole] = useState("student");
    const [newDept, setNewDept] = useState("Science");
    const [newGrade, setNewGrade] = useState("Grade 10-A");

    const [enrollMsg, setEnrollMsg] = useState("");

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
            });

            if (res.success) {
                setShowAddModal(false);
                setNewName("");
                setNewIdentifier("");
                setEnrollMsg(`Registered ${newName}. Now enroll facial profile.`);
                setTimeout(() => setEnrollMsg(""), 4000);
                await loadPeople();
            }
        } catch (err) {
            alert(err.response?.data?.detail || "Registration failed");
        }
    };

    const handleEnrollFace = async (person) => {
        try {
            const res = await enrollPersonFace(person.id);
            if (res.success) {
                setEnrollMsg(`✓ Face enrolled & feature vector generated for ${person.name}!`);
                setTimeout(() => setEnrollMsg(""), 4000);
                await loadPeople();
            }
        } catch (err) {
            alert(err.response?.data?.detail || "Face enrollment failed");
        }
    };

    return (
        <div className="people-module-container">
            <div className="module-header-row">
                <div>
                    <h2>People & Facial Identity Registry</h2>
                    <p>Enrolled Student, Staff & Authorized Personnel Profiles</p>
                </div>
                <div className="attendance-action-group">
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

            {enrollMsg && (
                <div className="checkin-feedback-banner">
                    {enrollMsg}
                </div>
            )}

            {/* People Cards Grid */}
            <div className="people-cards-grid">
                {people.map((p) => {
                    const isEnrolled = p.is_enrolled === 1;
                    return (
                        <div key={p.id} className="person-profile-card">
                            <div className="profile-header">
                                <div className="avatar-large">
                                    {p.name.charAt(0)}
                                </div>
                                <div className="profile-meta">
                                    <h3>{p.name}</h3>
                                    <span className="profile-id">{p.identifier}</span>
                                </div>
                                <span className={`enroll-status-badge ${isEnrolled ? "enrolled" : "pending"}`}>
                                    {isEnrolled ? "● FACE ENROLLED" : "○ ENROLLMENT PENDING"}
                                </span>
                            </div>

                            <div className="profile-details-list">
                                <div className="detail-item">
                                    <span>ROLE</span>
                                    <strong>{p.role.toUpperCase()}</strong>
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
                                    <span>TODAY'S STATUS</span>
                                    <strong className={p.today_attendance?.status === "PRESENT" ? "text-success" : ""}>
                                        {p.today_attendance?.status || "NOT LOGGED"}
                                    </strong>
                                </div>
                            </div>

                            <div className="profile-card-footer">
                                {!isEnrolled ? (
                                    <button
                                        className="btn-primary small full-width"
                                        onClick={() => handleEnrollFace(p)}
                                    >
                                        📷 Capture & Enroll Face
                                    </button>
                                ) : (
                                    <button
                                        className="btn-secondary small full-width"
                                        onClick={() => handleEnrollFace(p)}
                                    >
                                        🔄 Re-enroll Facial Vector
                                    </button>
                                )}
                            </div>
                        </div>
                    );
                })}
            </div>

            {/* Add Person Modal */}
            {showAddModal && (
                <div className="modal-overlay">
                    <div className="modal-dialog">
                        <div className="modal-header">
                            <h3>Register Person</h3>
                            <button className="close-btn" onClick={() => setShowAddModal(false)}>×</button>
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
                            <div className="form-group">
                                <label>Role</label>
                                <select value={newRole} onChange={(e) => setNewRole(e.target.value)}>
                                    <option value="student">Student</option>
                                    <option value="staff">Staff / Faculty</option>
                                    <option value="visitor">Visitor</option>
                                </select>
                            </div>
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
                            <div className="modal-actions">
                                <button type="button" className="btn-secondary" onClick={() => setShowAddModal(false)}>
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
