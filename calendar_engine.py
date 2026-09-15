from datetime import datetime,date,time,timedelta

def overlaps(a_start,a_end,b_start,b_end):
    return a_start < b_end and b_start < a_end

def recurring_instances(rules, shifts, start, end):
    """Materialise recurring rules. A work shift wins over a recurring sport event."""
    out=[]; cancelled=[]
    for r in rules:
        if not int(r.get('active',1)): continue
        rule_start=date.fromisoformat(r['start_date']); rule_end=date.fromisoformat(r['end_date']) if r.get('end_date') else end
        d=max(start,rule_start)
        while d<=min(end,rule_end):
            if d.weekday()==int(r['weekday']):
                hh,mm=map(int,r['start_time'].split(':')[:2]); ev_start=datetime.combine(d,time(hh,mm)); ev_end=ev_start+timedelta(minutes=int(r.get('duration_min') or 90)); conflict=None
                for s in shifts:
                    try:
                        ss=datetime.fromisoformat(s['start_at']); se=datetime.fromisoformat(s['end_at'])
                        if overlaps(ev_start,ev_end,ss,se): conflict=s; break
                    except: pass
                item={'date':d,'start_at':ev_start,'end_at':ev_end,'title':r['title'],'event_type':r['event_type'],'duration_min':r['duration_min'],'intensity':r['intensity'],'rule_id':r['id']}
                if conflict:
                    item['reason']='Conflit avec garde '+conflict['shift_type']; cancelled.append(item)
                else: out.append(item)
            d+=timedelta(days=1)
    return out,cancelled

def combined_constraints(db_constraints, recurring):
    out=list(db_constraints)
    for x in recurring:
        out.append({'event_date':x['date'].isoformat(),'event_type':x['event_type'],'title':x['title'],'duration_min':x['duration_min'],'intensity':x['intensity'],'fixed':1,'notes':'Récurrence'})
    return out
