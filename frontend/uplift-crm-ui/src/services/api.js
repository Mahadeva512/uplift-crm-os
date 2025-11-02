// src/services/api.js
// Keeps older imports working, but points to the real client
import client, { API_BASE_URL } from "../api/client";

export { client as apiClient, API_BASE_URL };
export default client;
