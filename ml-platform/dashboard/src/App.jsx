import { useState, useEffect } from "react";
import Navbar from "./components/Navbar";
import Sidebar from "./components/Sidebar";
import AIAssistantWidget from "./components/AIAssistantWidget";

import AuthPage from "./pages/AuthPage";
import EnvironmentSelectPage from "./pages/EnvironmentSelectPage";

import LiveSurveillanceView from "./pages/LiveSurveillanceView";
import JarvisCoreView from "./pages/JarvisCoreView";
import SettingsView from "./pages/SettingsView";
import CampusMapView from "./pages/CampusMapView";
import VisionSearchView from "./pages/VisionSearchView";
import AttendanceView from "./pages/AttendanceView";
import AlertsView from "./pages/AlertsView";
import PeopleView from "./pages/PeopleView";
import RulesView from "./pages/RulesView";
import AnalyticsView from "./pages/AnalyticsView";
import CameraManagerView from "./pages/CameraManagerView";
import SystemHealthView from "./pages/SystemHealthView";

import { getAlerts, getStatus } from "./api/api";
import "./pages/Dashboard.css";

const ZOOM_STEPS = ["80%", "90%", "100%", "110%", "125%"];

export default function App() {
    const [user, setUser] = useState(null);
    const [environment, setEnvironment] = useState(null);
    const [activeTab, setActiveTab] = useState("surveillance");
    const [isAssistantOpen, setIsAssistantOpen] = useState(false);
    const [systemOnline, setSystemOnline] = useState(true);
    const [alertCount, setAlertCount] = useState(0);

    // Personalization & Royal Theme preferences
    const [themeMode, setThemeMode] = useState(() => localStorage.getItem("sentronix_theme") || "light");
    const [fontStyle, setFontStyle] = useState(() => localStorage.getItem("sentronix_font") || "modern");
    const [zoomLevel, setZoomLevel] = useState(() => localStorage.getItem("sentronix_zoom") || "100%");
    const [voiceEnabled, setVoiceEnabled] = useState(() => localStorage.getItem("sentronix_voice") !== "false");

    // Load initial session from localStorage
    useEffect(() => {
        const storedUser = localStorage.getItem("sentronix_user");
        const storedEnv = localStorage.getItem("sentronix_env");

        if (storedUser) {
            try {
                setUser(JSON.parse(storedUser));
            } catch (e) {
                setUser(null);
            }
        }
        if (storedEnv) {
            try {
                setEnvironment(JSON.parse(storedEnv));
            } catch (e) {
                setEnvironment(null);
            }
        }

        // Heartbeat check
        const checkHealth = async () => {
            try {
                const res = await getStatus();
                setSystemOnline(res.AI === "running" || res.status === "running");
            } catch (err) {
                setSystemOnline(false);
            }
        };

        const fetchAlertCount = async () => {
            try {
                const res = await getAlerts();
                const active = (res.alerts || []).filter(
                    (a) => String(a.status).toUpperCase() === "ACTIVE"
                );
                setAlertCount(active.length);
            } catch (err) {
                // silent
            }
        };

        checkHealth();
        fetchAlertCount();

        const timer = setInterval(() => {
            checkHealth();
            fetchAlertCount();
        }, 5000);

        return () => clearInterval(timer);
    }, []);

    // Synchronize Theme, Font, and Zoom into DOM
    useEffect(() => {
        localStorage.setItem("sentronix_theme", themeMode);
        document.documentElement.setAttribute("data-theme", themeMode);
    }, [themeMode]);

    useEffect(() => {
        localStorage.setItem("sentronix_font", fontStyle);
        document.documentElement.setAttribute("data-font", fontStyle);
    }, [fontStyle]);

    useEffect(() => {
        localStorage.setItem("sentronix_zoom", zoomLevel);
    }, [zoomLevel]);

    useEffect(() => {
        localStorage.setItem("sentronix_voice", String(voiceEnabled));
    }, [voiceEnabled]);

    const handleAuthenticated = (userData) => {
        setUser(userData);
        setEnvironment(null);
        localStorage.removeItem("sentronix_env");
    };

    const handleEnvironmentSelected = (envData) => {
        setEnvironment(envData);
    };

    const handleSwitchEnvironment = () => {
        setEnvironment(null);
        localStorage.removeItem("sentronix_env");
    };

    const handleLogout = () => {
        localStorage.removeItem("sentronix_token");
        localStorage.removeItem("sentronix_user");
        localStorage.removeItem("sentronix_env");
        setUser(null);
        setEnvironment(null);
    };

    const handleZoomIn = () => {
        const currIdx = ZOOM_STEPS.indexOf(zoomLevel);
        if (currIdx < ZOOM_STEPS.length - 1) {
            setZoomLevel(ZOOM_STEPS[currIdx + 1]);
        }
    };

    const handleZoomOut = () => {
        const currIdx = ZOOM_STEPS.indexOf(zoomLevel);
        if (currIdx > 0) {
            setZoomLevel(ZOOM_STEPS[currIdx - 1]);
        }
    };

    const handleToggleTheme = () => {
        setThemeMode((prev) => (prev === "dark" ? "light" : "dark"));
    };

    // Mode-specific class for dynamic background and palette (Point 3)
    const getModeClass = () => {
        if (!environment) return "mode-campus";
        const t = (environment.type || "").toLowerCase();
        if (t.includes("milit")) return "mode-military";
        if (t.includes("indus") || t.includes("plant")) return "mode-industry";
        if (t.includes("hosp") || t.includes("public")) return "mode-public";
        return "mode-campus";
    };

    // Flow Step 1: Authentication required (User ID, name, email, phone, password - NO OTP)
    if (!user) {
        return (
            <div className={`theme-${themeMode} font-${fontStyle}`}>
                <AuthPage onAuthenticated={handleAuthenticated} />
            </div>
        );
    }

    // Flow Step 2: Operational Mode selection required (Points 2 & 3)
    if (!environment) {
        return (
            <div className={`theme-${themeMode} font-${fontStyle}`}>
                <EnvironmentSelectPage
                    user={user}
                    onEnvironmentSelected={handleEnvironmentSelected}
                />
            </div>
        );
    }

    // Flow Step 3: Main Command Center
    const zoomNumeric = parseInt(zoomLevel, 10) / 100;

    return (
        <div
            className={`sentronix-app-root theme-${themeMode} font-${fontStyle} ${getModeClass()}`}
        >
            <Navbar
                user={user}
                environment={environment}
                systemOnline={systemOnline}
                themeMode={themeMode}
                onToggleTheme={handleToggleTheme}
                onOpenAssistant={() => setIsAssistantOpen(true)}
                onOpenJarvis={() => setActiveTab("jarvis_core")}
                onOpenSettings={() => setActiveTab("settings")}
                onSwitchEnvironment={handleSwitchEnvironment}
                onLogout={handleLogout}
            />

            <div
                className="soc-layout-body"
                style={{
                    zoom: zoomLevel !== "100%" ? zoomNumeric : undefined,
                }}
            >
                <Sidebar
                    activeTab={activeTab}
                    setActiveTab={setActiveTab}
                    alertCount={alertCount}
                />

                <main className="soc-main-content">
                    {activeTab === "surveillance" && (
                        <LiveSurveillanceView
                            environment={environment}
                            systemOnline={systemOnline}
                        />
                    )}

                    {activeTab === "jarvis_core" && (
                        <JarvisCoreView environment={environment} />
                    )}

                    {activeTab === "settings" && (
                        <SettingsView
                            user={user}
                            onUserUpdated={(updated) => setUser(updated)}
                            themeMode={themeMode}
                            onThemeChange={(m) => setThemeMode(m)}
                            fontStyle={fontStyle}
                            onFontChange={(f) => setFontStyle(f)}
                            zoomLevel={zoomLevel}
                            onZoomChange={(z) => setZoomLevel(z)}
                            voiceEnabled={voiceEnabled}
                            onVoiceToggle={(v) => setVoiceEnabled(v)}
                        />
                    )}

                    {activeTab === "people" && (
                        <PeopleView environment={environment} />
                    )}

                    {activeTab === "attendance" && <AttendanceView />}

                    {activeTab === "alerts" && <AlertsView />}

                    {activeTab === "cameras" && <CameraManagerView />}

                    {activeTab === "map" && <CampusMapView />}

                    {activeTab === "vision_search" && <VisionSearchView />}

                    {activeTab === "rules" && <RulesView />}

                    {activeTab === "analytics" && <AnalyticsView />}

                    {activeTab === "health" && <SystemHealthView />}
                </main>
            </div>

            {/* Floating Zoom In / Out Controls Pill (Point 15) */}
            <div
                className="floating-zoom-pill"
                style={{
                    position: "fixed",
                    bottom: "20px",
                    right: "24px",
                    background: "var(--card-bg)",
                    border: "1px solid var(--border-color)",
                    borderRadius: "30px",
                    padding: "6px 14px",
                    display: "flex",
                    alignItems: "center",
                    gap: "8px",
                    boxShadow: "0 4px 16px rgba(0,0,0,0.15)",
                    zIndex: 9000,
                    fontSize: "12px",
                    fontWeight: 600,
                }}
            >
                <button
                    type="button"
                    onClick={handleZoomOut}
                    title="Zoom Out Dashboard"
                    style={{ background: "transparent", border: "none", cursor: "pointer", fontSize: "14px", padding: "0 4px", fontWeight: 700, color: "var(--text-primary)" }}
                >
                    −
                </button>
                <span style={{ minWidth: "40px", textAlign: "center", color: "var(--text-primary)" }}>{zoomLevel}</span>
                <button
                    type="button"
                    onClick={handleZoomIn}
                    title="Zoom In Dashboard"
                    style={{ background: "transparent", border: "none", cursor: "pointer", fontSize: "14px", padding: "0 4px", fontWeight: 700, color: "var(--text-primary)" }}
                >
                    +
                </button>
                {zoomLevel !== "100%" && (
                    <button
                        type="button"
                        onClick={() => setZoomLevel("100%")}
                        style={{ fontSize: "10px", background: "var(--bg-secondary)", border: "1px solid var(--border-color)", borderRadius: "4px", padding: "2px 6px", cursor: "pointer", marginLeft: "4px" }}
                    >
                        Reset
                    </button>
                )}
            </div>

            {/* In-App Floating AI Surveillance Operations Assistant */}
            <AIAssistantWidget
                isOpen={isAssistantOpen}
                onClose={() => setIsAssistantOpen(false)}
            />
        </div>
    );
}
