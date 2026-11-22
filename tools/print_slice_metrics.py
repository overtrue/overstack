"""Read material, time and support extrusion from a Bambu sliced archive."""
import math,re,zipfile,xml.etree.ElementTree as ET


def metrics(path):
    rows=[]
    with zipfile.ZipFile(path) as archive:
        info=ET.fromstring(archive.read('Metadata/slice_info.config'))
        for plate in info.findall('plate'):
            meta={m.get('key'):m.get('value') for m in plate.findall('metadata')}
            name='Metadata/plate_'+meta['index']+'.gcode'
            feature=b'';relative=True;last=0;support=0
            with archive.open(name) as data:
                for line in data:
                    if line.startswith(b'; FEATURE: '):feature=line[11:].strip()
                    code=line.split(b';')[0].strip()
                    if code==b'M83':relative=True
                    elif code==b'M82':relative=False
                    elif code.startswith(b'G92 '):
                        e=re.search(rb'\bE([-\d.]+)',code)
                        if e:last=float(e[1])
                    elif code.startswith((b'G0 ',b'G1 ',b'G2 ',b'G3 ')):
                        e=re.search(rb'\bE([-\d.]+)',code)
                        if not e:continue
                        value=float(e[1]);delta=value if relative else value-last;last=value
                        if feature in [b'Support',b'Support interface'] and delta>0 and re.search(rb'\b[XY][-\d.]',code):support+=delta
            rows.append({'plate':int(meta['index']),'total_g':float(meta['weight']),
                         'seconds':float(meta['prediction']),
                         'support_g':round(support*math.pi*(1.75/2)**2*1.25/1000,3)})
    return {'plates':rows,'plate_count':len(rows),'total_g':round(sum(r['total_g'] for r in rows),2),
            'hours':round(sum(r['seconds'] for r in rows)/3600,3),
            'support_g':round(sum(r['support_g'] for r in rows),3)}
