from datetime import timedelta, date

def srpe(duration,rpe):
    try:return float(duration or 0)*float(rpe or 0)
    except:return 0

def readiness(ci,recent_shift=None):
    if not ci:return 60,"NORMAL",["Check-in absent."]
    score=76; reasons=[]
    sleep=float(ci.get("sleep_hours") or 7); fatigue=int(ci.get("fatigue") or 3); soreness=int(ci.get("soreness") or 3); stress=int(ci.get("stress") or 3); motivation=int(ci.get("motivation") or 3)
    if sleep<5: score-=25; reasons.append("Sommeil très court.")
    elif sleep<6.5: score-=12; reasons.append("Sommeil sous la référence habituelle.")
    elif sleep>=8: score+=4
    score-=max(0,fatigue-3)*7; score-=max(0,soreness-3)*5; score-=max(0,stress-3)*4; score+=max(0,motivation-3)*3
    if recent_shift:
        typ=recent_shift.get("shift_type") or ""; h=float(recent_shift.get("hours_since") or 999)
        # Formation and SST block time in the calendar but never reduce readiness.
        if typ=="24h" and h<24: score-=10; reasons.append("Sortie récente d'une garde 24 h.")
        elif typ=="12h_nuit" and h<18: score-=15; reasons.append("Récupération après garde de nuit.")
        elif typ=="12h_jour" and h<12: score-=8; reasons.append("Récupération après garde de jour.")
    score=max(0,min(100,score)); status="EXCELLENT" if score>=85 else "GOOD" if score>=72 else "NORMAL" if score>=58 else "REDUCED" if score>=45 else "LOW" if score>=30 else "VERY_LOW"
    return round(score),status,reasons

def decision(ci,session,recent_shift=None,rugby_recent=False):
    score,status,reasons=readiness(ci,recent_shift); s=session or {}; pain=float((ci or {}).get("pain_score") or 0); trend=(ci or {}).get("pain_trend") or "stable"; sport=str(s.get("sport") or "").lower(); intensity=str(s.get("intensity") or "easy").lower(); priority=str(s.get("priority") or "P2"); hard=intensity in {"threshold","vo2","hard","race","quality"}
    if pain>=7 or (pain>=5 and trend=="aggravation"): return "MEDICAL_FLAG",score,status,"Douleur importante ou en aggravation : éviter la séance déclenchante et envisager un avis professionnel.","Repos / activité indolore selon tolérance."
    if sport in {"running","trail"} and pain>=4:return "REPLACE",score,status,"Douleur incompatible avec une séance à impacts aujourd'hui.","Natation facile ou vélo facile si indolore."
    if rugby_recent and sport in {"running","trail"} and hard:return ("MOVE" if priority in {"P0","P1"} else "REPLACE"),score,status,"Rugby récent + course intense : densité d'impacts trop élevée.","Natation technique ou endurance facile."
    if status in {"LOW","VERY_LOW"}:return ("ADJUST" if priority in {"P0","P1"} else "RECOVERY"),score,status,"Récupération insuffisante. "+" ".join(reasons),"Réduire 30–50 % et retirer l'intensité."
    if status=="REDUCED" and hard:return "ADJUST",score,status,"Préparation réduite : conserver l'intention en abaissant le coût.","Réduire le bloc intense d'environ 30 %."
    if session:return "EXECUTE",score,status,"Aucun signal majeur ne justifie une modification.","Séance maintenue."
    return "RECOVERY",score,status,"Aucune séance planifiée aujourd'hui.","Activité facile ou repos selon sensations."

def template_for(sport,kind,minutes):
    if sport=="running" and kind=="easy":return "Endurance facile",minutes,"easy","Développer l'endurance aérobie avec faible coût."
    if sport=="running" and kind=="quality":return "Qualité course",minutes,"threshold","Échauffement, travail contrôlé, retour au calme."
    if sport=="running" and kind=="long":return "Sortie longue",minutes,"moderate","Endurance et tolérance à la durée."
    if sport=="trail":return "Trail progressif",minutes,"moderate","Dénivelé, marche active, technique et endurance musculaire."
    if sport=="swimming":return "Natation technique",minutes,"easy","Technique, aisance et continuité."
    if sport=="cycling":return "Vélo endurance",minutes,"easy","Base aérobie et endurance spécifique."
    if sport=="strength":return "Renforcement",minutes,"moderate","Force générale, robustesse et prévention."
    return "Endurance",minutes,"easy","Développement général."

def short_plan(next_goal_name,next_goal_date,start_date=None):
    start=start_date or date.today(); out=[]; days_to=(next_goal_date-start).days if next_goal_date else 999
    if "Porto" in next_goal_name: pattern=[(0,"running","easy",50,"P1"),(1,"swimming","swim",45,"P2"),(2,"running","quality",65,"P0"),(3,"strength","strength",45,"P2"),(4,"running","easy",45,"P2"),(5,"swimming","swim",50,"P2"),(6,"running","long",100 if days_to>21 else 85,"P0")]
    elif "Saint" in next_goal_name: pattern=[(0,"running","easy",45,"P1"),(1,"strength","strength",45,"P1"),(2,"trail","trail",65,"P0"),(4,"swimming","swim",45,"P3"),(5,"running","easy",45,"P2"),(6,"trail","trail",100,"P0")]
    else: pattern=[(0,"swimming","swim",45,"P1"),(1,"cycling","bike",90,"P1"),(2,"strength","strength",45,"P2"),(3,"running","easy",50,"P1"),(5,"swimming","swim",50,"P1"),(6,"cycling","bike",120,"P0")]
    for week in [0,7]:
        for off,sport,kind,mins,priority in pattern:
            d=start+timedelta(days=week+off); title,dur,intensity,obj=template_for(sport,kind,mins); out.append(dict(date=d,sport=sport,title=title,duration=dur,priority=priority,intensity=intensity,objective=obj))
    return out
