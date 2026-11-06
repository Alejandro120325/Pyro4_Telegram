import hashlib
import os
import secrets
import sqlite3
import time

import Pyro4
import requests

DB = "credenciales.db"
TOKEN = os.environ.get("TELEGRAM_TOKEN")
VIGENCIA = 300
MAX_INTENTOS = 3


def conectar():
    return sqlite3.connect(DB)


def crear_tablas():
    with conectar() as c:
        c.execute("""CREATE TABLE IF NOT EXISTS usuarios(
            usuario TEXT PRIMARY KEY,
            hash    TEXT NOT NULL,
            sal     TEXT NOT NULL,
            chat_id TEXT NOT NULL)""")
        c.execute("""CREATE TABLE IF NOT EXISTS codigos_mfa(
            usuario  TEXT PRIMARY KEY,
            codigo   TEXT NOT NULL,
            expira   REAL NOT NULL,
            intentos INTEGER NOT NULL DEFAULT 0)""")


def hashear(password, sal):
    # Nunca se guarda la contraseña en texto plano
    return hashlib.pbkdf2_hmac("sha256", password.encode(), bytes.fromhex(sal), 200_000).hex()


def enviar_telegram(chat_id, texto):
    try:
        r = requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage",
                          data={"chat_id": chat_id, "text": texto}, timeout=10)
        return r.ok
    except requests.RequestException:
        return False


@Pyro4.expose
@Pyro4.behavior(instance_mode="single")
class ServidorAuth:

    def registrar(self, usuario, password, chat_id):
        if not usuario or not password:
            return {"ok": False, "msg": "Usuario y contraseña son obligatorios"}
        sal = secrets.token_hex(16)
        try:
            with conectar() as c:
                c.execute("INSERT INTO usuarios VALUES (?,?,?,?)",
                          (usuario, hashear(password, sal), sal, str(chat_id)))
        except sqlite3.IntegrityError:
            return {"ok": False, "msg": "El usuario ya existe"}

        if not enviar_telegram(chat_id, f"Hola {usuario}, tu cuenta fue registrada ✅"):
            with conectar() as c:
                c.execute("DELETE FROM usuarios WHERE usuario=?", (usuario,))
            return {"ok": False, "msg": "chat_id inválido o no le has enviado /start al bot"}
        return {"ok": True, "msg": "Usuario registrado"}

    def iniciar_sesion(self, usuario, password):
        with conectar() as c:
            fila = c.execute("SELECT hash, sal, chat_id FROM usuarios WHERE usuario=?",
                             (usuario,)).fetchone()
        if not fila or not secrets.compare_digest(fila[0], hashear(password, fila[1])):
            return {"ok": False, "msg": "Usuario o contraseña incorrectos"}

        codigo = f"{secrets.randbelow(10**6):06d}"   # 6 dígitos aleatorios seguros
        with conectar() as c:
            c.execute("INSERT OR REPLACE INTO codigos_mfa VALUES (?,?,?,0)",
                      (usuario, codigo, time.time() + VIGENCIA))
        if not enviar_telegram(fila[2], f"🔐 Tu código de verificación es: {codigo}\nVence en 5 minutos."):
            return {"ok": False, "msg": "No se pudo enviar el código por Telegram"}
        return {"ok": True, "msg": "Código enviado a tu Telegram"}

    def verificar_codigo(self, usuario, codigo):
        with conectar() as c:
            fila = c.execute("SELECT codigo, expira, intentos FROM codigos_mfa WHERE usuario=?",
                             (usuario,)).fetchone()
            if not fila:
                return {"ok": False, "reintentar": False, "msg": "Primero inicia sesión"}
            guardado, expira, intentos = fila
            if time.time() > expira or intentos >= MAX_INTENTOS:
                c.execute("DELETE FROM codigos_mfa WHERE usuario=?", (usuario,))
                return {"ok": False, "reintentar": False,
                        "msg": "Código vencido o demasiados intentos. Inicia sesión de nuevo"}
            if secrets.compare_digest(guardado, str(codigo).strip()):
                c.execute("DELETE FROM codigos_mfa WHERE usuario=?", (usuario,))
                return {"ok": True, "reintentar": False, "msg": f"✅ Bienvenido, {usuario}"}
            c.execute("UPDATE codigos_mfa SET intentos = intentos + 1 WHERE usuario=?", (usuario,))
            return {"ok": False, "reintentar": True, "msg": "Código incorrecto"}


def main():
    if not TOKEN:
        raise SystemExit("Falta la variable TELEGRAM_TOKEN (export TELEGRAM_TOKEN=...)")
    crear_tablas()
    daemon = Pyro4.Daemon(host="localhost", port=9090)
    uri = daemon.register(ServidorAuth(), objectId="servidor.auth")
    print("Servidor listo en:", uri)
    daemon.requestLoop()


if __name__ == "__main__":
    main()
