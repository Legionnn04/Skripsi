"""widgets/popups.py - Semua popup: TambahJadwalPopup, TambahAlarmPopup, TimePicker, DatePicker."""
import os, sys, time, re
from datetime import datetime
from kivy.uix.popup import Popup
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.button import Button
from kivy.uix.widget import Widget
from kivy.uix.filechooser import FileChooserListView
from kivy.uix.progressbar import ProgressBar
from kivy.uix.spinner import Spinner
from kivy.metrics import dp
from widgets.common import mk_lbl, mk_input, MBtn, draw_bg
from utils.theme import p, PAL
from utils.audio import AZAN_AUDIO, record_audio, play_audio
from utils.storage import load_alarm, save_alarm, get_favorite_alarm, DIR_AUDIO


class TimePickerPopup(Popup):
    def __init__(self, initial='00:00', on_select=None, **kw):
        super().__init__(title='Pilih Waktu',size_hint=(.8,.4),**kw)
        self.on_select=on_select; hh,mm=initial.split(':') if ':' in initial else ('00','00')
        layout=BoxLayout(orientation='vertical',spacing=dp(8),padding=dp(12))
        row=BoxLayout(spacing=dp(8))
        self.sp_h=Spinner(text=hh.zfill(2),values=[f"{i:02d}" for i in range(24)],size_hint_x=None,width=dp(60))
        self.sp_m=Spinner(text=mm.zfill(2),values=[f"{i:02d}" for i in range(60)],size_hint_x=None,width=dp(60))
        from kivy.uix.label import Label
        row.add_widget(self.sp_h); row.add_widget(Label(text=':',size_hint_x=None,width=dp(10))); row.add_widget(self.sp_m)
        layout.add_widget(row)
        btn=MBtn(text='OK',style='primary',size_hint_y=None,height=dp(40)); btn.bind(on_press=self._ok); layout.add_widget(btn); self.content=layout

    def _ok(self,*a):
        if self.on_select: self.on_select(f"{self.sp_h.text}:{self.sp_m.text}")
        self.dismiss()


class DatePickerPopup(Popup):
    def __init__(self, initial=None, on_select=None, **kw):
        super().__init__(title='Pilih Tanggal',size_hint=(.9,.5),**kw)
        self.on_select=on_select; today=datetime.now()
        if initial:
            try: today=datetime.strptime(initial,'%Y-%m-%d')
            except: pass
        layout=BoxLayout(orientation='vertical',spacing=dp(8),padding=dp(12))
        row1=BoxLayout(spacing=dp(8))
        self.sp_y=Spinner(text=str(today.year),values=[str(y) for y in range(today.year-5,today.year+6)],size_hint_x=None,width=dp(80))
        self.sp_m=Spinner(text=str(today.month).zfill(2),values=[str(m).zfill(2) for m in range(1,13)],size_hint_x=None,width=dp(60))
        self.sp_d=Spinner(text=str(today.day).zfill(2),values=[str(d).zfill(2) for d in range(1,32)],size_hint_x=None,width=dp(60))
        row1.add_widget(self.sp_y); row1.add_widget(self.sp_m); row1.add_widget(self.sp_d); layout.add_widget(row1)
        btn=MBtn(text='OK',style='primary',size_hint_y=None,height=dp(40)); btn.bind(on_press=self._ok); layout.add_widget(btn); self.content=layout

    def _ok(self,*a):
        if self.on_select: self.on_select(f"{self.sp_y.text}-{self.sp_m.text}-{self.sp_d.text}")
        self.dismiss()


def _mk_scrollable_popup(root_box):
    """Wrap konten popup dalam ScrollView agar aman di layar kecil."""
    sc = ScrollView(do_scroll_x=False)
    root_box.bind(minimum_height=root_box.setter('height'))
    sc.add_widget(root_box)
    return sc


class TambahAlarmPopup(Popup):
    def __init__(self, on_save=None, **kw):
        super().__init__(title='',separator_height=0,background='',background_color=(0,0,0,0),
                         size_hint=(.93,.92),**kw)
        self._on_save=on_save; self._fp=None; self._rp=None; self._rec_busy=False; self._build()

    def _build(self):
        # outer card
        outer=BoxLayout(orientation='vertical',padding=[dp(16),dp(16)],spacing=dp(0))
        draw_bg(outer,'card',16)

        # header (tidak di-scroll)
        hdr=BoxLayout(size_hint_y=None,height=dp(40))
        hdr.add_widget(mk_lbl('Tambah Alarm Baru',17,bold=True,size_hint_x=1))
        bx=Button(text='X',size_hint=(None,1),width=dp(34),font_size=dp(16),
                  background_normal='',background_color=(0,0,0,0),color=p('txt2'))
        bx.bind(on_press=lambda *a: self.dismiss()); hdr.add_widget(bx)
        outer.add_widget(hdr)

        # scrollable content
        inner=BoxLayout(orientation='vertical',size_hint_y=None,spacing=dp(8),padding=[0,dp(6),0,dp(6)])
        inner.bind(minimum_height=inner.setter('height'))

        inner.add_widget(mk_lbl('Label Alarm',11,'txt2',size_hint_y=None,height=dp(16)))
        self.inp_label=mk_input(hint_text='Nama alarm...'); inner.add_widget(self.inp_label)
        inner.add_widget(mk_lbl('Waktu',11,'txt2',size_hint_y=None,height=dp(16)))
        self.wkt_btn=MBtn(text=datetime.now().strftime('%H:%M'),style='neutral',size_hint_y=None,height=dp(42))
        self.wkt_btn.bind(on_press=lambda *a: TimePickerPopup(initial=self.wkt_btn.text,on_select=lambda t: setattr(self.wkt_btn,'text',t)).open())
        inner.add_widget(self.wkt_btn)
        inner.add_widget(mk_lbl('Tanggal',11,'txt2',size_hint_y=None,height=dp(16)))
        self.tgl_btn=MBtn(text=datetime.now().strftime('%Y-%m-%d'),style='neutral',size_hint_y=None,height=dp(42))
        self.tgl_btn.bind(on_press=lambda *a: DatePickerPopup(initial=self.tgl_btn.text,on_select=lambda d: setattr(self.tgl_btn,'text',d)).open())
        inner.add_widget(self.tgl_btn)
        inner.add_widget(mk_lbl('Sumber Suara Alarm',11,'txt2',size_hint_y=None,height=dp(16)))
        self.lbl_fp=mk_lbl('Belum ada file dipilih',11,'txt2',size_hint_y=None,height=dp(18))
        inner.add_widget(self.lbl_fp)
        b_fc=MBtn(text='Pilih File Audio (WAV/MP3/OGG)',style='neutral',font_size=dp(12),size_hint_y=None,height=dp(40))
        b_fc.bind(on_press=self._open_fc); inner.add_widget(b_fc)
        self.lbl_rek=mk_lbl('Tekan tombol untuk merekam (10 detik)',11,'txt2',size_hint_y=None,height=dp(18))
        inner.add_widget(self.lbl_rek)
        inner.add_widget(mk_lbl('Publikkan alarm?',11,'txt2',size_hint_y=None,height=dp(16)))
        self._is_public=False
        self.pub_al_bt=MBtn(text='Tidak',style='neutral',size_hint_y=None,height=dp(38))
        self.pub_al_bt.bind(on_press=self._toggle_alarm_public)
        inner.add_widget(self.pub_al_bt)
        self.pb=ProgressBar(max=100,value=0,size_hint_y=None,height=dp(8)); inner.add_widget(self.pb)
        brow=BoxLayout(size_hint_y=None,height=dp(40),spacing=dp(10))
        self.b_rec=MBtn(text='Mulai Rekam',style='orange',font_size=dp(13))
        self.b_prev=MBtn(text='Putar',style='neutral',font_size=dp(13),size_hint_x=None,width=dp(80)); self.b_prev.disabled=True
        self.b_rec.bind(on_press=self._do_rec)
        self.b_prev.bind(on_press=lambda *a: self._rp and os.path.exists(self._rp) and play_audio(self._rp))
        brow.add_widget(self.b_rec); brow.add_widget(self.b_prev); inner.add_widget(brow)
        self.lbl_err=mk_lbl('',11,'red',size_hint_y=None,height=dp(18)); inner.add_widget(self.lbl_err)
        bs=MBtn(text='Simpan Alarm',style='success',font_size=dp(14),size_hint_y=None,height=dp(46))
        bs.bind(on_press=self._simpan); inner.add_widget(bs)

        sc=ScrollView(do_scroll_x=False)
        sc.add_widget(inner)
        outer.add_widget(sc)
        self.content=outer

    def _open_fc(self,*a):
        lay=BoxLayout(orientation='vertical',spacing=dp(8),padding=dp(10))
        fc=FileChooserListView(path=os.path.expanduser('~'),filters=['*.wav','*.mp3','*.ogg','*.WAV','*.MP3','*.OGG']); lay.add_widget(fc)
        br=BoxLayout(size_hint_y=None,height=dp(44),spacing=dp(10))
        bb=MBtn(text='Batal',style='neutral',font_size=dp(13)); bp=MBtn(text='Pilih',style='success',font_size=dp(13))
        br.add_widget(bb); br.add_widget(bp); lay.add_widget(br)
        pop=Popup(title='Pilih File Audio',content=lay,size_hint=(.95,.85),background='',background_color=(0,0,0,.8),separator_height=1)
        def _ok(*a):
            if fc.selection: self._fp=fc.selection[0]; self.lbl_fp.text=f'Terpilih: {os.path.basename(self._fp)}'; self.lbl_fp.color=p('green')
            pop.dismiss()
        bb.bind(on_press=lambda *a: pop.dismiss()); bp.bind(on_press=_ok); pop.open()

    def _do_rec(self,*a):
        if self._rec_busy: return
        self._rec_busy=True; self.b_rec.text='Merekam...'; self.b_rec.background_color=p('red')
        self.pb.value=0; self.b_prev.disabled=True; self.lbl_rek.text='Sedang merekam!'; self.lbl_rek.color=p('red')
        os.makedirs(DIR_AUDIO,exist_ok=True)
        out=os.path.join(DIR_AUDIO,f'rekaman_{int(time.time())}.wav')
        record_audio(out,secs=10,cb_done=self._rec_done,cb_prog=lambda pct: setattr(self.pb,'value',pct))

    def _rec_done(self,ok,res):
        self._rec_busy=False; self.b_rec.background_color=p('orange'); self.pb.value=100
        if ok: self._rp=res; self.b_rec.text='Rekam Ulang'; self.b_prev.disabled=False; self.lbl_rek.text=f'Tersimpan: {os.path.basename(res)}'; self.lbl_rek.color=p('green')
        else: self.b_rec.text='Mulai Rekam'; self.lbl_rek.text=f'Gagal: {res[:50]}'; self.lbl_rek.color=p('red')

    def _simpan(self,*a):
        label=self.inp_label.text.strip() or 'Alarm'
        waktu=self.wkt_btn.text.strip(); tanggal=self.tgl_btn.text.strip()
        apath=(self._fp or self._rp) or ''
        tipe='file' if self._fp else ('rekam' if self._rp else '')
        if not apath: self.lbl_err.text='Pilih atau rekam suara alarm dulu!'; return
        if not os.path.exists(apath): self.lbl_err.text='File audio tidak ditemukan!'; return
        alarm={'id':str(int(time.time()*1000)),'label':label,'waktu':waktu,'tanggal':tanggal,
               'audio_path':apath,'tipe_audio':tipe,'aktif':True,
               'dibuat':datetime.now().strftime('%Y-%m-%d %H:%M:%S'),'public':self._is_public}
        s=load_alarm(); s.append(alarm); save_alarm(s); self.dismiss()
        if self._on_save: self._on_save(alarm)

    def _toggle_alarm_public(self,*a):
        self._is_public=not self._is_public
        self.pub_al_bt.text='Ya' if self._is_public else 'Tidak'


class TambahJadwalPopup(Popup):
    def __init__(self, on_save=None, jadwal=None, **kw):
        super().__init__(title='',separator_height=0,background='',background_color=(0,0,0,0),
                         size_hint=(.93,.88),**kw)
        self._on_save=on_save; self._init_jadwal=jadwal or {}; self._fp=None; self._rp=None; self._rec_busy=False; self._build()
        if self._init_jadwal:
            self.inp_judul.text=self._init_jadwal.get('judul','')
            self.wkt_btn.text=self._init_jadwal.get('waktu',self.wkt_btn.text)
            self.tgl_btn.text=self._init_jadwal.get('tanggal',self.tgl_btn.text)
            self._is_public=bool(self._init_jadwal.get('public'))
            self.pub_btn.text='Ya' if self._is_public else 'Tidak'

    def _build(self):
        outer=BoxLayout(orientation='vertical',padding=[dp(16),dp(16)],spacing=dp(0))
        draw_bg(outer,'card',16)

        hdr=BoxLayout(size_hint_y=None,height=dp(40))
        hdr.add_widget(mk_lbl('Tambah Jadwal Manual',17,bold=True,size_hint_x=1))
        bx=Button(text='X',size_hint=(None,1),width=dp(34),font_size=dp(16),
                  background_normal='',background_color=(0,0,0,0),color=p('txt2'))
        bx.bind(on_press=lambda *a: self.dismiss()); hdr.add_widget(bx)
        outer.add_widget(hdr)

        inner=BoxLayout(orientation='vertical',size_hint_y=None,spacing=dp(8),padding=[0,dp(6),0,dp(6)])
        inner.bind(minimum_height=inner.setter('height'))

        inner.add_widget(mk_lbl('Judul',11,'txt2',size_hint_y=None,height=dp(16)))
        self.inp_judul=mk_input(hint_text='Judul kegiatan'); inner.add_widget(self.inp_judul)
        inner.add_widget(mk_lbl('Waktu',11,'txt2',size_hint_y=None,height=dp(16)))
        self.wkt_btn=MBtn(text=datetime.now().strftime('%H:%M'),style='neutral',size_hint_y=None,height=dp(42))
        self.wkt_btn.bind(on_press=lambda *a: TimePickerPopup(initial=self.wkt_btn.text,on_select=lambda t: setattr(self.wkt_btn,'text',t)).open())
        inner.add_widget(self.wkt_btn)
        inner.add_widget(mk_lbl('Tanggal',11,'txt2',size_hint_y=None,height=dp(16)))
        self.tgl_btn=MBtn(text=datetime.now().strftime('%Y-%m-%d'),style='neutral',size_hint_y=None,height=dp(42))
        self.tgl_btn.bind(on_press=lambda *a: DatePickerPopup(initial=self.tgl_btn.text,on_select=lambda d: setattr(self.tgl_btn,'text',d)).open())
        inner.add_widget(self.tgl_btn)
        inner.add_widget(mk_lbl('Audio Alarm (opsional)',11,'txt2',size_hint_y=None,height=dp(16)))
        self.lbl_fp=mk_lbl('Belum ada file dipilih',11,'txt2',size_hint_y=None,height=dp(18)); inner.add_widget(self.lbl_fp)
        inner.add_widget(mk_lbl('Publikkan jadwal?',11,'txt2',size_hint_y=None,height=dp(16)))
        self._is_public=False
        self.pub_btn=MBtn(text='Tidak',style='neutral',size_hint_y=None,height=dp(42))
        self.pub_btn.bind(on_press=self._toggle_public); inner.add_widget(self.pub_btn)
        b_fc=MBtn(text='Pilih File Audio',style='neutral',font_size=dp(12),size_hint_y=None,height=dp(40))
        b_fc.bind(on_press=self._open_fc); inner.add_widget(b_fc)
        self.lbl_rek=mk_lbl('Rekam suara sendiri (10 detik)',11,'txt2',size_hint_y=None,height=dp(18)); inner.add_widget(self.lbl_rek)
        self.pb=ProgressBar(max=100,value=0,size_hint_y=None,height=dp(8)); inner.add_widget(self.pb)
        brow=BoxLayout(size_hint_y=None,height=dp(40),spacing=dp(10))
        self.b_rec=MBtn(text='Mulai Rekam',style='orange',font_size=dp(13))
        self.b_prev=MBtn(text='Putar',style='neutral',font_size=dp(13),size_hint_x=None,width=dp(80)); self.b_prev.disabled=True
        self.b_rec.bind(on_press=self._do_rec)
        self.b_prev.bind(on_press=lambda *a: self._rp and os.path.exists(self._rp) and play_audio(self._rp))
        brow.add_widget(self.b_rec); brow.add_widget(self.b_prev); inner.add_widget(brow)
        self.lbl_err=mk_lbl('',11,'txt2',size_hint_y=None,height=dp(18)); inner.add_widget(self.lbl_err)
        bs=MBtn(text='Simpan Jadwal',style='success',font_size=dp(14),size_hint_y=None,height=dp(46))
        bs.bind(on_press=self._simpan); inner.add_widget(bs)

        sc=ScrollView(do_scroll_x=False)
        sc.add_widget(inner)
        outer.add_widget(sc)
        self.content=outer

    def _simpan(self,*a):
        judul=self.inp_judul.text.strip(); waktu=self.wkt_btn.text.strip()
        tanggal=self.tgl_btn.text.strip() or datetime.now().strftime('%Y-%m-%d')
        if not judul: self.lbl_err.text='Judul tidak boleh kosong'; self.lbl_err.color=p('red'); return
        if not re.match(r'^\d{2}:\d{2}$',waktu): self.lbl_err.text='Format waktu salah (HH:MM)'; self.lbl_err.color=p('red'); return
        if not re.match(r'^\d{4}-\d{2}-\d{2}$',tanggal): self.lbl_err.text='Format tanggal salah (YYYY-MM-DD)'; self.lbl_err.color=p('red'); return
        apath=(self._fp or self._rp) or ''
        if not apath:
            fav=get_favorite_alarm()
            if fav: apath=fav.get('audio_path',''); tipe=fav.get('tipe_audio','')
            else: tipe=''
        else: tipe='file' if self._fp else ('rekam' if self._rp else '')
        alarm_id=self._init_jadwal.get('alarm_id') if self._init_jadwal else None
        if not alarm_id: alarm_id=str(int(time.time()*1000))
        alarm={'id':alarm_id,'label':judul,'waktu':waktu,'tanggal':tanggal,'audio_path':apath,
               'tipe_audio':tipe,'aktif':True,'dibuat':datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        alist=load_alarm(); alist=[a for a in alist if a.get('id')!=alarm_id]; alist.append(alarm); save_alarm(alist)
        jadwal={'judul':judul,'waktu':waktu,'tanggal':tanggal,'prioritas':'normal','catatan':'',
                'audio_path':apath,'tipe_audio':tipe,'alarm_id':alarm_id,'public':self._is_public}
        if self._on_save: self._on_save(jadwal)
        self.dismiss()

    def _toggle_public(self,*a):
        self._is_public=not self._is_public
        self.pub_btn.text='Ya' if self._is_public else 'Tidak'

    def _open_fc(self,*a):
        lay=BoxLayout(orientation='vertical',spacing=dp(8),padding=dp(10))
        fc=FileChooserListView(path=os.path.expanduser('~'),filters=['*.wav','*.mp3','*.ogg','*.WAV','*.MP3','*.OGG']); lay.add_widget(fc)
        br=BoxLayout(size_hint_y=None,height=dp(44),spacing=dp(10))
        bb=MBtn(text='Batal',style='neutral',font_size=dp(13)); bp=MBtn(text='Pilih',style='success',font_size=dp(13))
        br.add_widget(bb); br.add_widget(bp); lay.add_widget(br)
        pop=Popup(title='Pilih File Audio',content=lay,size_hint=(.95,.85),background='',background_color=(0,0,0,.8),separator_height=1)
        def _ok(*a):
            if fc.selection: self._fp=fc.selection[0]; self.lbl_fp.text=f'Terpilih: {os.path.basename(self._fp)}'; self.lbl_fp.color=p('green')
            pop.dismiss()
        bb.bind(on_press=lambda *a: pop.dismiss()); bp.bind(on_press=_ok); pop.open()

    def _do_rec(self,*a):
        if self._rec_busy: return
        self._rec_busy=True; self.b_rec.text='Merekam...'; self.b_rec.background_color=p('red')
        self.pb.value=0; self.b_prev.disabled=True; self.lbl_rek.text='Sedang merekam!'; self.lbl_rek.color=p('red')
        os.makedirs(DIR_AUDIO,exist_ok=True)
        out=os.path.join(DIR_AUDIO,f'rekaman_{int(time.time())}.wav')
        record_audio(out,secs=10,cb_done=self._rec_done,cb_prog=lambda pct: setattr(self.pb,'value',pct))

    def _rec_done(self,ok,res):
        self._rec_busy=False; self.b_rec.background_color=p('orange'); self.pb.value=100
        if ok: self._rp=res; self.b_rec.text='Rekam Ulang'; self.b_prev.disabled=False; self.lbl_rek.text=f'Tersimpan: {os.path.basename(res)}'; self.lbl_rek.color=p('green')
        else: self.b_rec.text='Mulai Rekam'; self.lbl_rek.text=f'Gagal: {res[:50]}'; self.lbl_rek.color=p('red')