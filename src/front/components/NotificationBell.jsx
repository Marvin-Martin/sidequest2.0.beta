import React, { useEffect } from "react";
import { Link } from "react-router-dom";
import { useNotifications } from "../hooks/useNotifications.jsx";

export const NotificationBell = () => {
  const { notifications, unreadCount, fetchNotifications, markAsRead, markAllAsRead } = useNotifications();

  const handleOpen = () => fetchNotifications();

  return (
    <div className="nav-item dropdown px-2">
      <button
        className="btn position-relative bg-transparent border-0 text-white"
        type="button"
        data-bs-toggle="dropdown"
        aria-expanded="false"
        onClick={handleOpen}
      >
        <i className="fas fa-bell fs-5"></i>
        {unreadCount > 0 && (
          <span className="position-absolute top-0 start-100 translate-middle badge rounded-pill bg-danger">
            {unreadCount > 99 ? "99+" : unreadCount}
          </span>
        )}
      </button>

      <ul
        className="dropdown-menu dropdown-menu-end shadow"
        style={{ width: "340px", maxHeight: "440px", overflowY: "auto" }}
      >
        <li className="d-flex justify-content-between align-items-center px-3 py-2 border-bottom">
          <span className="fw-bold">Notificaciones</span>
          {unreadCount > 0 && (
            <button
              className="btn btn-sm btn-link text-decoration-none p-0"
              onClick={(e) => { e.stopPropagation(); markAllAsRead(); }}
            >
              Marcar todas
            </button>
          )}
        </li>

        {!notifications || notifications.length === 0 ? (
          <li>
            <span className="dropdown-item text-muted text-center py-3">
              No tienes notificaciones
            </span>
          </li>
        ) : (
          notifications.map((n) => (
            <li
              key={n.id}
              className={`dropdown-item d-flex justify-content-between align-items-start border-bottom ${
                n.is_read ? "text-muted" : "fw-semibold"
              }`}
              style={{ whiteSpace: "normal" }}
            >
              <NotificationContent notif={n} />
              {!n.is_read && (
                <button
                  className="btn btn-sm btn-outline-success p-1 flex-shrink-0 ms-2"
                  onClick={(e) => { e.stopPropagation(); markAsRead(n.id); }}
                  title="Marcar como leída"
                >
                  <i className="fas fa-check"></i>
                </button>
              )}
            </li>
          ))
        )}
      </ul>
    </div>
  );
};

// Renderiza la notificación con enlace según el tipo
const NotificationContent = ({ notif }) => {
  const link = getLinkFor(notif);
  const body = (
    <div className="me-3" style={{ fontSize: "0.9rem" }}>
      <div>{notif.message}</div>
      <small className="text-muted">{new Date(notif.created_at).toLocaleString()}</small>
    </div>
  );
  return link ? <Link to={link} className="text-decoration-none text-reset flex-grow-1">{body}</Link> : body;
};

const getLinkFor = (notif) => {
  switch (notif.type) {
    case "new_message":     return notif.related_id ? `/messages/${notif.related_id}` : "/messages";
    case "friend_request":
    case "friend_accepted": return notif.related_id ? `/friends/${notif.related_id}` : "/friends";
    case "event_update":
    case "event_cancelled": return notif.related_id ? `/single/${notif.related_id}` : null;
    default: return null;
  }
};