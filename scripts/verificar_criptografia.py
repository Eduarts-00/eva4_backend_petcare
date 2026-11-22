"""
Actividad 3 (Evaluación N.º 4): Demostración práctica de Protección de Contraseñas
y Criptografía en Django (PBKDF2-HMAC-SHA256, Salt único e iteraciones).

Ejecutar con:
  python scripts/verificar_criptografia.py
"""
import os
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'petcare_config.settings')

import django  # noqa: E402
django.setup()

from django.conf import settings  # noqa: E402
from django.contrib.auth.hashers import make_password, check_password, identify_hasher  # noqa: E402
from users.models import CustomUser  # noqa: E402


def demostrar_hashing():
    print("=" * 90)
    print("  ACTIVIDAD 3 — EVIDENCIA PRÁCTICA DE PROTECCIÓN DE CONTRASEÑAS Y CRIPTOGRAFÍA (DJANGO)")
    print("=" * 90)
    print("\n1. Hashers configurados en petcare_config/settings.py (PASSWORD_HASHERS):")
    for idx, h in enumerate(settings.PASSWORD_HASHERS, start=1):
        print(f"   [{idx}] {h}")

    clave_prueba = "PetCareClinica2026!"
    hash_1 = make_password(clave_prueba)
    hash_2 = make_password(clave_prueba)

    partes_1 = hash_1.split('$')
    partes_2 = hash_2.split('$')
    hasher_obj = identify_hasher(hash_1)

    print(f"\n2. Generación de Hash con Salt aleatorio para la contraseña '{clave_prueba}':")
    print(f"   - Clase Hasher Django : {hasher_obj.__class__.__name__}")
    print(f"   - Formato Estructural : <algoritmo>$<iteraciones>$<salt>$<digest_base64>")
    print(f"   - Ejecución #1        : {hash_1}")
    print(f"     * Algoritmo         : {partes_1[0]}")
    print(f"     * Iteraciones       : {partes_1[1]}")
    print(f"     * Salt único #1     : {partes_1[2]}")
    print(f"     * Digest Base64 #1  : {partes_1[3]}")
    print(f"   - Ejecución #2        : {hash_2}")
    print(f"     * Salt único #2     : {partes_2[2]}")
    print(f"     * Digest Base64 #2  : {partes_2[3]}")
    print(f"   - ¿Hashes idénticos?  : {hash_1 == hash_2} (Falso gracias al Salt único por ejecución)")
    print(f"   - check_password #1   : {check_password(clave_prueba, hash_1)}")
    print(f"   - check_password #2   : {check_password(clave_prueba, hash_2)}")

    print("\n3. Verificación en Base de Datos PostgreSQL (tabla users_customuser):")
    try:
        usuarios = CustomUser.objects.all()[:4]
        for u in usuarios:
            p = u.password.split('$')
            alg = p[0] if len(p) > 0 else 'N/A'
            it = p[1] if len(p) > 1 else 'N/A'
            salt = p[2] if len(p) > 2 else 'N/A'
            print(f"   - Usuario @{u.username:<14} | Rol: {u.rol:<11} | Alg: {alg} | Iter: {it} | Salt: {salt[:10]}... | Hash: {u.password[:48]}...")
    except Exception as exc:
        print(f"   (Aviso: base de datos local no inicializada aún: {exc})")

    print("=" * 90)


if __name__ == '__main__':
    demostrar_hashing()
