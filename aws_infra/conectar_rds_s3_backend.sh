#!/usr/bin/env bash
# ==============================================================================
# Script para conectar la EC2 Backend (98.85.49.169) con la instancia separada
# de Amazon RDS PostgreSQL, el bucket de Amazon S3 y la URL de Amazon API Gateway.
#
# Uso en la EC2 Backend:
#   sudo bash aws_infra/conectar_rds_s3_backend.sh <RDS_ENDPOINT> <DB_USER> <DB_PASSWORD> <S3_BUCKET> <API_GATEWAY_URL>
# ==============================================================================
set -e

RDS_HOST="${1:-localhost}"
RDS_USER="${2:-postgres}"
RDS_PASS="${3:-inacap.2030}"
S3_BUCKET="${4:-petcare-eva4-static-media-2026}"
APIGW_URL="${5:-https://petcaree.duckdns.org}"

echo "=================================================================="
echo "  VINCULANDO EC2 BACKEND CON AMAZON RDS, S3 Y API GATEWAY"
echo "=================================================================="
echo "  - RDS Endpoint   : $RDS_HOST:5432 (TLS sslmode=require)"
echo "  - S3 Bucket      : $S3_BUCKET (SSE-S3 AES256)"
echo "  - API Gateway URL: $APIGW_URL"

cat >/etc/systemd/system/gunicorn.service <<EOF
[Unit]
Description=Gunicorn daemon for PetCare Veterinary System (EVA 4 AWS)
After=network.target

[Service]
User=ubuntu
Group=www-data
WorkingDirectory=/home/ubuntu/apps
UMask=007
Environment="DJANGO_DEBUG=False"
Environment="EC2_PUBLIC_IP=98.85.49.169"
Environment="EC2_DOMAIN=petcaree.duckdns.org"
Environment="DB_NAME=petcare_db"
Environment="DB_USER=${RDS_USER}"
Environment="DB_PASSWORD=${RDS_PASS}"
Environment="DB_HOST=${RDS_HOST}"
Environment="DB_PORT=5432"
Environment="DB_SSLMODE=require"
Environment="AWS_STORAGE_BUCKET_NAME=${S3_BUCKET}"
Environment="API_GATEWAY_URL=${APIGW_URL}"
ExecStart=/home/ubuntu/apps/venv/bin/gunicorn --workers 3 --bind unix:/home/ubuntu/apps/petcare.sock petcare_config.wsgi:application
Restart=always

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl restart gunicorn

echo "[+] Ejecutando migraciones y carga inicial sobre RDS ($RDS_HOST)..."
export DB_NAME="petcare_db"
export DB_USER="$RDS_USER"
export DB_PASSWORD="$RDS_PASS"
export DB_HOST="$RDS_HOST"
export DB_PORT="5432"
export DB_SSLMODE="require"

cd /home/ubuntu/apps
/home/ubuntu/apps/venv/bin/python manage.py migrate --noinput
/home/ubuntu/apps/venv/bin/python poblar_datos.py

systemctl restart gunicorn
echo "=================================================================="
echo "  ✅ EC2 BACKEND CONECTADA EXITOSAMENTE A RDS, S3 Y API GATEWAY"
echo "=================================================================="
