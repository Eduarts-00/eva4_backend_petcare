#!/usr/bin/env bash
# ==============================================================================
# Script de Actualización y Despliegue Automatizado en AWS EC2 (Ubuntu 22.04/24.04)
# Proyecto: PetCare — Evaluación N.º 4 (Arquitectura AWS, Integración y Seguridad)
# Repositorio: https://github.com/Eduarts-00/eva4_backend_petcare.git
# Uso directo en la VM:
#   curl -sSL https://raw.githubusercontent.com/Eduarts-00/eva4_backend_petcare/main/deploy_aws.sh | sudo bash
# ==============================================================================
set -e

echo "=================================================================="
echo "  ACTUALIZANDO PETCARE A EVALUACIÓN N.º 4 (AWS, RDS, S3 & SEGURIDAD)"
echo "=================================================================="

# Detectar directorio existente de la EVA 3 o crear /var/www/petcare
APP_DIR=""
for candidate in "/home/ubuntu/eva3_petcare" "/home/ubuntu/petcare" "/var/www/petcare" "/var/www/eva3_petcare"; do
    if [ -d "$candidate" ] && [ -f "$candidate/manage.py" ]; then
        APP_DIR="$candidate"
        break
    fi
done

if [ -z "$APP_DIR" ]; then
    # Buscar manage.py de petcare en /home/ubuntu o /var/www
    FOUND_MANAGE=$(find /home/ubuntu /var/www -maxdepth 3 -name "manage.py" 2>/dev/null | head -n 1 || true)
    if [ -n "$FOUND_MANAGE" ]; then
        APP_DIR=$(dirname "$FOUND_MANAGE")
    else
        APP_DIR="/home/ubuntu/eva3_petcare"
    fi
fi

echo "[1/5] Directorio de la aplicación detectado: $APP_DIR"

if [ -d "$APP_DIR/.git" ]; then
    cd "$APP_DIR"
    git remote set-url origin https://github.com/Eduarts-00/eva4_backend_petcare.git
    git fetch --all
    git reset --hard origin/main
else
    rm -rf "$APP_DIR"
    git clone https://github.com/Eduarts-00/eva4_backend_petcare.git "$APP_DIR"
    cd "$APP_DIR"
fi

echo "[2/5] Instalando dependencias de Python (boto3, django-storages, simplejwt)..."
if [ -d "$APP_DIR/venv" ]; then
    VENV_DIR="$APP_DIR/venv"
elif [ -d "$APP_DIR/.venv" ]; then
    VENV_DIR="$APP_DIR/.venv"
else
    python3 -m venv "$APP_DIR/venv"
    VENV_DIR="$APP_DIR/venv"
fi

"$VENV_DIR/bin/pip" install --upgrade pip -q
"$VENV_DIR/bin/pip" install -r "$APP_DIR/requirements.txt" -q

echo "[3/5] Aplicando migraciones, recolectando estáticos y poblando datos..."
"$VENV_DIR/bin/python" "$APP_DIR/manage.py" makemigrations --noinput
"$VENV_DIR/bin/python" "$APP_DIR/manage.py" migrate --noinput
"$VENV_DIR/bin/python" "$APP_DIR/manage.py" collectstatic --noinput
"$VENV_DIR/bin/python" "$APP_DIR/poblar_datos.py"

echo "[4/5] Ajustando permisos y reiniciando servicios Gunicorn y Nginx..."
chown -R ubuntu:www-data "$APP_DIR" || true
chmod -R 755 "$APP_DIR" || true

systemctl daemon-reload || true
for svc in gunicorn petcare gunicorn-petcare; do
    if systemctl list-unit-files | grep -q "^${svc}\.service"; then
        systemctl restart "$svc"
        echo "  -> Servicio $svc reiniciado."
    fi
done
systemctl reload nginx || systemctl restart nginx || true

echo "[5/5] Ejecutando suite de pruebas automatizadas EVA 4..."
"$VENV_DIR/bin/python" "$APP_DIR/manage.py" test --verbosity=1

echo "=================================================================="
echo "  ✅ PETCARE EVA 4 DESPLEGADO Y VERIFICADO EXITOSAMENTE"
echo "=================================================================="
