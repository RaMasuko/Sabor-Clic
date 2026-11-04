import sqlite3

import pytest
from app import create_app
from app.models.database import get_db


def test_migracao_preserva_funcionario_e_nao_promove_admin(tmp_path):
    path = tmp_path / "legado.db"
    db = sqlite3.connect(path)
    db.execute(
        """CREATE TABLE funcionarios (id_funcionario INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT NOT NULL, cpf TEXT UNIQUE NOT NULL, email TEXT UNIQUE NOT NULL,
        senha TEXT NOT NULL, telefone TEXT, cargo TEXT NOT NULL, salario MONEY)"""
    )
    db.execute(
        "INSERT INTO funcionarios (nome,cpf,email,senha,cargo) VALUES ('Existente','12345678900','existente@teste.com','hash-legado','Cozinheiro')"
    )
    db.commit()
    db.close()
    config = {
        "DATABASE": str(path),
        "SECRET_KEY": "migration-test-key-with-32-characters-minimum",
        "TESTING": True,
    }
    for _ in range(2):
        application = create_app(config)
        with application.app_context():
            row = get_db().execute("SELECT * FROM funcionarios").fetchone()
            assert (row["nome"], row["senha"], row["perfil"], row["status"]) == (
                "Existente",
                "hash-legado",
                "cozinheiro",
                "inativo",
            )
            assert (
                get_db().execute("SELECT count(*) FROM funcionarios").fetchone()[0] == 1
            )


def test_producao_exige_chave_do_ambiente(monkeypatch):
    monkeypatch.setenv("SABOR_ENV", "production")
    monkeypatch.delenv("SABOR_SECRET_KEY", raising=False)
    with pytest.raises(RuntimeError, match="SABOR_SECRET_KEY"):
        create_app()


def test_producao_exige_https_e_cookie_secure(monkeypatch, tmp_path):
    monkeypatch.setenv("SABOR_ENV", "production")
    monkeypatch.setenv(
        "SABOR_SECRET_KEY", "production-fixture-only-01234567890123456789"
    )
    application = create_app({"TESTING": True, "DATABASE": str(tmp_path / "prod.db")})
    client = application.test_client()
    assert client.get("/login").status_code == 400
    response = application.test_client().get("/login", base_url="https://localhost")
    assert response.status_code == 200
    assert "Secure" in response.headers["Set-Cookie"]
    assert response.headers["Strict-Transport-Security"] == "max-age=31536000"
