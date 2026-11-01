#!/usr/bin/env python
"""
Utilidad de línea de comandos de Django para tareas administrativas de PetCare.
Alumno: Angel Eduardo Lara Manriquez
Docente: Marcelo Alvarado Aravena
Evaluación Parcial N°3 - Desarrollo Backend (2026)
"""
import os
import sys


def main():
    """Punto de entrada administrativo de Django."""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'petcare_config.settings')
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "No se pudo importar Django. Verifica que el entorno virtual esté activado."
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    main()
