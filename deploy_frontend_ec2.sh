#!/usr/bin/env bash
# ==============================================================================
# Script de Despliegue para la 2.ª Instancia: EC2 - FRONTEND (Evaluación N.º 4)
# Separa físicamente la capa de presentación (Frontend) de la EC2 Backend (DRF).
# Uso en la instancia EC2 Frontend:
#   curl -sSL https://raw.githubusercontent.com/Eduarts-00/eva4_backend_petcare/main/deploy_frontend_ec2.sh | sudo bash -s -- https://petcaree.duckdns.org
# ==============================================================================
set -e

BACKEND_OR_APIGW_URL="${1:-https://petcaree.duckdns.org}"
BACKEND_OR_APIGW_URL="${BACKEND_OR_APIGW_URL%/}"

echo "=================================================================="
echo "  CONFIGURANDO INSTANCIA EC2 - FRONTEND DESACOPLADA (PETCARE EVA 4)"
echo "  Conectada a API Backend / API Gateway: $BACKEND_OR_APIGW_URL"
echo "=================================================================="

apt-get update -y -q
DEBIAN_FRONTEND=noninteractive apt-get install -y -q nginx git curl

FRONTEND_DIR="/var/www/petcare_frontend"
mkdir -p "$FRONTEND_DIR"

curl -sSL https://raw.githubusercontent.com/Eduarts-00/eva4_backend_petcare/main/templates/index.html -o "$FRONTEND_DIR/index.html"

cat >/etc/nginx/sites-available/petcare_frontend <<EOF
server {
    listen 80 default_server;
    listen [::]:80 default_server;
    server_name _;

    root /var/www/petcare_frontend;
    index index.html;

    # Cabeceras de seguridad DAST (OWASP ZAP) en EC2 Frontend
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-Frame-Options "DENY" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;

    location / {
        try_files \$uri /index.html;
    }
}
EOF

rm -f /etc/nginx/sites-enabled/default
ln -sf /etc/nginx/sites-available/petcare_frontend /etc/nginx/sites-enabled/petcare_frontend
nginx -t
systemctl enable nginx
systemctl restart nginx

echo "=================================================================="
echo "  ✅ EC2 FRONTEND LISTA Y CONECTADA A: $BACKEND_OR_APIGW_URL"
echo "=================================================================="
