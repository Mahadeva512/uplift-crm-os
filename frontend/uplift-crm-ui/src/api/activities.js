// src/api/activities.js
import client from "./client";

export const listActivities = (params) =>
  client.get("/activities", { params }).then((r) => r.data);

export const getActivity = (id) =>
  client.get(`/activities/${id}`).then((r) => r.data);

export const createActivity = (data) =>
  client.post("/activities", data).then((r) => r.data);

export const updateActivity = (id, data) =>
  client.put(`/activities/${id}`, data).then((r) => r.data);

export const verifyActivity = (data) =>
  client.post("/activities/verify", data).then((r) => r.data);

export const summaryOverview = () =>
  client.get("/activities/summary/overview").then((r) => r.data);
