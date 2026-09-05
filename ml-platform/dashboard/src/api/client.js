import axios from "axios";

const API = axios.create({
    baseURL: "http://127.0.0.1:8000",
    headers: {
        "Content-Type": "application/json",
    },
});

export const getSystemStatus = async () => {
    const response = await API.get("/status");
    return response.data;
};

export const getAlerts = async () => {
    const response = await API.get("/alerts");
    return response.data;
};

export const getDetections = async () => {
    const response = await API.get("/detections");
    return response.data;
};

export const getCameras = async () => {
    const response = await API.get("/cameras");
    return response.data;
};

export default API;
