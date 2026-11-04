"""Servidor de teste local: contas fictícias em banco temporário, nunca no banco real."""

import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app import create_app
from app.models.database import get_db
from werkzeug.security import generate_password_hash

if __name__ == "__main__":
    with tempfile.TemporaryDirectory() as directory:
        app = create_app(
            {
                "DATABASE": str(Path(directory) / "browser.db"),
                "SECRET_KEY": "browser-test-only-key-01234567890123456789",
                "SESSION_COOKIE_SECURE": False,
            }
        )
        with app.app_context():
            db = get_db()
            hashed = generate_password_hash("TesteSeguro123!")
            db.execute(
                "INSERT INTO clientes (nome,email,senha) VALUES (?,?,?)",
                ("Cliente Teste", "browser@teste.com", hashed),
            )
            db.execute(
                "INSERT INTO clientes (nome,email,senha) VALUES (?,?,?)",
                ("Cliente Outro", "outro@teste.com", hashed),
            )
            db.executemany(
                "INSERT INTO funcionarios (nome,cpf,email,senha,cargo,perfil) VALUES (?,?,?,?,?,?)",
                [
                    (
                        "Admin Teste",
                        "11111111111",
                        "admin.browser@teste.com",
                        hashed,
                        "Administrador",
                        "administrador",
                    ),
                    (
                        "Cozinheiro Teste",
                        "22222222222",
                        "cozinha.browser@teste.com",
                        hashed,
                        "Cozinheiro",
                        "cozinheiro",
                    ),
                ],
            )
            db.execute("UPDATE clientes SET endereco='Rua do Teste, 123'")
            db.execute("UPDATE funcionarios SET turno='Noite',especialidade='Massas'")
            db.execute(
                "INSERT INTO bancadas(nome,localizacao) VALUES ('Bancada Teste','Centro')"
            )
            db.commit()
        app.run(host="127.0.0.1", port=5001, debug=False, use_reloader=False)
