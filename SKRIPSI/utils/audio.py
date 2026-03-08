"""utils/audio.py - Play/record audio, AlarmEngine, PrayerNotifier."""
import os, sys, time, threading, wave

# patch wave writer
_orig_wave_close = wave.Wave_write.close
def _safe_wave_close(self):
    try: _orig_wave_close(self)
    except AttributeError: pass
wave.Wave_write.close = _safe_wave_close

if hasattr(wave.Wave_write, '__del__'):
    _orig_wave_del = wave.Wave_write.__del__
    def _safe_wave_del(self):
        try: _orig_wave_del(self)
        except AttributeError: pass
    wave.Wave_write.__del__ = _safe_wave_del

from datetime import datetime
from kivy.clock import Clock

# Fix base path untuk PyInstaller bundle
_BASE = getattr(sys, '_MEIPASS', os.path.abspath('.'))

# DIR_AUDIO pakai folder writable di samping .exe
def _get_dir_audio():
    if getattr(sys, 'frozen', False):
        return os.path.join(os.path.dirname(sys.executable), 'alarm_audio')
    return os.path.join(os.path.abspath('.'), 'alarm_audio')

DIR_AUDIO = _get_dir_audio()
os.makedirs(DIR_AUDIO, exist_ok=True)

# Cari file azan
AZAN_AUDIO = None
for _search_dir in [_BASE, os.path.abspath('.')]:
    for _r, _d, _f in os.walk(_search_dir):
        for _fn in _f:
            if 'azan' in _fn.lower() and _fn.lower().endswith(('.wav','.mp3','.ogg','.aac')):
                AZAN_AUDIO = os.path.join(_r, _fn); break
        if AZAN_AUDIO: break
    if AZAN_AUDIO: break

if AZAN_AUDIO is None:
    AZAN_AUDIO = os.path.join(_BASE, 'azan1.mp3')

print(f"[info] AZAN_AUDIO: {AZAN_AUDIO}")
print(f"[info] DIR_AUDIO: {DIR_AUDIO}")


def _resolve_path(path):
    if not path: return path
    if os.path.isabs(path) and os.path.exists(path): return path
    candidate = os.path.join(_BASE, os.path.basename(path))
    if os.path.exists(candidate): return candidate
    if os.path.exists(path): return path
    return path


def play_audio(path):
    def _go():
        resolved = _resolve_path(path)
        if not resolved or not os.path.exists(resolved):
            print(f"[play_audio] File tidak ditemukan: {path}"); return
        print(f"[play_audio] Memutar: {resolved}")
        # Coba playsound dulu (lebih simpel di Windows)
        try:
            from playsound import playsound
            playsound(resolved)
            return
        except Exception as e:
            print(f"[play_audio] playsound error: {e}")
        # Fallback ke winsound untuk WAV
        try:
            import winsound
            if resolved.lower().endswith('.wav'):
                winsound.PlaySound(resolved, winsound.SND_FILENAME)
                return
        except Exception as e:
            print(f"[play_audio] winsound error: {e}")
        # Fallback ke pygame
        try:
            import pygame
            if not pygame.mixer.get_init():
                pygame.mixer.pre_init(44100,-16,2,512); pygame.mixer.init()
            pygame.mixer.music.load(resolved)
            pygame.mixer.music.play()
            while pygame.mixer.music.get_busy():
                time.sleep(0.2)
            pygame.mixer.music.stop()
        except Exception as e:
            print(f"[play_audio] pygame error: {e}")
    threading.Thread(target=_go, daemon=True).start()


def record_audio(out_path, secs=5, cb_done=None, cb_prog=None):
    def _go():
        try:
            import pyaudio
            CHUNK,FMT,CH,RATE=1024,pyaudio.paInt16,1,44100
            pa=pyaudio.PyAudio(); st=pa.open(format=FMT,channels=CH,rate=RATE,input=True,frames_per_buffer=CHUNK)
            frames,total=[],int(RATE/CHUNK*secs)
            for i in range(total):
                frames.append(st.read(CHUNK,exception_on_overflow=False))
                if cb_prog and i%8==0: Clock.schedule_once(lambda dt,pct=int(i/total*100): cb_prog(pct))
            st.stop_stream(); st.close(); pa.terminate()
            wf = wave.open(out_path, 'wb')
            try:
                wf.setnchannels(CH)
                wf.setsampwidth(pa.get_sample_size(FMT))
                wf.setframerate(RATE)
                wf.writeframes(b''.join(frames))
            finally:
                wf.close()
            if cb_done: Clock.schedule_once(lambda dt: cb_done(True, out_path))
        except Exception as e:
            _err = str(e)
            if cb_done: Clock.schedule_once(lambda dt, err=_err: cb_done(False, err))
    threading.Thread(target=_go, daemon=True).start()


class AlarmEngine:
    def __init__(self): self._fired={}; self._ev=None; self.on_ring=None
    def start(self):
        if not self._ev: self._ev=Clock.schedule_interval(self._tick,10)
    def stop(self):
        if self._ev: self._ev.cancel(); self._ev=None
    def _tick(self,dt):
        from utils.storage import load_alarm
        now=datetime.now(); hhmm,today=now.strftime('%H:%M'),now.strftime('%Y-%m-%d')
        for a in load_alarm():
            aid=a.get('id')
            if not a.get('aktif',True) or aid in self._fired: continue
            if a.get('waktu')==hhmm and a.get('tanggal',today)==today:
                self._fired[aid]=True
                Clock.schedule_once(lambda dt,i=aid: self._fired.pop(i,None),90)
                if self.on_ring: Clock.schedule_once(lambda dt,aa=a: self.on_ring(aa))

ALARM_ENGINE = AlarmEngine()

PRAYER_TIMES={'Subuh':'05:01','Dzuhur':'12:23','Ashar':'15:30','Maghrib':'18:29','Isya':'19:38'}

class PrayerNotifier:
    def __init__(self): self._fired=set(); self._event=None
    def start(self):
        if not self._event: self._event=Clock.schedule_interval(self._tick,20)
    def stop(self):
        if self._event: self._event.cancel(); self._event=None; self._fired.clear()
    def _tick(self,dt):
        now=datetime.now(); hm,today=now.strftime('%H:%M'),now.strftime('%Y-%m-%d')
        for name,ts in PRAYER_TIMES.items():
            key=f"{today}-{name}"
            if ts==hm and key not in self._fired:
                self._fired.add(key); Clock.schedule_once(lambda dt,n=name: self._notify(n))
    def _notify(self,name):
        from kivy.uix.boxlayout import BoxLayout
        from kivy.uix.popup import Popup
        from kivy.metrics import dp
        from widgets.common import draw_bg,mk_lbl
        from utils.pet import pet_say
        box=BoxLayout(orientation='vertical',spacing=dp(12),padding=dp(18))
        draw_bg(box,'card',14)
        box.add_widget(mk_lbl(f'Waktunya Azan {name}',18,'orange',bold=True,align='center',size_hint_y=None,height=dp(30)))
        pop=Popup(title='',content=box,separator_height=0,background='',background_color=(0,0,0,.75),size_hint=(.8,.3))
        pop.open(); pet_say(f'Azan {name} berkumandang')
        azan_path = _resolve_path(AZAN_AUDIO)
        if os.path.exists(azan_path): play_audio(azan_path)

PRAYER_NOTIFIER = PrayerNotifier()