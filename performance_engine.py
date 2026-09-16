from datetime import date,timedelta

def activity_load(a):
    dur=float(a.get('duration_min') or 0); rpe=float(a.get('rpe') or 0); sport=str(a.get('sport') or '').lower()
    factor={'running':1.15,'trail':1.25,'rugby':1.30,'cycling':0.85,'swimming':0.70,'strength':1.0,'dance':0.75}.get(sport,1.0)
    return round(dur*rpe*factor)

def load_summary(activities,today=None):
    today=today or date.today(); daily={}
    for a in activities:
        try:d=date.fromisoformat(str(a['start_at'])[:10])
        except:continue
        daily[d]=daily.get(d,0)+activity_load(a)
    load7=sum(v for d,v in daily.items() if today-timedelta(days=6)<=d<=today)
    load28=sum(v for d,v in daily.items() if today-timedelta(days=27)<=d<=today)
    baseline=load28/4 if load28 else 0
    ratio=round(load7/baseline,2) if baseline else None
    return {'load7':round(load7),'load28':round(load28),'weekly_baseline':round(baseline),'ratio':ratio,'daily':daily}

def sport_summary(activities,days=28,today=None):
    today=today or date.today(); start=today-timedelta(days=days-1); out={}
    for a in activities:
        try:d=date.fromisoformat(str(a['start_at'])[:10])
        except:continue
        if not start<=d<=today:continue
        s=a.get('sport') or 'other'; x=out.setdefault(s,{'minutes':0,'distance_km':0,'elevation_m':0,'sessions':0,'load':0})
        x['minutes']+=float(a.get('duration_min') or 0); x['distance_km']+=float(a.get('distance_km') or 0); x['elevation_m']+=float(a.get('elevation_m') or 0); x['sessions']+=1; x['load']+=activity_load(a)
    return out

def readiness_trend(checkins,n=14):
    rows=[]
    for c in checkins[:n]:
        sleep=float(c.get('sleep_hours') or 7); fatigue=float(c.get('fatigue') or 3); stress=float(c.get('stress') or 3); soreness=float(c.get('soreness') or 3); pain=float(c.get('pain_score') or 0)
        score=max(0,min(100,80+(sleep-7)*5-(fatigue-3)*8-(stress-3)*4-(soreness-3)*5-pain*2))
        rows.append({'date':str(c.get('created_at'))[:10],'score':round(score)})
    return rows
