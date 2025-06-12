import os
import logging
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import httpx
import json # Added import for json.load in validate_with_schema

try:
    import requests_cache
except ImportError:
    requests_cache = None

try:
    import jsonschema
    from jsonschema import ValidationError
except ImportError:
    jsonschema = None
    ValidationError = None # Or some base exception

# Load environment variables from .env (ensure .env is loaded by the main script)
# No direct call to load_dotenv() here, assumes caller handles it.

# --- Configuration Defaults ---
API_BASE = os.getenv('FEDREG_API_BASE', 'https://www.federalregister.gov/api/v1')
DEFAULT_DATA_DIR = os.getenv('FEDREG_DATA_DIR', './data')
DEFAULT_TIMEOUT = 10  # seconds

# --- Retry Settings ---
RETRIES = 3
BACKOFF_FACTOR = 0.3
STATUS_FORCELIST = (500, 502, 504, 429) # Added 429 for rate limiting

# --- Logging ---
# Basic logger setup, can be configured by the calling script
logger = logging.getLogger(__name__)

# --- Functions ---

def get_api_key(cli_api_key: str = None, env_var_name: str = 'FEDREG_API_KEY') -> str | None:
    """
    Retrieve API key from CLI argument or environment variable.
    Returns None if no key is found.
    """
    if cli_api_key:
        return cli_api_key
    return os.getenv(env_var_name)

def create_sync_session(use_cache: bool = True) -> requests.Session:
    """
    Create a requests.Session with retry logic and optional caching.
    Caching uses requests_cache with SQLite backend if available.
    """
    if use_cache and requests_cache:
        session = requests_cache.CachedSession(
            cache_name='fr_cache',  # Name of the cache file/db
            backend='sqlite',       # Use SQLite backend
            expire_after=3600,      # Cache expires after 1 hour
            allowable_methods=['GET'] # Cache only GET requests
        )
        logger.info("Using requests_cache for synchronous HTTP caching.")
    else:
        session = requests.Session()
        if use_cache and not requests_cache:
            logger.warning("requests_cache not installed; caching for sync requests is disabled.")

    retry_strategy = Retry(
        total=RETRIES,
        read=RETRIES,
        connect=RETRIES,
        backoff_factor=BACKOFF_FACTOR,
        status_forcelist=STATUS_FORCELIST,
        allowed_methods=['GET', 'POST'] # Adjusted to also allow POST for other potential uses
    )
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("https://", adapter)
    session.mount("http://", adapter)

    logger.info(f"Created synchronous session with retries (total={RETRIES}) for statuses {STATUS_FORCELIST}.")
    return session

def create_async_client() -> httpx.AsyncClient:
    """
    Create an httpx.AsyncClient with default timeout.
    Retry logic for httpx is typically handled per-request or via HTTPTransport.
    This provides a basic client; specific retry mechanisms can be added if needed around its usage.
    """
    # httpx supports Limits, Timeouts, and Transports for more complex retry/config
    # For now, just a basic client. Retries are handled in the calling code for async.
    logger.info(f"Created asynchronous httpx client with default timeout {DEFAULT_TIMEOUT}s.")
    return httpx.AsyncClient(timeout=DEFAULT_TIMEOUT)

def validate_schema(instance: dict, schema_path: str) -> bool: # Renamed function
    """
    Validates a JSON instance against a schema file.
    Returns True if valid or if jsonschema is not available/schema_path is None.
    Logs an error and returns False on validation failure.
    """
    if not schema_path or not jsonschema or not ValidationError:
        if schema_path and (not jsonschema or not ValidationError):
            logger.warning("JSON schema validation requested but 'jsonschema' library not installed.")
        return True # Skip validation if not configured or library missing

    try:
        with open(schema_path, 'r', encoding='utf-8') as f:
            schema = json.load(f)
        jsonschema.validate(instance=instance, schema=schema)
        logger.info(f"Instance successfully validated against schema: {schema_path}")
        return True
    except FileNotFoundError:
        logger.error(f"Schema file not found: {schema_path}")
        return False
    except json.JSONDecodeError as e:
        logger.error(f"Error decoding schema file {schema_path}: {e}")
        return False
    except ValidationError as e: # jsonschema.exceptions.ValidationError
        logger.error(f"Schema validation error against {schema_path}: {e.message}")
        return False
    except Exception as e: # Catch any other jsonschema related errors
        logger.error(f"An unexpected error occurred during schema validation with {schema_path}: {e}")
        return False
