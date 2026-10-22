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
        reader = db.query(User).filter(User.username == "Maku").first()
        if not reader:
            reader = User(
                username="Maku",
                hashed_password=hash_password("123"),
                role="reader",
            )
            db.add(reader)
            print("✓ Creado usuario: 'Maku' | Rol: reader | Clave: 123")
        else:
            print("• Usuario 'Maku' ya existía.")

        # 2. Usuario Editor (role: editor -> scopes: read, write)
        editor = db.query(User).filter(User.username == "Lin").first()
        if not editor:
            editor = User(
                username="Lin",
                hashed_password=hash_password("aguapanela"),
                role="editor",
            )
            db.add(editor)
            print("✓ Creado usuario: 'Lin' | Rol: editor | Clave: aguapanela")
        else:
            print("• Usuario 'Lin' ya existía.")

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
