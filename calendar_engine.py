from datetime import datetime,date,time,timedelta

def overlaps(a_start,a_end,b_start,b_end): return a_start < b_end and b_start < a_end

def work_cycle_instances(cycles,start,end,exceptions=None):
    """Generate theoretical 24h/72h shifts, then apply one-off exceptions without shifting the cycle."""
    out=[]; exceptions=exceptions or []
    exmap={(int(x['cycle_id']),x['original_date']):x for x in exceptions}
    for c in cycles:
        if not int(c.get('active',1)): continue
        anchor=date.fromisoformat(c['anchor_date']); step=max(1,int(c.get('cycle_days') or 4)); d=anchor
        while d>start: d-=timedelta(days=step)
        while d<start: d+=timedelta(days=step)
        while d<=end:
            original=d.isoformat(); ex=exmap.get((int(c['id']),original))
            if ex and ex['action']=='delete':
                d+=timedelta(days=step); continue
            if ex and ex['action']=='move' and ex.get('new_start_at') and ex.get('new_end_at'):
                ss=datetime.fromisoformat(ex['new_start_at']); se=datetime.fromisoformat(ex['new_end_at']); moved=True
            else:
                ss=datetime.combine(d,time(8)); se=ss+timedelta(hours=24); moved=False
            if ss.date()<=end and se.date()>=start:
                out.append({'start_at':ss.isoformat(timespec='minutes'),'end_at':se.isoformat(timespec='minutes'),'shift_type':'24h','notes':'Cycle automatique','virtual':True,'cycle_id':c['id'],'original_date':original,'moved':moved})
            d+=timedelta(days=step)
    return out

def all_shifts(manual,cycles,start,end,exceptions=None):
    auto=work_cycle_instances(cycles,start,end,exceptions); seen={(x['start_at'],x['end_at']) for x in manual}; return manual+[x for x in auto if (x['start_at'],x['end_at']) not in seen]

def recurring_instances(rules, shifts, start, end):
    out=[]; cancelled=[]
    for r in rules:
        if not int(r.get('active',1)): continue
        rule_start=date.fromisoformat(r['start_date']); rule_end=date.fromisoformat(r['end_date']) if r.get('end_date') else end; d=max(start,rule_start)
        while d<=min(end,rule_end):
            if d.weekday()==int(r['weekday']):
                hh,mm=map(int,r['start_time'].split(':')[:2]); ev_start=datetime.combine(d,time(hh,mm)); ev_end=ev_start+timedelta(minutes=int(r.get('duration_min') or 90)); conflict=None
                for s in shifts:
                    try:
                        if overlaps(ev_start,ev_end,datetime.fromisoformat(s['start_at']),datetime.fromisoformat(s['end_at'])): conflict=s; break
                    except: pass
                item={'date':d,'start_at':ev_start,'end_at':ev_end,'title':r['title'],'event_type':r['event_type'],'duration_min':r['duration_min'],'intensity':r['intensity'],'rule_id':r['id']}
                if conflict: item['reason']='Conflit avec garde '+conflict['shift_type']; cancelled.append(item)
                else: out.append(item)
            d+=timedelta(days=1)
    return out,cancelled

def combined_constraints(db_constraints, recurring):
    out=list(db_constraints)
    for x in recurring: out.append({'event_date':x['date'].isoformat(),'event_type':x['event_type'],'title':x['title'],'duration_min':x['duration_min'],'intensity':x['intensity'],'fixed':1,'notes':'Récurrence'})
    return out
