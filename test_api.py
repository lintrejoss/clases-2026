"""
Suite de pruebas para validar autenticación, autorización y scopes con ambos usuarios (reader y editor).
Ejecutar con: python test_api.py  o  pytest test_api.py
"""

from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)


def test_flujo_completo_dos_usuarios():
    print("\n--- INICIO DE PRUEBAS CON AMBOS ROLES ---")

    # 1. Login con usuario lector (reader)
    res_login_reader = client.post("/api/auth/login", data={"username": "Maku", "password": "123"})
    assert res_login_reader.status_code == 200, f"Fallo login Maku: {res_login_reader.text}"
    token_reader = res_login_reader.json()["access_token"]
    print("✓ 1. Login exitoso Maku (rol reader)")

    # 2. Login con usuario editor (editor)
    res_login_editor = client.post("/api/auth/login", data={"username": "Lin", "password": "aguapanela"})
    assert res_login_editor.status_code == 200, f"Fallo login Lin: {res_login_editor.text}"
    token_editor = res_login_editor.json()["access_token"]
    print("✓ 2. Login exitoso Lin (rol editor)")

    # 3. Verificar /api/me para ambos
    me_reader = client.get("/api/me", headers={"Authorization": f"Bearer {token_reader}"})
    assert me_reader.status_code == 200 and me_reader.json()["username"] == "Maku" and me_reader.json()["role"] == "reader"
    print("✓ 3. Endpoint /api/me responde correctamente para Maku (role: reader)")

    me_editor = client.get("/api/me", headers={"Authorization": f"Bearer {token_editor}"})
    assert me_editor.status_code == 200 and me_editor.json()["username"] == "Lin" and me_editor.json()["role"] == "editor"
    print("✓ 4. Endpoint /api/me responde correctamente para Lin (role: editor)")

    # 4. Probar lectura (scope 'read') con ambos usuarios
    items_reader = client.get("/api/items", headers={"Authorization": f"Bearer {token_reader}"})
    assert items_reader.status_code == 200
    print("✓ 5. Maku puede consultar items (GET /api/items)")

    items_editor = client.get("/api/items", headers={"Authorization": f"Bearer {token_editor}"})
    assert items_editor.status_code == 200
    print("✓ 6. Lin puede consultar items (GET /api/items)")

    # 5. Probar que Maku NO puede crear items (scope 'write' requerido)
    intento_crear = client.post(
        "/api/items",
        json={"name": "Intento de item", "description": "Debería fallar"},
        headers={"Authorization": f"Bearer {token_reader}"}
    )
    assert intento_crear.status_code == 401, f"El lector no debería poder crear items: {intento_crear.status_code}"
    print("✓ 7. Control de acceso: Maku BLOQUEADO al intentar crear items (scope write ausente)")

    # 6. Probar que Lin SÍ puede crear items
    crear_ok = client.post(
        "/api/items",
        json={"name": "Nuevo Sensor Pro", "description": "Creado por el editor Lin"},
        headers={"Authorization": f"Bearer {token_editor}"}
    )
    assert crear_ok.status_code == 201
    item_id = crear_ok.json()["id"]
    print("✓ 8. Control de acceso: Lin AUTORIZADO para crear items (scope write presente)")

    # 7. Probar que Lin puede editar y eliminar
    editar_ok = client.put(
        f"/api/items/{item_id}",
        json={"name": "Sensor Pro Actualizado", "description": "Modificado por Lin"},
        headers={"Authorization": f"Bearer {token_editor}"}
    )
    assert editar_ok.status_code == 200
    print("✓ 9. Lin modifica item exitosamente")

    eliminar_ok = client.delete(
        f"/api/items/{item_id}",
        headers={"Authorization": f"Bearer {token_editor}"}
    )
    assert eliminar_ok.status_code == 204
    print("✓ 10. Lin elimina item exitosamente")

    print("\n--> TODAS LAS PRUEBAS DE AMBOS USUARIOS Y ROLES PASARON SATISFACTORIAMENTE <--\n")


if __name__ == "__main__":
    test_flujo_completo_dos_usuarios()
