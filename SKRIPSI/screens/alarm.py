"""screens/alarm.py - Layar manajemen alarm."""
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.label import Label
from kivy.metrics import dp
from screens.base import BaseScreen
from widgets.common import mk_lbl, MBtn, draw_bg
from widgets.alarm_card import AlarmCard
from widgets.popups import TambahAlarmPopup
from utils.storage import load_alarm, save_alarm, fill_empty_jadwals_with_favorite, force_sync, _fb_delete
from utils.audio import ALARM_ENGINE, play_audio
from utils.theme import p

def show_ring_popup(alarm):
    from screens.beranda import show_ring_popup as srp
    srp(alarm)

class AlarmScreen(BaseScreen):
    _NAV_KEY='alarm'
    def __init__(self,**kw): super().__init__(name='alarm',**kw); self._build_content()

    def _build_content(self):
        main=BoxLayout(orientation='vertical',padding=[dp(14),dp(14),dp(14),dp(8)],spacing=dp(10))
        hdr=BoxLayout(size_hint_y=None,height=dp(46),spacing=dp(8))
        back=MBtn(text='Kembali',style='neutral',size_hint_x=None,width=dp(90),font_size=dp(12))
        back.bind(on_press=lambda *a: setattr(self.manager,'current','beranda')); hdr.add_widget(back)
        hdr.add_widget(mk_lbl('Alarm',19,bold=True,size_hint_x=1))
        self.btn_ref=MBtn(text='⟳',style='neutral',size_hint=(None,1),width=dp(38),font_size=dp(15))
        self.btn_ref.bind(on_press=self._do_sync); hdr.add_widget(self.btn_ref)
        b_add=MBtn(text='+ Tambah Alarm',style='primary',font_size=dp(12),size_hint=(None,1),width=dp(130))
        b_add.bind(on_press=lambda *a: TambahAlarmPopup(on_save=lambda al: self._refresh()).open())
        hdr.add_widget(b_add); main.add_widget(hdr)
        info=BoxLayout(size_hint_y=None,height=dp(58),spacing=dp(8))
        for ttl,sub,col in [('Dari File','Pilih WAV/MP3/OGG','blue'),('Rekam Suara','Rekam suaramu','orange')]:
            bx=BoxLayout(orientation='vertical',padding=[dp(10),dp(6)],spacing=dp(2)); draw_bg(bx,'card',10)
            bx.add_widget(mk_lbl(ttl,12,col,bold=True,align='center',size_hint_y=None,height=dp(22)))
            bx.add_widget(mk_lbl(sub,10,'txt2',align='center',size_hint_y=None,height=dp(16))); info.add_widget(bx)
        main.add_widget(info)
        sc=ScrollView()
        self.albox=BoxLayout(orientation='vertical',size_hint_y=None,spacing=dp(8),padding=[0,dp(4)])
        self.albox.bind(minimum_height=self.albox.setter('height')); sc.add_widget(self.albox); main.add_widget(sc)
        self._set_content(main)

    def on_enter(self): super().on_enter(); self._refresh(); ALARM_ENGINE.on_ring=show_ring_popup

    def _refresh(self):
        self.albox.clear_widgets(); alarms=load_alarm()
        if not alarms:
            self.albox.add_widget(Label(text='Belum ada alarm\nTekan + Tambah Alarm',font_size=dp(13),color=p('txt2'),size_hint_y=None,height=dp(100),halign='center'))
        else:
            for a in sorted(alarms,key=lambda x:x.get('waktu','')):
                self.albox.add_widget(AlarmCard(a,on_delete=self._del,on_toggle=self._tog,on_play=play_audio,on_fav=self._fav,on_public=self._pub))

    def _del(self,a):
        aid=a.get('id')
        save_alarm([x for x in load_alarm() if x.get('id')!=aid])
        import threading
        threading.Thread(target=lambda: _fb_delete(f'alarms/{aid}'),daemon=True).start()
        self._refresh()

    def _tog(self,a):
        s=load_alarm()
        for x in s:
            if x.get('id')==a.get('id'): x['aktif']=not x.get('aktif',True)
        save_alarm(s); self._refresh()

    def _fav(self,a):
        s=load_alarm()
        for x in s: x['favorite']=(x.get('id')==a.get('id'))
        save_alarm(s); self._refresh(); fill_empty_jadwals_with_favorite()

    def _pub(self,a):
        s=load_alarm()
        for x in s:
            if x.get('id')==a.get('id'): x['public']=not x.get('public',False)
        save_alarm(s); self._refresh()

    def _do_sync(self,*a):
        self.btn_ref.text='...'; self.btn_ref.disabled=True
        def _run():
            try: ok,msg=force_sync()
            except Exception as e: ok=False; msg=str(e)
            from kivy.clock import Clock
            def _done(dt):
                self._refresh(); self.btn_ref.text='⟳'; self.btn_ref.disabled=False
            Clock.schedule_once(_done,0)
        import threading
        threading.Thread(target=_run,daemon=True).start()