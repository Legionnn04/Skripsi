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
    def __init__(self, alarm, on_delete=None, on_toggle=None, on_play=None, on_fav=None, on_public=None, **kw):
        super().__init__(orientation='vertical',size_hint_y=None,height=dp(110),
                         padding=[dp(16),dp(10)],spacing=dp(5),**kw)
        aktif=alarm.get('aktif',True); sc=p('green') if aktif else p('txt2')
        fav=alarm.get('favorite',False)
        with self.canvas.before:
            Color(*p('card')); self._bg=RoundedRectangle(pos=self.pos,size=self.size,radius=[dp(12)])
            Color(*sc[:3],0.8); self._bar=RoundedRectangle(pos=self.pos,size=(dp(4),self.height),radius=[dp(2)])
        self.bind(pos=self._u,size=self._u)
        hdr=BoxLayout(size_hint_y=None,height=dp(26))
        star=Button(text='*' if fav else 'o',size_hint=(None,1),width=dp(30),font_size=dp(14),
                    background_normal='',background_color=(0,0,0,0),color=p('yellow'))
        star.bind(on_press=lambda *a: on_fav and on_fav(alarm)); hdr.add_widget(star)
        # privacy toggle
        pub=alarm.get('public',False)
        pub_bt=Button(text='Publik' if pub else 'Pribadi',size_hint=(None,1),width=dp(60),font_size=dp(12),
                    background_normal='',background_color=(0,0,0,0),color=p('blue'))
        # capture on_public in local variable to appease static analysis
        _op = on_public
        pub_bt.bind(on_press=lambda *a, op=_op, alm=alarm: op and op(alm)); hdr.add_widget(pub_bt)
        hdr.add_widget(mk_lbl(alarm.get('label','Alarm'),14,bold=True,size_hint_x=1))
        tp=alarm.get('tipe_audio','file'); bt_txt,bt_col=('Rekaman','orange') if tp=='rekam' else ('File','blue')
        hdr.add_widget(mk_lbl(bt_txt,10,bt_col,bold=True,size_hint_x=None,width=dp(80),align='right'))
        self.add_widget(hdr)
        try: tgl=datetime.strptime(alarm.get('tanggal',''),'%Y-%m-%d').strftime('%d %b %Y')
        except: tgl='Setiap hari'
        self.add_widget(mk_lbl(f'Waktu {alarm.get("waktu","--:--")}   Tanggal {tgl}',12,'txt2',size_hint_y=None,height=dp(20)))
        ap=alarm.get('audio_path','')
        self.add_widget(mk_lbl(f'Audio: {os.path.basename(ap) if ap else "Tidak ada audio"}',11,'txt2',size_hint_y=None,height=dp(18)))
        aksi=BoxLayout(size_hint_y=None,height=dp(28),spacing=dp(8)); aksi.add_widget(Widget())
        if ap and os.path.exists(ap):
            bp=Button(text='Dengar',size_hint=(None,1),width=dp(74),font_size=dp(11),
                      background_normal='',background_color=(*p('blue2')[:3],.22),color=p('blue'),bold=True)
            bp.bind(on_press=lambda *a: on_play and on_play(ap)); aksi.add_widget(bp)
        tog_t,tog_c=('Nonaktif','yellow') if aktif else ('Aktifkan','green')
        bt2=Button(text=tog_t,size_hint=(None,1),width=dp(74),font_size=dp(11),
                   background_normal='',background_color=(*p(tog_c)[:3],.18),color=p(tog_c),bold=True)
        bt2.bind(on_press=lambda *a: on_toggle and on_toggle(alarm)); aksi.add_widget(bt2)
        bd=Button(text='Hapus',size_hint=(None,1),width=dp(60),font_size=dp(11),
                  background_normal='',background_color=(*p('red')[:3],.18),color=p('red'),bold=True)
        bd.bind(on_press=lambda *a: on_delete and on_delete(alarm))
        aksi.add_widget(bd); self.add_widget(aksi)

    def _u(self,*a):
        self._bg.pos,self._bg.size=self.pos,self.size
        self._bar.pos,self._bar.size=self.pos,(dp(4),self.height)
