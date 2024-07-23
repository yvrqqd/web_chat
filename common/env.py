import os
from typing import Any
from pathlib import Path
from dotenv import load_dotenv



def get_init_data() -> dict[str, Any]:
    dotenv_path = Path(__file__).resolve().parent.parent / '.env' # .env file should be specified in parent dir
    if os.path.exists(dotenv_path):
        load_dotenv(dotenv_path)

    host: str = os.getenv('HOST', 'localhost')
    port: int = os.getenv('PORT', 8888)
    return {'host':host, 'port':port}
