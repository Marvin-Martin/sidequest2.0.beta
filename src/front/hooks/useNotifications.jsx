import { useEffect, useCallback } from "react";
import useGlobalReducer from "./useGlobalReducer.jsx";
import { api } from "../services/api";

const POLL_INTERVAL = 5000;

export const useNotifications = () => {
  const { store, dispatch } = useGlobalReducer();

  const fetchNotifications = useCallback(async () => {
    if (!store.token) return;
    try {
      const data = await api.get("/notifications");
      dispatch({ type: "set_notifications", payload: data });
    } catch (e) { console.error(e); }
  }, [store.token, dispatch]);

  const fetchUnreadCount = useCallback(async () => {
    if (!store.token) return;
    try {
      const { count } = await api.get("/notifications/unread-count");
      dispatch({ type: "set_unread_count", payload: count });
    } catch (e) { /* silencioso */ }
  }, [store.token, dispatch]);

  const markAsRead = useCallback(async (id) => {
    try {
      await api.post(`/notifications/${id}/read`);
      dispatch({ type: "mark_notification_read", payload: id });
    } catch (e) { console.error(e); }
  }, [dispatch]);

  const markAllAsRead = useCallback(async () => {
    try {
      await api.post("/notifications/read-all");
      dispatch({ type: "mark_all_notifications_read" });
    } catch (e) { console.error(e); }
  }, [dispatch]);

  useEffect(() => {
    if (!store.token) return;
    fetchUnreadCount();
    const id = setInterval(fetchUnreadCount, POLL_INTERVAL);
    return () => clearInterval(id);
  }, [store.token, fetchUnreadCount]);

  return {
    notifications: store.notifications,
    unreadCount: store.unreadCount,
    fetchNotifications,
    fetchUnreadCount,
    markAsRead,
    markAllAsRead,
  };
};