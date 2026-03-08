"""
generate_modules.py
Jalankan script ini sekali untuk menghasilkan struktur folder modular:
    python generate_modules.py
"""
import os, zipfile, textwrap

FILES = {}

# ═══════════════════════════════════════════════════════════════
FILES['utils/__init__.py'] = "# utils package\n"

FILES['utils/theme.py'] = '''\
"""utils/theme.py - Tema warna & pergantian tema otomatis."""
from datetime import datetime
from kivy.utils import get_color_from_hex
from kivy.core.window import Window

PAL = {
    \'bg\':\'#0D1117\',\'card\':\'#161B22\',\'card2\':\'#21262D\',
    \'blue\':\'#58A6FF\',\'blue2\':\'#1F6FEB\',\'green\':\'#3FB950\',
    \'yellow\':\'#D29922\',\'red\':\'#F85149\',\'purple\':\'#BC8CFF\',
    \'orange\':\'#F0883E\',\'orange2\':\'#9A3412\',\'txt\':\'#E6EDF3\',
    \'txt2\':\'#8B949E\',\'border\':\'#30363D\',\'nav\':\'#0D1117\',
}

THEME_PALETTES = {
    \'morning\':{\'bg\':\'#FFF8E1\',\'card\':\'#FFFDE7\',\'card2\':\'#FFF3E0\',
               \'blue\':\'#90A4AE\',\'orange\':\'#FFB74D\',\'purple\':\'#CE93D8\',\'txt\':\'#212121\',\'txt2\':\'#455A64\'},
    \'day\':{\'bg\':\'#E3F2FD\',\'card\':\'#FFFFFF\',\'card2\':\'#E1F5FE\',
            \'blue\':\'#64B5F6\',\'orange\':\'#FFCC80\',\'purple\':\'#B39DDB\',\'txt\':\'#212121\',\'txt2\':\'#546E7A\'},
    \'evening\':{\'bg\':\'#F6E5CA\',\'card\':\'#FFE0B2\',\'card2\':\'#FFECB3\',
                \'blue\':\'#78909C\',\'orange\':\'#FFAB91\',\'purple\':\'#B39DDB\',\'txt\':\'#212121\',\'txt2\':\'#546E7A\'},
    \'night\':{\'bg\':\'#263238\',\'card\':\'#37474F\',\'card2\':\'#455A64\',
              \'blue\':\'#90A4AE\',\'orange\':\'#FFCCBC\',\'purple\':\'#B39DDB\',\'txt\':\'#ECEFF1\',\'txt2\':\'#B0BEC5\'},
}

CURRENT_THEME = None

def p(k): return get_color_from_hex(PAL[k])

def get_time_of_day():
    h = datetime.now().hour
    if 5<=h<11: return \'morning\'
    if 11<=h<17: return \'day\'
    if 17<=h<19: return \'evening\'
    return \'night\'

def apply_theme(name):
    global CURRENT_THEME
    if name == CURRENT_THEME: return
    CURRENT_THEME = name
    PAL.update(THEME_PALETTES.get(name, {}))
    Window.clearcolor = p(\'bg\')
    from kivy.app import App
    app = App.get_running_app()
    if not app or not getattr(app,\'root\',None): return
    sm = app.root; cur = sm.current
    sm.clear_widgets()
    from screens.splash   import SplashScreen
    from screens.beranda  import BerandaScreen
    from screens.jadwal   import JadwalScreen
    from screens.kalender import KalenderScreen
    from screens.alarm    import AlarmScreen
    for S in [SplashScreen,BerandaScreen,JadwalScreen,KalenderScreen,AlarmScreen]:
        sm.add_widget(S())
    sm.current = cur
'''

FILES['utils/storage.py'] = '''\
"""utils/storage.py - Load/save JSON jadwal & alarm, helper alarm favorit."""
import json, os, time
from datetime import datetime

F_JADWAL  = \'jadwal_data.json\'
F_ALARM   = \'alarm_data.json\'
DIR_AUDIO = \'alarm_audio\'
os.makedirs(DIR_AUDIO, exist_ok=True)

def _load(f):
    if os.path.exists(f):
        with open(f,\'r\',encoding=\'utf-8\') as fp: return json.load(fp)
    return []

def _save(f,d):
    with open(f,\'w\',encoding=\'utf-8\') as fp: json.dump(d,fp,ensure_ascii=False,indent=2)

def load_jadwal():  return _load(F_JADWAL)
def save_jadwal(d): _save(F_JADWAL, d)
def load_alarm():   return _load(F_ALARM)
def save_alarm(d):  _save(F_ALARM, d)

def get_favorite_alarm():
    for a in load_alarm():
        if a.get(\'favorite\'): return a
    return None

def fill_empty_jadwals_with_favorite():
    fav = get_favorite_alarm()
    if not fav: return
    fav_audio = fav.get(\'audio_path\',\'\'); fav_type = fav.get(\'tipe_audio\',\'\')
    if not fav_audio: return
    jd = load_jadwal(); modified = False
    for j in jd:
        if not j.get(\'audio_path\') and not j.get(\'alarm_id\'):
            aid = str(int(time.time()*1000))
            alarm = {\'id\':aid,\'label\':j.get(\'judul\',\'Alarm\'),\'waktu\':j.get(\'waktu\',\'\'),
                     \'tanggal\':j.get(\'tanggal\',\'\'),\'audio_path\':fav_audio,\'tipe_audio\':fav_type,
                     \'aktif\':True,\'dibuat\':datetime.now().strftime(\'%Y-%m-%d %H:%M:%S\')}
            al = load_alarm(); al.append(alarm); save_alarm(al)
            j[\'audio_path\']=fav_audio; j[\'tipe_audio\']=fav_type; j[\'alarm_id\']=aid
            modified = True
    if modified: save_jadwal(jd)
'''

FILES['utils/nlp.py'] = '''\
"""utils/nlp.py - Parser teks jadwal bahasa Indonesia."""
import re
from datetime import datetime, timedelta

_HARI  = {\'senin\':0,\'selasa\':1,\'rabu\':2,\'kamis\':3,\'jumat\':4,\'sabtu\':5,\'minggu\':6}
_BULAN = {\'januari\':1,\'februari\':2,\'maret\':3,\'april\':4,\'mei\':5,\'juni\':6,
          \'juli\':7,\'agustus\':8,\'september\':9,\'oktober\':10,\'november\':11,\'desember\':12}

def parse_jadwal(teks):
    lo = teks.lower()
    r  = {\'judul\':\'\',\'tanggal\':\'\',\'waktu\':\'\',\'lokasi\':\'\',\'catatan\':teks,\'prioritas\':\'normal\'}
    for pat in [r\'jam\\s*(\\d{1,2})(?:[:.](\\d{2}))?\\s*(pagi|siang|sore|malam)?\',
                r\'pukul\\s*(\\d{1,2})(?:[:.](\\d{2}))?\\s*(pagi|siang|sore|malam)?\',
                r\'(\\d{1,2})[.:](\\d{2})\\s*(pagi|siang|sore|malam)?\']:
        m = re.search(pat, lo)
        if m:
            j,mn = int(m.group(1)),int(m.group(2) or 0); pr = m.group(3)
            if pr in (\'sore\',\'malam\') and j<12: j+=12
            elif pr==\'siang\' and j<7: j+=12
            r[\'waktu\']=f"{j:02d}:{mn:02d}"; break
    now=datetime.now(); tset=False
    m=re.search(r"(\\d+)\\s*(?:menit|mnt)\\s*(?:ke\\s*depan|kedepan|dari sekarang)",lo)
    if m:
        dt=now+timedelta(minutes=int(m.group(1))); r[\'tanggal\']=dt.strftime(\'%Y-%m-%d\'); r[\'waktu\']=dt.strftime(\'%H:%M\'); tset=True
    else:
        m=re.search(r"(\\d+)\\s*jam\\s*(?:ke\\s*depan|kedepan|dari sekarang)",lo)
        if m:
            dt=now+timedelta(hours=int(m.group(1))); r[\'tanggal\']=dt.strftime(\'%Y-%m-%d\'); r[\'waktu\']=dt.strftime(\'%H:%M\'); tset=True
    if not tset:
        if \'besok\' in lo: r[\'tanggal\']=(now+timedelta(1)).strftime(\'%Y-%m-%d\'); tset=True
        elif \'lusa\' in lo: r[\'tanggal\']=(now+timedelta(2)).strftime(\'%Y-%m-%d\'); tset=True
        elif \'hari ini\' in lo or \'sekarang\' in lo: r[\'tanggal\']=now.strftime(\'%Y-%m-%d\'); tset=True
    if not tset:
        for nm,idx in _HARI.items():
            if nm in lo:
                s=(idx-now.weekday())%7 or 7; r[\'tanggal\']=(now+timedelta(s)).strftime(\'%Y-%m-%d\'); tset=True; break
    if not tset:
        m=re.search(r\'tanggal\\s*(\\d{1,2})\\s*(\\w+)?\',lo)
        if m:
            tgl,bln=int(m.group(1)),_BULAN.get(m.group(2) or \'\',now.month)
            try:
                t=datetime(now.year,bln,tgl)
                if t<now: t=datetime(now.year+1,bln,tgl)
                r[\'tanggal\']=t.strftime(\'%Y-%m-%d\'); tset=True
            except: pass
    if not tset: r[\'tanggal\']=now.strftime(\'%Y-%m-%d\')
    if any(w in lo for w in [\'penting\',\'urgent\',\'segera\',\'darurat\']): r[\'prioritas\']=\'tinggi\'
    elif any(w in lo for w in [\'santai\',\'biasa\',\'opsional\']): r[\'prioritas\']=\'rendah\'
    m=re.search(r\'di\\s+([A-Za-z][A-Za-z\\s]{2,30}?)(?:\\s+(?:jam|pukul|tanggal|pada)|$)\',lo)
    if m: r[\'lokasi\']=m.group(1).strip().title()
    judul=teks
    for pat in [r\'(besok|lusa|hari ini|sekarang)\',r\'(jam|pukul)\\s*\\d{1,2}[:.].\\d{0,2}\\s*(pagi|siang|sore|malam)?\',
                r\'\\d{1,2}[.:]\\d{2}\\s*(pagi|siang|sore|malam)\',r\'tanggal\\s*\\d{1,2}\\s*\\w*\',
                r\'(senin|selasa|rabu|kamis|jumat|sabtu|minggu)\',r\'di\\s+[A-Za-z][A-Za-z\\s]{2,30}\',
                r\'(penting|urgent|segera|darurat|santai|biasa)\',
                r\'(buatkan|tambahkan|buat|set|catat|ingatkan|jadwalkan)\\s*(jadwal|kegiatan|acara|reminder|pengingat|saya|aku)?\',
                r\'(untuk|dengan|pada|di)\']:
        judul=re.sub(pat,\'\',judul,flags=re.IGNORECASE)
    judul=re.sub(r\'\\s+\',\' \',judul).strip()
    if not judul or len(judul)<3:
        kata=[w for w in teks.split() if len(w)>3][:3]
        judul=\' \'.join(kata) if kata else \'Kegiatan Baru\'
    r[\'judul\']=judul.title()[:50]
    return r
'''

FILES['utils/pet.py'] = '''\
"""utils/pet.py - Virtual pet helper."""
import os, random
from kivy.clock import Clock
from datetime import datetime

PET_MESSAGES = [\'Halo! Senang bertemu denganmu.\',\'Aku akan mengingatkanmu nanti.\',
                \'Jangan lupa istirahat ya!\',\'Ayo semangat jalani hari!\']

PET_STICKERS = [
    {\'file\':\'mengantuk.gif\',\'msg\':\'Saya ngantuk...\',\'start\':22,\'end\':6,\'dur\':4},
    {\'file\':\'berpikir.gif\',\'msg\':\'Sedang berpikir...\',\'dur\':3},
    {\'file\':\'kagum.gif\',\'msg\':\'Wah, keren!\',\'dur\':2},
    {\'file\':\'marah.gif\',\'msg\':\'Aduh, marah nih!\',\'dur\':2},
    {\'file\':\'menyapa.gif\',\'msg\':\'Hai teman!\',\'dur\':4},
    {\'file\':\'normal.png\',\'msg\':\'\'},
    {\'file\':\'mengingatkan.gif\',\'msg\':\'Sudah kuingatkan, ya!\',\'dur\':3},
]

def pet_say(msg=None, dur=3, sticker_override=None):
    from kivy.app import App
    app = App.get_running_app()
    if not app or not getattr(app,\'root\',None): return
    try:
        screen = app.root.get_screen(\'beranda\')
        choice = None
        if sticker_override:
            choice = {\'file\':sticker_override}
        else:
            nowh = datetime.now().hour; candidates = []
            for stk in PET_STICKERS:
                s=stk.get(\'start\'); e=stk.get(\'end\')
                if s is not None and e is not None:
                    if s<=e:
                        if s<=nowh<e: candidates.append(stk)
                    else:
                        if nowh>=s or nowh<e: candidates.append(stk)
                else:
                    candidates.append(stk)
            choice = random.choice(candidates) if candidates else random.choice(PET_STICKERS)
        if hasattr(screen,\'pet_img\') and choice:
            path=choice.get(\'file\')
            if path and os.path.exists(path): screen.pet_img.source=path
        if msg is None and choice: msg=choice.get(\'msg\',\'\')
        if hasattr(screen,\'pet_bubble\'):
            screen.pet_bubble.text=msg or \'\'
            bubble_dur=choice.get(\'dur\',dur) if choice else dur
            Clock.schedule_once(lambda dt: setattr(screen.pet_bubble,\'text\',\'\'),bubble_dur)
        else:
            pet_lbl=screen.pet_msg; pet_lbl.text=msg or \'\'
            Clock.schedule_once(lambda dt: setattr(pet_lbl,\'text\',\'\'),dur)
    except Exception: pass
'''

FILES['utils/audio.py'] = '''\
"""utils/audio.py - Play/record audio, AlarmEngine, PrayerNotifier."""
import os, time, threading, wave
from datetime import datetime
from kivy.clock import Clock

AZAN_AUDIO = None
for _r, _d, _f in os.walk(\'.\'):
    for _fn in _f:
        if \'azan\' in _fn.lower() and _fn.lower().endswith((\'.wav\',\'.mp3\',\'.ogg\',\'.aac\')):
            AZAN_AUDIO = os.path.join(_r, _fn); break
    if AZAN_AUDIO: break
if AZAN_AUDIO is None: AZAN_AUDIO = \'azan.wav\'
print(f"[info] AZAN_AUDIO: {AZAN_AUDIO}")

def play_audio(path):
    def _go():
        try:
            from kivy.core.audio import SoundLoader
            s=SoundLoader.load(path)
            if not s: return
            s.play(); time.sleep(s.length+0.5); s.stop(); s.unload()
        except Exception as e: print(f"[play_audio] {e}")
    threading.Thread(target=_go,daemon=True).start()

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
            with wave.open(out_path,\'wb\') as wf:
                wf.setnchannels(CH); wf.setsampwidth(pa.get_sample_size(FMT))
                wf.setframerate(RATE); wf.writeframes(b\'\'.join(frames))
            if cb_done: Clock.schedule_once(lambda dt: cb_done(True,out_path))
        except Exception as e:
            if cb_done: Clock.schedule_once(lambda dt: cb_done(False,str(e)))
    threading.Thread(target=_go,daemon=True).start()

class AlarmEngine:
    def __init__(self): self._fired={}; self._ev=None; self.on_ring=None
    def start(self):
        if not self._ev: self._ev=Clock.schedule_interval(self._tick,10)
    def stop(self):
        if self._ev: self._ev.cancel(); self._ev=None
    def _tick(self,dt):
        from utils.storage import load_alarm
        now=datetime.now(); hhmm,today=now.strftime(\'%H:%M\'),now.strftime(\'%Y-%m-%d\')
        for a in load_alarm():
            aid=a.get(\'id\')
            if not a.get(\'aktif\',True) or aid in self._fired: continue
            if a.get(\'waktu\')==hhmm and a.get(\'tanggal\',today)==today:
                self._fired[aid]=True
                Clock.schedule_once(lambda dt,i=aid: self._fired.pop(i,None),90)
                if self.on_ring: Clock.schedule_once(lambda dt,aa=a: self.on_ring(aa))

ALARM_ENGINE = AlarmEngine()

PRAYER_TIMES={\'Subuh\':\'05:01\',\'Dzuhur\':\'12:23\',\'Ashar\':\'15:30\',\'Maghrib\':\'18:29\',\'Isya\':\'19:38\'}

class PrayerNotifier:
    def __init__(self): self._fired=set(); self._event=None
    def start(self):
        if not self._event: self._event=Clock.schedule_interval(self._tick,20)
    def stop(self):
        if self._event: self._event.cancel(); self._event=None; self._fired.clear()
    def _tick(self,dt):
        now=datetime.now(); hm,today=now.strftime(\'%H:%M\'),now.strftime(\'%Y-%m-%d\')
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
        box=BoxLayout(orientation=\'vertical\',spacing=dp(12),padding=dp(18))
        draw_bg(box,\'card\',14)
        box.add_widget(mk_lbl(f\'Waktunya Azan {name}\',18,\'orange\',bold=True,align=\'center\',size_hint_y=None,height=dp(30)))
        pop=Popup(title=\'\',content=box,separator_height=0,background=\'\',background_color=(0,0,0,.75),size_hint=(.8,.3))
        pop.open(); pet_say(f\'Azan {name} berkumandang\')
        if os.path.exists(AZAN_AUDIO): play_audio(AZAN_AUDIO)

PRAYER_NOTIFIER = PrayerNotifier()
'''

FILES['widgets/__init__.py'] = "# widgets package\n"

FILES['widgets/common.py'] = '''\
"""widgets/common.py - Helper widget: draw_bg, mk_lbl, mk_input, MBtn."""
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.graphics import Color, RoundedRectangle
from kivy.animation import Animation
from kivy.metrics import dp
from kivy.utils import get_color_from_hex
from utils.theme import p, PAL

def draw_bg(w, clr_key=\'card\', r=12):
    def _d(*a):
        w.canvas.before.clear()
        with w.canvas.before:
            Color(*p(clr_key)); RoundedRectangle(pos=w.pos,size=w.size,radius=[dp(r)])
    w.bind(pos=_d,size=_d); _d()

def mk_lbl(text, sz=13, clr=\'txt\', bold=False, align=\'left\', **kw):
    lb=Label(text=text,font_size=dp(sz),color=p(clr),bold=bold,halign=align,valign=\'middle\',**kw)
    lb.bind(size=lb.setter(\'text_size\')); return lb

def mk_input(**kw):
    d=dict(font_size=dp(13),background_normal=\'\',background_color=p(\'card2\'),
           foreground_color=p(\'txt\'),cursor_color=p(\'blue\'),hint_text_color=p(\'txt2\'),
           size_hint_y=None,height=dp(44),padding=[dp(12),dp(12)],multiline=False)
    d.update(kw); return TextInput(**d)

def _style_colors(style):
    base={\'primary\':PAL.get(\'blue\',\'#1F6FEB\'),\'success\':PAL.get(\'green\',\'#2EA043\'),
          \'danger\':\'#B91C1C\',\'neutral\':PAL.get(\'card\',\'#21262D\'),
          \'orange\':PAL.get(\'orange\',\'#9A3412\')}.get(style,PAL.get(\'blue\',\'#1F6FEB\'))
    n=get_color_from_hex(base); h=[max(0,c*.9) for c in n]; return n,h

class MBtn(Button):
    def __init__(self, style=\'primary\', **kw):
        super().__init__(**kw)
        self.background_normal=\'\'; self.background_down=\'\'
        self.bold=True; self.color=p(\'txt\')
        self._n,self._h=_style_colors(style); self.background_color=self._n
        self.bind(
            on_press=lambda *a: Animation(background_color=self._h,duration=0.1).start(self),
            on_release=lambda *a: Animation(background_color=self._n,duration=0.2).start(self))
'''

FILES['widgets/bottom_nav.py'] = '''\
"""widgets/bottom_nav.py - Bottom navigation bar."""
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.graphics import Color, Rectangle
from kivy.metrics import dp
from kivy.uix.screenmanager import FadeTransition
from utils.theme import p

NAV_ITEMS=[('beranda','Beranda'),('jadwal','Jadwal'),('kalender','Kalender'),('alarm','Alarm')]

class BottomNav(BoxLayout):
    def __init__(self, sm, current=\'beranda\', **kw):
        super().__init__(size_hint_y=None,height=dp(56),orientation=\'horizontal\',
                         spacing=dp(2),padding=[dp(4),dp(4)],**kw)
        self.sm=sm; self._btns={}
        with self.canvas.before:
            Color(*p(\'nav\')); self._bgr=Rectangle(pos=self.pos,size=self.size)
        self.bind(pos=lambda *a:setattr(self._bgr,\'pos\',self.pos),
                  size=lambda *a:setattr(self._bgr,\'size\',self.size))
        for name,label in NAV_ITEMS:
            btn=self._mk(name,label,active=(name==current))
            self._btns[name]=btn; self.add_widget(btn)

    def _mk(self,name,label,active):
        btn=Button(text=label,font_size=dp(13),bold=active,background_normal=\'\',
                   background_color=p(\'blue2\') if active else p(\'card2\'),
                   background_down=\'\',color=p(\'txt\') if active else p(\'txt2\'),size_hint_x=1)
        btn.bind(on_press=lambda *a,n=name: self._go(n)); return btn

    def _go(self,name):
        if name not in self.sm.screen_names: return
        self.sm.transition=FadeTransition(duration=0.12)
        self.sm.current=name; self.set_active(name)

    def set_active(self,name):
        for n,btn in self._btns.items():
            active=(n==name)
            btn.background_color=p(\'blue2\') if active else p(\'card2\')
            btn.color=p(\'txt\') if active else p(\'txt2\'); btn.bold=active
'''

FILES['widgets/jadwal_card.py'] = '''\
"""widgets/jadwal_card.py - Card untuk satu item jadwal."""
from datetime import datetime
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.widget import Widget
from kivy.graphics import Color, RoundedRectangle
from kivy.metrics import dp
from widgets.common import mk_lbl
from utils.theme import p

class JadwalCard(BoxLayout):
    def __init__(self, jadwal, on_delete=None, on_edit=None, **kw):
        super().__init__(orientation=\'vertical\',size_hint_y=None,height=dp(112),
                         padding=[dp(16),dp(10)],spacing=dp(5),**kw)
        pw={\'tinggi\':p(\'red\'),\'normal\':p(\'blue\'),\'rendah\':p(\'green\')}
        pc=pw.get(jadwal.get(\'prioritas\',\'normal\'),p(\'blue\'))
        with self.canvas.before:
            Color(*p(\'card\')); self._bg=RoundedRectangle(pos=self.pos,size=self.size,radius=[dp(12)])
            Color(*pc[:3],0.8); self._bar=RoundedRectangle(pos=self.pos,size=(dp(4),self.height),radius=[dp(2)])
        self.bind(pos=self._u,size=self._u)
        hdr=BoxLayout(size_hint_y=None,height=dp(26))
        hdr.add_widget(mk_lbl(jadwal.get(\'judul\',\'Kegiatan\'),14,bold=True,size_hint_x=1))
        bm={\'tinggi\':\'PENTING\',\'normal\':\'NORMAL\',\'rendah\':\'SANTAI\'}
        hdr.add_widget(mk_lbl(bm.get(jadwal.get(\'prioritas\',\'normal\'),\'NORMAL\'),
                               10,\'txt2\',size_hint_x=None,width=dp(80),align=\'right\'))
        self.add_widget(hdr)
        try: tgl=datetime.strptime(jadwal.get(\'tanggal\',\'\'),\'%Y-%m-%d\').strftime(\'%d %b %Y\')
        except: tgl=jadwal.get(\'tanggal\',\'\')
        pts=([f\'Tanggal {tgl}\'] if tgl else [])+([f\'Waktu {jadwal["waktu"]}\'] if jadwal.get(\'waktu\') else [])+([f\'Lokasi {jadwal["lokasi"]}\'] if jadwal.get(\'lokasi\') else [])
        self.add_widget(mk_lbl(\'   \'.join(pts) or \'Tanggal belum ditentukan\',12,\'txt2\',size_hint_y=None,height=dp(20)))
        cat=jadwal.get(\'catatan\',\'\')
        if cat: self.add_widget(mk_lbl(cat[:78]+(\'...\' if len(cat)>78 else \'\'),11,\'txt2\',size_hint_y=None,height=dp(18)))
        aksi=BoxLayout(size_hint_y=None,height=dp(26),spacing=dp(8)); aksi.add_widget(Widget())
        if on_edit:
            be=Button(text=\'Ubah\',size_hint=(None,1),width=dp(64),font_size=dp(11),
                      background_normal=\'\',background_color=(*p(\'blue2\')[:3],.18),color=p(\'blue\'),bold=True)
            be.bind(on_press=lambda *a: on_edit(jadwal)); aksi.add_widget(be)
        bd=Button(text=\'Hapus\',size_hint=(None,1),width=dp(64),font_size=dp(11),
                  background_normal=\'\',background_color=(*p(\'red\')[:3],.18),color=p(\'red\'),bold=True)
        bd.bind(on_press=lambda *a: on_delete and on_delete(jadwal))
        aksi.add_widget(bd); self.add_widget(aksi)

    def _u(self,*a):
        self._bg.pos,self._bg.size=self.pos,self.size
        self._bar.pos,self._bar.size=self.pos,(dp(4),self.height)
'''

FILES['widgets/alarm_card.py'] = '''\
"""widgets/alarm_card.py - Card untuk satu item alarm."""
import os
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.widget import Widget
from kivy.graphics import Color, RoundedRectangle
from kivy.metrics import dp
from datetime import datetime
from widgets.common import mk_lbl
from utils.theme import p
from utils.audio import play_audio

class AlarmCard(BoxLayout):
    def __init__(self, alarm, on_delete=None, on_toggle=None, on_play=None, on_fav=None, **kw):
        super().__init__(orientation=\'vertical\',size_hint_y=None,height=dp(110),
                         padding=[dp(16),dp(10)],spacing=dp(5),**kw)
        aktif=alarm.get(\'aktif\',True); sc=p(\'green\') if aktif else p(\'txt2\')
        fav=alarm.get(\'favorite\',False)
        with self.canvas.before:
            Color(*p(\'card\')); self._bg=RoundedRectangle(pos=self.pos,size=self.size,radius=[dp(12)])
            Color(*sc[:3],0.8); self._bar=RoundedRectangle(pos=self.pos,size=(dp(4),self.height),radius=[dp(2)])
        self.bind(pos=self._u,size=self._u)
        hdr=BoxLayout(size_hint_y=None,height=dp(26))
        star=Button(text=\'*\' if fav else \'o\',size_hint=(None,1),width=dp(30),font_size=dp(14),
                    background_normal=\'\',background_color=(0,0,0,0),color=p(\'yellow\'))
        star.bind(on_press=lambda *a: on_fav and on_fav(alarm)); hdr.add_widget(star)
        hdr.add_widget(mk_lbl(alarm.get(\'label\',\'Alarm\'),14,bold=True,size_hint_x=1))
        tp=alarm.get(\'tipe_audio\',\'file\'); bt_txt,bt_col=(\'Rekaman\',\'orange\') if tp==\'rekam\' else (\'File\',\'blue\')
        hdr.add_widget(mk_lbl(bt_txt,10,bt_col,bold=True,size_hint_x=None,width=dp(80),align=\'right\'))
        self.add_widget(hdr)
        try: tgl=datetime.strptime(alarm.get(\'tanggal\',\'\'),\'%Y-%m-%d\').strftime(\'%d %b %Y\')
        except: tgl=\'Setiap hari\'
        self.add_widget(mk_lbl(f\'Waktu {alarm.get("waktu","--:--")}   Tanggal {tgl}\',12,\'txt2\',size_hint_y=None,height=dp(20)))
        ap=alarm.get(\'audio_path\',\'\')
        self.add_widget(mk_lbl(f\'Audio: {os.path.basename(ap) if ap else "Tidak ada audio"}\',11,\'txt2\',size_hint_y=None,height=dp(18)))
        aksi=BoxLayout(size_hint_y=None,height=dp(28),spacing=dp(8)); aksi.add_widget(Widget())
        if ap and os.path.exists(ap):
            bp=Button(text=\'Dengar\',size_hint=(None,1),width=dp(74),font_size=dp(11),
                      background_normal=\'\',background_color=(*p(\'blue2\')[:3],.22),color=p(\'blue\'),bold=True)
            bp.bind(on_press=lambda *a: on_play and on_play(ap)); aksi.add_widget(bp)
        tog_t,tog_c=(\'Nonaktif\',\'yellow\') if aktif else (\'Aktifkan\',\'green\')
        bt2=Button(text=tog_t,size_hint=(None,1),width=dp(74),font_size=dp(11),
                   background_normal=\'\',background_color=(*p(tog_c)[:3],.18),color=p(tog_c),bold=True)
        bt2.bind(on_press=lambda *a: on_toggle and on_toggle(alarm)); aksi.add_widget(bt2)
        bd=Button(text=\'Hapus\',size_hint=(None,1),width=dp(60),font_size=dp(11),
                  background_normal=\'\',background_color=(*p(\'red\')[:3],.18),color=p(\'red\'),bold=True)
        bd.bind(on_press=lambda *a: on_delete and on_delete(alarm))
        aksi.add_widget(bd); self.add_widget(aksi)

    def _u(self,*a):
        self._bg.pos,self._bg.size=self.pos,self.size
        self._bar.pos,self._bar.size=self.pos,(dp(4),self.height)
'''

FILES['screens/__init__.py'] = "# screens package\n"

FILES['screens/base.py'] = '''\
"""screens/base.py - BaseScreen dengan content area + nav bar placeholder."""
from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.graphics import Color, Rectangle
from kivy.metrics import dp
from utils.theme import p
from widgets.bottom_nav import BottomNav

class BaseScreen(Screen):
    _NAV_KEY = \'beranda\'
    def __init__(self, **kw):
        super().__init__(**kw)
        self._wrap=BoxLayout(orientation=\'vertical\')
        with self._wrap.canvas.before:
            Color(*p(\'bg\')); self._bgr=Rectangle(pos=self._wrap.pos,size=self._wrap.size)
        self._wrap.bind(pos=lambda *a:setattr(self._bgr,\'pos\',self._wrap.pos),
                        size=lambda *a:setattr(self._bgr,\'size\',self._wrap.size))
        self._content_area=BoxLayout(orientation=\'vertical\',size_hint_y=1)
        self._wrap.add_widget(self._content_area)
        self._nav_placeholder=BoxLayout(size_hint_y=None,height=dp(64))
        self._wrap.add_widget(self._nav_placeholder)
        self._nav=None; self.add_widget(self._wrap)

    def _set_content(self, widget):
        self._content_area.add_widget(widget)

    def on_enter(self):
        if self._nav is None:
            self._nav=BottomNav(self.manager,current=self._NAV_KEY)
            self._nav_placeholder.add_widget(self._nav)
        else:
            self._nav.set_active(self._NAV_KEY)
'''

FILES['screens/splash.py'] = '''\
"""screens/splash.py - Layar splash dengan logo kampus."""
from kivy.uix.screenmanager import Screen
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.image import Image
from kivy.graphics import Color, Rectangle
from kivy.core.window import Window
from kivy.clock import Clock
from utils.theme import p

class SplashScreen(Screen):
    def __init__(self, **kw):
        super().__init__(name=\'splash\', **kw)
        root=FloatLayout()
        with root.canvas.before:
            Color(*p(\'bg\')); Rectangle(pos=root.pos,size=Window.size)
        img=Image(source=\'logokampus.png\',allow_stretch=True,keep_ratio=True,
                  size_hint=(0.6,0.6),pos_hint={\'center_x\':.5,\'center_y\':.5})
        root.add_widget(img); self.add_widget(root)

    def on_enter(self):
        def goto(dt):
            if self.manager: self.manager.current=\'beranda\'
            else: Clock.schedule_once(goto,0.5)
        Clock.schedule_once(goto,2.2)
'''

FILES['screens/beranda.py'] = '''\
"""screens/beranda.py - Layar utama (Beranda) dengan input jadwal & jam."""
import os, random, threading
from datetime import datetime
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.label import Label
from kivy.uix.widget import Widget
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.image import Image
from kivy.graphics import Color, Rectangle
from kivy.clock import Clock
from kivy.metrics import dp
from kivy.animation import Animation
from screens.base import BaseScreen
from widgets.common import mk_lbl, mk_input, MBtn, draw_bg
from widgets.jadwal_card import JadwalCard
from utils.theme import p, apply_theme, get_time_of_day
from utils.storage import load_jadwal, save_jadwal, load_alarm, get_favorite_alarm
from utils.audio import ALARM_ENGINE, PRAYER_NOTIFIER, play_audio
from utils.nlp import parse_jadwal
from utils.pet import pet_say, PET_MESSAGES
from widgets.popups import TambahJadwalPopup
import time

def show_ring_popup(alarm):
    from utils.pet import pet_say
    from utils.audio import AZAN_AUDIO, play_audio
    from widgets.common import draw_bg, mk_lbl, MBtn
    from kivy.uix.boxlayout import BoxLayout
    from kivy.uix.widget import Widget
    from kivy.uix.popup import Popup
    from kivy.metrics import dp
    pet_say(\'Waktu alarm!\')
    box=BoxLayout(orientation=\'vertical\',spacing=dp(12),padding=dp(22))
    draw_bg(box,\'card\',14)
    box.add_widget(mk_lbl(\'ALARM BERBUNYI!\',20,\'yellow\',bold=True,align=\'center\',size_hint_y=None,height=dp(36)))
    box.add_widget(mk_lbl(alarm.get(\'label\',\'Alarm\'),16,\'txt\',bold=True,align=\'center\',size_hint_y=None,height=dp(30)))
    box.add_widget(mk_lbl(f\'Waktu: {alarm.get("waktu","")}\',14,\'blue\',align=\'center\',size_hint_y=None,height=dp(26)))
    tipe=\'Rekaman suara\' if alarm.get(\'tipe_audio\')==\'rekam\' else \'File audio\'
    box.add_widget(mk_lbl(tipe,11,\'txt2\',align=\'center\',size_hint_y=None,height=dp(20)))
    path=alarm.get(\'audio_path\',\'\')
    if not path or not os.path.exists(path):
        if os.path.exists(AZAN_AUDIO): path=AZAN_AUDIO
        else: path=\'\'
    box.add_widget(Widget(size_hint_y=1))
    pop=Popup(title=\'\',content=box,separator_height=0,background=\'\',
              background_color=(0,0,0,.75),size_hint=(.84,.44),auto_dismiss=False)
    sound=None
    if path:
        try:
            from kivy.core.audio import SoundLoader
            sound=SoundLoader.load(path)
            if sound: sound.loop=True; sound.play()
        except Exception as e: print(f"[ring] {e}")
    pop.bind(on_dismiss=lambda *a: sound.stop() if sound else None)
    b=MBtn(text=\'Matikan Alarm\',style=\'success\',font_size=dp(14),size_hint_y=None,height=dp(46))
    b.bind(on_press=lambda *a: pop.dismiss()); box.add_widget(b); pop.open()


class BerandaScreen(BaseScreen):
    _NAV_KEY=\'beranda\'
    def __init__(self,**kw):
        super().__init__(name=\'beranda\',**kw)
        self._sr=False; self._pet_greeted=False
        self._fl=FloatLayout()
        self._main=BoxLayout(orientation=\'vertical\',padding=[dp(20),dp(20),dp(20),dp(10)],spacing=dp(13))
        self._fl.add_widget(self._main)
        self.toast=mk_lbl(\'\',13,align=\'center\',size_hint=(None,None),size=(dp(290),dp(42)),pos_hint={\'center_x\':.5,\'y\':.04})
        self.toast.color=(*p(\'green\')[:3],0); self._fl.add_widget(self.toast)
        self.pet=BoxLayout(orientation=\'vertical\',size_hint=(None,None),size=(dp(80),dp(100)),pos_hint={\'x\':.02,\'y\':.02})
        with self.pet.canvas.before:
            Color(0,0,0,0); self._pet_bg_rect=Rectangle(pos=self.pet.pos,size=self.pet.size)
        self.pet.bind(pos=lambda *a:setattr(self._pet_bg_rect,\'pos\',self.pet.pos),
                      size=lambda *a:setattr(self._pet_bg_rect,\'size\',self.pet.size))
        self.pet_img=Image(source=\'normal.png\',allow_stretch=True)
        self.pet.add_widget(self.pet_img); self.pet.bind(on_touch_down=self._pet_touched)
        self._fl.add_widget(self.pet)
        self.pet_bubble=mk_lbl(\'\',12,\'txt\',align=\'center\',size_hint=(None,None),size=(dp(120),dp(30)))
        def update_bubble(*args): self.pet_bubble.pos=(self.pet.x-dp(20),self.pet.top+dp(4))
        self.pet.bind(pos=update_bubble,size=update_bubble); update_bubble()
        self._fl.add_widget(self.pet_bubble); self._set_content(self._fl); self._build_main()

    def _pet_touched(self,instance,touch):
        if self.pet.collide_point(*touch.pos): pet_say(random.choice(PET_MESSAGES)); return True
        return False

    def _build_main(self):
        m=self._main
        hdr=BoxLayout(size_hint_y=None,height=dp(58))
        tb=BoxLayout(orientation=\'vertical\',spacing=dp(3))
        self.lbl_time=mk_lbl(datetime.now().strftime(\'%H:%M:%S\'),22,bold=True,size_hint_y=None,height=dp(32))
        tb.add_widget(self.lbl_time)
        self.lbl_dt=mk_lbl(datetime.now().strftime(\'%A, %d %B %Y\'),11,\'txt2\',size_hint_y=None,height=dp(18))
        tb.add_widget(self.lbl_dt); hdr.add_widget(tb); m.add_widget(hdr)
        stats=BoxLayout(size_hint_y=None,height=dp(76),spacing=dp(10))
        def mk_stat(v,lb,col):
            bx=BoxLayout(orientation=\'vertical\',padding=[dp(10),dp(8)],spacing=dp(2)); draw_bg(bx,\'card\',12)
            n=Label(text=v,font_size=dp(24),bold=True,color=p(col),size_hint_y=None,height=dp(32))
            t=Label(text=lb,font_size=dp(10),color=p(\'txt2\'),size_hint_y=None,height=dp(16))
            bx.add_widget(n); bx.add_widget(t); stats.add_widget(bx); return n
        self._n_hari=mk_stat(\'0\',\'Hari Ini\',\'blue\')
        self._n_alarm=mk_stat(\'0\',\'Alarm Aktif\',\'orange\')
        Clock.schedule_interval(self._update_clock,1)
        self._n_total=mk_stat(\'0\',\'Total Jadwal\',\'purple\')
        m.add_widget(stats)
        inp=BoxLayout(orientation=\'vertical\',size_hint_y=None,height=dp(168),padding=[dp(14),dp(12)],spacing=dp(8))
        draw_bg(inp,\'card\',14)
        inp.add_widget(mk_lbl(\'Ketik perintah jadwal\',13,\'blue\',bold=True,size_hint_y=None,height=dp(22)))
        inp.add_widget(mk_lbl(\'Contoh: "Rapat besok jam 2 siang di kantor"\',11,\'txt2\',size_hint_y=None,height=dp(18)))
        self.txt=mk_input(hint_text=\'Masukkan jadwal di sini...\')
        self.txt.bind(on_text_validate=self._tambah); inp.add_widget(self.txt)
        brow=BoxLayout(size_hint_y=None,height=dp(42),spacing=dp(10))
        try:
            import speech_recognition; self._sr=True
            bs=MBtn(text=\'Suara\',style=\'success\',size_hint_x=None,width=dp(80),font_size=dp(12))
            bs.bind(on_press=self._voice); brow.add_widget(bs)
        except ImportError: pass
        bm=MBtn(text=\'Manual\',style=\'neutral\',size_hint_x=None,width=dp(80),font_size=dp(12))
        bm.bind(on_press=lambda *a: TambahJadwalPopup(on_save=self._manual_added).open()); brow.add_widget(bm)
        bal=MBtn(text=\'+ Alarm\',style=\'orange\',size_hint_x=None,width=dp(80),font_size=dp(12))
        bal.bind(on_press=lambda *a: setattr(self.manager,\'current\',\'alarm\')); brow.add_widget(bal)
        ba=MBtn(text=\'+ Tambah Jadwal\',style=\'primary\',font_size=dp(13))
        ba.bind(on_press=self._tambah); brow.add_widget(ba); inp.add_widget(brow); m.add_widget(inp)
        m.add_widget(mk_lbl(\'Jadwal Hari Ini\',15,bold=True,size_hint_y=None,height=dp(28)))
        sc=ScrollView()
        self.jlist=BoxLayout(orientation=\'vertical\',size_hint_y=None,spacing=dp(10))
        self.jlist.bind(minimum_height=self.jlist.setter(\'height\')); sc.add_widget(self.jlist); m.add_widget(sc)

    def on_enter(self):
        super().on_enter(); self._refresh()
        ALARM_ENGINE.start(); ALARM_ENGINE.on_ring=show_ring_popup; PRAYER_NOTIFIER.start()

    def _update_clock(self,dt):
        self.lbl_time.text=datetime.now().strftime(\'%H:%M:%S\'); apply_theme(get_time_of_day())

    def _refresh(self):
        if not self._pet_greeted:
            self._pet_greeted=True
            pet_say(\'Hai, selamat datang!\',sticker_override=\'menyapa.gif\')
            Clock.schedule_once(lambda dt: pet_say(\'\',sticker_override=\'normal.png\'),4)
        self.jlist.clear_widgets()
        all_j=load_jadwal(); today=datetime.now().strftime(\'%Y-%m-%d\')
        hari=[j for j in all_j if j.get(\'tanggal\')==today]
        aktif=[a for a in load_alarm() if a.get(\'aktif\',True)]
        self._n_hari.text=str(len(hari)); self._n_alarm.text=str(len(aktif)); self._n_total.text=str(len(all_j))
        if not hari:
            self.jlist.add_widget(Label(text=\'Tidak ada jadwal hari ini\',font_size=dp(13),color=p(\'txt2\'),size_hint_y=None,height=dp(60)))
            pet_say(\'Tidak ada jadwal hari ini, santai ya!\')
        else:
            pet_say(f\'Ada {len(hari)} jadwal hari ini, semangat ya!\')
            for j in sorted(hari,key=lambda x:x.get(\'waktu\',\'00:00\')):
                self.jlist.add_widget(JadwalCard(j,on_delete=self._del))

    def _add_from_text(self,teks,auto_audio=False):
        t=teks.strip()
        if not t: self._toast(\'Isi teks jadwal dulu!\',err=True); return None
        info=parse_jadwal(t)
        if auto_audio or not info.get(\'audio_path\'):
            fav=get_favorite_alarm()
            if fav:
                ap=fav.get(\'audio_path\',\'\'); tp=fav.get(\'tipe_audio\',\'\')
                if ap and not info.get(\'audio_path\'): info[\'audio_path\']=ap; info[\'tipe_audio\']=tp
        info[\'id\']=str(int(time.time()*1000)); info[\'dibuat\']=datetime.now().strftime(\'%Y-%m-%d %H:%M:%S\')
        if info.get(\'audio_path\'):
            aid=str(int(time.time()*1000))
            alarm={\'id\':aid,\'label\':info.get(\'judul\',\'Alarm\'),\'waktu\':info.get(\'waktu\',\'\'),
                   \'tanggal\':info.get(\'tanggal\',\'\'),\'audio_path\':info.get(\'audio_path\',\'\'),
                   \'tipe_audio\':info.get(\'tipe_audio\',\'\'),\'aktif\':True,\'dibuat\':info[\'dibuat\']}
            alist=load_alarm(); alist.append(alarm); from utils.storage import save_alarm; save_alarm(alist)
            info[\'alarm_id\']=aid
        s=load_jadwal(); s.append(info); save_jadwal(s); return info

    def _tambah(self,*a):
        info=self._add_from_text(self.txt.text)
        if not info: return
        self.txt.text=\'\'; self._refresh()
        self._toast(f\'Jadwal "{info["judul"]}" berhasil ditambahkan!\')
        pet_say(\'Jadwal baru ditambahkan!\',sticker_override=\'mengingatkan.gif\')
        Clock.schedule_once(lambda dt: pet_say(\'\',sticker_override=random.choice([\'berpikir.gif\',\'kagum.gif\',\'marah.gif\'])),2)

    def _manual_added(self,info):
        info[\'id\']=str(int(time.time()*1000)); info[\'dibuat\']=datetime.now().strftime(\'%Y-%m-%d %H:%M:%S\')
        s=load_jadwal(); s.append(info); save_jadwal(s); self._refresh()
        pet_say(\'Jadwal telah disimpan.\',sticker_override=\'mengingatkan.gif\')
        Clock.schedule_once(lambda dt: pet_say(\'\',sticker_override=random.choice([\'berpikir.gif\',\'kagum.gif\',\'marah.gif\'])),2)
        self._toast(f\'Jadwal "{info["judul"]}" berhasil ditambahkan!\')

    def _voice(self,*a):
        if not self._sr: self._toast(\'Speech Recognition tidak tersedia\',err=True); return
        self._toast(\'Mendengarkan...\'); threading.Thread(target=self._do_voice,daemon=True).start()

    def _do_voice(self):
        try:
            import speech_recognition as sr
            r=sr.Recognizer()
            with sr.Microphone() as src: r.adjust_for_ambient_noise(src,.5); audio=r.listen(src,timeout=5)
            t=r.recognize_google(audio,language=\'id-ID\')
            def _apply(dt):
                self.txt.text=t; info=self._add_from_text(t,auto_audio=True)
                if info:
                    self._refresh(); self._toast(f\'Jadwal "{info["judul"]}" ditambahkan via suara!\')
                    pet_say(\'Jadwal sudah kucatat dari suaramu.\',sticker_override=\'mengingatkan.gif\')
                    Clock.schedule_once(lambda dt: pet_say(\'\',sticker_override=random.choice([\'berpikir.gif\',\'kagum.gif\',\'marah.gif\'])),2)
            Clock.schedule_once(_apply,0)
        except Exception as e: Clock.schedule_once(lambda dt: self._toast(str(e)[:40],err=True))

    def _del(self,j):
        save_jadwal([x for x in load_jadwal() if x.get(\'id\')!=j.get(\'id\')]); self._refresh(); self._toast(\'Jadwal dihapus\')

    def _toast(self,msg,err=False,dur=2.8):
        c=p(\'red\') if err else p(\'green\')
        self.toast.text=msg
        a=Animation(color=(*c[:3],1),duration=.2)+Animation(color=(*c[:3],1),duration=dur-.4)+Animation(color=(*c[:3],0),duration=.2)
        a.start(self.toast)
'''

FILES['screens/jadwal.py'] = '''\
"""screens/jadwal.py - Layar daftar semua jadwal dengan filter dan pencarian."""
from datetime import datetime, timedelta
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.metrics import dp
from screens.base import BaseScreen
from widgets.common import mk_lbl, mk_input, MBtn
from widgets.jadwal_card import JadwalCard
from widgets.popups import TambahJadwalPopup
from utils.storage import load_jadwal, save_jadwal, load_alarm, save_alarm
from utils.theme import p

class JadwalScreen(BaseScreen):
    _NAV_KEY=\'jadwal\'
    def __init__(self,**kw):
        super().__init__(name=\'jadwal\',**kw); self._f=\'semua\'; self._build_content()

    def _build_content(self):
        main=BoxLayout(orientation=\'vertical\',padding=[dp(20),dp(20),dp(20),dp(10)],spacing=dp(12))
        hdr=BoxLayout(size_hint_y=None,height=dp(50),spacing=dp(8))
        back=MBtn(text=\'Kembali\',style=\'neutral\',size_hint_x=None,width=dp(100),font_size=dp(13))
        back.bind(on_press=lambda *a: setattr(self.manager,\'current\',\'beranda\')); hdr.add_widget(back)
        hdr.add_widget(mk_lbl(\'Semua Jadwal\',20,bold=True,size_hint_y=None,height=dp(36))); main.add_widget(hdr)
        tabs=BoxLayout(size_hint_y=None,height=dp(36),spacing=dp(8)); self.fb={}
        for k,lb in [(\'semua\',\'Semua\'),(\'hari_ini\',\'Hari Ini\'),(\'minggu\',\'Minggu\'),(\'tinggi\',\'Penting\')]:
            b=Button(text=lb,font_size=dp(11),background_normal=\'\',
                     background_color=p(\'blue2\') if k==\'semua\' else p(\'card2\'),color=p(\'txt\'),bold=(k==\'semua\'))
            b.bind(on_press=lambda x,kk=k: self._sf(kk)); self.fb[k]=b; tabs.add_widget(b)
        main.add_widget(tabs)
        self.ts=mk_input(hint_text=\'Cari jadwal...\',background_color=p(\'card\'))
        self.ts.bind(text=lambda *a: self._refresh()); main.add_widget(self.ts)
        sc=ScrollView()
        self.lb2=BoxLayout(orientation=\'vertical\',size_hint_y=None,spacing=dp(10),padding=[0,dp(4)])
        self.lb2.bind(minimum_height=self.lb2.setter(\'height\')); sc.add_widget(self.lb2); main.add_widget(sc)
        self._set_content(main)

    def on_enter(self): super().on_enter(); self._refresh()

    def _sf(self,k):
        self._f=k
        for kk,b in self.fb.items(): b.background_color=p(\'blue2\') if kk==k else p(\'card2\'); b.bold=(kk==k)
        self._refresh()

    def _refresh(self):
        self.lb2.clear_widgets(); all_j=load_jadwal(); q=self.ts.text.lower().strip()
        today=datetime.now().strftime(\'%Y-%m-%d\'); f=all_j
        if self._f==\'hari_ini\': f=[j for j in all_j if j.get(\'tanggal\')==today]
        elif self._f==\'minggu\':
            tn=datetime.now(); st=tn-timedelta(days=tn.weekday()); en=st+timedelta(6)
            f=[j for j in all_j if self._rng(j.get(\'tanggal\',\'\'),st.date(),en.date())]
        elif self._f==\'tinggi\': f=[j for j in all_j if j.get(\'prioritas\')==\'tinggi\']
        if q: f=[j for j in f if q in (j.get(\'judul\',\'\')+j.get(\'catatan\',\'\')).lower()]
        f=sorted(f,key=lambda x:(x.get(\'tanggal\',\'9999\'),x.get(\'waktu\',\'99:99\')))
        if not f:
            self.lb2.add_widget(Label(text=\'Tidak ada jadwal ditemukan\',font_size=dp(13),color=p(\'txt2\'),size_hint_y=None,height=dp(70)))
        else:
            for j in f: self.lb2.add_widget(JadwalCard(j,on_delete=self._del,on_edit=self._edit))

    def _rng(self,s,st,en):
        try: d=datetime.strptime(s,\'%Y-%m-%d\').date(); return st<=d<=en
        except: return False

    def _del(self,j):
        aid=j.get(\'alarm_id\')
        if aid:
            al=load_alarm(); al=[a for a in al if a.get(\'id\')!=aid]; save_alarm(al)
        save_jadwal([x for x in load_jadwal() if x.get(\'id\')!=j.get(\'id\')]); self._refresh()

    def _edit(self,j):
        def _save_cb(info):
            info[\'id\']=j.get(\'id\'); info[\'dibuat\']=j.get(\'dibuat\')
            lst=load_jadwal()
            for idx,x in enumerate(lst):
                if x.get(\'id\')==j.get(\'id\'): lst[idx]=info; break
            save_jadwal(lst); self._refresh()
        p2=TambahJadwalPopup(on_save=_save_cb,jadwal=j); p2.title=\'Ubah Jadwal\'; p2.open()
'''

FILES['screens/kalender.py'] = '''\
"""screens/kalender.py - Layar kalender bulanan."""
import calendar as _calendar
from datetime import datetime
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.widget import Widget
from kivy.metrics import dp
from screens.base import BaseScreen
from widgets.common import mk_lbl, MBtn
from widgets.jadwal_card import JadwalCard
from widgets.popups import TambahJadwalPopup
from utils.storage import load_jadwal, save_jadwal, load_alarm, save_alarm
from utils.theme import p

class KalenderScreen(BaseScreen):
    _NAV_KEY=\'kalender\'
    def __init__(self,**kw): super().__init__(name=\'kalender\',**kw); self._build_content()

    def _build_content(self):
        main=BoxLayout(orientation=\'vertical\',padding=[dp(20),dp(20),dp(20),dp(10)],spacing=dp(12))
        hdr=BoxLayout(size_hint_y=None,height=dp(50),spacing=dp(8))
        back=MBtn(text=\'Kembali\',style=\'neutral\',size_hint_x=None,width=dp(100),font_size=dp(13))
        back.bind(on_press=lambda *a: setattr(self.manager,\'current\',\'beranda\')); hdr.add_widget(back)
        hdr.add_widget(mk_lbl(\'Kalender\',20,bold=True,size_hint_y=None,height=dp(36))); main.add_widget(hdr)
        self.cal_grid=BoxLayout(orientation=\'vertical\',spacing=dp(2)); main.add_widget(self.cal_grid)
        self._show_month(datetime.now().year,datetime.now().month)
        self.detail_box=BoxLayout(orientation=\'vertical\',size_hint_y=None)
        self.detail_box.bind(minimum_height=self.detail_box.setter(\'height\'))
        sc=ScrollView(); sc.add_widget(self.detail_box); main.add_widget(sc); self._set_content(main)

    def _show_month(self,year,month):
        self.cal_grid.clear_widgets()
        names=[\'Min\',\'Sen\',\'Sel\',\'Rab\',\'Kam\',\'Jum\',\'Sab\']
        row=BoxLayout(size_hint_y=None,height=dp(24))
        for n in names: row.add_widget(mk_lbl(n,11,\'txt2\',size_hint_x=1,align=\'center\'))
        self.cal_grid.add_widget(row)
        for week in _calendar.Calendar().monthdayscalendar(year,month):
            row=BoxLayout(size_hint_y=None,height=dp(32))
            for d in week:
                if d==0: row.add_widget(Widget())
                else:
                    btn=Button(text=str(d),font_size=dp(12),background_normal=\'\',background_color=p(\'card2\'),color=p(\'txt\'),size_hint_x=1)
                    ds=f"{year}-{month:02d}-{d:02d}"; btn.bind(on_press=lambda x,s=ds: self._show_day(s)); row.add_widget(btn)
            self.cal_grid.add_widget(row)

    def _show_day(self,date_str):
        self.detail_box.clear_widgets()
        f=[j for j in load_jadwal() if j.get(\'tanggal\')==date_str]
        if not f:
            self.detail_box.add_widget(Label(text=\'Tidak ada jadwal untuk \'+date_str,font_size=dp(13),color=p(\'txt2\'),size_hint_y=None,height=dp(70)))
        else:
            for j in f: self.detail_box.add_widget(JadwalCard(j,on_delete=self._del,on_edit=self._edit))

    def _del(self,j):
        aid=j.get(\'alarm_id\')
        if aid:
            al=load_alarm(); al=[a for a in al if a.get(\'id\')!=aid]; save_alarm(al)
        save_jadwal([x for x in load_jadwal() if x.get(\'id\')!=j.get(\'id\')]); self._show_day(j.get(\'tanggal\',\'\'))

    def _edit(self,j):
        def _save_cb(info):
            info[\'id\']=j.get(\'id\'); info[\'dibuat\']=j.get(\'dibuat\')
            lst=load_jadwal()
            for idx,x in enumerate(lst):
                if x.get(\'id\')==j.get(\'id\'): lst[idx]=info; break
            save_jadwal(lst); self._show_day(info.get(\'tanggal\',\'\'))
        p2=TambahJadwalPopup(on_save=_save_cb,jadwal=j); p2.title=\'Ubah Jadwal\'; p2.open()
'''

FILES['screens/alarm.py'] = '''\
"""screens/alarm.py - Layar manajemen alarm."""
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.label import Label
from kivy.metrics import dp
from screens.base import BaseScreen
from widgets.common import mk_lbl, MBtn, draw_bg
from widgets.alarm_card import AlarmCard
from widgets.popups import TambahAlarmPopup
from utils.storage import load_alarm, save_alarm, fill_empty_jadwals_with_favorite
from utils.audio import ALARM_ENGINE, play_audio
from utils.theme import p

def show_ring_popup(alarm):
    from screens.beranda import show_ring_popup as srp
    srp(alarm)

class AlarmScreen(BaseScreen):
    _NAV_KEY=\'alarm\'
    def __init__(self,**kw): super().__init__(name=\'alarm\',**kw); self._build_content()

    def _build_content(self):
        main=BoxLayout(orientation=\'vertical\',padding=[dp(20),dp(20),dp(20),dp(10)],spacing=dp(12))
        hdr=BoxLayout(size_hint_y=None,height=dp(50),spacing=dp(10))
        back=MBtn(text=\'Kembali\',style=\'neutral\',size_hint_x=None,width=dp(100),font_size=dp(13))
        back.bind(on_press=lambda *a: setattr(self.manager,\'current\',\'beranda\')); hdr.add_widget(back)
        hdr.add_widget(mk_lbl(\'Alarm\',20,bold=True,size_hint_x=1))
        b_add=MBtn(text=\'+ Tambah Alarm\',style=\'primary\',font_size=dp(13),size_hint=(None,1),width=dp(140))
        b_add.bind(on_press=lambda *a: TambahAlarmPopup(on_save=lambda al: self._refresh()).open()); hdr.add_widget(b_add); main.add_widget(hdr)
        info=BoxLayout(size_hint_y=None,height=dp(66),spacing=dp(10))
        for ttl,sub,col in [(\'Dari File\',\'Pilih WAV / MP3 / OGG\',\'blue\'),(\'Rekam Suara\',\'Rekam suaramu sendiri\',\'orange\')]:
            bx=BoxLayout(orientation=\'vertical\',padding=[dp(12),dp(8)],spacing=dp(2)); draw_bg(bx,\'card\',10)
            bx.add_widget(mk_lbl(ttl,13,col,bold=True,align=\'center\',size_hint_y=None,height=dp(24)))
            bx.add_widget(mk_lbl(sub,11,\'txt2\',align=\'center\',size_hint_y=None,height=dp(18))); info.add_widget(bx)
        main.add_widget(info)
        sc=ScrollView()
        self.albox=BoxLayout(orientation=\'vertical\',size_hint_y=None,spacing=dp(10),padding=[0,dp(4)])
        self.albox.bind(minimum_height=self.albox.setter(\'height\')); sc.add_widget(self.albox); main.add_widget(sc); self._set_content(main)

    def on_enter(self): super().on_enter(); self._refresh(); ALARM_ENGINE.on_ring=show_ring_popup

    def _refresh(self):
        self.albox.clear_widgets(); alarms=load_alarm()
        if not alarms:
            self.albox.add_widget(Label(text=\'Belum ada alarm\nTekan + Tambah Alarm\',font_size=dp(13),color=p(\'txt2\'),size_hint_y=None,height=dp(100),halign=\'center\'))
        else:
            for a in sorted(alarms,key=lambda x:x.get(\'waktu\',\'\')):
                self.albox.add_widget(AlarmCard(a,on_delete=self._del,on_toggle=self._tog,on_play=play_audio,on_fav=self._fav))

    def _del(self,a):
        save_alarm([x for x in load_alarm() if x.get(\'id\')!=a.get(\'id\')]); self._refresh()

    def _tog(self,a):
        s=load_alarm()
        for x in s:
            if x.get(\'id\')==a.get(\'id\'): x[\'aktif\']=not x.get(\'aktif\',True)
        save_alarm(s); self._refresh()

    def _fav(self,a):
        s=load_alarm()
        for x in s: x[\'favorite\']=(x.get(\'id\')==a.get(\'id\'))
        save_alarm(s); self._refresh(); fill_empty_jadwals_with_favorite()
'''

FILES['widgets/popups.py'] = '''\
"""widgets/popups.py - Semua popup: TambahJadwalPopup, TambahAlarmPopup, TimePicker, DatePicker."""
import os, time, re
from datetime import datetime
from kivy.uix.popup import Popup
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.widget import Widget
from kivy.uix.filechooser import FileChooserListView
from kivy.uix.progressbar import ProgressBar
from kivy.uix.spinner import Spinner
from kivy.metrics import dp
from widgets.common import mk_lbl, mk_input, MBtn, draw_bg
from utils.theme import p, PAL
from utils.audio import DIR_AUDIO, AZAN_AUDIO, record_audio, play_audio
from utils.storage import load_alarm, save_alarm, get_favorite_alarm


class TimePickerPopup(Popup):
    def __init__(self, initial=\'00:00\', on_select=None, **kw):
        super().__init__(title=\'Pilih Waktu\',size_hint=(.8,.4),**kw)
        self.on_select=on_select; hh,mm=initial.split(\':\') if \':\' in initial else (\'00\',\'00\')
        layout=BoxLayout(orientation=\'vertical\',spacing=dp(8),padding=dp(12))
        row=BoxLayout(spacing=dp(8))
        self.sp_h=Spinner(text=hh.zfill(2),values=[f"{i:02d}" for i in range(24)],size_hint_x=None,width=dp(60))
        self.sp_m=Spinner(text=mm.zfill(2),values=[f"{i:02d}" for i in range(60)],size_hint_x=None,width=dp(60))
        from kivy.uix.label import Label
        row.add_widget(self.sp_h); row.add_widget(Label(text=\':\',size_hint_x=None,width=dp(10))); row.add_widget(self.sp_m)
        layout.add_widget(row)
        btn=MBtn(text=\'OK\',style=\'primary\',size_hint_y=None,height=dp(40)); btn.bind(on_press=self._ok); layout.add_widget(btn); self.content=layout

    def _ok(self,*a):
        if self.on_select: self.on_select(f"{self.sp_h.text}:{self.sp_m.text}")
        self.dismiss()


class DatePickerPopup(Popup):
    def __init__(self, initial=None, on_select=None, **kw):
        super().__init__(title=\'Pilih Tanggal\',size_hint=(.9,.6),**kw)
        self.on_select=on_select; today=datetime.now()
        if initial:
            try: today=datetime.strptime(initial,\'%Y-%m-%d\')
            except: pass
        layout=BoxLayout(orientation=\'vertical\',spacing=dp(8),padding=dp(12))
        row1=BoxLayout(spacing=dp(8))
        self.sp_y=Spinner(text=str(today.year),values=[str(y) for y in range(today.year-5,today.year+6)],size_hint_x=None,width=dp(80))
        self.sp_m=Spinner(text=str(today.month).zfill(2),values=[str(m).zfill(2) for m in range(1,13)],size_hint_x=None,width=dp(60))
        self.sp_d=Spinner(text=str(today.day).zfill(2),values=[str(d).zfill(2) for d in range(1,32)],size_hint_x=None,width=dp(60))
        row1.add_widget(self.sp_y); row1.add_widget(self.sp_m); row1.add_widget(self.sp_d); layout.add_widget(row1)
        btn=MBtn(text=\'OK\',style=\'primary\',size_hint_y=None,height=dp(40)); btn.bind(on_press=self._ok); layout.add_widget(btn); self.content=layout

    def _ok(self,*a):
        if self.on_select: self.on_select(f"{self.sp_y.text}-{self.sp_m.text}-{self.sp_d.text}")
        self.dismiss()


class TambahAlarmPopup(Popup):
    def __init__(self, on_save=None, **kw):
        super().__init__(title=\'\',separator_height=0,background=\'\',background_color=(0,0,0,0),size_hint=(.93,.9),**kw)
        self._on_save=on_save; self._fp=None; self._rp=None; self._rec_busy=False; self._build()

    def _build(self):
        root=BoxLayout(orientation=\'vertical\',spacing=dp(10),padding=[dp(18),dp(18)]); draw_bg(root,\'card\',16)
        hdr=BoxLayout(size_hint_y=None,height=dp(40))
        hdr.add_widget(mk_lbl(\'Tambah Alarm Baru\',17,bold=True,size_hint_x=1))
        bx=Button(text=\'X\',size_hint=(None,1),width=dp(34),font_size=dp(16),background_normal=\'\',background_color=(0,0,0,0),color=p(\'txt2\'))
        bx.bind(on_press=lambda *a: self.dismiss()); hdr.add_widget(bx); root.add_widget(hdr)
        root.add_widget(mk_lbl(\'Sumber Suara Alarm\',11,\'txt2\',size_hint_y=None,height=dp(16)))
        self.lbl_fp=mk_lbl(\'Belum ada file dipilih\',11,\'txt2\',size_hint_y=None,height=dp(18))
        root.add_widget(self.lbl_fp)
        b_fc=MBtn(text=\'Pilih File Audio (WAV/MP3/OGG)\',style=\'neutral\',font_size=dp(12),size_hint_y=None,height=dp(42))
        b_fc.bind(on_press=self._open_fc); root.add_widget(b_fc)
        self.lbl_rek=mk_lbl(\'Tekan tombol untuk merekam (5 detik)\',11,\'txt2\',size_hint_y=None,height=dp(18)); root.add_widget(self.lbl_rek)
        self.pb=ProgressBar(max=100,value=0,size_hint_y=None,height=dp(8)); root.add_widget(self.pb)
        brow=BoxLayout(size_hint_y=None,height=dp(42),spacing=dp(10))
        self.b_rec=MBtn(text=\'Mulai Rekam\',style=\'orange\',font_size=dp(13))
        self.b_prev=MBtn(text=\'Putar\',style=\'neutral\',font_size=dp(13),size_hint_x=None,width=dp(84)); self.b_prev.disabled=True
        self.b_rec.bind(on_press=self._do_rec); self.b_prev.bind(on_press=lambda *a: self._rp and os.path.exists(self._rp) and play_audio(self._rp))
        brow.add_widget(self.b_rec); brow.add_widget(self.b_prev); root.add_widget(brow)
        self.lbl_err=mk_lbl(\'\',11,\'txt2\',size_hint_y=None,height=dp(18)); root.add_widget(self.lbl_err)
        root.add_widget(Widget(size_hint_y=1))
        bs=MBtn(text=\'Simpan Alarm\',style=\'success\',font_size=dp(14),size_hint_y=None,height=dp(48)); bs.bind(on_press=self._simpan); root.add_widget(bs); self.content=root

    def _open_fc(self,*a):
        lay=BoxLayout(orientation=\'vertical\',spacing=dp(8),padding=dp(10))
        fc=FileChooserListView(path=os.path.expanduser(\'~\'),filters=[\'*.wav\',\'*.mp3\',\'*.ogg\',\'*.WAV\',\'*.MP3\',\'*.OGG\']); lay.add_widget(fc)
        br=BoxLayout(size_hint_y=None,height=dp(44),spacing=dp(10))
        bb=MBtn(text=\'Batal\',style=\'neutral\',font_size=dp(13)); bp=MBtn(text=\'Pilih\',style=\'success\',font_size=dp(13))
        br.add_widget(bb); br.add_widget(bp); lay.add_widget(br)
        pop=Popup(title=\'Pilih File Audio\',content=lay,size_hint=(.95,.85),background=\'\',background_color=(0,0,0,.8),separator_height=1)
        def _ok(*a):
            if fc.selection: self._fp=fc.selection[0]; self.lbl_fp.text=f\'Terpilih: {os.path.basename(self._fp)}\'; self.lbl_fp.color=p(\'green\')
            pop.dismiss()
        bb.bind(on_press=lambda *a: pop.dismiss()); bp.bind(on_press=_ok); pop.open()

    def _do_rec(self,*a):
        if self._rec_busy: return
        self._rec_busy=True; self.b_rec.text=\'Merekam...\'; self.b_rec.background_color=p(\'red\')
        self.pb.value=0; self.b_prev.disabled=True; self.lbl_rek.text=\'Sedang merekam!\'; self.lbl_rek.color=p(\'red\')
        out=os.path.join(DIR_AUDIO,f\'rekaman_{int(time.time())}.wav\')
        record_audio(out,secs=5,cb_done=self._rec_done,cb_prog=lambda pct: setattr(self.pb,\'value\',pct))

    def _rec_done(self,ok,res):
        self._rec_busy=False; self.b_rec.background_color=p(\'orange\'); self.pb.value=100
        if ok: self._rp=res; self.b_rec.text=\'Rekam Ulang\'; self.b_prev.disabled=False; self.lbl_rek.text=f\'Tersimpan: {os.path.basename(res)}\'; self.lbl_rek.color=p(\'green\')
        else: self.b_rec.text=\'Mulai Rekam\'; self.lbl_rek.text=f\'Gagal: {res[:50]}\'; self.lbl_rek.color=p(\'red\')

    def _simpan(self,*a):
        apath=(self._fp or self._rp) or \'\'
        if not apath:
            if os.path.exists(AZAN_AUDIO): apath=AZAN_AUDIO
            else: self.lbl_err.text=\'Tidak ada audio dipilih dan file azan tidak ditemukan.\'; self.lbl_err.color=p(\'yellow\')
        tipe=\'file\' if self._fp else (\'rekam\' if self._rp else \'\')
        alarm={\'id\':str(int(time.time()*1000)),\'label\':\'Alarm\',\'waktu\':\'\',\'tanggal\':\'\',
               \'audio_path\':apath,\'tipe_audio\':tipe,\'aktif\':True,\'dibuat\':datetime.now().strftime(\'%Y-%m-%d %H:%M:%S\')}
        s=load_alarm(); s.append(alarm); save_alarm(s); self.dismiss()
        if self._on_save: self._on_save(alarm)


class TambahJadwalPopup(Popup):
    def __init__(self, on_save=None, jadwal=None, **kw):
        super().__init__(title=\'\',separator_height=0,background=\'\',background_color=(0,0,0,0),size_hint=(.93,.8),**kw)
        self._on_save=on_save; self._init_jadwal=jadwal or {}; self._fp=None; self._rp=None; self._rec_busy=False; self._build()
        if self._init_jadwal:
            self.inp_judul.text=self._init_jadwal.get(\'judul\',\'\')
            self.wkt_btn.text=self._init_jadwal.get(\'waktu\',self.wkt_btn.text)
            self.tgl_btn.text=self._init_jadwal.get(\'tanggal\',self.tgl_btn.text)

    def _build(self):
        root=BoxLayout(orientation=\'vertical\',spacing=dp(8),padding=dp(18)); draw_bg(root,\'card\',16)
        hdr=BoxLayout(size_hint_y=None,height=dp(40))
        hdr.add_widget(mk_lbl(\'Tambah Jadwal Manual\',17,bold=True,size_hint_x=1))
        bx=Button(text=\'X\',size_hint=(None,1),width=dp(34),font_size=dp(16),background_normal=\'\',background_color=(0,0,0,0),color=p(\'txt2\'))
        bx.bind(on_press=lambda *a: self.dismiss()); hdr.add_widget(bx); root.add_widget(hdr)
        root.add_widget(mk_lbl(\'Judul\',11,\'txt2\',size_hint_y=None,height=dp(16)))
        self.inp_judul=mk_input(hint_text=\'Judul kegiatan\'); root.add_widget(self.inp_judul)
        root.add_widget(mk_lbl(\'Waktu\',11,\'txt2\',size_hint_y=None,height=dp(16)))
        self.wkt_btn=MBtn(text=datetime.now().strftime(\'%H:%M\'),style=\'neutral\',size_hint_y=None,height=dp(44))
        self.wkt_btn.bind(on_press=lambda *a: TimePickerPopup(initial=self.wkt_btn.text,on_select=lambda t: setattr(self.wkt_btn,\'text\',t)).open()); root.add_widget(self.wkt_btn)
        root.add_widget(mk_lbl(\'Tanggal\',11,\'txt2\',size_hint_y=None,height=dp(16)))
        self.tgl_btn=MBtn(text=datetime.now().strftime(\'%Y-%m-%d\'),style=\'neutral\',size_hint_y=None,height=dp(44))
        self.tgl_btn.bind(on_press=lambda *a: DatePickerPopup(initial=self.tgl_btn.text,on_select=lambda d: setattr(self.tgl_btn,\'text\',d)).open()); root.add_widget(self.tgl_btn)
        root.add_widget(mk_lbl(\'Audio Alarm (opsional)\',11,\'txt2\',size_hint_y=None,height=dp(16)))
        self.lbl_fp=mk_lbl(\'Belum ada file dipilih\',11,\'txt2\',size_hint_y=None,height=dp(18)); root.add_widget(self.lbl_fp)
        b_fc=MBtn(text=\'Pilih File Audio\',style=\'neutral\',font_size=dp(12),size_hint_y=None,height=dp(42)); b_fc.bind(on_press=self._open_fc); root.add_widget(b_fc)
        self.lbl_rek=mk_lbl(\'Rekam suara sendiri (5 detik)\',11,\'txt2\',size_hint_y=None,height=dp(18)); root.add_widget(self.lbl_rek)
        self.pb=ProgressBar(max=100,value=0,size_hint_y=None,height=dp(8)); root.add_widget(self.pb)
        brow=BoxLayout(size_hint_y=None,height=dp(42),spacing=dp(10))
        self.b_rec=MBtn(text=\'Mulai Rekam\',style=\'orange\',font_size=dp(13))
        self.b_prev=MBtn(text=\'Putar\',style=\'neutral\',font_size=dp(13),size_hint_x=None,width=dp(84)); self.b_prev.disabled=True
        self.b_rec.bind(on_press=self._do_rec); self.b_prev.bind(on_press=lambda *a: self._rp and os.path.exists(self._rp) and play_audio(self._rp))
        brow.add_widget(self.b_rec); brow.add_widget(self.b_prev); root.add_widget(brow)
        self.lbl_err=mk_lbl(\'\',11,\'txt2\',size_hint_y=None,height=dp(18)); root.add_widget(self.lbl_err)
        root.add_widget(Widget(size_hint_y=1))
        bs=MBtn(text=\'Simpan Jadwal\',style=\'success\',font_size=dp(14),size_hint_y=None,height=dp(48)); bs.bind(on_press=self._simpan); root.add_widget(bs); self.content=root

    def _simpan(self,*a):
        judul=self.inp_judul.text.strip(); waktu=self.wkt_btn.text.strip()
        tanggal=self.tgl_btn.text.strip() or datetime.now().strftime(\'%Y-%m-%d\')
        if not judul: self.lbl_err.text=\'Judul tidak boleh kosong\'; self.lbl_err.color=p(\'red\'); return
        if not re.match(r\'^\d{2}:\d{2}$\',waktu): self.lbl_err.text=\'Format waktu salah (HH:MM)\'; self.lbl_err.color=p(\'red\'); return
        if not re.match(r\'^\d{4}-\d{2}-\d{2}$\',tanggal): self.lbl_err.text=\'Format tanggal salah (YYYY-MM-DD)\'; self.lbl_err.color=p(\'red\'); return
        apath=(self._fp or self._rp) or \'\'
        if not apath and os.path.exists(AZAN_AUDIO): apath=AZAN_AUDIO
        if not apath:
            fav=get_favorite_alarm()
            if fav: apath=fav.get(\'audio_path\',\'\'); tipe=fav.get(\'tipe_audio\',\'\')
            else: tipe=\'\'
        else: tipe=\'file\' if self._fp else (\'rekam\' if self._rp else \'\')
        alarm_id=self._init_jadwal.get(\'alarm_id\') if self._init_jadwal else None
        if not alarm_id: alarm_id=str(int(time.time()*1000))
        alarm={\'id\':alarm_id,\'label\':judul,\'waktu\':waktu,\'tanggal\':tanggal,\'audio_path\':apath,\'tipe_audio\':tipe,\'aktif\':True,\'dibuat\':datetime.now().strftime(\'%Y-%m-%d %H:%M:%S\')}
        alist=load_alarm(); alist=[a for a in alist if a.get(\'id\')!=alarm_id]; alist.append(alarm); save_alarm(alist)
        jadwal={\'judul\':judul,\'waktu\':waktu,\'tanggal\':tanggal,\'prioritas\':\'normal\',\'catatan\':\'\',\'audio_path\':apath,\'tipe_audio\':tipe,\'alarm_id\':alarm_id}
        if self._on_save: self._on_save(jadwal)
        self.dismiss()

    def _open_fc(self,*a):
        lay=BoxLayout(orientation=\'vertical\',spacing=dp(8),padding=dp(10))
        fc=FileChooserListView(path=os.path.expanduser(\'~\'),filters=[\'*.wav\',\'*.mp3\',\'*.ogg\',\'*.WAV\',\'*.MP3\',\'*.OGG\']); lay.add_widget(fc)
        br=BoxLayout(size_hint_y=None,height=dp(44),spacing=dp(10))
        bb=MBtn(text=\'Batal\',style=\'neutral\',font_size=dp(13)); bp=MBtn(text=\'Pilih\',style=\'success\',font_size=dp(13))
        br.add_widget(bb); br.add_widget(bp); lay.add_widget(br)
        pop=Popup(title=\'Pilih File Audio\',content=lay,size_hint=(.95,.85),background=\'\',background_color=(0,0,0,.8),separator_height=1)
        def _ok(*a):
            if fc.selection: self._fp=fc.selection[0]; self.lbl_fp.text=f\'Terpilih: {os.path.basename(self._fp)}\'; self.lbl_fp.color=p(\'green\')
            pop.dismiss()
        bb.bind(on_press=lambda *a: pop.dismiss()); bp.bind(on_press=_ok); pop.open()

    def _do_rec(self,*a):
        if self._rec_busy: return
        self._rec_busy=True; self.b_rec.text=\'Merekam...\'; self.b_rec.background_color=p(\'red\')
        self.pb.value=0; self.b_prev.disabled=True; self.lbl_rek.text=\'Sedang merekam!\'; self.lbl_rek.color=p(\'red\')
        out=os.path.join(DIR_AUDIO,f\'rekaman_{int(time.time())}.wav\')
        record_audio(out,secs=5,cb_done=self._rec_done,cb_prog=lambda pct: setattr(self.pb,\'value\',pct))

    def _rec_done(self,ok,res):
        self._rec_busy=False; self.b_rec.background_color=p(\'orange\'); self.pb.value=100
        if ok: self._rp=res; self.b_rec.text=\'Rekam Ulang\'; self.b_prev.disabled=False; self.lbl_rek.text=f\'Tersimpan: {os.path.basename(res)}\'; self.lbl_rek.color=p(\'green\')
        else: self.b_rec.text=\'Mulai Rekam\'; self.lbl_rek.text=f\'Gagal: {res[:50]}\'; self.lbl_rek.color=p(\'red\')
'''

FILES['main.py'] = '''\
"""
main.py - Entry point Aplikasi Asisten Virtual Pengolahan Jadwal + Alarm
Oleh: Jhesen Marlino Ibrahim - 2155201108
Universitas Muhammadiyah Bengkulu
"""
from kivy.app             import App
from kivy.core.window     import Window
from kivy.uix.screenmanager import ScreenManager, FadeTransition
from utils.theme          import p
from utils.audio          import ALARM_ENGINE
from screens.splash       import SplashScreen
from screens.beranda      import BerandaScreen
from screens.jadwal       import JadwalScreen
from screens.kalender     import KalenderScreen
from screens.alarm        import AlarmScreen


class AsistenJadwalApp(App):
    title = \'Asisten Jadwal + Alarm\'

    def build(self):
        Window.clearcolor = p(\'bg\')
        sm = ScreenManager(transition=FadeTransition(duration=0.12))
        sm.add_widget(SplashScreen())
        sm.add_widget(BerandaScreen())
        sm.add_widget(JadwalScreen())
        sm.add_widget(KalenderScreen())
        sm.add_widget(AlarmScreen())
        return sm

    def on_stop(self):
        ALARM_ENGINE.stop()


if __name__ == \'__main__\':
    AsistenJadwalApp().run()
'''

FILES['widgets/__init__.py'] = "# widgets package\n"

# ═══════════════════════════════════════════════════════════════
# Tulis semua file ke disk
# ═══════════════════════════════════════════════════════════════
import os
for rel_path, content in FILES.items():
    os.makedirs(os.path.dirname(rel_path) or '.', exist_ok=True)
    with open(rel_path, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"[OK] {rel_path}")

# ═══════════════════════════════════════════════════════════════
# Buat juga ZIP untuk distribusi mudah
# ═══════════════════════════════════════════════════════════════
with zipfile.ZipFile('asisten_jadwal_modular.zip', 'w', zipfile.ZIP_DEFLATED) as zf:
    for rel_path, content in FILES.items():
        zf.writestr(rel_path, content)

print("\n[SELESAI] Semua file berhasil dibuat!")
print("[SELESAI] ZIP: asisten_jadwal_modular.zip")
print("\nStruktur folder:")
for rel_path in FILES:
    print(f"  {rel_path}")
