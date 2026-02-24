"""Генерация самоподписанных OPC UA клиентских сертификатов."""

from __future__ import annotations

import logging
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path

from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import NameOID

logger = logging.getLogger("opc-collector")

CERTS_BASE_DIR = Path(os.environ.get("OPC_CERTS_DIR", "/app/certificates"))


def get_cert_paths(station_code: str) -> tuple[Path, Path]:
    """Возвращает (cert_path, key_path) для станции."""
    station_dir = CERTS_BASE_DIR / station_code
    return station_dir / "client_cert.der", station_dir / "client_key.pem"


def certs_exist(station_code: str) -> bool:
    cert_path, key_path = get_cert_paths(station_code)
    return cert_path.exists() and key_path.exists()


def generate_certs(
    station_code: str,
    station_name: str = "OPC UA Client",
    validity_days: int = 3650,
) -> tuple[str, str]:
    """
    Генерация самоподписанного сертификата и ключа для OPC UA клиента.

    Возвращает (cert_path, key_path) — абсолютные пути к файлам.

    Процесс для Kepware:
    1. Этот метод создаёт client_cert.der + client_key.pem
    2. Файл client_cert.der нужно скопировать на машину с Kepware
    3. В Kepware Administration → OPC UA → Trusted Clients → добавить этот .der
    4. После этого наш коллектор сможет подключиться с шифрованием
    """
    cert_path, key_path = get_cert_paths(station_code)
    station_dir = cert_path.parent
    station_dir.mkdir(parents=True, exist_ok=True)

    # RSA 2048
    key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
    )

    subject = issuer = x509.Name([
        x509.NameAttribute(NameOID.COUNTRY_NAME, "UZ"),
        x509.NameAttribute(NameOID.ORGANIZATION_NAME, "UTG"),
        x509.NameAttribute(NameOID.COMMON_NAME, f"OPC UA Client - {station_name}"),
    ])

    now = datetime.now(timezone.utc)
    cert = (
        x509.CertificateBuilder()
        .subject_name(subject)
        .issuer_name(issuer)
        .public_key(key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(now)
        .not_valid_after(now + timedelta(days=validity_days))
        .add_extension(
            x509.SubjectAlternativeName([
                x509.UniformResourceIdentifier(f"urn:utg:opcua:{station_code}"),
            ]),
            critical=False,
        )
        .add_extension(
            x509.BasicConstraints(ca=False, path_length=None),
            critical=True,
        )
        .add_extension(
            x509.KeyUsage(
                digital_signature=True,
                key_encipherment=True,
                content_commitment=True,
                data_encipherment=True,
                key_agreement=False,
                key_cert_sign=False,
                crl_sign=False,
                encipher_only=False,
                decipher_only=False,
            ),
            critical=True,
        )
        .add_extension(
            x509.ExtendedKeyUsage([
                x509.oid.ExtendedKeyUsageOID.CLIENT_AUTH,
            ]),
            critical=False,
        )
        .sign(key, hashes.SHA256())
    )

    # DER сертификат (для Kepware)
    with open(cert_path, "wb") as f:
        f.write(cert.public_bytes(serialization.Encoding.DER))

    # PEM ключ (для нашего клиента)
    with open(key_path, "wb") as f:
        f.write(key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.TraditionalOpenSSL,
            encryption_algorithm=serialization.NoEncryption(),
        ))

    logger.info("Certificates generated for station '%s': %s", station_code, station_dir)
    return str(cert_path), str(key_path)
