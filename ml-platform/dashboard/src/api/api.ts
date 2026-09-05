import axios from "axios";

const API = axios.create({
    baseURL: "http://127.0.0.1:8000",
    headers: {
        "Content-Type": "application/json",
    },
});

export interface Camera {
    id: number;
    camera_name: string;
    location: string;
    status: string;
}

export interface Detection {
    id: number;
    timestamp: string;
    camera_id: string;
    object: string;
    confidence: number;
    bbox: string;
}

export interface Alert {
    id: number;
    timestamp: string;
    object: string;
    priority: string;
    confidence: number;
    status: string;
}

export interface CamerasResponse {
    count?: number;
    cameras: Camera[];
}

export interface DetectionsResponse {
    count?: number;
    detections: Detection[];
}

export interface AlertsResponse {
    count?: number;
    alerts: Alert[];
}

export const getCameras = async (): Promise<CamerasResponse> => {
    const response = await API.get<CamerasResponse>("/cameras");
    return response.data;
};

export const getDetections = async (): Promise<DetectionsResponse> => {
    const response = await API.get<DetectionsResponse>("/detections");
    return response.data;
};

export const getAlerts = async (): Promise<AlertsResponse> => {
    const response = await API.get<AlertsResponse>("/alerts");
    return response.data;
};

export default API;
