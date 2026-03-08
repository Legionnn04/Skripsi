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
    def __init__(self, jadwal, on_delete=None, on_edit=None, on_public=None, **kw):
        super().__init__(orientation='vertical',size_hint_y=None,height=dp(112),
                         padding=[dp(16),dp(10)],spacing=dp(5),**kw)
        pw={'tinggi':p('red'),'normal':p('blue'),'rendah':p('green')}
        pc=pw.get(jadwal.get('prioritas','normal'),p('blue'))
        with self.canvas.before:
            Color(*p('card')); self._bg=RoundedRectangle(pos=self.pos,size=self.size,radius=[dp(12)])
            Color(*pc[:3],0.8); self._bar=RoundedRectangle(pos=self.pos,size=(dp(4),self.height),radius=[dp(2)])
        self.bind(pos=self._u,size=self._u)
        hdr=BoxLayout(size_hint_y=None,height=dp(26))
        # title
        hdr.add_widget(mk_lbl(jadwal.get('judul','Kegiatan'),14,bold=True,size_hint_x=1))
        # privacy badge - warna berbeda untuk publik vs pribadi
        pub=jadwal.get('public',False)
        badge_color = (*p('blue')[:3], 0.15) if pub else (*p('orange')[:3], 0.15)
        badge_text_color = p('blue') if pub else p('orange')
        badge_text = ' Publik' if pub else ' Pribadi'
        pub_bt=Button(text=badge_text,size_hint=(None,1),width=dp(80),font_size=dp(11),
                      background_normal='',background_color=badge_color,color=badge_text_color,bold=True)
        pub_bt.bind(on_press=lambda *a: on_public and on_public(jadwal))
        hdr.add_widget(pub_bt)
        # priority indicator (small label); hide normal
        bm={'tinggi':'PENTING','normal':'','rendah':'SANTAI'}
        hdr.add_widget(mk_lbl(bm.get(jadwal.get('prioritas','normal'),''),
                               10,'txt2',size_hint_x=None,width=dp(80),align='right'))
        self.add_widget(hdr)
        try: tgl=datetime.strptime(jadwal.get('tanggal',''),'%Y-%m-%d').strftime('%d %b %Y')
        except: tgl=jadwal.get('tanggal','')
        pts=([f'Tanggal {tgl}'] if tgl else [])+([f'Waktu {jadwal["waktu"]}'] if jadwal.get('waktu') else [])+([f'Lokasi {jadwal["lokasi"]}'] if jadwal.get('lokasi') else [])
        self.add_widget(mk_lbl('   '.join(pts) or 'Tanggal belum ditentukan',12,'txt2',size_hint_y=None,height=dp(20)))
        cat=jadwal.get('catatan','')
        if cat: self.add_widget(mk_lbl(cat[:78]+('...' if len(cat)>78 else ''),11,'txt2',size_hint_y=None,height=dp(18)))
        aksi=BoxLayout(size_hint_y=None,height=dp(26),spacing=dp(8)); aksi.add_widget(Widget())
        if on_edit:
            be=Button(text='Ubah',size_hint=(None,1),width=dp(64),font_size=dp(11),
                      background_normal='',background_color=(*p('blue2')[:3],.18),color=p('blue'),bold=True)
            be.bind(on_press=lambda *a: on_edit(jadwal)); aksi.add_widget(be)
        bd=Button(text='Hapus',size_hint=(None,1),width=dp(64),font_size=dp(11),
                  background_normal='',background_color=(*p('red')[:3],.18),color=p('red'),bold=True)
        bd.bind(on_press=lambda *a: on_delete and on_delete(jadwal))
        aksi.add_widget(bd); self.add_widget(aksi)

    def _u(self,*a):
        self._bg.pos,self._bg.size=self.pos,self.size
        self._bar.pos,self._bar.size=self.pos,(dp(4),self.height)