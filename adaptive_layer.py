"""Conservative, explainable training adaptation; advisory until accepted."""
from datetime import date, timedelta
from db import query
from performance_engine import sport_summary

def _num(value, default=0):
    try:
        return float(value) if value is not None else default
    except (ValueError, TypeError):
        return default

def athlete_state(as_of=None):
    today=as_of or date.today()
    start=(today-timedelta(days=28)).isoformat()
    end=today.isoformat()
    activities=query("SELECT * FROM activities WHERE date(start_at)>=? AND date(start_at)<=?",(start,end))
    checkins=query("SELECT * FROM checkins WHERE date(created_at)<=? ORDER BY created_at DESC LIMIT 1",(end,))
    ci=checkins[0] if checkins else {}
    recent=query("SELECT * FROM activities WHERE date(start_at)>=? AND date(start_at)<=?",((today-timedelta(days=7)).isoformat(),end))
    sports=sport_summary(activities,28,today)
    run=sports.get("running",{})
    run_km=_num(run.get("distance_km"))
    recent_pain=max([_num(a.get("pain")) for a in recent]+[_num(ci.get("pain_score"))])
    reasons=[]
    level="normal"
    if recent_pain>=5 or str(ci.get("pain_trend") or "").lower() in ("worse","increasing","aggravation"):
        level="stop_running"
        reasons.append("Douleur élevée ou aggravée : aucune nouvelle séance de course à pied.")
    elif recent_pain>=3:
        level="reduce"
        reasons.append("Douleur présente : réduire la charge et supprimer les intensités.")
    if _num(ci.get("fatigue"),3)>=5 or _num(ci.get("sleep_hours"),7)<5.5:
        if level=="normal":level="reduce"
        reasons.append("Fatigue ou sommeil défavorable : privilégier la récupération.")
    if not activities:
        reasons.append("Historique récent absent : ne pas augmenter la charge sur la base d'une estimation.")
    return {"level":level,"reasons":reasons,"running_km_28d":round(run_km,1),
            "running_sessions_28d":int(run.get("sessions",0)),
            "activities_28d":len(activities),"latest_checkin":ci}

def adapt_prescription(plan, as_of=None):
    state=athlete_state(as_of)
    adjusted=[]
    changes=[]
    for sport,title,duration,intensity,objective in plan:
        original=duration
        if state["level"]=="stop_running" and sport in ("running","trail"):
            changes.append(title+" : retirée (douleur)")
            continue
        if state["level"] in ("reduce","stop_running"):
            if intensity!="easy":
                intensity="easy"
                title="Endurance facile — "+title
            duration=max(20,round(duration*0.7/5)*5)
        if state["activities_28d"]==0 and sport in ("running","trail"):
            duration=min(duration,75 if "longue" in title.lower() else 45)
            intensity="easy"
        if duration!=original:
            changes.append(title+f" : {original} → {duration} min")
        adjusted.append((sport,title,int(duration),intensity,objective))
    return adjusted,state,changes
