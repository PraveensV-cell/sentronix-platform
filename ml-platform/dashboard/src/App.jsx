import { useState, useEffect } from "react";
import Navbar from "./components/Navbar";
import Sidebar from "./components/Sidebar";
import AIAssistantWidget from "./components/AIAssistantWidget";

import AuthPage from "./pages/AuthPage";
import EnvironmentSelectPage from "./pages/EnvironmentSelectPage";

import LiveSurveillanceView from "./pages/LiveSurveillanceView";
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

export default function App() {
    const [user, setUser] = useState(null);
    const [environment, setEnvironment] = useState(null);
    const [activeTab, setActiveTab] = useState("surveillance");
    const [isAssistantOpen, setIsAssistantOpen] = useState(false);
    const [systemOnline, setSystemOnline] = useState(true);
    const [alertCount, setAlertCount] = useState(0);

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

        // Check backend heartbeat
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

    const handleAuthenticated = (userData) => {
        setUser(userData);
        // Step 2 Flow: Always present Environment / Mode selection window upon login
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

    // Flow Step 1: Authentication required
    if (!user) {
        return <AuthPage onAuthenticated={handleAuthenticated} />;
    }

    // Flow Step 2: Environment / Mode selection required
    if (!environment) {
        return (
            <EnvironmentSelectPage
                user={user}
                onEnvironmentSelected={handleEnvironmentSelected}
            />
        );
    }

    // Flow Step 3: Main Command Center
    return (
        <div className="sentronix-app-root">
            <Navbar
                user={user}
                environment={environment}
                systemOnline={systemOnline}
                onOpenAssistant={() => setIsAssistantOpen(true)}
                onSwitchEnvironment={handleSwitchEnvironment}
                onLogout={handleLogout}
            />

            <div className="soc-layout-body">
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

                    {activeTab === "map" && <CampusMapView />}

                    {activeTab === "vision_search" && <VisionSearchView />}

                    {activeTab === "attendance" && <AttendanceView />}

                    {activeTab === "alerts" && <AlertsView />}

                    {activeTab === "people" && <PeopleView />}

                    {activeTab === "rules" && <RulesView />}

                    {activeTab === "analytics" && <AnalyticsView />}

                    {activeTab === "cameras" && <CameraManagerView />}

                    {activeTab === "health" && <SystemHealthView />}
                </main>
            </div>

            {/* In-App Floating AI Surveillance Operations Assistant */}
            <AIAssistantWidget
                isOpen={isAssistantOpen}
                onClose={() => setIsAssistantOpen(false)}
            />
        </div>
    );
}
