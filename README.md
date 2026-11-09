# 🔐 Autenticación MFA con Pyro4, Telegram y SQLite

Proyecto de **Sistemas Distribuidos** que implementa un sistema de inicio de sesión con **autenticación de dos factores (MFA)**. El servidor y el cliente se comunican mediante objetos remotos con **Pyro4**, las credenciales se guardan en **SQLite** y el código de verificación de **6 dígitos** se envía al usuario a través de un **bot de Telegram**.

---

## 📋 Funcionamiento

```
┌──────────┐   Pyro4 (RMI)   ┌──────────────┐   HTTP API   ┌──────────────┐
│ Cliente  │ ──────────────► │   Servidor   │ ───────────► │ Bot Telegram │
│          │ ◄────────────── │  + SQLite    │              │  (usuario)   │
└──────────┘                 └──────────────┘              └──────────────┘
```

1. El usuario se **registra** desde el cliente con usuario, contraseña y su `chat_id` de Telegram.
2. Al **iniciar sesión**, el servidor valida usuario y contraseña en la base de datos.
3. Si son correctos, el servidor genera un **código aleatorio de 6 dígitos** y lo envía por Telegram.
4. El usuario escribe el código en el cliente y, si coincide, **accede al sistema**.

## 🛡️ Seguridad

- Las contraseñas se guardan con hash **PBKDF2-SHA256** y sal aleatoria (nunca en texto plano).
- El código MFA se genera con el módulo `secrets` (aleatorio criptográficamente seguro).
- El código **vence a los 5 minutos**, permite **máximo 3 intentos** y es de **un solo uso**.
- El token del bot se lee desde una **variable de entorno**, no está escrito en el código.

---

## 📁 Estructura del proyecto

```
Pyro4_Telegram/
├── servidor.py          # Servidor Pyro4: registro, login, envío y verificación del código
├── cliente.py           # Cliente con menú en consola
├── obtener_chat_id.py   # Script para obtener el chat_id de Telegram
├── requirements.txt     # Dependencias
└── README.md
```

La base de datos `credenciales.db` se crea automáticamente al ejecutar el servidor.

---

## ⚙️ Requisitos

- Python 3.8 o superior
- Una cuenta de Telegram
- Librerías: `Pyro4` y `requests`

---

## 🚀 Instalación y uso

### 1. Clonar el repositorio

```bash
git clone https://github.com/TU_USUARIO/Pyro4_Telegram.git
cd Pyro4_Telegram
```

### 2. Crear el entorno virtual e instalar dependencias

**Windows (PowerShell):**
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

**Linux:**
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 3. Crear el bot de Telegram

1. En Telegram, busca **@BotFather** y envíale `/newbot`.
2. Escribe un nombre y un username que termine en `bot`.
3. Copia el **token** que te entrega BotFather.
4. Busca tu bot, ábrelo y envíale `/start`.

### 4. Configurar el token

Solo es necesario en la máquina donde se ejecuta el **servidor**.

**Windows (PowerShell):**
```powershell
$env:TELEGRAM_TOKEN="TU_TOKEN_AQUI"
```
Para dejarlo guardado de forma permanente: `setx TELEGRAM_TOKEN "TU_TOKEN_AQUI"` (y reiniciar la terminal).

**Linux:**
```bash
export TELEGRAM_TOKEN="TU_TOKEN_AQUI"
```

### 5. Obtener tu chat_id

Después de enviarle `/start` a tu bot:

```bash
python obtener_chat_id.py
```

Mostrará algo como `usuario -> chat_id: 987654321`. Guarda ese número para registrarte.

### 6. Ejecutar el servidor

```bash
python servidor.py
```

### 7. Ejecutar el cliente

En otra terminal (o en otra máquina):

```bash
python cliente.py
```

```
1) Registrarse
2) Iniciar sesión
3) Salir
```

---

## 🌐 Ejecutar el cliente en otra máquina

1. En la máquina del servidor, obtén su IP con `ipconfig` (Windows) o `ip a` (Linux).
2. En `servidor.py`, el daemon debe escuchar en todas las interfaces:
   ```python
   daemon = Pyro4.Daemon(host="0.0.0.0", port=9090)
   ```
3. En `cliente.py`, coloca la IP del servidor:
   ```python
   URI = "PYRO:servidor.auth@192.168.1.25:9090"
   ```
4. Permite el puerto **9090** en el firewall del servidor (Windows, PowerShell como administrador):
   ```powershell
   New-NetFirewallRule -DisplayName "Pyro4 9090" -Direction Inbound -Protocol TCP -LocalPort 9090 -Action Allow
   ```
5. Comprueba la conexión desde el cliente:
   ```powershell
   Test-NetConnection 192.168.1.25 -Port 9090
   ```

Ambas máquinas deben estar en la misma red. La máquina del cliente solo necesita `cliente.py` y `pip install Pyro4`.

---

## 🗄️ Base de datos

Tabla `usuarios`:

| Campo   | Descripción                         |
|---------|-------------------------------------|
| usuario | Nombre de usuario (clave primaria)  |
| hash    | Hash PBKDF2 de la contraseña        |
| sal     | Sal aleatoria usada en el hash      |
| chat_id | ID del chat de Telegram del usuario |

Tabla `codigos_mfa`:

| Campo    | Descripción                          |
|----------|--------------------------------------|
| usuario  | Usuario al que pertenece el código   |
| codigo   | Código de 6 dígitos                  |
| expira   | Momento en que vence el código       |
| intentos | Intentos fallidos realizados         |

---

## 🧩 Métodos remotos del servidor

| Método                                  | Descripción                                      |
|-----------------------------------------|--------------------------------------------------|
| `registrar(usuario, password, chat_id)` | Crea el usuario y envía un mensaje de bienvenida |
| `iniciar_sesion(usuario, password)`     | Valida credenciales y envía el código MFA        |
| `verificar_codigo(usuario, codigo)`     | Comprueba el código y permite el acceso          |

---

## ❗ Solución de problemas

| Problema | Solución |
|----------|----------|
| `KeyError: 'TELEGRAM_TOKEN'` | No se configuró el token en esa terminal (ver paso 4). En Windows se usa `$env:`, no `export`. |
| `chat_id inválido o no le has enviado /start al bot` | Envía `/start` a tu bot y verifica el chat_id. |
| `obtener_chat_id.py` no muestra nada | Vuelve a enviar `/start` al bot y ejecuta el script de nuevo. |
| El cliente no conecta desde otra máquina | Revisa la IP, que el servidor esté corriendo, el firewall y que estén en la misma red. |

```
.venv/
__pycache__/
credenciales.db
.env
```

---

## 👤 Autores

**Alejandro Ojeda**
**Adrian Barriga**
Sistemas Distribuidos, 6.º semestre
