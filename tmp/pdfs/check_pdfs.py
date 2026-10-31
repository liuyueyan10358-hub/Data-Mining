from pathlib import Path
from PIL import Image, ImageOps, ImageDraw, ImageFont
from pypdf import PdfReader
import json, re

root=Path('/Users/yueyan_liu/Desktop/Data Mining/project')
tmp=root/'tmp/pdfs'
font=ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial.ttf',20)
for prefix in ['tutorial','manual']:
    pages=sorted(tmp.glob(prefix+'-*.png'))
    for start in range(0,len(pages),8):
        group=pages[start:start+8]
        sheet=Image.new('RGB',(4*310,2*462),'#DDE5E9')
        draw=ImageDraw.Draw(sheet)
        for n,p in enumerate(group):
            im=Image.open(p).convert('RGB');im.thumbnail((290,412))
            x=(n%4)*310+10;y=(n//4)*462+32
            sheet.paste(im,(x,y))
            draw.text((x,y-26),p.stem,fill='black',font=font)
        sheet.save(tmp/f'{prefix}_sheet_{start//8+1}.jpg',quality=90)

report=[]
for file in sorted((root/'output/pdf').glob('*.pdf')):
    r=PdfReader(file)
    texts=[p.extract_text() for p in r.pages]
    all_text='\n'.join(texts)
    assert '\ufffd' not in all_text
    assert 'git status' in all_text and 'git push' in all_text
    assert '2026-10-31' in all_text
    assert len(r.outline)==len(r.pages)
    bad_lines=[(i+1,l) for i,t in enumerate(texts) for l in t.splitlines()
               if re.match(r'^[，。！？：；、）》】”’]',l)]
    assert not bad_lines, (file.name,bad_lines)
    links=[]
    for i,p in enumerate(r.pages):
        for a in p.get('/Annots',[]):
            a=a.get_object()
            if a.get('/A',{}).get('/URI'): links.append(a['/A']['/URI'])
    report.append({'file':file.name,'pages':len(r.pages),'bookmarks':len(r.outline),
                   'external_links':len(links),'nonempty_pages':all(bool(t.strip()) for t in texts),
                   'embedded_truetype_fonts':all('/FontFile2' in f.get_object().get('/FontDescriptor',{})
                       for p in r.pages for f in p['/Resources']['/Font'].values()
                       if f.get_object().get('/Subtype')=='/TrueType')})
(tmp/'pdf_checks.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
print(json.dumps(report,ensure_ascii=False,indent=2))
