import axios from "axios";

const API = axios.create({
    baseURL: "http://127.0.0.1:8000",
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
    camera_name: string;
    location: string;
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

export const verifyOtp = async (data: any) => {
    const res = await API.post("/auth/verify-otp", data);
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

export const updateEnvironmentFeatures = async (envId: number, features: string[]) => {
    const res = await API.patch(`/environments/${envId}/features`, { enabled_features: features });
    return res.data;
};

export const getCameras = async () => {
    const res = await API.get("/cameras");
    return res.data;
};

export const createCamera = async (data: any) => {
    const res = await API.post("/cameras", null, { params: data });
    return res.data;
};

export const getPeople = async (role?: string) => {
    const res = await API.get("/people", { params: { role } });
    return res.data;
};

export const createPerson = async (data: any) => {
    const res = await API.post("/people", data);
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

export default API;
