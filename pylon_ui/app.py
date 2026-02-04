from flask import Flask, render_template, request, redirect, url_for, jsonify, session, flash
import json
import os
import time
import subprocess
import bcrypt
from functools import wraps
import socket
import tempfile
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'change-this-to-something-secret'

STATE_FILE = 'data/pylon_state.json'
USERS_FILE = 'data/users.json'
HISTORY_RETENTION_SECONDS = 15 * 60  # 15 minutes buffer

# ---- Pylon UI config used by nascar_ui.py (renderer) ----
UI_CONFIG_PATH = "/home/tonicinnovations/pylon_ui/pylon_config.json"
DEFAULT_UI_CONFIG = {
    "series": "XFINITY",         # CUP | XFINITY | TRUCKS | ARCA
    "display": "last_name",      # last_name | delta | both
    "favorite_driver": None,      # int or None
    "sync_delay": 0.0             # seconds (float)
}

DEFAULT_STATE = {
    "lapDelay": 0,
    "selectedSeries": "CUP",
    "displayMode": "lastName",
    "history": []
}

# ---------------- Helpers: UI Config (atomic) ----------------
def _ensure_parent(path: str):
    os.makedirs(os.path.dirname(path), exist_ok=True)

def atomic_save_json(path: str, data: dict, mode=0o664):
    """Write JSON atomically to avoid partial writes."""
    _ensure_parent(path)
    dir_ = os.path.dirname(path)
    fd, tmp = tempfile.mkstemp(prefix=".pylon_cfg_", dir=dir_)
    os.close(fd)
    try:
        with open(tmp, "w") as f:
            json.dump(data, f, indent=2)
            f.write("\n")
        os.replace(tmp, path)  # atomic on same filesystem
        try:
            os.chmod(path, mode)
        except Exception:
            pass
    finally:
        if os.path.exists(tmp):
            try:
                os.remove(tmp)
            except Exception:
                pass

def load_ui_config() -> dict:
    _ensure_parent(UI_CONFIG_PATH)
    try:
        with open(UI_CONFIG_PATH, "r") as f:
            cfg = json.load(f)
            # Fill any missing defaults (future-proof)
            merged = {**DEFAULT_UI_CONFIG, **cfg}
            # normalize types
            fav = merged.get("favorite_driver")
            if isinstance(fav, str) and fav.strip().isdigit():
                merged["favorite_driver"] = int(fav.strip())
            try:
                merged["sync_delay"] = float(merged.get("sync_delay", 0))
            except Exception:
                merged["sync_delay"] = 0.0
            return merged
    except Exception:
        # If missing or invalid, start with defaults and create the file
        atomic_save_json(UI_CONFIG_PATH, DEFAULT_UI_CONFIG)
        return DEFAULT_UI_CONFIG.copy()

def save_ui_config(new_values: dict):
    cfg = load_ui_config()
    # Only accept known keys
    for k in ("series", "display", "favorite_driver", "sync_delay", "show_deltas", "auto_restart"):
        if k in new_values and new_values[k] is not None:
            cfg[k] = new_values[k]
    atomic_save_json(UI_CONFIG_PATH, cfg)

# ---------------- Existing state helpers ----------------
def load_state():
    if not os.path.exists(STATE_FILE):
        return DEFAULT_STATE.copy()
    with open(STATE_FILE) as f:
        state = json.load(f)
    for k, v in DEFAULT_STATE.items():
        if k not in state:
            state[k] = v
    return state

def save_state(state):
    _ensure_parent(STATE_FILE)
    with open(STATE_FILE, 'w') as f:
        json.dump(state, f)

def prune_history(history):
    cutoff = time.time() - HISTORY_RETENTION_SECONDS
    return [entry for entry in history if entry['timestamp'] >= cutoff]

# ---------------- Auth helpers ----------------
def load_user():
    with open(USERS_FILE) as f:
        return json.load(f)

def check_login():
    return session.get('logged_in', False)

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not check_login():
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# ---------------- System helpers ----------------
def is_service_running(service: str = "pylon.service") -> bool:
    try:
        subprocess.check_call(["systemctl", "is-active", "--quiet", service])
        return True
    except subprocess.CalledProcessError:
        return False

def svc(cmd: str, service: str = "pylon.service") -> str:
    try:
        out = subprocess.check_output(["sudo", "systemctl", cmd, service], stderr=subprocess.STDOUT).decode()
        return out
    except subprocess.CalledProcessError as e:
        return e.output.decode()


def get_recent_logs(service: str = "pylon.service", lines: int = 200) -> str:
    try:
        out = subprocess.check_output(["journalctl", "-u", service, "-n", str(lines), "--no-pager"]).decode()
        return out
    except Exception as e:
        return f"(logs unavailable) {e}"

# ---------------- Auth ----------------
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password'].encode('utf-8')

        user = load_user()

        if username == user['username'] and bcrypt.checkpw(password, user['password_hash'].encode('utf-8')):
            session['logged_in'] = True
            return redirect(url_for('index'))
        else:
            flash('Invalid username or password', 'danger')
            return redirect(url_for('login'))

    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# ---------------- New Dashboard wired to the responsive template ----------------
@app.route('/')
@login_required
def index():
    state = load_state()
    history = prune_history(state.get('history', []))
    state['history'] = history
    save_state(state)

    # UI config read (this is what nascar-ui.py reads, too)
    ui_cfg = load_ui_config()

    # Build options for the template
    series_options = [
        {"label": "Cup",    "value": "CUP",     "icon": "bi-flag"},
        {"label": "Xfinity", "value": "XFINITY", "icon": "bi-flag-fill"},
        {"label": "Trucks",  "value": "TRUCKS",  "icon": "bi-truck"},
        {"label": "ARCA",    "value": "ARCA",    "icon": "bi-shield-check"},
    ]

    display_modes = [
        {"label": "Last Name", "value": "last",  "icon": "bi-person-badge"},
        {"label": "Delta",     "value": "delta", "icon": "bi-graph-up"},
        {"label": "Both",      "value": "both",  "icon": "bi-layers"},
    ]

    # Translate backend keys to UI-facing keys
    ui_display = {"last_name": "last", "delta": "delta", "both": "both"}.get(ui_cfg.get("display", "last_name"), "last")

    config = {
        "series": ui_cfg.get("series", "XFINITY"),
        "display_mode": ui_display,
        "favorite_driver": ui_cfg.get("favorite_driver"),
        "tv_sync_delay": ui_cfg.get("sync_delay", 0.0),
        "show_deltas": bool(ui_cfg.get("show_deltas", True)),
        "auto_restart": bool(ui_cfg.get("auto_restart", False)),
    }

    return render_template(
        'index.html',
        pylon_running=is_service_running(),
        config=config,
        series_options=series_options,
        display_modes=display_modes,
        logs=get_recent_logs(),
        hostname=socket.gethostname(),
        year=datetime.now().year,
    )

# ---------------- Buttons/Forms from the new template ----------------
@app.post('/save')
@login_required
def save():
    # Map UI form -> backend config keys used by renderer
    series = (request.form.get('series') or 'XFINITY').upper()

    ui_mode = request.form.get('display_mode') or 'last'
    display_map = {"last": "last_name", "delta": "delta", "both": "both"}
    display = display_map.get(ui_mode, "last_name")

    fav_raw = (request.form.get('favorite_driver') or '').strip()
    favorite_driver = int(fav_raw) if fav_raw.isdigit() else None

    try:
        sync_delay = float(request.form.get('tv_sync_delay', 0))
    except Exception:
        sync_delay = 0.0

    show_deltas = 'show_deltas' in request.form
    auto_restart = 'auto_restart' in request.form

    save_ui_config({
        "series": series,
        "display": display,
        "favorite_driver": favorite_driver,
        "sync_delay": sync_delay,
        "show_deltas": show_deltas,
        "auto_restart": auto_restart,
    })

    flash('Configuration saved', 'success')

    if auto_restart:
        svc('restart')
        flash('Pylon restarted', 'info')

    return redirect(url_for('index'))

@app.post('/start')
@login_required
def start():
    svc('start')
    flash('Pylon started', 'success')
    return redirect(url_for('index'))

@app.post('/stop')
@login_required
def stop():
    svc('stop')
    flash('Pylon stopped', 'warning')
    return redirect(url_for('index'))

@app.post('/restart')
@login_required
def restart():
    svc('restart')
    flash('Pylon restarted', 'info')
    return redirect(url_for('index'))

@app.post('/refresh')
@login_required
def refresh():
    flash('Refreshed', 'secondary')
    return redirect(url_for('index'))

@app.post('/logs/refresh')
@login_required
def logs_refresh():
    flash('Logs refreshed', 'secondary')
    return redirect(url_for('index'))

# ---------------- Legacy/aux routes kept for compatibility ----------------
@app.route('/adjust_delay', methods=['POST'])
@login_required
def adjust_delay():
    change = int(request.form.get('change'))
    state = load_state()
    state['lapDelay'] += change
    save_state(state)
    return redirect(url_for('index'))

@app.route('/apply_tv_correction', methods=['POST'])
@login_required
def apply_tv_correction():
    tv_lap = int(request.form.get('tv_lap'))
    now = time.time()

    state = load_state()
    history = prune_history(state.get('history', []))
    if not history:
        flash("No history available to correct against.")
        return redirect(url_for('index'))

    closest = min(history, key=lambda h: abs(h['timestamp'] - now))
    feed_lap_then = closest['lap']
    new_delay = tv_lap - feed_lap_then

    state['lapDelay'] = new_delay
    state['history'] = history
    save_state(state)

    return redirect(url_for('index'))

@app.route('/set_config', methods=['POST'])
@login_required
def set_config():
    # Backward-compatible: accepts old form names and maps to new config
    selectedSeries = (request.form.get('series', 'XFINITY') or 'XFINITY').upper()
    displayMode = request.form.get('display_mode', 'last')
    display_map = {"last": "last_name", "delta": "delta", "both": "both"}

    save_ui_config({
        "series": selectedSeries,
        "display": display_map.get(displayMode, 'last_name')
    })

    # Also mirror legacy state.json for any old templates that still reference it
    state = load_state()
    state['selectedSeries'] = selectedSeries
    state['displayMode'] = displayMode
    save_state(state)

    flash(f"Saved settings (series={selectedSeries}, display={displayMode}).", "success")
    return redirect(url_for('index'))

@app.route('/post_feed', methods=['POST'])
def post_feed():
    data = request.get_json()
    lap = int(data['lapNumber'])
    ts = time.time()

    state = load_state()
    history = state.get('history', [])
    history.append({"timestamp": ts, "lap": lap})
    history = prune_history(history)

    state['history'] = history
    save_state(state)
    return jsonify({"status": "ok"})

@app.route('/history')
@login_required
def view_history():
    state = load_state()
    history = prune_history(state.get('history', []))
    return render_template('history.html', history=history)

@app.route('/network', methods=['GET', 'POST'])
@login_required
def network():
    if request.method == 'POST':
        ssid = request.form.get('ssid')
        password = request.form.get('password')
        with open('/tmp/new_network_config.txt', 'w') as f:
            f.write(f'SSID={ssid}\n')
            f.write(f'PASSWORD={password}\n')
        subprocess.call(['sudo', '/usr/local/bin/apply_wifi_settings.sh', '/tmp/new_network_config.txt'])
        flash("Network settings applied. You may need to reconnect.")
        return redirect(url_for('network'))

    try:
        ip_address = subprocess.check_output(['hostname', '-I']).decode().strip()
    except:
        ip_address = "Unavailable"
    return render_template('network.html', ip_address=ip_address)

@app.route('/pylon_control', methods=['GET', 'POST'])
@login_required
def pylon_control():
    status = 'active' if is_service_running() else 'inactive'

    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'start':
            svc('start')
        elif action == 'stop':
            svc('stop')
        elif action == 'restart':
            svc('restart')
        return redirect(url_for('pylon_control'))

    return render_template('pylon_control.html', status=status)

# ---------------- Main ----------------
if __name__ == '__main__':
    os.makedirs('data', exist_ok=True)
    app.run(host='0.0.0.0', port=5000, debug=True)
