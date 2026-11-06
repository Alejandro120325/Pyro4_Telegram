import getpass
import Pyro4

# La URI ahora se arma automáticamente apuntando a la IP externa
URI = "PYRO:servidor.auth@172.17.44.90:9090"

def main():
    servidor = Pyro4.Proxy(URI)
    while True:
        print("\n1) Registrarse\n2) Iniciar sesión\n3) Salir")
        op = input("Opción: ").strip()

        if op == "1":
            usuario = input("Usuario: ").strip()
            password = getpass.getpass("Contraseña: ")
            chat_id = input("Tu chat_id de Telegram: ").strip()
            print(servidor.registrar(usuario, password, chat_id)["msg"])

        elif op == "2":
            usuario = input("Usuario: ").strip()
            password = getpass.getpass("Contraseña: ")
            r = servidor.iniciar_sesion(usuario, password)
            print(r["msg"])
            if r["ok"]:
                while True:
                    r = servidor.verificar_codigo(usuario, input("Código de 6 dígitos: "))
                    print(r["msg"])
                    if not r["reintentar"]:
                        break

        elif op == "3":
            break


if __name__ == "__main__":
    main()