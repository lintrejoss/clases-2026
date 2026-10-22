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
    res_login_reader = client.post("/api/auth/login", data={"username": "usuario_lector", "password": "lector123"})
    assert res_login_reader.status_code == 200, f"Fallo login usuario_lector: {res_login_reader.text}"
    token_reader = res_login_reader.json()["access_token"]
    print("✓ 1. Login exitoso usuario_lector (rol reader)")

    # 2. Login con usuario editor (editor)
    res_login_editor = client.post("/api/auth/login", data={"username": "usuario_editor", "password": "editor123"})
    assert res_login_editor.status_code == 200, f"Fallo login usuario_editor: {res_login_editor.text}"
    token_editor = res_login_editor.json()["access_token"]
    print("✓ 2. Login exitoso usuario_editor (rol editor)")

    # 3. Verificar /api/me para ambos
    me_reader = client.get("/api/me", headers={"Authorization": f"Bearer {token_reader}"})
    assert me_reader.status_code == 200 and me_reader.json()["role"] == "reader"
    print("✓ 3. Endpoint /api/me responde correctamente para usuario_lector (role: reader)")

    me_editor = client.get("/api/me", headers={"Authorization": f"Bearer {token_editor}"})
    assert me_editor.status_code == 200 and me_editor.json()["role"] == "editor"
    print("✓ 4. Endpoint /api/me responde correctamente para usuario_editor (role: editor)")

    # 4. Probar lectura (scope 'read') con ambos usuarios
    items_reader = client.get("/api/items", headers={"Authorization": f"Bearer {token_reader}"})
    assert items_reader.status_code == 200
    print("✓ 5. usuario_lector puede consultar items (GET /api/items)")

    items_editor = client.get("/api/items", headers={"Authorization": f"Bearer {token_editor}"})
    assert items_editor.status_code == 200
    print("✓ 6. usuario_editor puede consultar items (GET /api/items)")

    # 5. Probar que usuario_lector NO puede crear items (scope 'write' requerido)
    intento_crear = client.post(
        "/api/items",
        json={"name": "Intento de item", "description": "Debería fallar"},
        headers={"Authorization": f"Bearer {token_reader}"}
    )
    assert intento_crear.status_code == 401, f"El lector no debería poder crear items: {intento_crear.status_code}"
    print("✓ 7. Control de acceso: usuario_lector BLOQUEADO al intentar crear items (scope write ausente)")

    # 6. Probar que usuario_editor SÍ puede crear items
    crear_ok = client.post(
        "/api/items",
        json={"name": "Nuevo Sensor Pro", "description": "Creado por el editor"},
        headers={"Authorization": f"Bearer {token_editor}"}
    )
    assert crear_ok.status_code == 201
    item_id = crear_ok.json()["id"]
    print("✓ 8. Control de acceso: usuario_editor AUTORIZADO para crear items (scope write presente)")

    # 7. Probar que usuario_editor puede editar y eliminar
    editar_ok = client.put(
        f"/api/items/{item_id}",
        json={"name": "Sensor Pro Actualizado", "description": "Modificado por editor"},
        headers={"Authorization": f"Bearer {token_editor}"}
    )
    assert editar_ok.status_code == 200
    print("✓ 9. usuario_editor modifica item exitosamente")

    eliminar_ok = client.delete(
        f"/api/items/{item_id}",
        headers={"Authorization": f"Bearer {token_editor}"}
    )
    assert eliminar_ok.status_code == 204
    print("✓ 10. usuario_editor elimina item exitosamente")

    print("\n--> TODAS LAS PRUEBAS DE AMBOS USUARIOS Y ROLES PASARON SATISFACTORIAMENTE <--\n")


if __name__ == "__main__":
    test_flujo_completo_dos_usuarios()
