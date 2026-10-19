import { useState, useEffect } from "react";
import { getAttendance, getAttendanceSummary, recordManualAttendance, getPeople } from "../api/api";

export default function AttendanceView() {
    const [attendanceList, setAttendanceList] = useState([]);
    const [summary, setSummary] = useState({
        total_enrolled: 0,
        present_count: 0,
        late_count: 0,
        absent_count: 0,
        attendance_rate: 0
    });
    const [enrolledPeople, setEnrolledPeople] = useState([]);
    const [selectedStudent, setSelectedStudent] = useState("");
    const [loading, setLoading] = useState(true);
    const [checkinMsg, setCheckinMsg] = useState("");

    const loadData = async () => {
        try {
            const [attRes, sumRes, peopleRes] = await Promise.all([
                getAttendance(),
                getAttendanceSummary(),
                getPeople()
            ]);

            setAttendanceList(attRes.attendance || []);
            setSummary(sumRes);
            const people = peopleRes.people || [];
            setEnrolledPeople(people);
            if (people.length > 0 && !selectedStudent) {
                setSelectedStudent(people[0].id);
            }
        } catch (err) {
            console.error("Error loading attendance data", err);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        loadData();
        const interval = setInterval(loadData, 5000);
        return () => clearInterval(interval);
    }, []);

    const handleSimulateCheckin = async () => {
        if (!selectedStudent) return;
        try {
            const res = await recordManualAttendance({
                person_id: parseInt(selectedStudent, 10),
                camera_id: 1,
                confidence: 0.95,
                presence_seconds: 6
            });

            if (res.success) {
                setCheckinMsg(`Success: ${res.message}`);
            } else {
                setCheckinMsg(res.message);
            }
            setTimeout(() => setCheckinMsg(""), 4000);
            await loadData();
        } catch (err) {
            alert(err.response?.data?.detail || "Check-in failed");
        }
    };

    return (
        <div className="attendance-module-container">
            {/* Header with Title and Simulation Trigger */}
            <div className="module-header-row">
                <div>
                    <h2>Campus Attendance System</h2>
                    <p>Automated Face Recognition & Temporal Presence Verification</p>
                </div>
                <div className="attendance-action-group">
                    <select
                        className="student-select-box"
                        value={selectedStudent}
                        onChange={(e) => setSelectedStudent(e.target.value)}
                    >
                        {enrolledPeople.map((p) => (
                            <option key={p.id} value={p.id}>
                                {p.name} ({p.identifier})
                            </option>
                        ))}
                    </select>
                    <button className="btn-primary" onClick={handleSimulateCheckin}>
                        ✓ Test Face Recognition Check-in
                    </button>
                </div>
            </div>

            {checkinMsg && (
                <div className="checkin-feedback-banner">
                    {checkinMsg}
                </div>
            )}

            {/* Attendance Summary KPI Cards */}
            <div className="kpi-grid">
                <div className="kpi-card">
                    <span className="kpi-label">TOTAL REGISTERED</span>
                    <strong className="kpi-val">{summary.total_enrolled}</strong>
                    <span className="kpi-sub">Students & Staff</span>
                </div>
                <div className="kpi-card">
                    <span className="kpi-label">ON-TIME PRESENT</span>
                    <strong className="kpi-val success">{summary.present_count}</strong>
                    <span className="kpi-sub">Before 09:00 AM</span>
                </div>
                <div className="kpi-card">
                    <span className="kpi-label">LATE ARRIVALS</span>
                    <strong className="kpi-val warning">{summary.late_count}</strong>
                    <span className="kpi-sub">After 09:00 AM</span>
                </div>
                <div className="kpi-card">
                    <span className="kpi-label">ATTENDANCE RATE</span>
                    <strong className="kpi-val accent">{summary.attendance_rate}%</strong>
                    <span className="kpi-sub">{summary.absent_count} Currently Absent</span>
                </div>
            </div>

            {/* Attendance Log Table */}
            <div className="attendance-table-card">
                <div className="panel-title-bar">
                    <h4>Today's Real-Time Verification Records</h4>
                    <span>{attendanceList.length} logs recorded</span>
                </div>

                <div className="table-wrapper">
                    <table className="soc-table">
                        <thead>
                            <tr>
                                <th>STUDENT / STAFF ID</th>
                                <th>FULL NAME</th>
                                <th>ROLE / GRADE</th>
                                <th>RECOGNITION CONFIDENCE</th>
                                <th>VERIFIED TIME</th>
                                <th>CAMERA SOURCE</th>
                                <th>STATUS</th>
                            </tr>
                        </thead>
                        <tbody>
                            {attendanceList.length === 0 ? (
                                <tr>
                                    <td colSpan="7" className="empty-cell">
                                        No attendance records marked yet today. Use the button above to simulate a face verification check-in.
                                    </td>
                                </tr>
                            ) : (
                                attendanceList.map((a) => (
                                    <tr key={a.id}>
                                        <td>
                                            <span className="id-code-badge">{a.identifier}</span>
                                        </td>
                                        <td>
                                            <div className="person-name-cell">
                                                <div className="avatar-circle">
                                                    {a.person_name.charAt(0)}
                                                </div>
                                                <strong>{a.person_name}</strong>
                                            </div>
                                        </td>
                                        <td>
                                            <span className="role-tag">{a.role.toUpperCase()}</span>
                                            {a.class_grade && <span className="grade-sub">{a.class_grade}</span>}
                                        </td>
                                        <td>
                                            <div className="conf-bar-cell">
                                                <div
                                                    className="conf-bar-fill"
                                                    style={{ width: `${Math.min(100, a.confidence * 100)}%` }}
                                                ></div>
                                                <span>{(a.confidence * 100).toFixed(0)}%</span>
                                            </div>
                                        </td>
                                        <td>{a.timestamp}</td>
                                        <td>{a.camera_name || "Entrance Cam 01"}</td>
                                        <td>
                                            <span className={`status-badge-chip ${a.status.toLowerCase()}`}>
                                                {a.status}
                                            </span>
                                        </td>
                                    </tr>
                                ))
                            )}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    );
}
