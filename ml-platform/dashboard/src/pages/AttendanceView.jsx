import { useState, useEffect } from "react";
import { getAttendance, getAttendanceSummary, recordManualAttendance, getPeople, getExportCsvUrl } from "../api/api";

export default function AttendanceView() {
    const [attendanceList, setAttendanceList] = useState([]);
    const [summary, setSummary] = useState({
        total_enrolled: 0,
        present_count: 0,
        late_count: 0,
        absent_count: 0,
        attendance_rate: 0,
    });
    const [enrolledPeople, setEnrolledPeople] = useState([]);
    const [selectedStudent, setSelectedStudent] = useState("");
    const [searchQuery, setSearchQuery] = useState("");
    const [loading, setLoading] = useState(true);
    const [checkinMsg, setCheckinMsg] = useState("");
    const [activeTimesheetPerson, setActiveTimesheetPerson] = useState(null);

    const loadData = async () => {
        try {
            const [attRes, sumRes, peopleRes] = await Promise.all([
                getAttendance(),
                getAttendanceSummary(),
                getPeople(),
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
                presence_seconds: 6,
            });

            if (res.success) {
                setCheckinMsg(`Verified: ${res.message}`);
            } else {
                setCheckinMsg(res.message);
            }
            setTimeout(() => setCheckinMsg(""), 4000);
            await loadData();
        } catch (err) {
            alert(err.response?.data?.detail || "Check-in failed");
        }
    };

    const filteredRecords = attendanceList.filter((a) => {
        if (!searchQuery) return true;
        const q = searchQuery.toLowerCase();
        return (
            a.person_name.toLowerCase().includes(q) ||
            a.identifier.toLowerCase().includes(q) ||
            a.role.toLowerCase().includes(q)
        );
    });

    return (
        <div className="attendance-module-container">
            {/* Header with Title and Simulation Trigger */}
            <div className="module-header-row">
                <div>
                    <h2>Campus Attendance & Timesheet System</h2>
                    <p>Automated Face Recognition, Temporal Presence Verification & Daily Timesheets</p>
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
                        ✓ Test Face Verification Check-in
                    </button>
                    <a
                        href={getExportCsvUrl("attendance")}
                        target="_blank"
                        rel="noreferrer"
                        className="btn-secondary"
                        title="Download CSV Timesheet"
                    >
                        📥 Export CSV
                    </a>
                </div>
            </div>

            {checkinMsg && (
                <div className="checkin-feedback-banner">
                    {checkinMsg}
                </div>
            )}

            {/* Attendance Summary KPI Cards with % metrics (Worksy & ANPR inspired) */}
            <div className="kpi-grid">
                <div className="kpi-card">
                    <span className="kpi-label">TOTAL REGISTERED</span>
                    <strong className="kpi-val">{summary.total_enrolled}</strong>
                    <span className="kpi-sub">Students & Staff</span>
                </div>
                <div className="kpi-card">
                    <span className="kpi-label">ON-TIME PRESENT</span>
                    <strong className="kpi-val success">{summary.present_count}</strong>
                    <span className="kpi-sub">Before 09:00 AM (+7.1% vs prev)</span>
                </div>
                <div className="kpi-card">
                    <span className="kpi-label">LATE ARRIVALS</span>
                    <strong className="kpi-val warning">{summary.late_count}</strong>
                    <span className="kpi-sub">After 09:00 AM (-5% vs prev)</span>
                </div>
                <div className="kpi-card">
                    <span className="kpi-label">ATTENDANCE RATE</span>
                    <strong className="kpi-val accent">{summary.attendance_rate}%</strong>
                    <span className="kpi-sub">{summary.absent_count} Currently Absent</span>
                </div>
            </div>

            {/* Attendance Log Table with Search Bar */}
            <div className="attendance-table-card">
                <div className="panel-title-bar">
                    <div className="title-left">
                        <h4>Today's Real-Time Verification Records</h4>
                        <span>{filteredRecords.length} logs recorded</span>
                    </div>
                    <div className="search-filter-input-wrap">
                        <input
                            type="text"
                            placeholder="Search student, staff or ID..."
                            value={searchQuery}
                            onChange={(e) => setSearchQuery(e.target.value)}
                            className="table-search-field"
                        />
                    </div>
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
                                <th>ACTION</th>
                            </tr>
                        </thead>
                        <tbody>
                            {filteredRecords.length === 0 ? (
                                <tr>
                                    <td colSpan="8" className="empty-cell">
                                        No attendance records found. Use the verification button above or adjust your search filter.
                                    </td>
                                </tr>
                            ) : (
                                filteredRecords.map((a) => (
                                    <tr key={a.id}>
                                        <td>
                                            <span className="id-code-badge">{a.identifier}</span>
                                        </td>
                                        <td>
                                            <div
                                                className="person-name-cell clickable"
                                                onClick={() => setActiveTimesheetPerson(a)}
                                                title="View detailed Worksy-style timesheet"
                                            >
                                                <div className="avatar-circle">
                                                    {a.person_name.charAt(0)}
                                                </div>
                                                <div>
                                                    <strong>{a.person_name}</strong>
                                                    <span className="view-profile-hint">View Timesheet ↗</span>
                                                </div>
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
                                        <td>
                                            <button
                                                className="btn-inspect-mini"
                                                onClick={() => setActiveTimesheetPerson(a)}
                                            >
                                                Timesheet
                                            </button>
                                        </td>
                                    </tr>
                                ))
                            )}
                        </tbody>
                    </table>
                </div>
            </div>

            {/* Worksy-Style Timesheet Modal (Inspired by Image 1) */}
            {activeTimesheetPerson && (
                <div className="modal-backdrop" onClick={() => setActiveTimesheetPerson(null)}>
                    <div className="modal-content worksy-timesheet-modal" onClick={(e) => e.stopPropagation()}>
                        {/* Profile Bar */}
                        <div className="timesheet-header">
                            <div className="timesheet-profile-row">
                                <div className="avatar-circle-large">
                                    {activeTimesheetPerson.person_name.charAt(0)}
                                </div>
                                <div>
                                    <div className="timesheet-name-badge">
                                        <h3>{activeTimesheetPerson.person_name}</h3>
                                        <span className="status-pill-green">● Active</span>
                                    </div>
                                    <span className="timesheet-sub">
                                        {activeTimesheetPerson.identifier} • {activeTimesheetPerson.role.toUpperCase()} • Greenwood Campus
                                    </span>
                                </div>
                            </div>
                            <div className="timesheet-top-actions">
                                <button
                                    className="btn-primary-mini"
                                    onClick={() => alert(`Direct notification dispatched to ${activeTimesheetPerson.person_name}`)}
                                >
                                    💬 Send Message
                                </button>
                                <button className="modal-close-btn" onClick={() => setActiveTimesheetPerson(null)}>✕</button>
                            </div>
                        </div>

                        {/* Date Navigation & Controls */}
                        <div className="timesheet-nav-toolbar">
                            <div className="date-filter-group">
                                <span className="calendar-tag">📅 Today: {new Date().toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })}</span>
                                <span className="tab-pill-active">Attendance Timesheet</span>
                                <span className="tab-pill">Overtime</span>
                                <span className="tab-pill">Time Off</span>
                            </div>
                            <span className="policy-note">Campus Policy: Check-in before 09:00 AM</span>
                        </div>

                        {/* Worksy Metrics Breakdown Cards */}
                        <div className="timesheet-metrics-grid">
                            <div className="timesheet-metric-box">
                                <span className="m-label">Day Off</span>
                                <strong className="m-val">0</strong>
                                <span className="m-trend positive">+7.1% vs prev</span>
                            </div>
                            <div className="timesheet-metric-box">
                                <span className="m-label">Late Clock-in</span>
                                <strong className="m-val warning">{activeTimesheetPerson.status === "LATE" ? "1" : "0"}</strong>
                                <span className="m-trend negative">-5% vs prev</span>
                            </div>
                            <div className="timesheet-metric-box">
                                <span className="m-label">Early Clock-out</span>
                                <strong className="m-val">0</strong>
                                <span className="m-trend">-7% vs prev</span>
                            </div>
                            <div className="timesheet-metric-box">
                                <span className="m-label">Pending Clock-Out</span>
                                <strong className="m-val">1</strong>
                                <span className="m-trend">+2% vs prev</span>
                            </div>
                            <div className="timesheet-metric-box">
                                <span className="m-label">Leave</span>
                                <strong className="m-val">0</strong>
                                <span className="m-trend">-2% vs prev</span>
                            </div>
                            <div className="timesheet-metric-box">
                                <span className="m-label">Overtime</span>
                                <strong className="m-val">0h</strong>
                                <span className="m-trend">--</span>
                            </div>
                        </div>

                        {/* Legend row */}
                        <div className="timeline-legend-row">
                            <div className="legend-item"><span className="legend-dot working"></span> Working / Class Time</div>
                            <div className="legend-item"><span className="legend-dot break"></span> Break</div>
                            <div className="legend-item"><span className="legend-dot overtime"></span> Overtime</div>
                            <div className="legend-item"><span className="legend-dot late"></span> Late Clock-in</div>
                        </div>

                        {/* Visual Daily Timeline Bars */}
                        <div className="timesheet-days-list">
                            {/* Today */}
                            <div className="day-timeline-card">
                                <div className="day-card-header">
                                    <strong>Today (Current Session)</strong>
                                    <span>Duration: 8h 00m</span>
                                </div>
                                <div className="clock-times-row">
                                    <span className="clock-in-time">
                                        Clock-in: <strong>{activeTimesheetPerson.timestamp.split(" ")[1] || "08:52 AM"}</strong>
                                    </span>
                                    <span className="clock-out-time">
                                        Clock-out: <strong>05:00 PM (Scheduled)</strong>
                                    </span>
                                </div>
                                <div className="timeline-bar-track">
                                    {activeTimesheetPerson.status === "LATE" && (
                                        <div className="bar-segment late" style={{ width: "15%" }} title="Late arrival delay"></div>
                                    )}
                                    <div className="bar-segment working" style={{ width: activeTimesheetPerson.status === "LATE" ? "45%" : "60%" }} title="In-class working duration"></div>
                                    <div className="bar-segment break" style={{ width: "15%" }} title="Lunch / Intermission break"></div>
                                    <div className="bar-segment working" style={{ width: "25%" }} title="Afternoon session"></div>
                                </div>
                            </div>

                            {/* Yesterday */}
                            <div className="day-timeline-card">
                                <div className="day-card-header">
                                    <strong>Yesterday (Previous Session)</strong>
                                    <span>Duration: 7h 45m</span>
                                </div>
                                <div className="clock-times-row">
                                    <span className="clock-in-time">Clock-in: <strong>09:05 AM</strong></span>
                                    <span className="clock-out-time">Clock-out: <strong>04:50 PM</strong></span>
                                </div>
                                <div className="timeline-bar-track">
                                    <div className="bar-segment late" style={{ width: "10%" }} title="Late 15 mins"></div>
                                    <div className="bar-segment working" style={{ width: "55%" }}></div>
                                    <div className="bar-segment break" style={{ width: "15%" }}></div>
                                    <div className="bar-segment working" style={{ width: "20%" }}></div>
                                </div>
                            </div>
                        </div>

                        <div className="timesheet-modal-footer">
                            <span className="biometric-tag">
                                Biometric Source: Camera ID #{activeTimesheetPerson.camera_name || "1"} • Facial Confidence: {(activeTimesheetPerson.confidence * 100).toFixed(1)}%
                            </span>
                            <button className="btn-secondary" onClick={() => setActiveTimesheetPerson(null)}>
                                Close Timesheet
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}
