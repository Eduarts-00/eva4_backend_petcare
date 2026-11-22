"""
Actividad 4 (Evaluación N.º 4): Script de prueba de Rate Limiting / Throttling
para Amazon API Gateway y el endpoint protegido de PetCare.

Uso:
  python scripts/probar_rate_limit.py
  python scripts/probar_rate_limit.py https://<api-id>.execute-api.us-east-1.amazonaws.com/prod/api/aws/rate-limit-test/
"""
import sys
import time
import urllib.request
import urllib.error
import json


def ejecutar_rafaga(url_objetivo: str, total_solicitudes: int = 10):
    print("=" * 88)
    print("  PETCARE EVA 4 — PRUEBA DE RATE LIMITING / THROTTLING (API GATEWAY & DRF)")
    print("=" * 88)
    print(f"Endpoint evaluado : {url_objetivo}")
    print(f"Total solicitudes : {total_solicitudes} peticiones consecutivas en ráfaga")
    print("-" * 88)
    print(f"{'#':<4} | {'Código HTTP':<24} | {'Latencia':<10} | {'Detalle de Respuesta'}")
    print("-" * 88)

    conteo_200 = 0
    conteo_429 = 0

    for i in range(1, total_solicitudes + 1):
        t0 = time.perf_counter()
        req = urllib.request.Request(
            url_objetivo,
            headers={'Accept': 'application/json', 'User-Agent': 'PetCare-RateLimit-Tester/2.0'},
            method='GET',
        )
        try:
            with urllib.request.urlopen(req, timeout=8) as resp:
                ms = int((time.perf_counter() - t0) * 1000)
                status_code = resp.getcode()
                body = json.loads(resp.read().decode('utf-8'))
                detalle = body.get('estado') or body.get('mensaje') or 'Solicitud procesada (OK)'
                conteo_200 += 1
                print(f"{i:<4} | {f'{status_code} OK (Permitida)':<24} | {f'{ms} ms':<10} | {detalle[:45]}")
        except urllib.error.HTTPError as err:
            ms = int((time.perf_counter() - t0) * 1000)
            raw = err.read().decode('utf-8', errors='ignore')
            try:
                err_json = json.loads(raw)
                detalle = err_json.get('detail') or err_json.get('message') or raw
            except Exception:
                detalle = raw or str(err)
            if err.code == 429:
                conteo_429 += 1
                print(f"{i:<4} | {'429 Too Many Requests':<24} | {f'{ms} ms':<10} | BLOQUEADO POR THROTTLING: {detalle[:35]}")
            else:
                print(f"{i:<4} | {f'HTTP {err.code}':<24} | {f'{ms} ms':<10} | {detalle[:45]}")
        except Exception as exc:
            print(f"{i:<4} | {'ERROR CONEXIÓN':<24} | {'---':<10} | {exc}")

    print("-" * 88)
    print(f"RESUMEN: {conteo_200} solicitudes aceptadas (200 OK) | {conteo_429} solicitudes bloqueadas (429 Too Many Requests)")
    print("=" * 88)


if __name__ == '__main__':
    default_url = 'https://petcaree.duckdns.org/api/aws/rate-limit-test/'
    target = sys.argv[1] if len(sys.argv) > 1 else default_url
    ejecutar_rafaga(target, total_solicitudes=10)
