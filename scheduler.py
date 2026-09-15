from datetime import date, timedelta

HARD_TYPES={"rugby_match","rugby_training"}

def phase_for(goal_name):
    n=(goal_name or '').lower()
    if 'porto' in n:return 'SEMI'
    if 'saint' in n:return 'TRAIL'
    if 'marathon' in n or 'aveiro' in n:return 'MARATHON'
    if 'half' in n or 'annecy' in n:return 'HALF'
    if 'léman' in n or 'leman' in n:return 'FULL'
    return 'BASE'

def needs(phase):
    if phase=='SEMI': return [('running','quality',65,'P0'),('running','long',100,'P0'),('running','easy',50,'P1'),('swimming','easy',45,'P2'),('swimming','easy',50,'P2'),('strength','moderate',45,'P2')]
    if phase=='TRAIL': return [('trail','quality',70,'P0'),('trail','long',110,'P0'),('running','easy',45,'P1'),('strength','moderate',50,'P1'),('swimming','easy',45,'P3')]
    if phase=='MARATHON': return [('running','quality',75,'P0'),('running','long',120,'P0'),('running','easy',55,'P1'),('running','easy',45,'P2'),('cycling','easy',90,'P2'),('strength','moderate',45,'P2')]
    return [('swimming','easy',50,'P1'),('swimming','quality',55,'P1'),('cycling','easy',120,'P0'),('cycling','quality',90,'P1'),('running','easy',50,'P1'),('running','quality',65,'P1'),('strength','moderate',45,'P2')]

def title_for(sport,intensity):
    if sport=='running': return 'Course — qualité' if intensity=='quality' else 'Course — endurance'
    if sport=='trail': return 'Trail — spécifique' if intensity=='quality' else 'Trail — sortie longue'
    if sport=='cycling': return 'Vélo — travail spécifique' if intensity=='quality' else 'Vélo — endurance'
    if sport=='swimming': return 'Natation — qualité' if intensity=='quality' else 'Natation — technique/endurance'
    if sport=='strength': return 'Renforcement — robustesse'
    return 'Entraînement'

def objective_for(sport,intensity,phase):
    if sport in {'running','trail'} and intensity=='quality': return 'Stimulus spécifique contrôlé, sans transformer la séance en test.'
    if sport in {'running','trail'}: return 'Développer l’endurance et la tolérance à la durée.'
    if sport=='cycling': return 'Construire l’endurance cycliste avec un coût musculosquelettique modéré.'
    if sport=='swimming': return 'Technique, continuité et économie de nage.'
    return 'Force générale, robustesse et prévention.'

def day_state(d, shifts, constraints):
    state={'blocked':False,'hard':False,'recovery':False,'events':[],'capacity':120}
    for s in shifts:
        sd=date.fromisoformat(s['start_at'][:10]); ed=date.fromisoformat(s['end_at'][:10]); typ=s.get('shift_type','')
        if sd<=d<=ed:
            state['events'].append(typ)
            if typ in {'12h_jour','12h_nuit','24h'}: state['capacity']=35
            elif typ in {'formation','sst'}: state['capacity']=60
            if typ in {'12h_jour','12h_nuit'}: state['blocked']=True
        if ed==d-timedelta(days=1):
            if typ=='24h': state['recovery']=True; state['capacity']=min(state['capacity'],60)
            if typ=='12h_nuit': state['recovery']=True; state['capacity']=min(state['capacity'],45)
    for c in constraints:
        if date.fromisoformat(c['event_date'])==d:
            state['events'].append(c['title'])
            if c['event_type'] in HARD_TYPES or c.get('intensity')=='hard': state['hard']=True
            if c.get('fixed',1): state['capacity']=max(0,state['capacity']-int(c.get('duration_min') or 60))
    return state

def compatible(session,d,state,placed):
    sport,intensity,duration,priority=session
    same_day=[p for p in placed if p['date']==d]
    # V5.1: one generated endurance workout per day by default. Fixed rugby/dance remain separate constraints.
    if same_day: return False
    if state['blocked']: return False
    if duration>state['capacity']+25: return False
    if state['recovery'] and intensity=='quality': return False
    if state['hard'] and (intensity=='quality' or sport in {'running','trail'}): return False
    for p in placed:
        delta=abs((p['date']-d).days)
        if delta<=1 and p['intensity']=='quality' and intensity=='quality': return False
        if delta<=1 and p['sport'] in {'running','trail'} and sport in {'running','trail'} and (p['intensity']=='quality' or intensity=='quality'): return False
    return True

def score_day(session,d,state,placed,start):
    sport,intensity,duration,priority=session; score=100
    score-=max(0,duration-state['capacity'])*2
    if state['recovery']: score-=20
    if state['events']: score-=8*len(state['events'])
    if intensity=='quality' and d.weekday() in {1,2,3,5}: score+=5
    if duration>=90 and d.weekday() in {5,6}: score+=10
    if sport=='swimming' and d.weekday() in {1,3,5}: score+=4
    score-=sum(8 for p in placed if abs((p['date']-d).days)<=1 and p['priority'] in {'P0','P1'})
    return score

def build_plan(goal, shifts, constraints, start=None, days=14):
    start=start or date.today(); phase=phase_for(goal['name']); req=needs(phase); placed=[]; unscheduled=[]
    for week in range((days+6)//7):
        week_start=start+timedelta(days=7*week); week_end=min(start+timedelta(days=days-1),week_start+timedelta(days=6))
        for session in req:
            candidates=[]; d=week_start
            while d<=week_end:
                state=day_state(d,shifts,constraints)
                if compatible(session,d,state,placed): candidates.append((score_day(session,d,state,placed,start),d,state))
                d+=timedelta(days=1)
            if not candidates:
                unscheduled.append({'week':week+1,'sport':session[0],'priority':session[3]}); continue
            _,best,state=max(candidates,key=lambda x:x[0]); sport,intensity,duration,priority=session
            placed.append({'date':best,'sport':sport,'title':title_for(sport,intensity),'duration':duration,'priority':priority,'intensity':'threshold' if intensity=='quality' else intensity,'objective':objective_for(sport,intensity,phase),'context':', '.join(state['events']) if state['events'] else 'Fenêtre disponible'})
    placed.sort(key=lambda x:x['date'])
    return {'phase':phase,'sessions':placed,'unscheduled':unscheduled}
