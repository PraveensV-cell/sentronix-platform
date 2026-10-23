import axios from "axios";

export const getApiBaseUrl = (): string => {
    if (
        typeof window !== "undefined" &&
        window.location.hostname &&
        window.location.hostname !== "localhost" &&
        window.location.hostname !== "127.0.0.1"
    ) {
        return `http://${window.location.hostname}:8000`;
    }
    return "http://127.0.0.1:8000";
};

export const API_BASE_URL = getApiBaseUrl();

const API = axios.create({
    baseURL: API_BASE_URL,
    headers: {
        "Content-Type": "application/json",
    },
});

// Attach token if present in localStorage
API.interceptors.request.use((config) => {
    const token = localStorage.getItem("sentronix_token");
    if (token) {
        config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
});

export interface User {
    id: number;
    username: string;
    full_name: string;
    email: string;
    role: string;
    is_verified?: boolean;
}

export interface Environment {
    id: number;
    name: string;
    type: string;
    description?: string;
    location?: string;
    enabled_features: string[];
    is_active: number;
}

export interface Camera {
    id: number;
    environment_id?: number;
    group_id?: number;
    group_name?: string;
    camera_name: string;
    location: string;
    zone?: string;
    assigned_function?: string;
    status: string;
    source_type?: string;
    source_url?: string;
    ai_enabled?: number;
}

export interface Person {
    id: number;
    identifier: string;
    name: string;
    role: string;
    department?: string;
    class_grade?: string;
    allowed_dress?: string;
    phone?: string;
    email?: string;
    status?: string;
    photo_url?: string;
    is_enrolled: number;
    today_attendance?: {
        status: string;
        timestamp: string | null;
        confidence?: number;
    };
}

export interface AttendanceRecord {
    id: number;
    timestamp: string;
    confidence: number;
    status: string;
    presence_seconds: number;
    evidence_snapshot?: string;
    person_id: number;
    person_name: string;
    identifier: string;
    role: string;
    class_grade?: string;
    camera_name?: string;
}

export interface Rule {
    id: number;
    name: string;
    rule_type: string;
    conditions: Record<string, any>;
    severity: string;
    cooldown_seconds: number;
    is_enabled: number;
}

export interface Alert {
    id: number;
    timestamp: string;
    object: string;
    priority: string;
    confidence: number;
    status: string;
    camera_id?: string;
}

export interface Detection {
    id: number;
    timestamp: string;
    camera_id: string;
    object: string;
    confidence: number;
    bbox: string;
}

// ==========================================
// API FUNCTIONS
// ==========================================

export const loginUser = async (data: any) => {
    const res = await API.post("/auth/login", data);
    return res.data;
};

export const registerUser = async (data: any) => {
    const res = await API.post("/auth/register", data);
    return res.data;
};

export const getEnvironments = async () => {
    const res = await API.get("/environments");
    return res.data;
};

export const createEnvironment = async (data: any) => {
    const res = await API.post("/environments", data);
    return res.data;
};

export const updateEnvironment = async (envId: number, data: { name?: string; type?: string; description?: string; location?: string }) => {
    const res = await API.patch(`/environments/${envId}`, data);
    return res.data;
};

export const updateEnvironmentFeatures = async (envId: number, features: string[]) => {
    const res = await API.patch(`/environments/${envId}/features`, { enabled_features: features });
    return res.data;
};

export const getCameras = async (params: any = {}) => {
    const res = await API.get("/cameras", { params });
    return res.data;
};

export const createCamera = async (data: any) => {
    const res = await API.post("/cameras", data);
    return res.data;
};

export const assignCameraFunction = async (cameraId: number | string, assigned_function: string) => {
    const res = await API.patch(`/cameras/${cameraId}/function`, { assigned_function });
    return res.data;
};

export const assignCameraSource = async (
    cameraId: number | string,
    data: { source_type: string; source_url: string; location?: string; zone?: string }
) => {
    const res = await API.patch(`/cameras/${cameraId}/source`, data);
    return res.data;
};

export const toggleCameraAi = async (cameraId: number | string) => {
    const res = await API.patch(`/cameras/${cameraId}/toggle-ai`);
    return res.data;
};

export const getCameraFunctions = async () => {
    const res = await API.get("/cameras/functions/list");
    return res.data;
};

export const getPeople = async (role?: string) => {
    const res = await API.get("/people", { params: { role } });
    return res.data;
};

export const getPerson = async (personId: number) => {
    const res = await API.get(`/people/${personId}`);
    return res.data;
};

export const createPerson = async (data: any) => {
    const res = await API.post("/people", data);
    return res.data;
};

export const updatePerson = async (personId: number, data: any) => {
    const res = await API.patch(`/people/${personId}`, data);
    return res.data;
};

export const getPersonHistory = async (personId: number) => {
    const res = await API.get(`/people/${personId}/history`);
    return res.data;
};

export const markPersonPresent = async (personId: number) => {
    const res = await API.post(`/people/${personId}/mark-present`);
    return res.data;
};

export const deletePerson = async (personId: number) => {
    const res = await API.delete(`/people/${personId}`);
    return res.data;
};

export const enrollPersonFace = async (personId: number, data: any = {}) => {
    const res = await API.post(`/people/${personId}/enroll-face`, data);
    return res.data;
};

export const getAttendance = async (date?: string) => {
    const res = await API.get("/attendance", { params: { attendance_date: date } });
    return res.data;
};

export const getAttendanceSummary = async () => {
    const res = await API.get("/attendance/summary");
    return res.data;
};

export const recordManualAttendance = async (data: any) => {
    const res = await API.post("/attendance/record", data);
    return res.data;
};

export const getRules = async () => {
    const res = await API.get("/rules");
    return res.data;
};

export const createRule = async (data: any) => {
    const res = await API.post("/rules", data);
    return res.data;
};

export const toggleRule = async (ruleId: number) => {
    const res = await API.patch(`/rules/${ruleId}/toggle`);
    return res.data;
};

export const getAlerts = async () => {
    const res = await API.get("/alerts");
    return res.data;
};

export const updateAlertStatus = async (alertId: number, status: string) => {
    const res = await API.patch(`/alerts/${alertId}/status`, null, { params: { status } });
    return res.data;
};

export const getDetections = async () => {
    const res = await API.get("/detections");
    return res.data;
};

export const getStatus = async () => {
    const res = await API.get("/status");
    return res.data;
};

export const askAIAssistant = async (message: string) => {
    const res = await API.post("/assistant/chat", { message });
    return res.data;
};

export const searchVisionEvents = async (params: {
    q?: string;
    camera_id?: string;
    object_type?: string;
    start_date?: string;
    end_date?: string;
    sort_by?: string;
}) => {
    const res = await API.get("/vision/search", { params });
    return res.data;
};

export const getHardwareTelemetry = async () => {
    const res = await API.get("/system/hardware-telemetry");
    return res.data;
};

export const getExportCsvUrl = (reportType: string = "attendance") => {
    return `${API_BASE_URL}/reports/export/csv?report_type=${reportType}`;
};

export const getNetworkInfo = async () => {
    const res = await API.get("/stream/network-info");
    return res.data;
};

export const uploadCameraFrame = async (cameraId: number | string, blob: Blob) => {
    const formData = new FormData();
    formData.append("file", blob, "frame.jpg");
    const res = await API.post(`/stream/${cameraId}/upload-frame`, formData, {
        headers: { "Content-Type": "multipart/form-data" },
    });
    return res.data;
};

export default API;
