"""utils/nlp.py - Parser teks jadwal bahasa Indonesia."""
import re
from datetime import datetime, timedelta

_HARI  = {'senin':0,'selasa':1,'rabu':2,'kamis':3,'jumat':4,'sabtu':5,'minggu':6}
_BULAN = {'januari':1,'februari':2,'maret':3,'april':4,'mei':5,'juni':6,
          'juli':7,'agustus':8,'september':9,'oktober':10,'november':11,'desember':12}

def parse_jadwal(teks):
    lo = teks.lower()
    r  = {'judul':'','tanggal':'','waktu':'','lokasi':'','catatan':teks,'prioritas':'normal'}
    for pat in [r'jam\s*(\d{1,2})(?:[:.](\d{2}))?\s*(pagi|siang|sore|malam)?',
                r'pukul\s*(\d{1,2})(?:[:.](\d{2}))?\s*(pagi|siang|sore|malam)?',
                r'(\d{1,2})[.:](\d{2})\s*(pagi|siang|sore|malam)?']:
        m = re.search(pat, lo)
        if m:
            j,mn = int(m.group(1)),int(m.group(2) or 0); pr = m.group(3)
            if pr in ('sore','malam') and j<12: j+=12
            elif pr=='siang' and j<7: j+=12
            r['waktu']=f"{j:02d}:{mn:02d}"; break
    now=datetime.now(); tset=False
    m=re.search(r"(\d+)\s*(?:menit|mnt)\s*(?:ke\s*depan|kedepan|dari sekarang)",lo)
    if m:
        dt=now+timedelta(minutes=int(m.group(1))); r['tanggal']=dt.strftime('%Y-%m-%d'); r['waktu']=dt.strftime('%H:%M'); tset=True
    else:
        m=re.search(r"(\d+)\s*jam\s*(?:ke\s*depan|kedepan|dari sekarang)",lo)
        if m:
            dt=now+timedelta(hours=int(m.group(1))); r['tanggal']=dt.strftime('%Y-%m-%d'); r['waktu']=dt.strftime('%H:%M'); tset=True
    if not tset:
        if 'besok' in lo: r['tanggal']=(now+timedelta(1)).strftime('%Y-%m-%d'); tset=True
        elif 'lusa' in lo: r['tanggal']=(now+timedelta(2)).strftime('%Y-%m-%d'); tset=True
        elif 'hari ini' in lo or 'sekarang' in lo: r['tanggal']=now.strftime('%Y-%m-%d'); tset=True
    if not tset:
        for nm,idx in _HARI.items():
            if nm in lo:
                s=(idx-now.weekday())%7 or 7; r['tanggal']=(now+timedelta(s)).strftime('%Y-%m-%d'); tset=True; break
    if not tset:
        m=re.search(r'tanggal\s*(\d{1,2})\s*(\w+)?',lo)
        if m:
            tgl,bln=int(m.group(1)),_BULAN.get(m.group(2) or '',now.month)
            try:
                t=datetime(now.year,bln,tgl)
                if t<now: t=datetime(now.year+1,bln,tgl)
                r['tanggal']=t.strftime('%Y-%m-%d'); tset=True
            except: pass
    if not tset: r['tanggal']=now.strftime('%Y-%m-%d')
    if any(w in lo for w in ['penting','urgent','segera','darurat']): r['prioritas']='tinggi'
    elif any(w in lo for w in ['santai','biasa','opsional']): r['prioritas']='rendah'
    m=re.search(r'di\s+([A-Za-z][A-Za-z\s]{2,30}?)(?:\s+(?:jam|pukul|tanggal|pada)|$)',lo)
    if m: r['lokasi']=m.group(1).strip().title()
    judul=teks
    for pat in [r'(besok|lusa|hari ini|sekarang)',r'(jam|pukul)\s*\d{1,2}[:.].\d{0,2}\s*(pagi|siang|sore|malam)?',
                r'\d{1,2}[.:]\d{2}\s*(pagi|siang|sore|malam)',r'tanggal\s*\d{1,2}\s*\w*',
                r'(senin|selasa|rabu|kamis|jumat|sabtu|minggu)',r'di\s+[A-Za-z][A-Za-z\s]{2,30}',
                r'(penting|urgent|segera|darurat|santai|biasa)',
                r'(buatkan|tambahkan|buat|set|catat|ingatkan|jadwalkan)\s*(jadwal|kegiatan|acara|reminder|pengingat|saya|aku)?',
                r'(untuk|dengan|pada|di)']:
        judul=re.sub(pat,'',judul,flags=re.IGNORECASE)
    judul=re.sub(r'\s+',' ',judul).strip()
    if not judul or len(judul)<3:
        kata=[w for w in teks.split() if len(w)>3][:3]
        judul=' '.join(kata) if kata else 'Kegiatan Baru'
    r['judul']=judul.title()[:50]
    return r
