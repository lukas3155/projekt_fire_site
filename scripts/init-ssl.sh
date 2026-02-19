#!/bin/bash
# First-time SSL certificate setup with Let's Encrypt
# Run this ONCE on the server after DNS is configured
set -e

DOMAIN="projektfire.pl"
EMAIL="kontakt@projektfire.pl"

echo "=== Obtaining SSL certificate for $DOMAIN ==="

# Temporarily start nginx with HTTP only (for ACME challenge)
docker compose -f docker-compose.prod.yml up -d nginx

# Get certificate
docker compose -f docker-compose.prod.yml run --rm certbot certonly \
    --webroot \
    --webroot-path=/var/www/certbot \
    -d "$DOMAIN" \
    -d "www.$DOMAIN" \
    --email "$EMAIL" \
    --agree-tos \
    --no-eff-email

# Restart nginx with SSL
docker compose -f docker-compose.prod.yml restart nginx

echo "=== SSL certificate obtained! ==="
echo "Auto-renewal is handled by the certbot container."
