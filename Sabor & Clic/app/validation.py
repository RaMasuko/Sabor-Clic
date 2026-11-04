"""Validação de dados sem interpolação em SQL ou HTML."""

import re
from decimal import Decimal, InvalidOperation

from flask import abort, request


def json_object():
    if not request.is_json:
        abort(415)
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        abort(400, description="Envie um objeto JSON válido.")
    return data


def texto(value, field, minimum=1, maximum=100):
    if not isinstance(value, str):
        raise ValueError(f"{field}: informe um texto válido.")
    value = value.strip()
    if not minimum <= len(value) <= maximum or any(
        ord(c) < 32 and c not in "\n\r\t" for c in value
    ):
        raise ValueError(f"{field}: use entre {minimum} e {maximum} caracteres.")
    return value


def email_valido(value):
    value = texto(value, "E-mail", 3, 120).lower()
    if not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", value):
        raise ValueError("Informe um e-mail válido.")
    return value


def senha_valida(value):
    if not isinstance(value, str) or not 12 <= len(value) <= 128:
        raise ValueError("A senha deve ter entre 12 e 128 caracteres.")
    return value


def preco_valido(value):
    if isinstance(value, bool) or not isinstance(value, (int, float, str)):
        raise ValueError("Informe um preço válido.")
    try:
        amount = Decimal(str(value))
        if not amount.is_finite() or amount <= 0 or amount > Decimal("1000000"):
            raise ValueError("O preço deve ser positivo e de até R$ 1.000.000,00.")
        if amount != amount.quantize(Decimal("0.01")):
            raise ValueError("O preço deve ter no máximo duas casas decimais.")
    except InvalidOperation as exc:
        raise ValueError("Informe um preço válido.") from exc
    return amount.quantize(Decimal("0.01"))


def inteiro(value, field, minimum=1, maximum=2147483647):
    if type(value) is not int or not minimum <= value <= maximum:
        raise ValueError(f"{field}: informe um inteiro entre {minimum} e {maximum}.")
    return value
