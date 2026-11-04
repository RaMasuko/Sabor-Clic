"""Validação compartilhada pelo cadastro administrativo e pelo terminal."""

import re

from werkzeug.security import generate_password_hash

from .models.usuario_model import UsuarioModel
from .validation import email_valido, senha_valida, texto


def email_em_uso(email):
    return UsuarioModel.email_em_uso(email)


def criar_funcionario(nome, email, cpf, senha, perfil, turno="", especialidade=""):
    nome = texto(nome, "Nome", 3, 100)
    email = email_valido(email)
    senha_valida(senha)
    cpf = re.sub(r"[.\-\s]", "", texto(cpf, "CPF", 11, 14))
    if not re.fullmatch(r"\d{11}", cpf):
        raise ValueError("Informe um CPF com 11 dígitos.")
    if perfil not in ("administrador", "cozinheiro"):
        raise ValueError("Perfil inválido.")
    turno = texto(turno, "Turno", 1 if perfil == "cozinheiro" else 0, 100)
    especialidade = texto(
        especialidade, "Especialidade", 1 if perfil == "cozinheiro" else 0, 100
    )
    UsuarioModel.criar_funcionario(
        {
            "nome": nome,
            "email": email,
            "cpf": cpf,
            "senha": generate_password_hash(senha),
            "perfil": perfil,
            "turno": turno,
            "especialidade": especialidade,
        }
    )
