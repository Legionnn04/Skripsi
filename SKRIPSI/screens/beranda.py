"""screens/beranda.py - Layar utama (Beranda) dengan input jadwal & jam."""
import os, sys, random, threading, re
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
from kivy.core.window import Window
from screens.base import BaseScreen
from widgets.common import mk_lbl, mk_input, MBtn, draw_bg
from widgets.jadwal_card import JadwalCard
from utils.theme import p, apply_theme, get_time_of_day
from utils.storage import load_jadwal, save_jadwal, load_alarm, save_alarm, get_favorite_alarm, force_sync, _fb_delete
from utils.audio import ALARM_ENGINE, PRAYER_NOTIFIER, play_audio
from utils.nlp import parse_jadwal
from utils.pet import pet_say, PET_MESSAGES
from widgets.popups import TambahJadwalPopup
import time

def _res(filename):
    base = getattr(sys, '_MEIPASS', os.path.abspath('.'))
    full = os.path.join(base, filename)
    return full if os.path.exists(full) else filename

def show_ring_popup(alarm):
    from utils.pet import pet_say
    from utils.audio import AZAN_AUDIO
    from widgets.common import draw_bg, mk_lbl, MBtn
    from kivy.uix.boxlayout import BoxLayout
    from kivy.uix.widget import Widget
    from kivy.uix.popup import Popup
    from kivy.metrics import dp
    pet_say('Waktu alarm!')
    box=BoxLayout(orientation='vertical',spacing=dp(12),padding=dp(22))
    draw_bg(box,'card',14)
    box.add_widget(mk_lbl('ALARM BERBUNYI!',20,'yellow',bold=True,align='center',size_hint_y=None,height=dp(36)))
    box.add_widget(mk_lbl(alarm.get('label','Alarm'),16,'txt',bold=True,align='center',size_hint_y=None,height=dp(30)))
    box.add_widget(mk_lbl(f'Waktu: {alarm.get("waktu","")}',14,'blue',align='center',size_hint_y=None,height=dp(26)))
    tipe='Rekaman suara' if alarm.get('tipe_audio')=='rekam' else 'File audio'
    box.add_widget(mk_lbl(tipe,11,'txt2',align='center',size_hint_y=None,height=dp(20)))
    path=alarm.get('audio_path','')
    if path and not os.path.exists(path): path=_res(path)
    if not path or not os.path.exists(path):
        az=_res(AZAN_AUDIO)
        path=az if os.path.exists(az) else ''
    box.add_widget(Widget(size_hint_y=1))
    pop=Popup(title='',content=box,separator_height=0,background='',
              background_color=(0,0,0,.75),size_hint=(.84,.44),auto_dismiss=False)
    if path:
        try:
            import winsound
            winsound.PlaySound(path, winsound.SND_FILENAME|winsound.SND_LOOP|winsound.SND_ASYNC)
        except Exception as e:
            print(f"[ring] winsound error: {e}")
            try: play_audio(path)
            except: pass
    def _stop_audio(*a):
        try:
            import winsound; winsound.PlaySound(None, winsound.SND_PURGE)
        except: pass
    pop.bind(on_dismiss=_stop_audio)
    b=MBtn(text='Matikan Alarm',style='success',font_size=dp(14),size_hint_y=None,height=dp(46))
    b.bind(on_press=lambda *a: pop.dismiss()); box.add_widget(b); pop.open()


def _sp():
    """Padding adaptif berdasarkan tinggi window."""
    return dp(12) if Window.height < dp(600) else dp(20)

def _sh():
    """Apakah layar kecil (tinggi < 600dp)."""
    return Window.height < dp(600)


class BerandaScreen(BaseScreen):
    _NAV_KEY='beranda'
    def __init__(self,**kw):
        super().__init__(name='beranda',**kw)
        self._sr=False; self._pet_greeted=False
        self._fl=FloatLayout()
        self._main=BoxLayout(orientation='vertical',spacing=dp(10))
        self._fl.add_widget(self._main)
        self.toast=mk_lbl('',13,align='center',size_hint=(None,None),size=(dp(290),dp(42)),pos_hint={'center_x':.5,'y':.04})
        self.toast.color=(*p('green')[:3],0); self._fl.add_widget(self.toast)
        self.pet=BoxLayout(orientation='vertical',size_hint=(None,None),size=(dp(70),dp(90)),pos_hint={'x':.01,'y':.02})
        with self.pet.canvas.before:
            Color(0,0,0,0); self._pet_bg_rect=Rectangle(pos=self.pet.pos,size=self.pet.size)
        self.pet.bind(pos=lambda *a:setattr(self._pet_bg_rect,'pos',self.pet.pos),
                      size=lambda *a:setattr(self._pet_bg_rect,'size',self.pet.size))
        self.pet_img=Image(source=_res('normal.png'),allow_stretch=True)
        self.pet.add_widget(self.pet_img); self.pet.bind(on_touch_down=self._pet_touched)
        self._fl.add_widget(self.pet)
        self.pet_bubble=mk_lbl('',11,'txt',align='center',size_hint=(None,None),size=(dp(110),dp(28)))
        def update_bubble(*args): self.pet_bubble.pos=(self.pet.x-dp(15),self.pet.top+dp(4))
        self.pet.bind(pos=update_bubble,size=update_bubble); update_bubble()
        self._fl.add_widget(self.pet_bubble); self._set_content(self._fl); self._build_main()

    def _pet_touched(self,instance,touch):
        if self.pet.collide_point(*touch.pos): pet_say(random.choice(PET_MESSAGES)); return True
        return False

    def _build_main(self):
        m=self._main
        pad=dp(12)
        m.padding=[pad, pad, pad, dp(6)]

        # ── Header: jam + sync ──
        hdr=BoxLayout(size_hint_y=None,height=dp(52))
        tb=BoxLayout(orientation='vertical',spacing=dp(2))
        self.lbl_time=mk_lbl(datetime.now().strftime('%H:%M:%S'),20,bold=True,size_hint_y=None,height=dp(30))
        tb.add_widget(self.lbl_time)
        self.lbl_dt=mk_lbl(datetime.now().strftime('%A, %d %B %Y'),10,'txt2',size_hint_y=None,height=dp(16))
        tb.add_widget(self.lbl_dt); hdr.add_widget(tb)
        self.btn_sync=MBtn(text='⟳ Sync',style='neutral',size_hint=(None,None),size=(dp(76),dp(34)),font_size=dp(11))
        self.btn_sync.bind(on_press=self._do_sync); hdr.add_widget(self.btn_sync)
        m.add_widget(hdr)
        Clock.schedule_interval(self._update_clock,1)

        # ── Stats ──
        stats=BoxLayout(size_hint_y=None,height=dp(62),spacing=dp(8))
        def mk_stat(v,lb,col):
            bx=BoxLayout(orientation='vertical',padding=[dp(8),dp(6)],spacing=dp(2)); draw_bg(bx,'card',10)
            n=Label(text=v,font_size=dp(20),bold=True,color=p(col),size_hint_y=None,height=dp(28))
            t=Label(text=lb,font_size=dp(9),color=p('txt2'),size_hint_y=None,height=dp(14))
            bx.add_widget(n); bx.add_widget(t); stats.add_widget(bx); return n
        self._n_hari=mk_stat('0','Hari Ini','blue')
        self._n_alarm=mk_stat('0','Alarm Aktif','orange')
        self._n_total=mk_stat('0','Total Jadwal','purple')
        m.add_widget(stats)

        # ── Input box ──
        inp=BoxLayout(orientation='vertical',size_hint_y=None,padding=[dp(12),dp(10)],spacing=dp(6))
        inp.bind(minimum_height=inp.setter('height'))
        draw_bg(inp,'card',12)
        inp.add_widget(mk_lbl('Ketik perintah jadwal',12,'blue',bold=True,size_hint_y=None,height=dp(20)))
        inp.add_widget(mk_lbl('Contoh: "Rapat besok jam 2 siang di kantor"',10,'txt2',size_hint_y=None,height=dp(16)))
        self.txt=mk_input(hint_text='Masukkan jadwal di sini...')
        self.txt.bind(on_text_validate=self._tambah); inp.add_widget(self.txt)
        brow=BoxLayout(size_hint_y=None,height=dp(40),spacing=dp(8))
        try:
            import speech_recognition; self._sr=True
            bs=MBtn(text='Suara',style='success',size_hint_x=None,width=dp(72),font_size=dp(11))
            bs.bind(on_press=self._voice); brow.add_widget(bs)
        except ImportError: pass
        bm=MBtn(text='Manual',style='neutral',size_hint_x=None,width=dp(72),font_size=dp(11))
        bm.bind(on_press=lambda *a: TambahJadwalPopup(on_save=self._manual_added).open()); brow.add_widget(bm)
        bal=MBtn(text='+ Alarm',style='orange',size_hint_x=None,width=dp(72),font_size=dp(11))
        bal.bind(on_press=lambda *a: setattr(self.manager,'current','alarm')); brow.add_widget(bal)
        ba=MBtn(text='+ Jadwal',style='primary',font_size=dp(11))
        ba.bind(on_press=self._tambah); brow.add_widget(ba); inp.add_widget(brow)
        m.add_widget(inp)

        m.add_widget(mk_lbl('Jadwal Hari Ini',14,bold=True,size_hint_y=None,height=dp(26)))
        sc=ScrollView()
        self.jlist=BoxLayout(orientation='vertical',size_hint_y=None,spacing=dp(8))
        self.jlist.bind(minimum_height=self.jlist.setter('height')); sc.add_widget(self.jlist); m.add_widget(sc)

    def on_enter(self):
        super().on_enter(); self._refresh()
        ALARM_ENGINE.start(); ALARM_ENGINE.on_ring=show_ring_popup; PRAYER_NOTIFIER.start()
        from utils.storage import AUTO_SYNC
        AUTO_SYNC.start()

    def _update_clock(self,dt):
        self.lbl_time.text=datetime.now().strftime('%H:%M:%S'); apply_theme(get_time_of_day())

    def _do_sync(self,*a):
        self.btn_sync.text='...'; self.btn_sync.disabled=True
        def _run():
            try: ok,msg=force_sync()
            except: ok=False; msg='Tidak ada koneksi'
            def _done(dt):
                self._refresh()
                self._toast(('✓ '+msg) if ok else '✗ '+msg)
                self.btn_sync.text='⟳ Sync'; self.btn_sync.disabled=False
            Clock.schedule_once(_done,0)
        threading.Thread(target=_run,daemon=True).start()

    def _refresh(self):
        if not self._pet_greeted:
            self._pet_greeted=True
            pet_say('Hai, selamat datang!',sticker_override='menyapa.gif')
            Clock.schedule_once(lambda dt: pet_say('',sticker_override='normal.png'),4)
        self.jlist.clear_widgets()
        all_j=load_jadwal(); today=datetime.now().strftime('%Y-%m-%d')
        hari=[j for j in all_j if j.get('tanggal')==today]
        aktif=[a for a in load_alarm() if a.get('aktif',True)]
        self._n_hari.text=str(len(hari)); self._n_alarm.text=str(len(aktif)); self._n_total.text=str(len(all_j))
        if not hari:
            self.jlist.add_widget(Label(text='Tidak ada jadwal hari ini',font_size=dp(13),color=p('txt2'),size_hint_y=None,height=dp(60)))
            pet_say('Tidak ada jadwal hari ini, santai ya!')
        else:
            pet_say(f'Ada {len(hari)} jadwal hari ini, semangat ya!')
            for j in sorted(hari,key=lambda x:x.get('waktu','00:00')):
                self.jlist.add_widget(JadwalCard(j,on_delete=self._del,on_public=self._pub))

    def _add_from_text(self,teks,auto_audio=False):
        t=teks.strip()
        if not t: self._toast('Isi teks jadwal dulu!',err=True); return None
        lo=t.lower(); pub_flag='publik' in lo and 'pribadi' not in lo
        t=re.sub(r'\bpublik\b','',t,flags=re.IGNORECASE)
        t=re.sub(r'\bpribadi\b','',t,flags=re.IGNORECASE)
        info=parse_jadwal(t); info.setdefault('public',pub_flag)
        if auto_audio or not info.get('audio_path'):
            fav=get_favorite_alarm()
            if fav:
                ap=fav.get('audio_path',''); tp=fav.get('tipe_audio','')
                if ap and os.path.exists(ap) and not info.get('audio_path'):
                    info['audio_path']=ap; info['tipe_audio']=tp
        info['id']=str(int(time.time()*1000)); info['dibuat']=datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        if info.get('audio_path'):
            aid=str(int(time.time()*1000))
            alarm={'id':aid,'label':info.get('judul','Alarm'),'waktu':info.get('waktu',''),
                   'tanggal':info.get('tanggal',''),'audio_path':info.get('audio_path',''),
                   'tipe_audio':info.get('tipe_audio',''),'aktif':True,'dibuat':info['dibuat']}
            from utils.storage import save_alarm
            alist=load_alarm(); alist.append(alarm); save_alarm(alist); info['alarm_id']=aid
        s=load_jadwal(); s.append(info); save_jadwal(s); return info

    def _tambah(self,*a):
        info=self._add_from_text(self.txt.text)
        if not info: return
        self.txt.text=''; self._refresh()
        self._toast(f'Jadwal "{info["judul"]}" berhasil ditambahkan!' if info.get('audio_path') else 'Jadwal disimpan! Set alarm favorit untuk bunyi otomatis.',dur=4)
        pet_say('Jadwal baru ditambahkan!',sticker_override='mengingatkan.gif')
        Clock.schedule_once(lambda dt: pet_say('',sticker_override=random.choice(['berpikir.gif','kagum.gif','marah.gif'])),2)

    def _manual_added(self,info):
        info['id']=str(int(time.time()*1000)); info['dibuat']=datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        info.setdefault('public',False)
        s=load_jadwal(); s.append(info); save_jadwal(s); self._refresh()
        pet_say('Jadwal telah disimpan.',sticker_override='mengingatkan.gif')
        Clock.schedule_once(lambda dt: pet_say('',sticker_override=random.choice(['berpikir.gif','kagum.gif','marah.gif'])),2)
        self._toast(f'Jadwal "{info["judul"]}" berhasil ditambahkan!')

    def _voice(self,*a):
        if not self._sr: self._toast('Speech Recognition tidak tersedia',err=True); return
        self._toast('Mendengarkan...'); threading.Thread(target=self._do_voice,daemon=True).start()

    def _do_voice(self):
        try:
            import speech_recognition as sr
            r=sr.Recognizer()
            with sr.Microphone() as src: r.adjust_for_ambient_noise(src,.5); audio=r.listen(src,timeout=5)
            t=r.recognize_google(audio,language='id-ID')
            def _apply(dt):
                self.txt.text=t; info=self._add_from_text(t,auto_audio=True)
                if info:
                    self._refresh(); self._toast(f'Jadwal "{info["judul"]}" ditambahkan via suara!')
                    pet_say('Jadwal sudah kucatat dari suaramu.',sticker_override='mengingatkan.gif')
                    Clock.schedule_once(lambda dt: pet_say('',sticker_override=random.choice(['berpikir.gif','kagum.gif','marah.gif'])),2)
            Clock.schedule_once(_apply,0)
        except Exception as e: Clock.schedule_once(lambda dt,msg=str(e): self._toast(msg[:40],err=True))

    def _del(self,j):
        jid=j.get('id'); aid=j.get('alarm_id')
        if aid:
            al=load_alarm(); al=[a for a in al if a.get('id')!=aid]; save_alarm(al)
            threading.Thread(target=lambda: _fb_delete(f'alarms/{aid}'),daemon=True).start()
        save_jadwal([x for x in load_jadwal() if x.get('id')!=jid])
        threading.Thread(target=lambda: _fb_delete(f'jadwal/{jid}'),daemon=True).start()
        self._refresh(); self._toast('Jadwal dihapus')

    def _pub(self,j):
        lst=load_jadwal()
        for x in lst:
            if x.get('id')==j.get('id'): x['public']=not x.get('public',False)
        save_jadwal(lst); self._refresh()

    def _toast(self,msg,err=False,dur=2.8):
        c=p('red') if err else p('green')
        self.toast.text=msg
        a=Animation(color=(*c[:3],1),duration=.2)+Animation(color=(*c[:3],1),duration=dur-.4)+Animation(color=(*c[:3],0),duration=.2)
        a.start(self.toast)