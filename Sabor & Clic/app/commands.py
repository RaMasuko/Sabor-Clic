import sqlite3

import click

from .accounts import criar_funcionario
from .models.database import get_db
from .models.errors import DomainError


def register_commands(app):
    @app.cli.command("criar-admin")
    @click.option("--nome", prompt="Nome completo")
    @click.option("--email", prompt="E-mail")
    @click.option("--cpf", prompt="CPF (11 dígitos)")
    @click.password_option(prompt="Senha (12 a 128 caracteres)")
    def criar_admin(nome, email, cpf, password):
        """Cria administrador localmente, sem cadastro público privilegiado."""
        try:
            criar_funcionario(nome, email, cpf, password, "administrador")
        except (ValueError, DomainError, sqlite3.IntegrityError) as error:
            get_db().rollback()
            message = (
                str(error)
                if isinstance(error, (ValueError, DomainError))
                else "CPF já cadastrado."
            )
            raise click.ClickException(message) from error
        click.echo("Administrador criado. Faça login com a senha escolhida.")

    @app.cli.command("ativar-funcionario")
    @click.option("--email", prompt="E-mail da conta revisada")
    @click.confirmation_option(
        prompt="Confirma que verificou a legitimidade desta conta de funcionário?"
    )
    def ativar_funcionario(email):
        """Reativa conta revisada; nunca altera seu perfil."""
        db = get_db()
        rows = db.execute(
            "SELECT id_funcionario FROM funcionarios WHERE email = ? COLLATE NOCASE",
            (email.strip(),),
        ).fetchall()
        if len(rows) != 1:
            raise click.ClickException("Conta não encontrada ou e-mail ambíguo.")
        db.execute(
            "UPDATE funcionarios SET status = 'ativo' WHERE id_funcionario = ?",
            (rows[0]["id_funcionario"],),
        )
        db.commit()
        click.echo("Conta ativada. O perfil de acesso foi mantido.")

    @app.cli.command("carregar-bancadas")
    def carregar_bancadas():
        """Carrega as duas bancadas de referência, sem criar credenciais."""
        from pathlib import Path

        path = Path(__file__).resolve().parents[1] / "sql" / "02_insercoes_basicas.sql"
        db = get_db()
        db.executescript(path.read_text(encoding="utf-8"))
        click.echo("Bancadas de referência carregadas. Nenhuma conta foi criada.")
