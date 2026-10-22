"""
Script para poblar la base de datos con los usuarios de prueba requeridos para la Clase 7/8.
Crea un usuario con rol 'reader' y otro con rol 'editor'.
"""

from backend.auth import hash_password
from backend.database import Base, SessionLocal, engine
from backend.models import Item, User


def seed_database():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        # 1. Usuario Lector (role: reader -> scopes: read)
        reader = db.query(User).filter(User.username == "usuario_lector").first()
        if not reader:
            reader = User(
                username="usuario_lector",
                hashed_password=hash_password("lector123"),
                role="reader",
            )
            db.add(reader)
            print("✓ Creado usuario: 'usuario_lector' | Rol: reader | Clave: lector123")
        else:
            print("• Usuario 'usuario_lector' ya existía.")

        # 2. Usuario Editor (role: editor -> scopes: read, write)
        editor = db.query(User).filter(User.username == "usuario_editor").first()
        if not editor:
            editor = User(
                username="usuario_editor",
                hashed_password=hash_password("editor123"),
                role="editor",
            )
            db.add(editor)
            print("✓ Creado usuario: 'usuario_editor' | Rol: editor | Clave: editor123")
        else:
            print("• Usuario 'usuario_editor' ya existía.")

        # 3. Item inicial de prueba
        if db.query(Item).count() == 0:
            item = Item(
                name="Sensor Ambiental AQ-004",
                description="Dispositivo IoT para monitoreo de calidad del aire",
            )
            db.add(item)
            print("✓ Creado item inicial de prueba.")

        db.commit()
        print("\n--> Base de datos inicializada con éxito para pruebas.")
    finally:
        db.close()


if __name__ == "__main__":
    seed_database()
