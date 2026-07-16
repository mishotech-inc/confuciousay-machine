#!/usr/bin/env python3
"""Confuciousay carousel generator. 1080x1350 slides, on-brand parchment/ink.
Each carousel = a folder of slide PNGs ready to upload in order.
Slide types: hook, quote, point (label+body), takeaway, cta.
"""
import os
from PIL import Image, ImageDraw, ImageFont, ImageFilter

BASE=os.path.dirname(os.path.abspath(__file__))
OUT=os.path.join(BASE,"launch-carousels"); os.makedirs(OUT,exist_ok=True)
import matplotlib
MPL=os.path.join(os.path.dirname(matplotlib.__file__),"mpl-data","fonts","ttf")
def font(n,s): return ImageFont.truetype(os.path.join(MPL,n),s)
SERIF="STIXGeneral.ttf"; SERIF_B="STIXGeneralBol.ttf"; SERIF_I="STIXGeneralItalic.ttf"
SANS_B="DejaVuSans-Bold.ttf"; SANS="DejaVuSans.ttf"

W,H=1080,1350
PARCHMENT=(243,233,210); PARCH_EDGE=(224,210,181)
CHARCOAL=(26,24,20); CHARC_EDGE=(16,14,11)
GOLD=(199,163,90); GOLD_BR=(212,178,108)
INK=(28,28,28); JADE=(47,74,63); MIST=(107,123,130)
CREAM=(240,231,211)

def wrap(d,t,f,mw):
    words,lines,cur=t.split(),[],""
    for w in words:
        s=(cur+" "+w).strip()
        if d.textlength(s,font=f)<=mw: cur=s
        else:
            if cur: lines.append(cur)
            cur=w
    if cur: lines.append(cur)
    return lines

def fit(d,t,ff,mw,maxl,start,floor,maxbh):
    s=start
    while s>floor:
        f=font(ff,s); ls=wrap(d,t,f,mw)
        a,de=f.getmetrics(); bh=int((a+de)*1.18)*len(ls)
        if len(ls)<=maxl and bh<=maxbh: return f,ls
        s-=3
    f=font(ff,floor); return f,wrap(d,t,f,mw)

def block(d,lines,f,y,fill,gap=1.18,sh=None):
    a,de=f.getmetrics(); lh=int((a+de)*gap)
    for ln in lines:
        tw=d.textlength(ln,font=f); x=(W-tw)/2
        if sh: d.text((x+2,y+2),ln,font=f,fill=sh)
        d.text((x,y),ln,font=f,fill=fill); y+=lh
    return y

def bg(dark):
    if dark:
        img=Image.new("RGB",(W,H),CHARCOAL)
        v=Image.new("L",(W,H),0); ImageDraw.Draw(v).ellipse([int(W*.05),int(H*.04),int(W*.95),int(H*.96)],fill=255)
        v=v.filter(ImageFilter.GaussianBlur(120))
        img=Image.composite(img,Image.new("RGB",(W,H),CHARC_EDGE),v)
    else:
        img=Image.new("RGB",(W,H),PARCHMENT)
        m=Image.new("L",(W,H),0); ImageDraw.Draw(m).ellipse([int(W*.04),int(H*.03),int(W*.96),int(H*.97)],fill=255)
        m=m.filter(ImageFilter.GaussianBlur(110))
        img=Image.composite(img,Image.new("RGB",(W,H),PARCH_EDGE),m)
    return img

def seal(d,cx,cy,r,col):
    d.ellipse([cx-r,cy-r,cx+r,cy+r],outline=col,width=4)
    d.ellipse([cx-r+10,cy-r+10,cx+r-10,cy+r-10],outline=col,width=1)
    d.ellipse([cx-5,cy-5,cx+5,cy+5],fill=col)

def frame(d,gold):
    d.rectangle([40,40,W-40,H-40],outline=gold,width=2)

def kicker(d,gold,sh=None):
    kf=font(SANS_B,26); k=" ".join(list("CONFUCIUS")); kw=d.textlength(k,font=kf)
    if sh: d.text(((W-kw)/2+2,112),k,font=kf,fill=sh)
    d.text(((W-kw)/2,110),k,font=kf,fill=gold)
    d.line([(W/2-80,166),(W/2+80,166)],fill=gold,width=2)

def pageno(d,i,n,col):
    pf=font(SANS_B,24); t=f"{i} / {n}"; d.text((W-130,H-90),t,font=pf,fill=col)

def slide_hook(text,i,n,dark=False):
    img=bg(dark); d=ImageDraw.Draw(img)
    txt=CREAM if dark else INK; gold=GOLD_BR if dark else GOLD; sh=(0,0,0) if dark else None
    kicker(d,gold,sh)
    f,lines=fit(d,text,SANS_B,W-180,6,76,40,560)
    a,de=f.getmetrics(); bh=int((a+de)*1.22)*len(lines)
    block(d,lines,f,(H-bh)//2-20,txt,1.22,sh)
    # swipe cue
    cf=font(SANS_B,30); c="swipe →"; cw=d.textlength(c,font=cf)
    d.text(((W-cw)/2,H-150),c,font=cf,fill=gold)
    frame(d,gold); pageno(d,i,n,MIST if not dark else (130,120,100))
    return img

def slide_quote(quote,source,i,n,dark=False):
    img=bg(dark); d=ImageDraw.Draw(img)
    txt=CREAM if dark else INK; gold=GOLD_BR if dark else GOLD; sh=(0,0,0) if dark else None
    attrc=(200,190,168) if dark else JADE; srcc=(150,140,118) if dark else MIST
    kicker(d,gold,sh)
    qm=font(SERIF_B,140); d.text((W/2-d.textlength('“',font=qm)/2,200),'“',font=qm,fill=gold)
    q=quote
    f,lines=fit(d,q,SERIF,W-160,7,84,46,560)
    a,de=f.getmetrics(); bh=int((a+de)*1.2)*len(lines)
    end=block(d,lines,f,(H-bh)//2-10,txt,1.2,sh)
    af=font(SERIF_I,40); aw=d.textlength("Confucius",font=af)
    d.text(((W-aw)/2,end+40),"Confucius",font=af,fill=attrc)
    sf=font(SANS,24); sw=d.textlength(source,font=sf)
    d.text(((W-sw)/2,end+100),source,font=sf,fill=srcc)
    frame(d,gold); pageno(d,i,n,MIST if not dark else (130,120,100))
    return img

def slide_point(label,body,i,n,dark=False):
    img=bg(dark); d=ImageDraw.Draw(img)
    txt=CREAM if dark else INK; gold=GOLD_BR if dark else GOLD; sh=(0,0,0) if dark else None
    bodyc=(210,200,180) if dark else (70,70,70)
    kicker(d,gold,sh)
    # label (gold, sans bold)
    lf,llines=fit(d,label,SANS_B,W-180,3,58,34,260)
    a,de=lf.getmetrics(); lbh=int((a+de)*1.18)*len(llines)
    y=int(H*0.30)
    block(d,llines,lf,y,gold,1.18,sh)
    y+=lbh+40
    if body:
        bf,blines=fit(d,body,SERIF,W-180,6,52,34,360)
        block(d,blines,bf,y,txt,1.22,sh)
    frame(d,gold); pageno(d,i,n,MIST if not dark else (130,120,100))
    return img

def slide_cta(cta,i,n,dark=False):
    img=bg(dark); d=ImageDraw.Draw(img)
    txt=CREAM if dark else INK; gold=GOLD_BR if dark else GOLD; sh=(0,0,0) if dark else None
    kicker(d,gold,sh)
    f,lines=fit(d,cta,SERIF,W-200,4,64,40,360)
    a,de=f.getmetrics(); bh=int((a+de)*1.2)*len(lines)
    block(d,lines,f,(H-bh)//2-60,txt,1.2,sh)
    seal(d,W/2,H-300,34,gold)
    hf=font(SANS_B,30); h="@confuciousay"; hw=d.textlength(h,font=hf)
    d.text(((W-hw)/2,H-240),h,font=hf,fill=gold)
    frame(d,gold); pageno(d,i,n,MIST if not dark else (130,120,100))
    return img

def build(idx, dark, slides):
    folder=os.path.join(OUT,f"carousel_{idx:02d}"); os.makedirs(folder,exist_ok=True)
    n=len(slides)
    for i,s in enumerate(slides,1):
        kind=s[0]
        if kind=="hook": img=slide_hook(s[1],i,n,dark)
        elif kind=="quote": img=slide_quote(s[1],s[2],i,n,dark)
        elif kind=="point": img=slide_point(s[1],s[2],i,n,dark)
        elif kind=="cta": img=slide_cta(s[1],i,n,dark)
        img.save(os.path.join(folder,f"slide_{i}.png"))
    return n

# ---- Explicit slide content per carousel (from the 90-slot bank) ----
CAROUSELS = [
 # 1
 (False,[("hook","Confucius on the goal you keep wanting to quit."),
   ("quote","If your goal seems impossible, don't change the goal, change your approach.","Attributed to Confucius"),
   ("point","The goal isn't the problem.","The route is. Lowering the goal feels like relief. It's just slow surrender."),
   ("point","Adjust the steps, not the dream.","Same destination. Different road. Keep the goal, rebuild the plan."),
   ("cta","Save this for your next wobble.")]),
 # 2
 (False,[("hook","Confucius on why you keep grinding and getting nowhere."),
   ("quote","Life's results depend on effort. If you want good work, sharpen your tools first.","Analects 15:10"),
   ("point","More hours vs sharper system.","Working harder with a dull blade is suffering with extra steps."),
   ("point","Sharpen these first:","Your skills. Your systems. Your sleep. Then swing."),
   ("cta","Save before your next grind session.")]),
 # 3
 (False,[("hook","Confucius on doing it for the post vs doing it for real."),
   ("quote","Learn to improve yourself, not to impress everyone else.","Analects 14:25"),
   ("point","Learning for applause vs learning for you.","If the work is for the audience, the audience is the only thing growing."),
   ("point","Do it where no one's watching.","That's the only version that actually changes you."),
   ("cta","Save and screenshot the one that hit.")]),
 # 4
 (False,[("hook","Confucius on why you're quietly mad at everyone."),
   ("quote","Demand more from yourself and less from others, and resentment stays away.","Analects 15:14"),
   ("point","Unspoken standard = built-in resentment.","You're angry people failed a test you never told them about."),
   ("point","The fix:","Raise the bar on yourself. Lower the expectation on others."),
   ("cta","Send to someone holding a quiet grudge.")]),
 # 5
 (True,[("hook","Confucius on the shortcut you're tempted to take."),
   ("quote","Money won the wrong way means nothing to me.","Analects 7:15"),
   ("point","Dirty money spends the same.","It just sleeps a lot worse."),
   ("point","Some wins cost more than they pay.","Clean money keeps clean nights."),
   ("cta","Save this before the next shortcut.")]),
 # 6
 (False,[("hook","Confucius on why you keep blowing up your own plans."),
   ("quote","Smooth talk corrupts character; impatience over small things wrecks big plans.","Analects 15:26"),
   ("point","Big dreams die to small tempers.","Not to disasters. To a Tuesday."),
   ("point","The 3 small leaks:","A short temper. A petty text. An impatient choice."),
   ("cta","Save and guard the little moments.")]),
 # 7 (5 rules)
 (False,[("hook","5 Confucius rules for people who feel overlooked."),
   ("point","1. Work on the skill, not the spotlight.","The spotlight follows the skill, never the other way around."),
   ("point","2. Stop keeping score of credit.","Scorekeeping burns energy you could spend getting better."),
   ("point","3. Become undeniable, then quiet.","Let the work argue for you."),
   ("point","4. Recognition lags effort.","It always arrives late. Keep going anyway."),
   ("point","5. Be worth knowing, not just known.","Confucius chased being worthy of recognition, not the recognition. Build that and the spotlight catches up."),
   ("cta","Save this for the next time you feel invisible.")]),
 # 8
 (False,[("hook","Confucius on why your side project keeps stalling."),
   ("quote","If comfort is your goal, you're not serious about your craft.","Analects 14:3"),
   ("point","Mastery and comfort don't share an address.","Optimize for cozy and you opt out of great."),
   ("point","The craft costs the couch.","Pick one."),
   ("cta","Save this if your project keeps stalling.")]),
 # 9 (3 friends)
 (False,[("hook","Confucius on the three friends worth keeping."),
   ("quote","The best friends are honest, sincere, and wise.","Analects 16:4"),
   ("point","The honest one.","Tells you the truth even when it costs them."),
   ("point","The sincere one.","Means it. No performance, no agenda."),
   ("point","The wise one.","Sees what you can't see yet."),
   ("cta","Tag the friend who's all three.")]),
 # 10
 (False,[("hook","3 Confucius truths about slow progress."),
   ("quote","Progress is yours, one basket of effort at a time.","Analects 9:18"),
   ("point","1. One basket a day = a mound a year.","The math is quiet but it never lies."),
   ("point","2. Invisible progress is still progress.","Too slow to see doesn't mean it isn't happening."),
   ("point","3. The only way to lose is to stop.","Quit one basket short of the hill and the stopping is on you."),
   ("cta","Save this for a discouraging day.")]),
 # 11
 (False,[("hook","Confucius on finding the thing that makes time disappear."),
   ("quote","Chase knowledge so hard you forget to eat and forget your worries.","Analects 7:18"),
   ("point","The work that eats your hunger.","So good it quiets your problems while you do it."),
   ("point","Most quit before it gets interesting.","The good part is on the far side of boring."),
   ("cta","Save this until you find yours.")]),
 # 12
 (False,[("hook","Confucius on how to trust people without being naive."),
   ("quote","Don't expect deceit, but catch it the moment it comes.","Analects 14:33"),
   ("point","Naive and paranoid both lose.","One gets used. The other gets lonely."),
   ("point","The middle path:","Trust freely. Keep your eyes open. Notice fast."),
   ("cta","Save this for the next gut feeling.")]),
]

total=0
for i,(dark,slides) in enumerate(CAROUSELS,1):
    n=build(i,dark,slides); total+=n
    print(f"carousel_{i:02d}: {n} slides ({'ink' if dark else 'parchment'})")
print(f"\nTotal: {total} slides across {len(CAROUSELS)} carousels in {OUT}")
