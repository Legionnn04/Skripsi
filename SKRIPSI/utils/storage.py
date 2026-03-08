"""utils/storage.py - Load/save JSON jadwal & alarm, helper alarm favorit."""
import json, os, sys, time, threading
from datetime import datetime

# ── Path helpers ─────────────────────────────────────────────────────────────
# Saat di-bundle PyInstaller, _MEIPASS adalah folder temp (read-only).
# Data JSON & rekaman harus disimpan di folder yang sama dengan .exe (writable).
def _data_dir():
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

_DD = _data_dir()
F_JADWAL  = os.path.join(_DD, 'jadwal_data.json')
F_ALARM   = os.path.join(_DD, 'alarm_data.json')
DIR_AUDIO = os.path.join(_DD, 'alarm_audio')
os.makedirs(DIR_AUDIO, exist_ok=True)

# ─────────────────────────────────────────────────────────────────────────────
# Firebase configuration (REST API)
# ─────────────────────────────────────────────────────────────────────────────
FIREBASE_URL = "https://alarmku-22964-default-rtdb.asia-southeast1.firebasedatabase.app/"
USE_FIREBASE = True


def _load(f):
    if os.path.exists(f):
        with open(f,'r',encoding='utf-8') as fp: return json.load(fp)
    return []

def _save(f,d):
    with open(f,'w',encoding='utf-8') as fp: json.dump(d,fp,ensure_ascii=False,indent=2)


# ─────────────────────────────────────────────────────────────────────────────
# Firebase helpers
# ─────────────────────────────────────────────────────────────────────────────

def _fb_get(endpoint):
    import urllib.request
    try:
        url = f"{FIREBASE_URL}{endpoint}.json"
        with urllib.request.urlopen(url, timeout=8) as r:
            return json.loads(r.read().decode()), None
    except Exception as e:
        return None, str(e)

def _fb_put(endpoint, data):
    import urllib.request
    try:
        url = f"{FIREBASE_URL}{endpoint}.json"
        req = urllib.request.Request(url, data=json.dumps(data).encode(),
                                     headers={'Content-Type':'application/json'}, method='PUT')
        with urllib.request.urlopen(req, timeout=8):
            return True, None
    except Exception as e:
        return False, str(e)

def _fb_delete(endpoint):
    import urllib.request
    try:
        req = urllib.request.Request(f"{FIREBASE_URL}{endpoint}.json", method='DELETE')
        with urllib.request.urlopen(req, timeout=8):
            return True, None
    except Exception as e:
        return False, str(e)

def _merge(local, remote):
    merged = {}
    for item in local:
        aid = item.get('id')
        if aid: merged[aid] = item
    for item in remote:
        aid = item.get('id')
        if not aid: continue
        if aid not in merged:
            merged[aid] = item
        else:
            lt = merged[aid].get('synced_at', merged[aid].get('dibuat', ''))
            rt = item.get('synced_at', item.get('updated_at', ''))
            if rt > lt: merged[aid] = item
    return list(merged.values())

def _fb_to_list(raw):
    if not raw or not isinstance(raw, dict): return []
    result = []
    for kid, kdata in raw.items():
        if kdata:
            kdata['id'] = kid
            result.append(kdata)
    return result

# ─────────────────────────────────────────────────────────────────────────────
# Jadwal
# ─────────────────────────────────────────────────────────────────────────────

def load_jadwal():
    local = _load(F_JADWAL)
    for j in local: j.setdefault('public', False)
    if USE_FIREBASE:
        raw, err = _fb_get('jadwal')
        if not err:
            merged = _merge(local, _fb_to_list(raw))
            _save(F_JADWAL, merged)
            return merged
    return local


def save_jadwal(d):
    for j in d: j.setdefault('public', False)
    _save(F_JADWAL, d)
    if USE_FIREBASE:
        def _push():
            payload = {j['id']: {**j, 'synced_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
                       for j in d if j.get('id')}
            _fb_put('jadwal', payload)
        threading.Thread(target=_push, daemon=True).start()

# ─────────────────────────────────────────────────────────────────────────────
# Alarm
# ─────────────────────────────────────────────────────────────────────────────

def load_alarm():
    local = _load(F_ALARM)
    for a in local: a.setdefault('public', False)
    if USE_FIREBASE:
        raw, err = _fb_get('alarms')
        if not err:
            merged = _merge(local, _fb_to_list(raw))
            _save(F_ALARM, merged)
            return merged
    return local


def save_alarm(d):
    for a in d: a.setdefault('public', False)
    _save(F_ALARM, d)
    if USE_FIREBASE:
        def _push():
            payload = {a['id']: {**a, 'synced_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
                       for a in d if a.get('id')}
            _fb_put('alarms', payload)
        threading.Thread(target=_push, daemon=True).start()

# ─────────────────────────────────────────────────────────────────────────────
# Sync helpers
# ─────────────────────────────────────────────────────────────────────────────

def force_sync():
    if not USE_FIREBASE: return False, "Firebase tidak aktif"
    if '<your-project>' in FIREBASE_URL: return False, "FIREBASE_URL belum dikonfigurasi"
    msgs = []
    raw_j, err = _fb_get('jadwal')
    if err:
        msgs.append(f"Jadwal gagal: {err}")
    else:
        merged = _merge(_load(F_JADWAL), _fb_to_list(raw_j))
        _save(F_JADWAL, merged)
        payload = {j['id']: {**j, 'synced_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
                   for j in merged if j.get('id')}
        _fb_put('jadwal', payload)
        msgs.append(f"{len(merged)} jadwal")
    raw_a, err2 = _fb_get('alarms')
    if err2:
        msgs.append(f"Alarm gagal: {err2}")
    else:
        merged = _merge(_load(F_ALARM), _fb_to_list(raw_a))
        _save(F_ALARM, merged)
        payload = {a['id']: {**a, 'synced_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
                   for a in merged if a.get('id')}
        _fb_put('alarms', payload)
        msgs.append(f"{len(merged)} alarm")
    ok = not any('gagal' in m for m in msgs)
    return ok, "Synced: " + ", ".join(msgs)


class _AutoSync:
    def __init__(self, interval=30):
        self._interval = interval; self._running = False; self._thread = None
    def start(self):
        if self._running: return
        self._running = True
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()
    def stop(self): self._running = False
    def _loop(self):
        self._do()
        while self._running:
            time.sleep(self._interval); self._do()
    def _do(self):
        if not USE_FIREBASE: return
        try:
            ok, msg = force_sync(); print(f"[AutoSync] {msg}")
        except Exception as e:
            print(f"[AutoSync] error: {e}")

AUTO_SYNC = _AutoSync(interval=30)

def get_favorite_alarm():
    for a in load_alarm():
        if a.get('favorite'): return a
    return None

def fill_empty_jadwals_with_favorite():
    fav = get_favorite_alarm()
    if not fav: return
    fav_audio = fav.get('audio_path',''); fav_type = fav.get('tipe_audio','')
    if not fav_audio: return
    jd = load_jadwal(); modified = False
    for j in jd:
        if not j.get('audio_path') and not j.get('alarm_id'):
            aid = str(int(time.time()*1000))
            alarm = {'id':aid,'label':j.get('judul','Alarm'),'waktu':j.get('waktu',''),
                     'tanggal':j.get('tanggal',''),'audio_path':fav_audio,'tipe_audio':fav_type,
                     'aktif':True,'dibuat':datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
            al = load_alarm(); al.append(alarm); save_alarm(al)
            j['audio_path']=fav_audio; j['tipe_audio']=fav_type; j['alarm_id']=aid
            modified = True
    if modified: save_jadwal(jd)