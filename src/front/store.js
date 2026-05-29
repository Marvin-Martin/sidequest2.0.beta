export const initialStore = () => {
  return {
    message: null,
    user: JSON.parse(localStorage.getItem("user") || "null"),
    token: localStorage.getItem("token") || null,
    todos: [
      { id: 1, title: "Make the bed", background: null },
      { id: 2, title: "Do my homework", background: null },
    ],

    chatRooms: [],

    friends: [],
    incomingRequests: [],
    outgoingRequests: [],

    notifications: [],
    unreadCount: 0,
  };
};

export default function storeReducer(store, action = {}) {
  switch (action.type) {
    case "set_hello":
      return { ...store, message: action.payload };

    case "add_task": {
      const { id, color } = action.payload;
      return {
        ...store,
        todos: store.todos.map((t) =>
          t.id === id ? { ...t, background: color } : t
        ),
      };
    }

    // ── auth ──
    case "set_user":
      if (action.payload) localStorage.setItem("user", JSON.stringify(action.payload));
      else localStorage.removeItem("user");
      return { ...store, user: action.payload };

    case "set_token":
      if (action.payload) localStorage.setItem("token", action.payload);
      else localStorage.removeItem("token");
      return { ...store, token: action.payload };

    case "logout":
      localStorage.removeItem("token");
      localStorage.removeItem("user");
      return {
        ...store, user: null, token: null, chatRooms: [],
        friends: [], incomingRequests: [], outgoingRequests: [],
        notifications: [], unreadCount: 0,
      };

    // ── chat ──
    case "set_chat_rooms":
      return { ...store, chatRooms: action.payload };

    // ── friends ──
    case "set_friends":          return { ...store, friends: action.payload };
    case "set_incoming_requests": return { ...store, incomingRequests: action.payload };
    case "set_outgoing_requests": return { ...store, outgoingRequests: action.payload };
    case "remove_friend":
      return { ...store, friends: store.friends.filter(f => f.friend?.id !== action.payload) };
    case "remove_incoming_request":
      return { ...store, incomingRequests: store.incomingRequests.filter(r => r.id !== action.payload) };
    case "remove_outgoing_request":
      return { ...store, outgoingRequests: store.outgoingRequests.filter(r => r.id !== action.payload) };
    case "add_outgoing_request":
      return { ...store, outgoingRequests: [...store.outgoingRequests, action.payload] };
    case "add_friend":
      return { ...store, friends: [...store.friends, action.payload] };

    // ── notifications ──
    case "set_notifications":  return { ...store, notifications: action.payload };
    case "set_unread_count":   return { ...store, unreadCount: action.payload };
    case "add_notification":
      return {
        ...store,
        notifications: [action.payload, ...store.notifications],
        unreadCount: store.unreadCount + 1,
      };
    case "mark_notification_read":
      return {
        ...store,
        notifications: store.notifications.map(n =>
          n.id === action.payload ? { ...n, is_read: true } : n
        ),
        unreadCount: Math.max(0, store.unreadCount - 1),
      };
    case "mark_all_notifications_read":
      return {
        ...store,
        notifications: store.notifications.map(n => ({ ...n, is_read: true })),
        unreadCount: 0,
      };

    default:
      console.warn("Unknown action type:", action.type);
      return store;
  }
}