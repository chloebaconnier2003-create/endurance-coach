import streamlit as st
from datetime import date
from db import query
from v7_engine import roadmap

PHASES=['SPECIFIQUE CAP','TRAIL','RESET','BASE TRIATHLON','MARATHON','CLIMB','HALF','ULTRA BIKE','DURABILITY','FULL SPECIFIC','TAPER']
VOLUMES=['6–8 h','6–9 h','6–8 h','8–10 h','8–11 h','6–10 h','9–12 h','8–13 h','8–13 h','12–15 h','5–10 h']

def _fmt_date(value):
    try:return date.fromisoformat(str(value)[:10]).strftime('%d-%m')
    except:return str(value)

def _clean_blocks():
    blocks=[]
    for i,raw in enumerate(roadmap()):
        b=dict(raw);b['code']=f'M{i+1}';b['phase']=PHASES[i] if i<len(PHASES) else 'BUILD';b['hours']=VOLUMES[i] if i<len(VOLUMES) else '—'
        if 'Triathlon M' in b.get('name',''):
            b['name']='M4 · Base endurance triathlon';b['objective']='Construire le moteur aérobie avant le marathon';b['focus']='Aérobie / technique natation / endurance vélo / force';b['sessions']='Natation 2× · vélo 2× · CAP 2–3× · force 1–2× · rugby/danse intégrés.'
            b['weeks']=['S1 BASE · fréquence : 2 natations, 2 vélos, 2 CAP, force courte.','S2 BUILD · endurance : vélo long 2h15, natation technique/endurance, CAP facile.','S3 BUILD · force aérobie : vélo 2h30, CAP 1h15, travail CSS contrôlé.','S4 RECOVERY · volume -30 %, CSS ou FTP selon récupération.','S5 BUILD · tempo durable : premier brick vélo 2h15 + CAP 15 min.','S6 BUILD · durabilité : brick 2h30 + 20 min, natation 2.3–2.5 km.','S7 PEAK · endurance : vélo 3 h nutrition, CAP 1h20, natation longue.','S8 RECOVERY · volume -30 %, transition vers le bloc marathon.']
        blocks.append(b)
    return blocks

def _week_kind(text):
    t=text.upper()
    for k in ['RACE','CHALLENGE','TAPER','RECOVERY','PEAK','SPECIFIC','BUILD','BASE']:
        if k in t:return k
    if 'COURSE' in t or 'AFFÛTAGE' in t:return 'RACE'
    if 'RÉCUP' in t or 'ALLÉG' in t:return 'RECOVERY'
    return 'BUILD'

def roadmap_page():
    blocks=_clean_blocks();today=date.today().isoformat();active=next((b for b in blocks if b['start']<=today<=b['end']),blocks[0])
    st.markdown('''<style>.smhero{padding:1.1rem 1.15rem;border-radius:22px;background:linear-gradient(135deg,#101827,#263447);color:white;margin:.2rem 0 .8rem}.smhero h2{margin:.15rem 0}.smhero small{opacity:.72}.smtrack{display:flex;gap:7px;overflow-x:auto;padding:6px 1px 14px}.smblock{min-width:150px;padding:10px;border-radius:14px;background:rgba(128,128,128,.10);border:1px solid rgba(128,128,128,.20)}.smblock.on{border:2px solid #22c55e}.sphase{font-size:.66rem;font-weight:800;letter-spacing:.06em;opacity:.7}.smweek{padding:.9rem;border:1px solid rgba(128,128,128,.2);border-radius:16px;margin:.6rem 0}.build{border-left:5px solid #f59e0b}.base,.specific{border-left:5px solid #3b82f6}.recovery,.taper{border-left:5px solid #22c55e}.peak,.challenge{border-left:5px solid #ef4444}.race{border-left:5px solid #8b5cf6}@media(max-width:700px){.smtrack{display:grid;grid-template-columns:1fr 1fr}.smblock{min-width:0;font-size:.78rem}.smhero{padding:.9rem}.smhero h2{font-size:1.3rem}}</style>''',unsafe_allow_html=True)
    st.markdown(f"<div class='smhero'><small>SEASON MAP · 2026—2027</small><h2>Road to LéMan Full Distance</h2><b>Vous êtes ici → {active['name']}</b><br><small>{active['phase']} · {active['focus']}</small></div>",unsafe_allow_html=True);st.caption('Plan directeur : la semaine réelle reste adaptée aux gardes 24/72, nuits, rugby, danse, récupération et douleur.')
    html='<div class="smtrack">'
    for b in blocks:
        cls='smblock on' if b is active else 'smblock';html+=f"<div class='{cls}'><div class='sphase'>{b['phase']}</div><b>{b['code']}</b><br>{b['name'].replace(b['code']+' · ','')}<br><small>{_fmt_date(b['start'])} → {_fmt_date(b['end'])}</small><br><small>{b['hours']}</small></div>"
    html+='</div>';st.markdown(html,unsafe_allow_html=True)
    st.markdown('### Jalons');st.markdown('🏁 **18-10** Porto-Vecchio → 🌙 **28-11** SaintéLyon → 🏃 **fin 04** Aveiro → 🚵 **05** Mont Ventoux → 🏊🚴🏃 **06** Half Annecy → 🚵 **07** Cinglée → ⛰️ **08** Fêlés du Grand Colombier → ⭐ **09** LéMan Full')
    st.divider();st.markdown('## Explorer la saison');names=[b['name'] for b in blocks];idx=names.index(active['name']);chosen=st.selectbox('Macrocycle',names,index=idx,key='season_macro');b=blocks[names.index(chosen)]
    a,c,d=st.columns(3);a.metric('Volume cible',b['hours']);c.metric('Microcycles',len(b['weeks']));d.metric('Phase',b['phase']);st.markdown(f"### {b['name']}");st.caption(f"{_fmt_date(b['start'])} → {_fmt_date(b['end'])}");st.write(f"**Objectif :** {b['objective']}");st.write(f"**Focus :** {b['focus']}");st.info('Structure · '+b['sessions']);st.markdown('### Microcycles')
    wi=st.select_slider('Semaine',options=list(range(len(b['weeks']))),value=0,format_func=lambda i:f'S{i+1}',key='season_week');w=b['weeks'][wi];kind=_week_kind(w);st.markdown(f"<div class='smweek {kind.lower()}'><div class='sphase'>{kind}</div><h3>S{wi+1}</h3><p>{w}</p></div>",unsafe_allow_html=True);st.markdown('#### Lecture Coach');st.caption('Ce microcycle est une cible de charge, pas un emploi du temps figé. Une garde difficile peut déplacer ou alléger une séance ; le rugby compte comme charge intense ; la danse comme charge complémentaire ; Formation/SST affectent la disponibilité seulement ; un défi vélo remplace la sortie longue correspondante.')

def goals_page():
    st.header('Objectifs');goals=query("SELECT * FROM goals WHERE COALESCE(event_date,'')!='' AND lower(name) NOT LIKE '%triathlon m%' ORDER BY event_date")
    for g in goals:
        try:days=(date.fromisoformat(g['event_date'])-date.today()).days
        except:days=None
        title=f"🏁 {g['name']} · {_fmt_date(g['event_date'])}"+(f" · J-{days}" if days is not None and days>=0 else '')
        with st.expander(title):st.write(f"Priorité **{g.get('priority') or '—'}** · Sport **{g.get('sport') or '—'}**");st.write(g.get('qualitative_goal') or g.get('notes') or 'Objectif à préciser')
