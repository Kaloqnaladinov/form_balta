from pathlib import Path
BASE_DIR = Path(__file__).resolve().parent
DATABASE = BASE_DIR / "forn_balta.db"
SECRET_KEY = "CHANGE_THIS_IN_PRODUCTION"
ADMIN_EMAIL = "admin@fornbalta.cat"
DEFAULT_ADMIN_PASSWORD = "123456"
SITE = {"name":"Forn Baltà","phone":"+34 933 39 54 85","address":"Carrer de Sants, 119, Baixos, 08028 Barcelona"}
