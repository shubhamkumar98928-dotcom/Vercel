# ------------------------------------------------------------
# Number & Aadhaar Info API - Shubham Hacker Edition
# Fast Response · Cache · As-It-Is Output
# ------------------------------------------------------------

from flask import Flask, request, jsonify, Response
import requests
import json
import time
import hashlib
from threading import Lock

app = Flask(__name__)
app.config['JSON_AS_ASCII'] = False

# ============================================================
# CONFIG
# ============================================================
BACKEND_URL = "https://nexxonexploitsvip.vercel.app/search"

CACHE_TTL = 300
_cache = {}
_cache_lock = Lock()

MAX_RETRIES = 2
RETRY_DELAY = 0.5
TIMEOUT = 30

# Custom branding
CUSTOM_API_INFO = {
    "developed_by": "Creator Shubhambaudhist - CEO & Founder Of - Shubham Hacker",
    "organization": "Shubham_baudh",
    "purpose": "For Educational Purposes Only"
}


# ============================================================
# CACHE
# ============================================================
def cache_get(key):
    with _cache_lock:
        if key in _cache:
            data, expires = _cache[key]
            if time.time() < expires:
                return data
            del _cache[key]
    return None


def cache_set(key, value):
    with _cache_lock:
        if len(_cache) > 2000:
            now = time.time()
            expired = [k for k, (_, exp) in _cache.items() if exp < now]
            for k in expired:
                del _cache[k]
        _cache[key] = (value, time.time() + CACHE_TTL)


def make_cache_key(query):
    return hashlib.md5(f"search:{query}".encode()).hexdigest()


# ============================================================
# BACKEND CALL
# ============================================================
def call_backend(query):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "en-US,en;q=0.9",
        "Connection": "keep-alive"
    }

    last_error = None

    for attempt in range(MAX_RETRIES):
        try:
            resp = requests.get(
                BACKEND_URL,
                params={"q": query},
                headers=headers,
                timeout=TIMEOUT
            )

            if resp.status_code == 200:
                data = resp.json()
                if isinstance(data, dict):
                    return {"success": True, "data": data}

            last_error = f"HTTP {resp.status_code}"

        except requests.exceptions.Timeout:
            last_error = "Timeout"
        except requests.exceptions.ConnectionError:
            last_error = "Connection error"
        except Exception as e:
            last_error = str(e)

        if attempt < MAX_RETRIES - 1:
            time.sleep(RETRY_DELAY)

    return {"success": False, "error": last_error}


# ============================================================
# ROUTES
# ============================================================
@app.route("/", methods=["GET"])
def home():
    return jsonify({
        "api": "Number Info Api",
        "version": "3.0.0",
        "endpoint": "/search?q=YOUR_INPUT",
        "examples": [
            "/search?q=8800952843",
            "/search?q=1234567890"
        ],
        "status": "active",
        "api_info": CUSTOM_API_INFO
    })


@app.route("/search", methods=["GET"])
def search():
    query = request.args.get("q", "").strip()

    if not query:
        return jsonify({
            "status": "error",
            "message": "Missing 'q' parameter",
            "example": "/search?q=8800952843"
        }), 400

    if not query.isdigit():
        return jsonify({
            "status": "error",
            "message": "Invalid format. Must be numeric."
        }), 400

    if len(query) not in [10, 12]:
        return jsonify({
            "status": "error",
            "message": "Invalid length. Must be 10 digits."
        }), 400

    # Cache hit
    cache_key = make_cache_key(query)
    cached = cache_get(cache_key)
    if cached:
        return Response(
            json.dumps(cached, ensure_ascii=False, indent=2),
            mimetype='application/json',
            status=200
        )

    # Backend call
    result = call_backend(query)

    if not result["success"]:
        return jsonify({
            "status": "error",
            "message": f"Backend unavailable: {result.get('error', 'Unknown')}",
            "retry_hint": "Try again in a few seconds"
        }), 503

    # Pass through as-is
    data = result["data"]

    # Override api_info with custom branding
    data["api_info"] = CUSTOM_API_INFO

    # Cache customized response
    cache_set(cache_key, data.copy())

    return Response(
        json.dumps(data, ensure_ascii=False, indent=2),
        mimetype='application/json',
        status=200
    )


@app.errorhandler(404)
def not_found(e):
    return jsonify({
        "status": "error",
        "message": "Endpoint not found",
        "available": ["/", "/search"],
        "example": "/search?q=8918487393"
    }), 404


# ============================================================
# VERCEL HANDLER
# ============================================================
handler = app


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)