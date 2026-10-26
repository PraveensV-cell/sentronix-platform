export default function Sidebar({ activeTab, setActiveTab, alertCount = 0 }) {
    const tabs = [
        { id: "surveillance", label: "Live Surveillance", icon: "📹" },
        { id: "jarvis_core", label: "JARVIS AI Brain", icon: "🧠" },
        { id: "people", label: "People & Dossiers", icon: "👥" },
        { id: "attendance", label: "Attendance Records", icon: "🎓" },
        { id: "alerts", label: "Security Alerts", icon: "🚨", badge: alertCount },
        { id: "cameras", label: "Camera Devices", icon: "📹" },
        { id: "map", label: "Campus Tactical Map", icon: "🗺️" },
        { id: "vision_search", label: "VisionAI Search", icon: "✨" },
        { id: "rules", label: "Policy & Rules", icon: "⚖️" },
        { id: "analytics", label: "Analytics & KPIs", icon: "📊" },
        { id: "health", label: "System Health", icon: "🩺" },
        { id: "settings", label: "Personalization & Settings", icon: "⚙️" },
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
                <div className="version-tag">SENTRONIX 3.0 ENTERPRISE</div>
                <div className="runtime-tag">CORE: PyTorch • YOLO11n + FaceNet</div>
            </div>
        </aside>
    );
}
