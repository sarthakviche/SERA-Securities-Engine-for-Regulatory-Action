/**
 * NotificationPanel — Bell icon with a Radix Popover notification list.
 *
 * - Shows an unread count badge when there are unread notifications.
 * - Real-time updates via the useNotifications hook (SSE).
 * - "Mark all read" button in the panel header.
 * - Each item links to the relevant resource in the app.
 * - Minimal, enterprise-grade design consistent with the SERA design system.
 */

import { useNavigate } from "@tanstack/react-router";
import { formatDistanceToNow } from "date-fns";
import {
  AlertTriangle,
  Bell,
  CheckCircle2,
  Clock,
  FileCheck,
  FileX,
  ShieldAlert,
  ShieldCheck,
  Sparkles,
  TrendingUp,
  X,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover";
import { cn } from "@/lib/utils";
import { useNotifications, type AppNotification } from "@/hooks/useNotifications";

// ── Icon mapping by event type ────────────────────────────────────────────────

const EVENT_ICON: Record<
  string,
  { icon: React.ElementType; color: string }
> = {
  "task.created": { icon: Sparkles, color: "text-blue-500" },
  "task.overdue": { icon: Clock, color: "text-red-500" },
  "task.completed": { icon: CheckCircle2, color: "text-emerald-500" },
  "evidence.submitted": { icon: FileCheck, color: "text-blue-400" },
  "evidence.rejected": { icon: FileX, color: "text-red-500" },
  "evidence.accepted": { icon: FileCheck, color: "text-emerald-500" },
  "compliance.gap_detected": { icon: AlertTriangle, color: "text-amber-500" },
  "compliance.verified": { icon: ShieldCheck, color: "text-emerald-500" },
  "escalation.triggered": { icon: TrendingUp, color: "text-orange-500" },
  "gate_2.rejected": { icon: ShieldAlert, color: "text-red-500" },
  "workflow.stage_completed": { icon: Sparkles, color: "text-violet-500" },
};

function getIconMeta(eventType: string) {
  return (
    EVENT_ICON[eventType] ?? { icon: Bell, color: "text-muted-foreground" }
  );
}

// ── Individual notification item ───────────────────────────────────────────────

function NotificationItem({
  notification,
  onRead,
}: {
  notification: AppNotification;
  onRead: (id: string) => void;
}) {
  const navigate = useNavigate();
  const { icon: Icon, color } = getIconMeta(notification.event_type);

  const handleClick = () => {
    if (!notification.is_read) onRead(notification.id);

    // Navigate to the relevant resource
    const { resource_type } = notification;
    if (resource_type === "task") navigate({ to: "/implementation-tracker" });
    else if (resource_type === "workflow") navigate({ to: "/workspace" });
    else if (resource_type === "obligation") navigate({ to: "/obligations" });
  };

  return (
    <button
      type="button"
      onClick={handleClick}
      className={cn(
        "group relative flex w-full gap-3 rounded-lg px-3 py-3 text-left transition-colors",
        "hover:bg-surface-2/70",
        !notification.is_read && "bg-primary/[0.04]",
      )}
    >
      {/* Unread indicator */}
      {!notification.is_read && (
        <span className="absolute left-1.5 top-4 h-1.5 w-1.5 rounded-full bg-primary" />
      )}

      {/* Event icon */}
      <span
        className={cn(
          "mt-0.5 flex h-7 w-7 shrink-0 items-center justify-center rounded-full",
          "bg-surface-2",
        )}
      >
        <Icon className={cn("h-3.5 w-3.5", color)} />
      </span>

      {/* Content */}
      <div className="min-w-0 flex-1">
        <div
          className={cn(
            "truncate text-[13px] leading-tight",
            notification.is_read
              ? "font-medium text-foreground/80"
              : "font-semibold text-foreground",
          )}
        >
          {notification.title}
        </div>
        {notification.body && (
          <div className="mt-0.5 line-clamp-2 text-[11px] leading-relaxed text-muted-foreground">
            {notification.body}
          </div>
        )}
        <div className="mt-1 text-[10px] text-muted-foreground/70">
          {formatDistanceToNow(new Date(notification.created_at), {
            addSuffix: true,
          })}
        </div>
      </div>
    </button>
  );
}

// ── Main panel ─────────────────────────────────────────────────────────────────

export function NotificationPanel() {
  const { notifications, unreadCount, isLoading, markRead, markAllRead } =
    useNotifications();

  return (
    <Popover>
      <PopoverTrigger asChild>
        <Button
          variant="ghost"
          size="icon"
          className="relative"
          aria-label="Notifications"
          id="notification-bell-btn"
        >
          <Bell className="h-4 w-4" />
          {unreadCount > 0 && (
            <span className="absolute right-2 top-2 flex h-4 w-4 items-center justify-center rounded-full bg-destructive text-[9px] font-bold text-destructive-foreground">
              {unreadCount > 9 ? "9+" : unreadCount}
            </span>
          )}
        </Button>
      </PopoverTrigger>

      <PopoverContent
        align="end"
        sideOffset={8}
        className="w-80 p-0 shadow-xl"
      >
        {/* Header */}
        <div className="flex items-center justify-between border-b border-border px-4 py-3">
          <div className="flex items-center gap-2">
            <span className="text-[13px] font-semibold text-foreground">
              Notifications
            </span>
            {unreadCount > 0 && (
              <span className="rounded-full bg-primary/10 px-1.5 py-0.5 text-[10px] font-semibold text-primary">
                {unreadCount} new
              </span>
            )}
          </div>
          {unreadCount > 0 && (
            <button
              type="button"
              onClick={markAllRead}
              className="text-[11px] text-muted-foreground hover:text-foreground transition-colors"
            >
              Mark all read
            </button>
          )}
        </div>

        {/* Notification list */}
        <div className="max-h-[380px] overflow-y-auto overscroll-contain px-1 py-1">
          {isLoading ? (
            <div className="flex flex-col gap-2 px-3 py-4">
              {[1, 2, 3].map((i) => (
                <div key={i} className="flex gap-3 animate-pulse">
                  <div className="h-7 w-7 rounded-full bg-muted" />
                  <div className="flex-1 space-y-1.5 pt-0.5">
                    <div className="h-2.5 w-3/4 rounded bg-muted" />
                    <div className="h-2 w-1/2 rounded bg-muted" />
                  </div>
                </div>
              ))}
            </div>
          ) : notifications.length === 0 ? (
            <div className="flex flex-col items-center gap-2 py-10 text-center">
              <CheckCircle2 className="h-8 w-8 text-muted-foreground/30" />
              <p className="text-[12px] font-medium text-muted-foreground">
                You&apos;re all caught up
              </p>
              <p className="text-[11px] text-muted-foreground/60">
                No new notifications
              </p>
            </div>
          ) : (
            notifications.map((n) => (
              <NotificationItem key={n.id} notification={n} onRead={markRead} />
            ))
          )}
        </div>

        {/* Footer link */}
        {notifications.length > 0 && (
          <div className="border-t border-border px-4 py-2.5">
            <p className="text-[10px] text-muted-foreground/60 text-center">
              Manage preferences in{" "}
              <a
                href="/settings"
                className="text-primary hover:underline"
              >
                Settings → Notifications
              </a>
            </p>
          </div>
        )}
      </PopoverContent>
    </Popover>
  );
}
