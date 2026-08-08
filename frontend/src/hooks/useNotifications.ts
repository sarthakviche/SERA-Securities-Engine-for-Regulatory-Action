/**
 * useNotifications — React hook for in-app notification state.
 *
 * - Opens a persistent EventSource (SSE) connection to the backend stream.
 * - Fetches existing notifications via REST on mount.
 * - Merges SSE push events into local state in real-time (no page refresh needed).
 * - Fires a sonner toast for every new push notification.
 * - Exposes markRead / markAllRead helpers that optimistically update local state.
 */

import { useEffect, useRef, useState, useCallback } from "react";
import { toast } from "sonner";
import { api } from "@/lib/api";

export interface AppNotification {
  id: string;
  user_id: string;
  event_type: string;
  title: string;
  body?: string;
  resource_type?: string;
  resource_id?: string;
  is_read: boolean;
  idempotency_key: string;
  created_at: string;
}

export function useNotifications() {
  const [notifications, setNotifications] = useState<AppNotification[]>([]);
  const [unreadCount, setUnreadCount] = useState(0);
  const [isLoading, setIsLoading] = useState(true);
  const esRef = useRef<EventSource | null>(null);

  // ── Initial fetch ──────────────────────────────────────────────────────────
  const fetchNotifications = useCallback(async () => {
    try {
      const data = await api.getNotifications();
      if (data?.notifications) {
        setNotifications(data.notifications);
        setUnreadCount(data.unread_count ?? 0);
      }
    } catch (err) {
      // Backend may not be running in all dev scenarios; fail silently
      console.warn("[useNotifications] fetch failed:", err);
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchNotifications();
  }, [fetchNotifications]);

  // ── SSE connection ─────────────────────────────────────────────────────────
  useEffect(() => {
    const url = api.notificationStreamUrl();
    const es = new EventSource(url);
    esRef.current = es;

    es.addEventListener("notification", (e: MessageEvent) => {
      try {
        const notification: AppNotification = JSON.parse(e.data);

        // Merge into list (prepend, most-recent first)
        setNotifications((prev) => {
          // Deduplicate by id
          if (prev.some((n) => n.id === notification.id)) return prev;
          return [notification, ...prev];
        });
        setUnreadCount((c) => c + 1);

        // Show toast
        toast(notification.title, {
          description: notification.body ?? undefined,
          duration: 5000,
        });
      } catch (err) {
        console.warn("[useNotifications] SSE parse error:", err);
      }
    });

    es.onerror = () => {
      // EventSource auto-reconnects; no extra handling needed for MVP
      console.warn("[useNotifications] SSE connection error — will retry");
    };

    return () => {
      es.close();
      esRef.current = null;
    };
  }, []);

  // ── Actions ────────────────────────────────────────────────────────────────
  const markRead = useCallback(async (id: string) => {
    // Optimistic update
    setNotifications((prev) =>
      prev.map((n) => (n.id === id ? { ...n, is_read: true } : n)),
    );
    setUnreadCount((c) => Math.max(0, c - 1));

    try {
      await api.markNotificationRead(id);
    } catch (err) {
      console.warn("[useNotifications] markRead failed:", err);
      // Rollback
      setNotifications((prev) =>
        prev.map((n) => (n.id === id ? { ...n, is_read: false } : n)),
      );
      setUnreadCount((c) => c + 1);
    }
  }, []);

  const markAllRead = useCallback(async () => {
    // Optimistic update
    setNotifications((prev) => prev.map((n) => ({ ...n, is_read: true })));
    setUnreadCount(0);

    try {
      await api.markAllNotificationsRead();
    } catch (err) {
      console.warn("[useNotifications] markAllRead failed:", err);
      // Re-fetch to restore correct state
      fetchNotifications();
    }
  }, [fetchNotifications]);

  return {
    notifications,
    unreadCount,
    isLoading,
    markRead,
    markAllRead,
    refresh: fetchNotifications,
  };
}
