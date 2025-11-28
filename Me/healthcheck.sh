#!/usr/bin/env bash
#
# healthcheck.sh
# Quick health report for:
# Cloudflare Tunnel → nginx → Daphne → Django
#

set -u

# ===== Colors =====
RED="$(tput setaf 1)"
GREEN="$(tput setaf 2)"
YELLOW="$(tput setaf 3)"
BLUE="$(tput setaf 4)"
RESET="$(tput sgr0)"

ok()    { echo "  ${GREEN}✔${RESET} $*"; }
warn()  { echo "  ${YELLOW}⚠${RESET} $*"; }
fail()  { echo "  ${RED}✘${RESET} $*"; }
info()  { echo "  ${BLUE}ℹ${RESET} $*"; }

DOMAIN="williamspalding.com"
LAN_IP="192.168.1.119"
TUNNEL_NAME="my-website-tunnel"   # change if your tunnel has a different name

LINE="------------------------------------------------------------"

echo "$LINE"
echo " Healthcheck for ${DOMAIN}"
echo "$LINE"
echo

# ===== 1. Cloudflared (Tunnel) =====
echo "${BLUE}1) Cloudflared (Tunnel)${RESET}"

if systemctl is-active --quiet cloudflared; then
    ok "cloudflared service is active"
else
    fail "cloudflared service is NOT active"
fi

LAST_CLOUDFLARED_LOG=$(journalctl -u cloudflared -n 5 --no-pager 2>/dev/null)
if [[ -n "$LAST_CLOUDFLARED_LOG" ]]; then
    info "Last cloudflared log lines:"
    echo "$LAST_CLOUDFLARED_LOG" | sed 's/^/    /'
else
    warn "No cloudflared logs found"
fi

if command -v cloudflared >/dev/null 2>&1; then
    info "Configured tunnel list:"
    cloudflared tunnel list | sed 's/^/    /'
else
    warn "cloudflared CLI not found"
fi

echo

# ===== 2. nginx =====
echo "${BLUE}2) nginx${RESET}"

if systemctl is-active --quiet nginx; then
    ok "nginx service is active"
else
    fail "nginx service is NOT active"
fi

if nginx -t >/dev/null 2>&1; then
    ok "nginx config test (nginx -t) passed"
else
    fail "nginx config test FAILED (run: sudo nginx -t)"
fi

echo

# ===== 3. Daphne (ASGI) =====
echo "${BLUE}3) Daphne (ASGI)${RESET}"

if systemctl is-active --quiet daphne; then
    ok "daphne service is active"
else
    fail "daphne service is NOT active"
fi

# Test Daphne directly
DAPHNE_HTTP=$(curl -sS -o /dev/null -w "%{http_code}" http://127.0.0.1:8001/ || echo "ERR")
if [[ "$DAPHNE_HTTP" == "200" ]]; then
    ok "Daphne responds on http://127.0.0.1:8001/ (HTTP 200)"
else
    warn "Daphne did NOT return HTTP 200 on 127.0.0.1:8001 (got: $DAPHNE_HTTP)"
fi

echo

# ===== 4. nginx origin tests =====
echo "${BLUE}4) nginx origin (local)${RESET}"

HTTP_LOCAL=$(curl -sS -o /dev/null -w "%{http_code}" http://127.0.0.1/ -H "Host: ${DOMAIN}" || echo "ERR")
if [[ "$HTTP_LOCAL" == "200" ]]; then
    ok "nginx responds on http://127.0.0.1/ with Host: ${DOMAIN} (HTTP 200)"
else
    warn "nginx did NOT return HTTP 200 for Host: ${DOMAIN} on 127.0.0.1 (got: $HTTP_LOCAL)"
fi

HTTP_LAN=$(curl -sS -o /dev/null -w "%{http_code}" http://"${LAN_IP}"/ || echo "ERR")
if [[ "$HTTP_LAN" == "200" ]]; then
    ok "nginx responds on http://${LAN_IP}/ (HTTP 200)"
else
    warn "nginx did NOT return HTTP 200 on http://${LAN_IP}/ (got: $HTTP_LAN)"
fi

echo

# ===== 5. Full public path via Cloudflare =====
echo "${BLUE}5) Public HTTPS via Cloudflare${RESET}"

HTTPS_PUBLIC=$(curl -sS -o /dev/null -w "%{http_code}" https://"${DOMAIN}"/ || echo "ERR")
if [[ "$HTTPS_PUBLIC" == "200" ]]; then
    ok "Public HTTPS https://${DOMAIN}/ is returning HTTP 200"
else
    warn "Public HTTPS https://${DOMAIN}/ did NOT return HTTP 200 (got: $HTTPS_PUBLIC)"
fi

echo

# ===== 6. DNS Checks =====
echo "${BLUE}6) DNS Resolution${RESET}"

if command -v dig >/dev/null 2>&1; then
    info "dig ${DOMAIN} +short:"
    dig "${DOMAIN}" +short | sed 's/^/    /'
    info "dig www.${DOMAIN} +short:"
    dig "www.${DOMAIN}" +short | sed 's/^/    /'
else
    warn "dig not installed (install: sudo apt install dnsutils)"
fi

echo

# ===== 7. Django Deploy Check (optional, runs only if manage.py exists) =====
echo "${BLUE}7) Django deploy check (optional)${RESET}"

PROJECT_DIR="/home/f0rce0fwill/stuff/projects/PersonalWebsite/Me"

if [[ -f "${PROJECT_DIR}/manage.py" ]]; then
    info "Running: python manage.py check --deploy"
    (
      cd "${PROJECT_DIR}" || exit 1
      if command -v conda >/dev/null 2>&1; then
          # Try to activate env if available
          # Adjust env name if needed
          source "$(conda info --base 2>/dev/null)/etc/profile.d/conda.sh" 2>/dev/null || true
          conda activate personal_website_env 2>/dev/null || true
      fi
      python manage.py check --deploy
    )
else
    warn "manage.py not found at ${PROJECT_DIR} (skipping Django check)"
fi

echo
echo "$LINE"
echo " Healthcheck finished."
echo "$LINE"
