import { useEffect, useState } from "react";
import "./Dashboard.css";

const API_URL = "http://127.0.0.1:8000";

function Dashboard() {
    const [cameras, setCameras] = useState([]);
    const [selectedCamera, setSelectedCamera] = useState(null);
    const [detections, setDetections] = useState([]);
    const [alerts, setAlerts] = useState([]);
    const [cameraOnline, setCameraOnline] = useState(false);
    const [modelOnline, setModelOnline] = useState(false);
    const [loading, setLoading] = useState(true);

    const loadData = async () => {
        try {
            const [
                camerasResponse,
                detectionsResponse,
                alertsResponse,
                statusResponse,
            ] = await Promise.all([
                fetch(`${API_URL}/cameras`),
                fetch(`${API_URL}/detections`),
                fetch(`${API_URL}/alerts`),
                fetch(`${API_URL}/status`),
            ]);

            if (camerasResponse.ok) {
                const data = await camerasResponse.json();
                const cameraList = data.cameras || [];

                setCameras(cameraList);

                setSelectedCamera((current) => {
                    if (current === null && cameraList.length > 0) {
                        return cameraList[0];
                    }

                    if (current !== null) {
                        const updatedCamera = cameraList.find(
                            (camera) => camera.id === current.id,
                        );

                        return updatedCamera || current;
                    }

                    return current;
                });

                const online = cameraList.some(
                    (camera) =>
                        String(camera.status).toLowerCase() === "online",
                );

                setCameraOnline(online);
            }

            if (detectionsResponse.ok) {
                const data = await detectionsResponse.json();
                setDetections(data.detections || []);
            }

            if (alertsResponse.ok) {
                const data = await alertsResponse.json();
                setAlerts(data.alerts || []);
            }

            if (statusResponse.ok) {
                const data = await statusResponse.json();
                setModelOnline(data.AI === "running");
            }
        } catch (error) {
            console.error("Dashboard data error:", error);
            setCameraOnline(false);
            setModelOnline(false);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        loadData();

        const interval = setInterval(loadData, 3000);

        return () => {
            clearInterval(interval);
        };
    }, []);

    const activeAlerts = alerts.filter(
        (alert) => String(alert.status).toUpperCase() === "ACTIVE",
    );

    const latestDetection = detections.length > 0 ? detections[0] : null;

    const streamUrl = selectedCamera
        ? `${API_URL}/stream/${selectedCamera.id}`
        : null;

    const selectedCameraOnline = selectedCamera
        ? String(selectedCamera.status).toLowerCase() === "online"
        : false;

    return (
        <div className="dashboard">
            <header className="dashboard-header">
                <div>
                    <h1>Sentronix AI Security</h1>
                    <p>Intelligent Security Monitoring</p>
                </div>

                <div
                    className={
                        cameraOnline
                            ? "system-status online"
                            : "system-status offline"
                    }
                >
                    <span></span>
                    {cameraOnline ? "SYSTEM ONLINE" : "CAMERA OFFLINE"}
                </div>
            </header>

            <section className="dashboard-stats">
                <div className="stat-card">
                    <span className="stat-label">CAMERAS</span>
                    <strong>{cameras.length}</strong>
                </div>

                <div className="stat-card">
                    <span className="stat-label">DETECTIONS</span>
                    <strong>{detections.length}</strong>
                </div>

                <div className="stat-card">
                    <span className="stat-label">ACTIVE ALERTS</span>
                    <strong>{activeAlerts.length}</strong>
                </div>

                <div className="stat-card">
                    <span className="stat-label">AI MODEL</span>
                    <strong>{modelOnline ? "READY" : "OFFLINE"}</strong>
                </div>
            </section>

            <section className="camera-selector-panel">
                <div className="panel-header">
                    <div>
                        <h2>Cameras</h2>
                        <p>Select a camera to monitor</p>
                    </div>

                    <span>{cameras.length} registered</span>
                </div>

                <div className="camera-selector">
                    {loading ? (
                        <div className="empty-state">Loading cameras...</div>
                    ) : cameras.length === 0 ? (
                        <div className="empty-state">No cameras registered</div>
                    ) : (
                        cameras.map((camera) => {
                            const isSelected = selectedCamera?.id === camera.id;

                            const isOnline =
                                String(camera.status).toLowerCase() ===
                                "online";

                            return (
                                <button
                                    key={camera.id}
                                    type="button"
                                    className={
                                        isSelected
                                            ? "camera-card selected"
                                            : "camera-card"
                                    }
                                    onClick={() => setSelectedCamera(camera)}
                                >
                                    <div className="camera-card-top">
                                        <strong>{camera.camera_name}</strong>

                                        <span
                                            className={
                                                isOnline
                                                    ? "camera-dot online"
                                                    : "camera-dot offline"
                                            }
                                        ></span>
                                    </div>

                                    <span className="camera-location">
                                        {camera.location ||
                                            "Location unavailable"}
                                    </span>

                                    <span
                                        className={
                                            isOnline
                                                ? "camera-card-status online"
                                                : "camera-card-status offline"
                                        }
                                    >
                                        {camera.status || "UNKNOWN"}
                                    </span>
                                </button>
                            );
                        })
                    )}
                </div>
            </section>

            <main className="dashboard-main">
                <section className="camera-panel">
                    <div className="panel-header">
                        <div>
                            <h2>Live Camera</h2>

                            <p>
                                {selectedCamera
                                    ? selectedCamera.camera_name
                                    : "No camera selected"}
                            </p>
                        </div>

                        <span
                            className={
                                selectedCameraOnline
                                    ? "camera-status online"
                                    : "camera-status offline"
                            }
                        >
                            {selectedCameraOnline ? "LIVE" : "OFFLINE"}
                        </span>
                    </div>

                    <div className="camera-view">
                        {selectedCameraOnline && streamUrl ? (
                            <img src={streamUrl} alt="Sentronix live camera" />
                        ) : (
                            <div className="camera-placeholder">
                                <h3>Camera Offline</h3>

                                <p>Unable to connect to the selected camera</p>
                            </div>
                        )}
                    </div>

                    <div className="camera-info">
                        <div className="camera-info-item">
                            <span>CAMERA</span>

                            <strong>
                                {selectedCamera
                                    ? selectedCamera.camera_name
                                    : "--"}
                            </strong>
                        </div>

                        <div className="camera-info-item">
                            <span>LOCATION</span>

                            <strong>
                                {selectedCamera
                                    ? selectedCamera.location || "--"
                                    : "--"}
                            </strong>
                        </div>

                        <div className="camera-info-item">
                            <span>AI MODEL</span>

                            <strong>
                                {modelOnline ? "ACTIVE" : "OFFLINE"}
                            </strong>
                        </div>

                        <div className="camera-info-item">
                            <span>DETECTIONS</span>

                            <strong>{detections.length}</strong>
                        </div>
                    </div>
                </section>

                <section className="alerts-panel">
                    <div className="panel-header">
                        <div>
                            <h2>Recent Alerts</h2>
                            <p>Security events</p>
                        </div>

                        <span>{activeAlerts.length} active</span>
                    </div>

                    <div className="alerts-list">
                        {alerts.length === 0 ? (
                            <div className="empty-state">
                                No alerts detected
                            </div>
                        ) : (
                            alerts.slice(0, 8).map((alert) => (
                                <div className="alert-item" key={alert.id}>
                                    <div className="alert-info">
                                        <strong>{alert.object}</strong>

                                        <span>{alert.timestamp}</span>
                                    </div>

                                    <div className="alert-meta">
                                        <span
                                            className={`priority ${String(
                                                alert.priority,
                                            ).toLowerCase()}`}
                                        >
                                            {alert.priority}
                                        </span>

                                        <span>
                                            {(
                                                Number(alert.confidence) * 100
                                            ).toFixed(0)}
                                            %
                                        </span>
                                    </div>
                                </div>
                            ))
                        )}
                    </div>
                </section>
            </main>

            <section className="detection-summary">
                <div className="summary-card">
                    <span>LATEST DETECTION</span>

                    <strong>
                        {latestDetection ? latestDetection.object : "NONE"}
                    </strong>
                </div>

                <div className="summary-card">
                    <span>CONFIDENCE</span>

                    <strong>
                        {latestDetection
                            ? `${(
                                  Number(latestDetection.confidence) * 100
                              ).toFixed(1)}%`
                            : "--"}
                    </strong>
                </div>

                <div className="summary-card">
                    <span>CAMERA</span>

                    <strong>
                        {latestDetection ? latestDetection.camera_id : "--"}
                    </strong>
                </div>

                <div className="summary-card">
                    <span>LAST DETECTION</span>

                    <strong>
                        {latestDetection ? latestDetection.timestamp : "--"}
                    </strong>
                </div>
            </section>

            <section className="detections-panel">
                <div className="panel-header">
                    <div>
                        <h2>Recent Detections</h2>

                        <p>AI detection activity</p>
                    </div>

                    <span>{detections.length} detections</span>
                </div>

                <div className="detections-table">
                    <div className="table-header">
                        <span>ID</span>
                        <span>OBJECT</span>
                        <span>CAMERA</span>
                        <span>CONFIDENCE</span>
                        <span>TIMESTAMP</span>
                    </div>

                    {detections.length === 0 ? (
                        <div className="empty-state">
                            No detections available
                        </div>
                    ) : (
                        detections.slice(0, 10).map((detection) => (
                            <div className="table-row" key={detection.id}>
                                <span>#{detection.id}</span>

                                <strong>{detection.object}</strong>

                                <span>{detection.camera_id}</span>

                                <span>
                                    {(
                                        Number(detection.confidence) * 100
                                    ).toFixed(0)}
                                    %
                                </span>

                                <span>{detection.timestamp}</span>
                            </div>
                        ))
                    )}
                </div>
            </section>
        </div>
    );
}

export default Dashboard;
