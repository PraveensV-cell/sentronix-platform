export default function Sidebar({ activeTab, setActiveTab, alertCount = 0 }) {
    const tabs = [
        { id: "surveillance", label: "Live Surveillance", icon: "📹" },
        { id: "map", label: "Campus Tactical Map", icon: "🗺️" },
        { id: "vision_search", label: "VisionAI Search", icon: "✨" },
        { id: "attendance", label: "Attendance & Timesheets", icon: "🎓" },
        { id: "alerts", label: "Security Alerts", icon: "🚨", badge: alertCount },
        { id: "people", label: "People & Faces", icon: "👥" },
        { id: "rules", label: "Policy & Rules", icon: "⚖️" },
        { id: "analytics", label: "Analytics & KPIs", icon: "📊" },
        { id: "cameras", label: "Camera Devices", icon: "⚙️" },
        { id: "health", label: "System Health", icon: "🩺" },
    ];

    return (
        <aside className="soc-sidebar">
            <div className="sidebar-nav-list">
                {tabs.map((tab) => {
                    const isActive = activeTab === tab.id;
                    return (
                        <button
                            key={tab.id}
                            className={`sidebar-nav-item ${isActive ? "active" : ""}`}
                            onClick={() => setActiveTab(tab.id)}
                        >
                            <span className="nav-icon">{tab.icon}</span>
                            <span className="nav-label">{tab.label}</span>
                            {tab.badge > 0 && (
                                <span className="nav-alert-badge">{tab.badge}</span>
                            )}
                        </button>
                    );
                })}
            </div>

            <div className="sidebar-footer">
                <div className="version-tag">SENTRONIX v1.0.0</div>
                <div className="runtime-tag">CORE: PyTorch • YOLOv8/11</div>
            </div>
        </aside>
    );
}
