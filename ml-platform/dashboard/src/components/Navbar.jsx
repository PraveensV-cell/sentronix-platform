export default function Navbar({
    user,
    environment,
    systemOnline,
    onOpenAssistant,
    onSwitchEnvironment,
    onLogout
}) {
    return (
        <header className="soc-navbar">
            <div className="navbar-brand">
                <div className="brand-logo-icon">
                    <div className="inner-radar"></div>
                </div>
                <div>
                    <span className="brand-title">SENTRONIX AI</span>
                    <span className="brand-subtitle">INTELLIGENT SURVEILLANCE COMMAND CENTER</span>
                </div>
            </div>

            <div className="navbar-controls">
                {/* Active Environment Pill */}
                {environment && (
                    <div className="env-pill-badge" onClick={onSwitchEnvironment} title="Click to switch mode">
                        <span className="env-mode-type">{environment.type.toUpperCase()} MODE</span>
                        <span className="env-name">{environment.name}</span>
                        <span className="switch-icon">⇄</span>
                    </div>
                )}

                {/* System Telemetry Status */}
                <div className={`status-pill ${systemOnline ? "online" : "offline"}`}>
                    <span className="status-dot"></span>
                    <span>{systemOnline ? "VISION ENGINE ONLINE" : "SERVICES OFFLINE"}</span>
                </div>

                {/* Sentronix AI Assistant Button */}
                <button className="ai-assistant-toggle-btn" onClick={onOpenAssistant}>
                    <span className="ai-spark-icon">✨</span>
                    <span>AI OPERATOR</span>
                </button>

                {/* User Profile */}
                {user && (
                    <div className="user-profile-badge">
                        <div className="user-avatar">{user.username.charAt(0).toUpperCase()}</div>
                        <div className="user-details">
                            <span className="user-name">{user.full_name || user.username}</span>
                            <span className="user-role">{user.role.toUpperCase()}</span>
                        </div>
                    </div>
                )}

                <button className="logout-btn" onClick={onLogout} title="Sign Out">
                    ⎋
                </button>
            </div>
        </header>
    );
}
