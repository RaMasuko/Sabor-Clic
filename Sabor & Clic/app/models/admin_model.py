"""Cria a conta de demonstração para execução local."""

from flask import current_app

from .database import get_db


class AdminModel:
    EMAIL = "admin@saborclic.local"
    CPF = "00000000001"
    SENHA_HASH = "scrypt:32768:8:1$ee04184cec46f249$86b4d3e0bf28f6641d71c03ca490b7c45677449f4928d5a9a7490a06dfe37a15cf40fe2393105265397d231461ac133f31352ac213f6aa00db5098860d3c8489"

    @classmethod
    def garantir_demo(cls):
        if current_app.testing or current_app.config["PRODUCTION"]:
            return
        if not current_app.config["ADMIN_DEMO"]:
            return

        db = get_db()
        with db:
            db.execute("BEGIN IMMEDIATE")
            db.execute(
                """INSERT INTO funcionarios (nome, cpf, email, senha, cargo, perfil, status)
                   SELECT ?, ?, ?, ?, 'Administrador', 'administrador', 'ativo'
                   WHERE NOT EXISTS (
                       SELECT 1 FROM funcionarios WHERE email = ? COLLATE NOCASE OR cpf = ?
                   ) AND NOT EXISTS (
                       SELECT 1 FROM clientes WHERE email = ? COLLATE NOCASE
                   )""",
                ("Administrador de Demonstração", cls.CPF, cls.EMAIL, cls.SENHA_HASH,
                 cls.EMAIL, cls.CPF, cls.EMAIL),
            )
