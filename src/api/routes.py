from flask import Blueprint, request, jsonify
from flask_cors import CORS
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from werkzeug.security import generate_password_hash, check_password_hash
from api.models import (
    db, User, Event, Friendship,
    Conversation, Message, Notification, NotificationType
)
from datetime import datetime, timedelta

api = Blueprint('api', __name__)
CORS(api)


# =========================================================
# INLINE HELPERS (no podemos tocar utils.py)
# =========================================================

def _get_or_create_conversation(event_id, user_a_id, user_b_id):
    """Devuelve/crea conversación. Normaliza ids para que user1 < user2."""
    if user_a_id == user_b_id:
        raise ValueError("You cannot start a conversation with yourself.")
    u1, u2 = sorted([user_a_id, user_b_id])
    conv = Conversation.query.filter_by(event_id=event_id, user1_id=u1, user2_id=u2).first()
    if conv:
        return conv
    conv = Conversation(event_id=event_id, user1_id=u1, user2_id=u2)
    db.session.add(conv)
    db.session.flush()
    return conv


def _notify(user_id, ntype, message, related_id=None):
    """Crea una notificación. No hace commit."""
    n = Notification(user_id=user_id, type=ntype, message=message, related_id=related_id)
    db.session.add(n)
    return n


# =========================================================
# HELLO
# =========================================================
@api.route('/hello', methods=['GET'])
def handle_hello():
    return jsonify({"message": "Hello! I'm a message that came from the backend"}), 200


# =========================================================
# REGISTER
# =========================================================
@api.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == "GET":
        return jsonify({
            "endpoint": "/api/register",
            "method": "POST",
            "body": {"email": "test@test.com", "password": "123456"}
        }), 200

    body = request.get_json() or {}
    email = body.get("email")
    password = body.get("password")

    if not email or not password:
        return jsonify({"msg": "Email and password are required"}), 400
    if User.query.filter_by(email=email).first():
        return jsonify({"msg": "User already exists"}), 400

    new_user = User(email=email, password=generate_password_hash(password), is_active=True)
    db.session.add(new_user)
    db.session.commit()
    return jsonify({"msg": "User registered successfully", "user": new_user.serialize()}), 201


# =========================================================
# LOGIN
# =========================================================
@api.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == "GET":
        return jsonify({
            "endpoint": "/api/login",
            "method": "POST",
            "body": {"email": "test@test.com", "password": "123456"}
        }), 200

    body = request.get_json() or {}
    email = body.get("email")
    password = body.get("password")

    if not email or not password:
        return jsonify({"msg": "Email and password are required"}), 400

    user = User.query.filter_by(email=email).first()
    if not user or not check_password_hash(user.password, password):
        return jsonify({"msg": "Invalid email or password"}), 401

    access_token = create_access_token(identity=str(user.id))
    return jsonify({"token": access_token, "user": user.serialize()}), 200


# =========================================================
# PRIVATE
# =========================================================
@api.route('/private', methods=['GET'])
@jwt_required()
def private():
    user = User.query.get(get_jwt_identity())
    if not user:
        return jsonify({"msg": "User not found"}), 404
    return jsonify({"msg": "Private route accessed", "user": user.serialize()}), 200


# =========================================================
# EVENTS
# =========================================================
@api.route('/events', methods=['POST'])
@jwt_required()
def create_event():
    current_user_id = int(get_jwt_identity())
    body = request.get_json() or {}

    required = ["date", "time", "location"]
    if not all(body.get(f) for f in required):
        return jsonify({"msg": "date, time and location are required"}), 400

    event = Event(
        date=body["date"], time=body["time"], location=body["location"],
        latitude=body.get("latitude"), longitude=body.get("longitude"),
        details=body.get("details"), image=body.get("image"),
        creator_id=current_user_id
    )

    creator = db.session.get(User, current_user_id)
    event.participants.append(creator)

    for friend_id in body.get("invitedFriends", []):
        friend = db.session.get(User, friend_id)
        if friend:
            event.participants.append(friend)

    db.session.add(event)
    db.session.commit()
    return jsonify({"msg": "Event created", "event": event.serialize()}), 201


@api.route('/events', methods=['GET'])
@jwt_required()
def get_events():
    current_user_id = int(get_jwt_identity())
    all_events = Event.query.all()
    visible = [
        e for e in all_events
        if e.creator_id == current_user_id or current_user_id in [p.id for p in e.participants]
    ]
    return jsonify([e.serialize() for e in visible]), 200


# =========================================================
# FRIENDS
# =========================================================
@api.route('/friends', methods=['GET'])
@jwt_required()
def list_friends():
    current_user_id = int(get_jwt_identity())
    friendships = Friendship.query.filter(
        Friendship.status == "accepted",
        (Friendship.requester_id == current_user_id) | (Friendship.addressee_id == current_user_id)
    ).all()
    return jsonify([f.serialize(current_user_id=current_user_id) for f in friendships]), 200


@api.route('/friends/requests', methods=['GET'])
@jwt_required()
def list_friend_requests():
    current_user_id = int(get_jwt_identity())
    direction = request.args.get("direction", "incoming").lower()
    base = Friendship.query.filter(Friendship.status == "pending")

    if direction == "incoming":
        base = base.filter(Friendship.addressee_id == current_user_id)
    elif direction == "outgoing":
        base = base.filter(Friendship.requester_id == current_user_id)
    elif direction == "all":
        base = base.filter(
            (Friendship.requester_id == current_user_id) |
            (Friendship.addressee_id == current_user_id)
        )
    else:
        return jsonify({"msg": "direction must be incoming, outgoing or all"}), 400

    return jsonify([f.serialize(current_user_id=current_user_id) for f in base.all()]), 200


@api.route('/friends/requests', methods=['POST'])
@jwt_required()
def send_friend_request():
    current_user_id = int(get_jwt_identity())
    body = request.get_json() or {}

    target = None
    if body.get("user_id"):
        target = db.session.get(User, body["user_id"])
    elif body.get("email"):
        target = User.query.filter_by(email=body["email"]).first()

    if not target:
        return jsonify({"msg": "Target user not found"}), 404
    if target.id == current_user_id:
        return jsonify({"msg": "You cannot friend yourself"}), 400

    existing = Friendship.query.filter(
        ((Friendship.requester_id == current_user_id) & (Friendship.addressee_id == target.id)) |
        ((Friendship.requester_id == target.id) & (Friendship.addressee_id == current_user_id))
    ).first()

    me = db.session.get(User, current_user_id)
    me_label = me.username or me.email

    if existing:
        if existing.status == "accepted":
            return jsonify({"msg": "You are already friends",
                            "friendship": existing.serialize(current_user_id=current_user_id)}), 409
        if existing.status == "pending":
            return jsonify({"msg": "A request is already pending",
                            "friendship": existing.serialize(current_user_id=current_user_id)}), 409
        existing.requester_id = current_user_id
        existing.addressee_id = target.id
        existing.status = "pending"
        # 🔔 notifica al destinatario
        _notify(target.id, NotificationType.FRIEND_REQUEST,
                f"{me_label} te envió una solicitud de amistad", related_id=current_user_id)
        db.session.commit()
        return jsonify({"msg": "Friend request re-sent",
                        "friendship": existing.serialize(current_user_id=current_user_id)}), 201

    new_friendship = Friendship(requester_id=current_user_id, addressee_id=target.id, status="pending")
    db.session.add(new_friendship)
    # 🔔 notifica al destinatario
    _notify(target.id, NotificationType.FRIEND_REQUEST,
            f"{me_label} te envió una solicitud de amistad", related_id=current_user_id)
    db.session.commit()
    return jsonify({"msg": "Friend request sent",
                    "friendship": new_friendship.serialize(current_user_id=current_user_id)}), 201


@api.route('/friends/requests/<int:request_id>/accept', methods=['PUT'])
@jwt_required()
def accept_friend_request(request_id):
    current_user_id = int(get_jwt_identity())
    friendship = db.session.get(Friendship, request_id)

    if not friendship:
        return jsonify({"msg": "Request not found"}), 404
    if friendship.addressee_id != current_user_id:
        return jsonify({"msg": "Only the addressee can accept this request"}), 403
    if friendship.status != "pending":
        return jsonify({"msg": f"Request is already {friendship.status}"}), 409

    friendship.status = "accepted"
    # 🔔 notifica al que envió la solicitud
    me = db.session.get(User, current_user_id)
    me_label = me.username or me.email
    _notify(friendship.requester_id, NotificationType.FRIEND_ACCEPTED,
            f"{me_label} aceptó tu solicitud de amistad", related_id=current_user_id)
    db.session.commit()
    return jsonify({"msg": "Friend request accepted",
                    "friendship": friendship.serialize(current_user_id=current_user_id)}), 200


@api.route('/friends/requests/<int:request_id>/refuse', methods=['PUT'])
@jwt_required()
def refuse_friend_request(request_id):
    current_user_id = int(get_jwt_identity())
    friendship = db.session.get(Friendship, request_id)

    if not friendship:
        return jsonify({"msg": "Request not found"}), 404
    if friendship.addressee_id != current_user_id:
        return jsonify({"msg": "Only the addressee can refuse this request"}), 403
    if friendship.status != "pending":
        return jsonify({"msg": f"Request is already {friendship.status}"}), 409

    friendship.status = "refused"
    db.session.commit()
    return jsonify({"msg": "Friend request refused",
                    "friendship": friendship.serialize(current_user_id=current_user_id)}), 200


@api.route('/friends/requests/<int:request_id>', methods=['DELETE'])
@jwt_required()
def cancel_friend_request(request_id):
    current_user_id = int(get_jwt_identity())
    friendship = db.session.get(Friendship, request_id)

    if not friendship:
        return jsonify({"msg": "Request not found"}), 404
    if friendship.requester_id != current_user_id:
        return jsonify({"msg": "Only the requester can cancel this request"}), 403
    if friendship.status != "pending":
        return jsonify({"msg": f"Request is already {friendship.status} and cannot be cancelled"}), 409

    db.session.delete(friendship)
    db.session.commit()
    return jsonify({"msg": "Friend request cancelled"}), 200


@api.route('/friends/<int:user_id>', methods=['DELETE'])
@jwt_required()
def unfriend(user_id):
    current_user_id = int(get_jwt_identity())
    friendship = Friendship.query.filter(Friendship.status == "accepted").filter(
        ((Friendship.requester_id == current_user_id) & (Friendship.addressee_id == user_id)) |
        ((Friendship.requester_id == user_id) & (Friendship.addressee_id == current_user_id))
    ).first()
    if not friendship:
        return jsonify({"msg": "Friendship not found"}), 404
    db.session.delete(friendship)
    db.session.commit()
    return jsonify({"msg": "Friend removed"}), 200


@api.route('/friends/search', methods=['GET'])
@jwt_required()
def search_users():
    current_user_id = int(get_jwt_identity())
    q = (request.args.get("q") or "").strip()
    if len(q) < 2:
        return jsonify({"msg": "q must be at least 2 characters"}), 400

    users = (User.query
             .filter(User.id != current_user_id, User.email.ilike(f"%{q}%"))
             .limit(20).all())

    results = []
    for u in users:
        pair = Friendship.query.filter(
            ((Friendship.requester_id == current_user_id) & (Friendship.addressee_id == u.id)) |
            ((Friendship.requester_id == u.id) & (Friendship.addressee_id == current_user_id))
        ).first()
        results.append({
            "id": u.id, "email": u.email,
            "status": pair.status if pair else "none",
            "direction": ("outgoing" if pair and pair.requester_id == current_user_id
                          else "incoming" if pair and pair.addressee_id == current_user_id else None),
            "friendship_id": pair.id if pair else None,
        })
    return jsonify(results), 200


# =========================================================
# PROFILE
# =========================================================
def _user_stats(user_id):
    """Helper para calcular las stats de actividad de un usuario."""
    events_created_count = Event.query.filter(Event.creator_id == user_id).count()
    all_events = Event.query.all()
    participated = [e for e in all_events if user_id in [p.id for p in e.participants]]
    events_participated_count = len(participated)

    today = datetime.utcnow().date()
    window_start = today - timedelta(weeks=4)
    recent_count = 0
    for e in participated:
        try:
            event_date = datetime.strptime(e.date, "%Y-%m-%d").date()
            if window_start <= event_date <= today:
                recent_count += 1
        except (ValueError, TypeError):
            continue

    activity_avg_per_week = round(recent_count / 4.0, 2)
    if activity_avg_per_week < 2:
        activity_level = "Peu actif"
    elif activity_avg_per_week < 3:
        activity_level = "Actif"
    else:
        activity_level = "Très actif"
    activity_percent = min(100, int((activity_avg_per_week / 5.0) * 100))

    return {
        "events_created_count":      events_created_count,
        "events_participated_count": events_participated_count,
        "activity_avg_per_week":     activity_avg_per_week,
        "activity_level":            activity_level,
        "activity_percent":          activity_percent,
    }


@api.route('/profile/me', methods=['GET'])
@jwt_required()
def get_my_profile():
    current_user_id = int(get_jwt_identity())
    user = db.session.get(User, current_user_id)
    if not user:
        return jsonify({"msg": "User not found"}), 404
    data = user.serialize()
    data["stats"] = _user_stats(current_user_id)
    return jsonify(data), 200


@api.route('/profile/me', methods=['PUT'])
@jwt_required()
def update_my_profile():
    current_user_id = int(get_jwt_identity())
    user = db.session.get(User, current_user_id)
    if not user:
        return jsonify({"msg": "User not found"}), 404
    body = request.get_json() or {}

    editable = ["username", "first_name", "last_name", "city", "bio",
                "profile_picture_url", "birthdate", "phone"]

    new_username = body.get("username")
    if new_username and new_username != user.username:
        clash = User.query.filter(User.username == new_username, User.id != current_user_id).first()
        if clash:
            return jsonify({"msg": "Username already taken"}), 409

    for field in editable:
        if field in body:
            value = body[field]
            setattr(user, field, value if value not in ("", None) else None)

    db.session.commit()
    return jsonify({"msg": "Profile updated", "user": user.serialize()}), 200


@api.route('/profile/<int:user_id>', methods=['GET'])
@jwt_required()
def get_user_profile(user_id):
    current_user_id = int(get_jwt_identity())
    user = db.session.get(User, user_id)
    if not user:
        return jsonify({"msg": "User not found"}), 404

    friendship = None
    if user_id != current_user_id:
        friendship = Friendship.query.filter(
            ((Friendship.requester_id == current_user_id) & (Friendship.addressee_id == user_id)) |
            ((Friendship.requester_id == user_id) & (Friendship.addressee_id == current_user_id))
        ).first()

    is_self = (user_id == current_user_id)
    is_friend = friendship is not None and friendship.status == "accepted"

    data = {
        "id":                  user.id,
        "username":            user.username,
        "first_name":          user.first_name,
        "last_name":           user.last_name,
        "city":                user.city,
        "bio":                 user.bio,
        "profile_picture_url": user.profile_picture_url,
        "created_at":          user.created_at.isoformat() if user.created_at else None,
    }
    if is_self or is_friend:
        data["email"]     = user.email
        data["phone"]     = user.phone
        data["birthdate"] = user.birthdate

    if is_self:
        data["friendship_status"] = "self"
        data["friendship_direction"] = None
        data["friendship_id"] = None
    elif friendship:
        data["friendship_status"] = friendship.status
        data["friendship_direction"] = "outgoing" if friendship.requester_id == current_user_id else "incoming"
        data["friendship_id"] = friendship.id
    else:
        data["friendship_status"] = "none"
        data["friendship_direction"] = None
        data["friendship_id"] = None

    data["stats"] = _user_stats(user_id)
    return jsonify(data), 200


# =========================================================
# CONVERSATIONS
# =========================================================
@api.route('/conversations', methods=['GET'])
@jwt_required()
def list_conversations():
    uid = int(get_jwt_identity())
    convs = Conversation.query.filter(
        (Conversation.user1_id == uid) | (Conversation.user2_id == uid)
    ).all()
    convs.sort(key=lambda c: c.messages[-1].created_at if c.messages else c.created_at, reverse=True)
    return jsonify([c.serialize(current_user_id=uid) for c in convs]), 200


@api.route('/conversations', methods=['POST'])
@jwt_required()
def create_conversation():
    """Body: { event_id, other_user_id }"""
    uid = int(get_jwt_identity())
    body = request.get_json() or {}
    event_id = body.get("event_id")
    other_id = body.get("other_user_id")
    if not event_id or not other_id:
        return jsonify({"msg": "event_id and other_user_id are required"}), 400
    try:
        conv = _get_or_create_conversation(event_id, uid, int(other_id))
    except ValueError as e:
        return jsonify({"msg": str(e)}), 400
    db.session.commit()
    return jsonify(conv.serialize(current_user_id=uid)), 200


# =========================================================
# MESSAGES
# =========================================================
@api.route('/conversations/<int:conv_id>/messages', methods=['GET'])
@jwt_required()
def get_messages(conv_id):
    uid = int(get_jwt_identity())
    conv = db.session.get(Conversation, conv_id)
    if not conv:
        return jsonify({"msg": "Conversation not found"}), 404
    if not conv.has_participant(uid):
        return jsonify({"msg": "You don't have access to this conversation"}), 403
    return jsonify([m.serialize() for m in conv.messages]), 200


@api.route('/conversations/<int:conv_id>/messages', methods=['POST'])
@jwt_required()
def send_message(conv_id):
    uid = int(get_jwt_identity())
    conv = db.session.get(Conversation, conv_id)
    if not conv:
        return jsonify({"msg": "Conversation not found"}), 404
    if not conv.has_participant(uid):
        return jsonify({"msg": "You don't have access to this conversation"}), 403

    content = (request.get_json() or {}).get("content", "").strip()
    if not content:
        return jsonify({"msg": "Message content cannot be empty"}), 400
    if len(content) > 2000:
        return jsonify({"msg": "Message too long (max 2000 chars)"}), 400

    msg = Message(conversation_id=conv.id, sender_id=uid, content=content)
    db.session.add(msg)

    sender = db.session.get(User, uid)
    sender_label = sender.username or sender.email
    _notify(
        user_id=conv.other_user_id(uid),
        ntype=NotificationType.NEW_MESSAGE,
        message=f"Nuevo mensaje de {sender_label}",
        related_id=conv.id,
    )
    db.session.commit()
    return jsonify(msg.serialize()), 201


@api.route('/conversations/<int:conv_id>/read', methods=['POST'])
@jwt_required()
def mark_conversation_read(conv_id):
    uid = int(get_jwt_identity())
    conv = db.session.get(Conversation, conv_id)
    if not conv:
        return jsonify({"msg": "Conversation not found"}), 404
    if not conv.has_participant(uid):
        return jsonify({"msg": "You don't have access to this conversation"}), 403

    Message.query.filter(
        Message.conversation_id == conv.id,
        Message.sender_id != uid,
        Message.is_read.is_(False),
    ).update({"is_read": True})
    db.session.commit()
    return jsonify({"msg": "ok"}), 200


# =========================================================
# NOTIFICATIONS
# =========================================================
@api.route('/notifications', methods=['GET'])
@jwt_required()
def list_notifications():
    uid = int(get_jwt_identity())
    notifs = (Notification.query.filter_by(user_id=uid)
              .order_by(Notification.created_at.desc()).limit(50).all())
    return jsonify([n.serialize() for n in notifs]), 200


@api.route('/notifications/unread-count', methods=['GET'])
@jwt_required()
def unread_count():
    """Endpoint ligero para el polling del badge."""
    uid = int(get_jwt_identity())
    count = Notification.query.filter_by(user_id=uid, is_read=False).count()
    return jsonify({"count": count}), 200


@api.route('/notifications/<int:nid>/read', methods=['POST'])
@jwt_required()
def mark_notification_read(nid):
    uid = int(get_jwt_identity())
    n = db.session.get(Notification, nid)
    if not n:
        return jsonify({"msg": "Notification not found"}), 404
    if n.user_id != uid:
        return jsonify({"msg": "Not authorized"}), 403
    n.is_read = True
    db.session.commit()
    return jsonify(n.serialize()), 200


@api.route('/notifications/read-all', methods=['POST'])
@jwt_required()
def mark_all_notifications_read():
    uid = int(get_jwt_identity())
    Notification.query.filter_by(user_id=uid, is_read=False).update({"is_read": True})
    db.session.commit()
    return jsonify({"msg": "ok"}), 200