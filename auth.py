from flask import session, redirect, url_for
from functools import wraps

# Dicionário com os usuários da equipe de TI
USUARIOS = {
    "ti1": {"senha": "ti123", "nome": "Christian Lucas"},
    "ti2": {"senha": "ti123", "nome": "Edson Farias"},
    "ti3": {"senha": "ti123", "nome": "Lucas Gabriel"},
    "ti4": {"senha": "ti123", "nome": "Brenan Araújo"},
    "ti5": {"senha": "ti123", "nome": "Técnico 5"},
    "ti6": {"senha": "ti123", "nome": "Técnico 6"}
}

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('logado'):
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def verificar_credenciais(usuario, senha):
    if usuario in USUARIOS and USUARIOS[usuario]["senha"] == senha:
        return True, USUARIOS[usuario]["nome"]
    return False, None 