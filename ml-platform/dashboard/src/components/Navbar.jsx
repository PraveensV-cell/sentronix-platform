export default function Navbar({
    user,
    environment,
    systemOnline,
    themeMode,
    onToggleTheme,
    onOpenAssistant,
    onOpenJarvis,
    onOpenSettings,
    onSwitchEnvironment,
    onLogout,
}) {
    return (
        <header className="soc-navbar">
            <div className="navbar-brand">
                <div className="brand-logo-icon">
                    <div className="inner-radar"></div>
                </div>
                <div>
                    <span className="brand-title">SENTRONIX AI</span>
                    <span className="brand-subtitle">24/7 SURVEILLANCE &amp; SAFETY COMMAND CENTER</span>
                </div>
            </div>

            <div className="navbar-controls">
                {/* Active Mode Pill */}
                {environment && (
                    <div className="env-pill-badge" onClick={onSwitchEnvironment} title="Click to switch deployment mode">
                        <span className="env-mode-type">{environment.type?.toUpperCase()} MODE</span>
                        <span className="env-name">{environment.name}</span>
                        <span className="switch-icon">⇄</span>
                    </div>
                )}

                {/* System Telemetry Status */}
                <div className={`status-pill ${systemOnline ? "online" : "offline"}`}>
                    <span className="status-dot"></span>
                    <span>{systemOnline ? "24/7 AI ONLINE" : "SERVICES OFFLINE"}</span>
                </div>

                {/* Quick Theme Toggle */}
                <button
                    type="button"
                    className="tool-btn btn-secondary-mini"
                    onClick={onToggleTheme}
                    title="Toggle Dark / Light Mode"
                    style={{ fontSize: "14px", padding: "5px 10px" }}
                >
                    {themeMode === "dark" ? "☀️" : "🌙"}
                </button>

                {/* JARVIS AI Command Brain Button */}
                <button
                    className="ai-assistant-toggle-btn"
                    onClick={onOpenJarvis}
                    style={{ background: "linear-gradient(135deg, #0ea5e9 0%, #0369a1 100%)", boxShadow: "0 2px 8px rgba(14,165,233,0.3)" }}
                >
                    <span className="ai-spark-icon">🧠</span>
                    <span>JARVIS BRAIN</span>
                </button>

                {/* AI Assistant Chat drawer */}
                <button className="tool-btn btn-secondary-mini" onClick={onOpenAssistant} title="Open AI Assistant Drawer">
                    <span>✨ Chat</span>
                </button>

                {/* Settings Shortcut */}
                <button className="tool-btn btn-secondary-mini" onClick={onOpenSettings} title="Settings & Personalization">
                    <span>⚙️</span>
                </button>

                {/* User Profile */}
                {user && (
                    <div className="user-profile-badge" onClick={onOpenSettings} style={{ cursor: "pointer" }} title="Click to manage account">
                        <div className="user-avatar">{(user.name || user.username).charAt(0).toUpperCase()}</div>
                        <div className="user-details">
                            <span className="user-name">{user.name || user.full_name || user.username}</span>
                            <span className="user-role">{user.role?.toUpperCase()}</span>
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
