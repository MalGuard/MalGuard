"""Build original GitHub-safe brand assets. Run after render_emblem.py."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import numpy as np, math, html, json

ROOT=Path(__file__).resolve().parents[1]
A=ROOT/'assets'
W,H=1000,420
FONT='/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
BOLD='/usr/share/fonts/truetype/dejavu/DejaVuSansCondensed-Bold.ttf'
MONO='/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf'
def font(size,bold=False,mono=False): return ImageFont.truetype(MONO if mono else BOLD if bold else FONT,size)

def background():
 y,x=np.mgrid[0:H,0:W]; c=np.zeros((H,W,3),dtype=float)+[8,14,31]
 for px,py,sx,sy,col in [(790,180,230,220,[7,42,66]),(560,430,450,160,[31,10,55]),(0,0,420,310,[4,11,22])]:
  g=np.exp(-((x-px)/sx)**2-((y-py)/sy)**2);c+=g[:,:,None]*np.array(col)
 im=Image.fromarray(np.clip(c,0,255).astype('uint8')).convert('RGBA');d=ImageDraw.Draw(im)
 for xx in range(630,1000,45): d.line((xx,24,xx,390),fill=(43,69,95,70))
 for yy in range(30,420,45): d.line((625,yy,980,yy),fill=(43,69,95,70))
 rng=np.random.default_rng(2026)
 for xx,yy,r in zip(rng.integers(620,976,28),rng.integers(30,388,28),rng.integers(1,3,28)):
  d.ellipse((int(xx-r),int(yy-r),int(xx+r),int(yy+r)),fill=(115,152,190,100))
 d.rounded_rectangle((1,1,W-2,H-2),radius=25,outline=(58,73,106,255),width=2)
 d.text((46,40),'MALGUARD  /  DEFENSIVE ENGINEERING',font=font(12,mono=True),fill='#66d5ff')
 d.line((46,74,103,74),fill='#00bdf4',width=3)
 # Text is kept still, while the original logo and orbital sculpture move.
 d.text((40,95),'MALGUARD',font=font(73,True),fill='#edf4ff',stroke_width=0)
 d.text((46,203),'Inspect before you trust.',font=font(28,True),fill='#c1d8fa')
 d.text((46,251),'Safer game mods. Evidence-led security.',font=font(16),fill='#8fa7c9')
 for xx,ww,label in [(46,126,'OPEN SOURCE'),(184,151,'DEFENSIVE DESIGN'),(347,126,'EVIDENCE FIRST')]:
  d.rounded_rectangle((xx,299,xx+ww,331),radius=16,fill='#112340',outline='#2a476c')
  d.text((xx+13,309),label,font=font(10,mono=True),fill='#8cdbfa')
 d.line((46,372,954,372),fill='#273451',width=1)
 d.text((46,389),'MOHAMMAD REZA AZARDERAKHSH',font=font(11,mono=True),fill='#9fb0cb')
 d.text((737,389),'malguard.github.io',font=font(12,mono=True),fill='#70cffa')
 return im

def compose():
 base=background();frames=[];mobile=[]
 mb=background().resize((540,640));md=ImageDraw.Draw(mb)
 md.rectangle((0,0,540,640),fill='#0b142a')
 md.rounded_rectangle((1,1,538,638),radius=24,outline='#293653',width=2)
 md.text((26,31),'MALGUARD / DEFENSIVE ENGINEERING',font=font(11,mono=True),fill='#66d5ff')
 md.text((23,64),'MALGUARD',font=font(64,True),fill='#edf4ff')
 md.text((27,153),'Inspect before you trust.',font=font(24,True),fill='#c1d8fa')
 md.text((27,594),'OPEN SOURCE  /  EVIDENCE FIRST',font=font(12,mono=True),fill='#70cffa')
 md.line((27,575,513,575),fill='#293653')
 for k in range(90):
  im=base.copy(); emblem=Image.open(ROOT/f'render/emblem-{k:03d}.png').convert('RGBA').filter(ImageFilter.GaussianBlur(.35)).resize((386,386),Image.Resampling.LANCZOS)
  im.alpha_composite(emblem,(604,-1))
  frames.append(im.convert('RGB'))
  mi=mb.copy();mi.alpha_composite(emblem.resize((414,414),Image.Resampling.LANCZOS),(63,180));mobile.append(mi.convert('RGB'))
 frames[0].save(A/'malguard-3d-poster.png',optimize=True)
 for k,im in enumerate(frames): im.save(ROOT/f'render/hero-{k:03d}.png')
 # A shared palette avoids flicker and preserves the dark color field.
 sheet=Image.new('RGB',(1000,420*6))
 for j,k in enumerate([0,15,30,45,60,75]):sheet.paste(frames[k],(0,j*420))
 palette=sheet.quantize(colors=256,method=Image.Quantize.MEDIANCUT)
 out=[im.quantize(palette=palette,dither=Image.Dither.NONE) for im in frames]
 out[0].save(A/'malguard-3d.gif',save_all=True,append_images=out[1:],duration=[70,60,70]*30,loop=0,optimize=True,disposal=1)
 mobile[0].save(A/'malguard-3d-mobile-poster.png',optimize=True)
 mobile=[im.resize((390,462),Image.Resampling.LANCZOS) for im in mobile]
 sheet=Image.new('RGB',(390,462*6))
 for j,k in enumerate([0,15,30,45,60,75]):sheet.paste(mobile[k],(0,j*462))
 mp=sheet.quantize(colors=256,method=Image.Quantize.MEDIANCUT)
 mout=[im.quantize(palette=mp,dither=Image.Dither.NONE) for im in mobile]
 mout[0].save(A/'malguard-3d-mobile.gif',save_all=True,append_images=mout[1:],duration=[70,60,70]*30,loop=0,optimize=True,disposal=1)
 avatar=Image.new('RGBA',(512,512),'#09132b');e=Image.open(ROOT/'render/emblem-000.png').convert('RGBA').filter(ImageFilter.GaussianBlur(.35));avatar.alpha_composite(e.resize((500,500)),(6,6));avatar.convert('RGB').save(A/'avatar-3d.png',optimize=True)
 social=background().resize((1280,640),Image.Resampling.LANCZOS)
 # Reuse the finished brand composition in a GitHub social-preview canvas.
 poster=frames[0].resize((1200,504),Image.Resampling.LANCZOS);social.paste(poster,(40,68));social.convert('RGB').save(A/'social-preview.png',optimize=True)

DEFS='''<defs><linearGradient id="bg" x2="1" y2="1"><stop stop-color="#0b172c"/><stop offset="1" stop-color="#16112d"/></linearGradient><linearGradient id="accent"><stop stop-color="#00bdf4"/><stop offset=".55" stop-color="#2F6BFF"/><stop offset="1" stop-color="#9a6bff"/></linearGradient><radialGradient id="aura"><stop stop-color="#2F6BFF" stop-opacity=".28"/><stop offset="1" stop-color="#2F6BFF" stop-opacity="0"/></radialGradient><filter id="glow"><feGaussianBlur stdDeviation="3"/></filter></defs>'''
STYLE='''<style>text{font-family:Arial,Helvetica,sans-serif}.mono{font-family:monospace;letter-spacing:2px}.orbit{transform-origin:center;animation:turn 14s linear infinite}.float{animation:float 6s ease-in-out infinite}.pulse{animation:pulse 4s ease-in-out infinite}@keyframes turn{to{transform:rotate(360deg)}}@keyframes float{50%{transform:translateY(-5px)}}@keyframes pulse{50%{opacity:.4}}@media(prefers-reduced-motion:reduce){*{animation:none!important}}</style>'''
logo=ET_LOGO=None
logo=(A/'official-logo.svg').read_text(); logo_inner=logo[logo.index('>')+1:logo.rindex('</svg>')]
def shell(w,h,title,body):
 return f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img" aria-labelledby="title"><title id="title">{html.escape(title)}</title>{DEFS}{STYLE}<rect x="1" y="1" width="{w-2}" height="{h-2}" rx="20" fill="url(#bg)" stroke="#293653"/>{body}</svg>'

def cards():
 data=[('core','01','MalGuard Core','Inspection. Integrity. Isolation.','Shared defensive foundations, built in the open.','OPEN SOURCE / MIT','#00bdf4'),('gta','02','GTA Guard','Game mods deserve a closer look.','The first product focus of the MalGuard project.','GAME-MOD SECURITY','#8186ff'),('website','03','The MalGuard website','Products, documentation and release status.','Explore the public platform and trust center.','OFFICIAL WEBSITE','#00bdf4'),('collaborate','04','Build with us','Careful engineering. Thoughtful review.','Explore contribution guidelines and public source.','CONTRIBUTIONS','#a28aff')]
 for key,n,title,line,desc,tag,col in data:
  body=f'''<circle cx="451" cy="15" r="180" fill="url(#aura)"/><path d="M30 1H130" stroke="{col}" stroke-width="3"/><text x="28" y="39" fill="{col}" font-size="11" class="mono">{tag}</text><text x="455" y="40" text-anchor="end" fill="#607599" font-size="11" class="mono">{n}</text><text x="28" y="94" fill="#edf4ff" font-size="32" font-weight="700">{title}</text><text x="28" y="130" fill="#bdd0ee" font-size="17">{line}</text><text x="28" y="158" fill="#8d9fbd" font-size="14">{desc}</text><path d="M28 190H459" stroke="#293653"/><text x="28" y="219" fill="{col}" font-size="12" class="mono">EXPLORE</text><g class="float"><path d="M429 210H451M444 203L451 210L444 217" fill="none" stroke="{col}" stroke-width="2"/></g>'''
  (A/f'card-{key}.svg').write_text(shell(488,242,title+'. '+line+' '+desc,body))
 body='''<circle cx="875" cy="85" r="210" fill="url(#aura)"/><text x="38" y="37" class="mono" font-size="11" fill="#69d5ff">THE PERSON BEHIND MALGUARD</text><text x="36" y="84" fill="#edf4ff" font-size="31" font-weight="700">Mohammad Reza Azarderakhsh</text><text x="38" y="117" fill="#a8bddc" font-size="16">Creator of MalGuard · Defensive engineering · Safer gaming</text><text x="38" y="147" fill="#7f95b6" font-size="14">Building tools that explain the evidence, the uncertainty and the next step.</text>'''+f'<g transform="translate(871 24) scale(.36)" class="pulse">{logo_inner}</g>'
 (A/'about.svg').write_text(shell(1000,176,'Mohammad Reza Azarderakhsh, creator of MalGuard. Building tools that explain evidence and uncertainty.',body))
 body=f'<g transform="translate(383 22) scale(.20)">{logo_inner}</g><text x="27" y="39" fill="#69d5ff" font-size="10" class="mono">CREATOR OF MALGUARD</text><text x="26" y="84" fill="#edf4ff" font-size="28" font-weight="700">Mohammad Reza</text><text x="26" y="120" fill="#edf4ff" font-size="28" font-weight="700">Azarderakhsh</text><text x="27" y="162" fill="#a8bddc" font-size="16">Defensive engineering. Safer gaming.</text><text x="27" y="193" fill="#8fa7c9" font-size="14">Evidence, uncertainty and the next step.</text>'
 (A/'about-mobile.svg').write_text(shell(480,223,'Mohammad Reza Azarderakhsh, creator of MalGuard.',body))
 # Motion follows four explicit steps. No claim of live telemetry.
 body='<text x="36" y="37" class="mono" font-size="11" fill="#69d5ff">THE ENGINEERING PRINCIPLE</text>'
 labels=[('01','INSPECT','Files, archives and scripts'),('02','VERIFY','Evidence and capability'),('03','ISOLATE','Only with verified support'),('04','REPORT','Findings and limitations')]
 for j,(n,title,sub) in enumerate(labels):
  x=36+j*243;body+=f'<text x="{x}" y="86" fill="#516c9e" font-size="15" class="mono">{n}</text><text x="{x}" y="118" fill="#e5edff" font-size="22" font-weight="700">{title}</text><text x="{x}" y="147" fill="#94a9cb" font-size="13">{sub}</text>'
  if j<3:body+=f'<path d="M{x+159} 108H{x+208}M{x+201} 101L{x+208} 108L{x+201} 115" stroke="#365985" stroke-width="1.5" fill="none"/>'
 body+='<path d="M36 176H964" stroke="#283654"/><path d="M36 176H964" stroke="url(#accent)" stroke-width="2" stroke-dasharray="90 838"><animate attributeName="stroke-dashoffset" values="0;-928" dur="6s" repeatCount="indefinite"/></path>'
 (A/'principles.svg').write_text(shell(1000,201,'Inspect files, verify evidence, isolate only with verified support, report findings and limitations.',body))
 body='<text x="26" y="35" class="mono" font-size="10" fill="#69d5ff">THE ENGINEERING PRINCIPLE</text>'
 for j,(n,title,sub) in enumerate(labels):
  x=26+(j%2)*235;y=73+(j//2)*112
  body+=f'<text x="{x}" y="{y}" fill="#516c9e" font-size="12" class="mono">{n}</text><text x="{x}" y="{y+29}" fill="#e5edff" font-size="22" font-weight="700">{title}</text><text x="{x}" y="{y+54}" fill="#94a9cb" font-size="12">{sub}</text>'
 body+='<path d="M26 269H454" stroke="url(#accent)"/>'
 (A/'principles-mobile.svg').write_text(shell(480,290,'Inspect, verify, isolate with verified support, and report limitations.',body))
 body=f'<circle cx="500" cy="40" r="250" fill="url(#aura)"/><text x="500" y="66" fill="#e4eeff" text-anchor="middle" font-size="30" font-weight="700">Security before trust.</text><text x="500" y="105" fill="#91a8cc" text-anchor="middle" font-size="15">Evidence first. Clear limits. Better decisions.</text><path d="M300 138H700" stroke="url(#accent)"/>'
 (A/'footer.svg').write_text(shell(1000,164,'Security before trust. Evidence first, clear limits, better decisions.',body))

if __name__=='__main__':
 cards()
 if (ROOT/'render/emblem-089.png').exists():compose()
 print(json.dumps({p.name:p.stat().st_size for p in A.iterdir()},indent=2))
