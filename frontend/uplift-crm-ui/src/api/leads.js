// src/api/leads.js
import client from "./client";

// List all leads
export const listLeads = (params) =>
  client.get("/leads", { params }).then((r) => r.data);

// Get a single lead
export const getLead = (id) =>
  client.get(`/leads/${id}`).then((r) => r.data);

// Create a new lead
export const createLead = (data) =>
  client.post("/leads", data).then((r) => r.data);

// Update an existing lead
export const updateLead = (id, data) =>
  client.put(`/leads/${id}`, data).then((r) => r.data);

// Delete a lead
export const deleteLead = (id) =>
  client.delete(`/leads/${id}`).then((r) => r.data);
