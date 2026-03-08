"""screens/jadwal.py - Layar daftar semua jadwal dengan filter dan pencarian."""
import threading
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
from utils.storage import load_jadwal, save_jadwal, load_alarm, save_alarm, force_sync, _fb_delete
from utils.theme import p

class JadwalScreen(BaseScreen):
    _NAV_KEY='jadwal'
    def __init__(self,**kw):
        super().__init__(name='jadwal',**kw); self._f='semua'; self._build_content()

    def _build_content(self):
        main=BoxLayout(orientation='vertical',padding=[dp(14),dp(14),dp(14),dp(8)],spacing=dp(10))
        hdr=BoxLayout(size_hint_y=None,height=dp(46),spacing=dp(8))
        back=MBtn(text='Kembali',style='neutral',size_hint_x=None,width=dp(90),font_size=dp(12))
        back.bind(on_press=lambda *a: setattr(self.manager,'current','beranda')); hdr.add_widget(back)
        hdr.add_widget(mk_lbl('Semua Jadwal',19,bold=True,size_hint_y=None,height=dp(34)))
        self.btn_ref=MBtn(text='⟳',style='neutral',size_hint=(None,1),width=dp(38),font_size=dp(15))
        self.btn_ref.bind(on_press=self._do_sync); hdr.add_widget(self.btn_ref)
        main.add_widget(hdr)
        # tabs - pakai ScrollView horizontal agar tidak kepotong di layar kecil
        tabs_sc=ScrollView(size_hint_y=None,height=dp(34),do_scroll_y=False)
        tabs=BoxLayout(size_hint=(None,1),spacing=dp(6)); tabs.bind(minimum_width=tabs.setter('width'))
        self.fb={}
        for k,lb in [('semua','Semua'),('hari_ini','Hari Ini'),('minggu','Minggu'),('tinggi','Penting'),('pribadi','Pribadi'),('publik','Publik')]:
            b=Button(text=lb,font_size=dp(11),background_normal='',
                     background_color=p('blue2') if k=='semua' else p('card2'),
                     color=p('txt'),bold=(k=='semua'),size_hint=(None,1),width=dp(78))
            b.bind(on_press=lambda x,kk=k: self._sf(kk)); self.fb[k]=b; tabs.add_widget(b)
        tabs_sc.add_widget(tabs); main.add_widget(tabs_sc)
        self.ts=mk_input(hint_text='Cari jadwal...',background_color=p('card'))
        self.ts.bind(text=lambda *a: self._refresh()); main.add_widget(self.ts)
        sc=ScrollView()
        self.lb2=BoxLayout(orientation='vertical',size_hint_y=None,spacing=dp(8),padding=[0,dp(4)])
        self.lb2.bind(minimum_height=self.lb2.setter('height')); sc.add_widget(self.lb2); main.add_widget(sc)
        self._set_content(main)

    def on_enter(self): super().on_enter(); self._refresh()

    def _sf(self,k):
        self._f=k
        for kk,b in self.fb.items(): b.background_color=p('blue2') if kk==k else p('card2'); b.bold=(kk==k)
        self._refresh()

    def _do_sync(self,*a):
        self.btn_ref.text='...'; self.btn_ref.disabled=True
        def _run():
            try: ok,msg=force_sync()
            except Exception as e: ok=False; msg=str(e)
            from kivy.clock import Clock
            def _done(dt):
                self._refresh(); self.btn_ref.text='⟳'; self.btn_ref.disabled=False
            Clock.schedule_once(_done,0)
        threading.Thread(target=_run,daemon=True).start()

    def _refresh(self):
        self.lb2.clear_widgets(); all_j=load_jadwal(); q=self.ts.text.lower().strip()
        today=datetime.now().strftime('%Y-%m-%d'); f=all_j
        if self._f=='hari_ini': f=[j for j in all_j if j.get('tanggal')==today]
        elif self._f=='minggu':
            tn=datetime.now(); st=tn-timedelta(days=tn.weekday()); en=st+timedelta(6)
            f=[j for j in all_j if self._rng(j.get('tanggal',''),st.date(),en.date())]
        elif self._f=='tinggi': f=[j for j in all_j if j.get('prioritas')=='tinggi']
        elif self._f=='pribadi': f=[j for j in all_j if not j.get('public')]
        elif self._f=='publik': f=[j for j in all_j if j.get('public')]
        if q: f=[j for j in f if q in (j.get('judul','')+j.get('catatan','')).lower()]
        f=sorted(f,key=lambda x:(x.get('tanggal','9999'),x.get('waktu','99:99')))
        if not f:
            self.lb2.add_widget(Label(text='Tidak ada jadwal ditemukan',font_size=dp(13),color=p('txt2'),size_hint_y=None,height=dp(70)))
        else:
            for j in f: self.lb2.add_widget(JadwalCard(j,on_delete=self._del,on_edit=self._edit,on_public=self._pub))

    def _rng(self,s,st,en):
        try: d=datetime.strptime(s,'%Y-%m-%d').date(); return st<=d<=en
        except: return False

    def _pub(self,j):
        lst=load_jadwal()
        for x in lst:
            if x.get('id')==j.get('id'): x['public']=not x.get('public',False)
        save_jadwal(lst); self._refresh()

    def _del(self,j):
        jid=j.get('id'); aid=j.get('alarm_id')
        if aid:
            al=load_alarm(); al=[a for a in al if a.get('id')!=aid]; save_alarm(al)
            threading.Thread(target=lambda: _fb_delete(f'alarms/{aid}'),daemon=True).start()
        save_jadwal([x for x in load_jadwal() if x.get('id')!=jid])
        threading.Thread(target=lambda: _fb_delete(f'jadwal/{jid}'),daemon=True).start()
        self._refresh()

    def _edit(self,j):
        def _save_cb(info):
            info['id']=j.get('id'); info['dibuat']=j.get('dibuat')
            lst=load_jadwal()
            for idx,x in enumerate(lst):
                if x.get('id')==j.get('id'): lst[idx]=info; break
            save_jadwal(lst); self._refresh()
        p2=TambahJadwalPopup(on_save=_save_cb,jadwal=j); p2.title='Ubah Jadwal'; p2.open()