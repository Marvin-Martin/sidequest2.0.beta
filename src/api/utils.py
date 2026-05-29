from flask import jsonify, url_for
from .models import db, Conversation, Notification, NotificationType


class APIException(Exception):
    status_code = 400

    def __init__(self, message, status_code=None, payload=None):
        Exception.__init__(self)
        self.message = message
        if status_code is not None:
            self.status_code = status_code
        self.payload = payload

    def to_dict(self):
        rv = dict(self.payload or ())
        rv['message'] = self.message
        return rv


def has_no_empty_params(rule):
    defaults = rule.defaults if rule.defaults is not None else ()
    arguments = rule.arguments if rule.arguments is not None else ()
    return len(defaults) >= len(arguments)


def generate_sitemap(app):
    links = ['/admin/']
    for rule in app.url_map.iter_rules():
        # Filter out rules we can't navigate to in a browser
        # and rules that require parameters
        if "GET" in rule.methods and has_no_empty_params(rule):
            url = url_for(rule.endpoint, **(rule.defaults or {}))
            if "/admin/" not in url:
                links.append(url)

    links_html = "".join(["<li><a href='" + y + "'>" + y + "</a></li>" for y in links])
    return """
        <div style="text-align: center;">
        <img style="max-height: 80px" src='https://storage.googleapis.com/breathecode/boilerplates/rigo-baby.jpeg' />
        <h1>Rigo welcomes you to your API!!</h1>
        <p>API HOST: <script>document.write('<input style="padding: 5px; width: 300px" type="text" value="'+window.location.href+'" />');</script></p>
        <p>Start working on your project by following the <a href="https://start.4geeksacademy.com/starters/full-stack" target="_blank">Quick Start</a></p>
        <p>Remember to specify a real endpoint path like: </p>
        <ul style="text-align: left;">""" + links_html + "</ul></div>"


# ============================================================
#  Helpers para Chat y Notificaciones
# ============================================================

def get_or_create_conversation(event_id: int, user_a_id: int, user_b_id: int) -> Conversation:
    """
    Devuelve la conversación entre dos usuarios para un evento.
    Si no existe, la crea. Normaliza el orden de los IDs para que
    la UniqueConstraint funcione (user1_id siempre menor que user2_id).
    """
    if user_a_id == user_b_id:
        raise ValueError("No puedes iniciar una conversación contigo mismo.")
    u1, u2 = sorted([user_a_id, user_b_id])

    conv = Conversation.query.filter_by(event_id=event_id, user1_id=u1, user2_id=u2).first()
    if conv:
        return conv

    conv = Conversation(event_id=event_id, user1_id=u1, user2_id=u2)
    db.session.add(conv)
    db.session.flush()  # para tener conv.id sin hacer commit todavía
    return conv


def notify(user_id: int, ntype: NotificationType, message: str, related_id: int | None = None) -> Notification:
    """
    Crea una notificación para un usuario.
    NO hace commit — el caller decide cuándo persistir
    (esto permite agrupar notificación + acción en una sola transacción).
    """
    n = Notification(user_id=user_id, type=ntype, message=message, related_id=related_id)
    db.session.add(n)
    return n