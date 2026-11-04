import re
import sys
from pathlib import Path

import pytest
from werkzeug.security import generate_password_hash

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


@pytest.fixture
def app(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    from app import create_app

    application = create_app(
        {
            "TESTING": True,
            "SECRET_KEY": "test-only-random-key-not-for-production-123456",
            "DATABASE": str(tmp_path / "teste.db"),
            "SESSION_COOKIE_SECURE": False,
        }
    )
    with application.app_context():
        from app.models.database import get_db

        db = get_db()
        password = generate_password_hash("TesteSeguro123!")
        db.executemany(
            "INSERT INTO clientes (nome,email,senha,status) VALUES (?,?,?,?)",
            [
                ("Cliente Um", "um@teste.com", password, "ativo"),
                ("Cliente Dois", "dois@teste.com", password, "ativo"),
                ("Cliente Inativo", "inativo@teste.com", password, "inativo"),
            ],
        )
        db.executemany(
            "INSERT INTO funcionarios (nome,cpf,email,senha,cargo) VALUES (?,?,?,?,?)",
            [
                ("Admin", "11111111111", "admin@teste.com", password, "Administrador"),
                (
                    "Cozinheiro",
                    "22222222222",
                    "cozinha@teste.com",
                    password,
                    "Cozinheiro",
                ),
            ],
        )
        columns = {r["name"] for r in db.execute("PRAGMA table_info(funcionarios)")}
        if "perfil" in columns:
            db.execute(
                "UPDATE funcionarios SET perfil='administrador' WHERE email='admin@teste.com'"
            )
        db.executemany(
            "INSERT INTO pratos (nome,descricao,preco,status) VALUES (?,?,?,?)",
            [
                ("Prato A", "Teste", 25.50, "disponivel"),
                ("Prato B", "Teste", 10.25, "indisponivel"),
            ],
        )
        db.execute("UPDATE clientes SET endereco='Rua de Teste, 123'")
        db.execute("UPDATE funcionarios SET turno='Noite',especialidade='Massas'")
        db.execute("UPDATE pratos SET estoque=100")
        db.execute(
            "INSERT INTO bancadas (nome,localizacao) VALUES ('Bancada de Teste','Centro')"
        )
        db.commit()
    yield application


@pytest.fixture
def client(app):
    return app.test_client()


def csrf(client, path="/login"):
    response = client.get(path)
    match = re.search(
        r'name="csrf-token" content="([^"]+)"', response.get_data(as_text=True)
    )
    return match.group(1) if match else ""


def login(client, email="um@teste.com"):
    return client.post(
        "/login",
        data={"email": email, "senha": "TesteSeguro123!", "csrf_token": csrf(client)},
    )


def post_json(client, path, data, method="POST"):
    return client.open(
        path, method=method, json=data, headers={"X-CSRFToken": csrf(client, "/")}
    )
