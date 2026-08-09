import os

from dotenv import load_dotenv

load_dotenv()

max_requests = 1000
max_requests_jitter = 50
log_file = "-"
# Railway/Render inyectan PORT; localmente/Docker usamos 50505 por defecto
bind = f"0.0.0.0:{os.environ.get('PORT', '50505')}"

# Limitado a un valor fijo y bajo (en vez de cpu_count()*2+1) para no
# quedarse sin memoria en planes gratuitos como el free tier de Render.
workers = int(os.environ.get("WEB_CONCURRENCY", 2))
threads = 4
timeout = 600