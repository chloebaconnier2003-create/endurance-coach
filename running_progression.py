"""Conservative phase-specific running progression, based on athlete's 2–3 h baseline.

Targets are provisional planning envelopes, not automatic requirements.
Rugby, symptoms and completed training can override them.
"""
from datetime import date

def running_target_minutes(start):
    if not isinstance(start,date):
        start=date.fromisoformat(str(start)[:10])
    anchors=[
        (date(2026,10,12),150),
        (date(2026,11,2),135),
        (date(2026,12,7),155),
        (date(2027,1,4),175),
        (date(2027,2,1),205),
        (date(2027,3,1),235),
        (date(2027,3,29),275),
        (date(2027,4,5),295),
        (date(2027,4,12),195),
        (date(2027,4,19),100),
        (date(2027,4,26),50),
        (date(2027,5,10),130),
        (date(2027,6,7),175),
        (date(2027,6,14),115),
        (date(2027,6,21),50),
        (date(2027,7,5),155),
        (date(2027,8,2),185),
        (date(2027,8,23),200),
        (date(2027,8,30),150),
        (date(2027,9,6),80),
    ]
    if start<=anchors[0][0]:return anchors[0][1]
    for (a,va),(b,vb) in zip(anchors,anchors[1:]):
        if a<=start<b:
            fraction=(start-a).days/(b-a).days
            return round((va+(vb-va)*fraction)/5)*5
    return anchors[-1][1]

def progress_running(plan,start,phase):
    """Adjust planned running exposure; do not force volume on constrained weeks."""
    target=running_target_minutes(start)
    if phase in ('marathon','base_run','reset'):
        running=[i for i,x in enumerate(plan) if x[0] in ('running','trail')]
        if not running:return plan
        # Cap long run at 45% of running target and 165 min, to avoid a
        # disproportionate single-session spike from the 13 km baseline.
        long_idx=max(running,key=lambda i:plan[i][2] if 'long' in plan[i][1].lower() else -1)
        adjusted=list(plan)
        if 'long' in plan[long_idx][1].lower():
            sp,ti,du,ins,ob=adjusted[long_idx]
            cap=min(165,max(75,round(target*.45/5)*5))
            adjusted[long_idx]=(sp,ti,min(du,cap),ins,ob)
        current=sum(adjusted[i][2] for i in running)
        if current>target:
            # Trim easier short runs first, preserving a useful minimum.
            for i in sorted(running,key=lambda j:('long' in adjusted[j][1].lower(),adjusted[j][3]!='easy')):
                if current<=target:break
                sp,ti,du,ins,ob=adjusted[i]
                cut=min(max(0,du-25),current-target)
                cut=(cut//5)*5
                adjusted[i]=(sp,ti,du-cut,ins,ob)
                current-=cut
        elif current<target and phase in ('base_run','marathon'):
            # Grow modestly via existing easy runs, not a sudden long-run spike.
            for i in running:
                if current>=target:break
                sp,ti,du,ins,ob=adjusted[i]
                if ins!='easy' or 'long' in ti.lower():continue
                add=min(15,target-current)
                adjusted[i]=(sp,ti,du+add,ins,ob)
                current+=add
        return adjusted
    return plan
