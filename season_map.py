import streamlit as st
from datetime import date
from db import query
from v7_engine import roadmap

PHASES=['SPECIFIQUE CAP','TRAIL','RESET CAP','BASE MARATHON + TRI','MARATHON','CLIMB','HALF','ULTRA BIKE','DURABILITY','FULL SPECIFIC','TAPER']
VOLUMES=['6–8 h','6–9 h','6–8 h','8–10 h','8–11 h','6–10 h','9–12 h','8–13 h','8–13 h','12–15 h','5–10 h']

def _fmt_date(value):
    try:return date.fromisoformat(str(value)[:10]).strftime('%d-%m')
    except:return str(value)

def _clean_blocks():
    blocks=[]
    for i,raw in enumerate(roadmap()):
        b=dict(raw);b['code']=f'M{i+1}';b['phase']=PHASES[i] if i<len(PHASES) else 'BUILD';b['hours']=VOLUMES[i] if i<len(VOLUMES) else '—'
        # Dès le RESET, la CAP redevient progressivement prioritaire pour préparer Aveiro,
        # tout en gardant natation/vélo comme travail aérobie complémentaire à faible impact.
        if i==2:
            b['name']='M3 · Reset + reconstruction CAP';b['objective']='Récupérer de la SaintéLyon puis reconstruire fréquence, tolérance mécanique et régularité CAP';b['focus']='CAP facile / technique / force / natation récupération';b['sessions']='CAP 3×/sem au départ puis 3–4× si tolérée · natation 2× · vélo Z2 1× · force 1–2×. Majorité du temps d’endurance à basse intensité.'
            b['weeks']=['S1 RECOVERY · post-SaintéLyon : marche/mobilité, natation facile, 2 footings de 25–35 min seulement si indolores.','S2 BASE · CAP 3× : 40 min facile + 45 min facile avec 6 lignes droites + 60 min longue facile ; natation 2× ; force 1×.','S3 BUILD · CAP 3× : 45 min facile + 50 min dont 3×6 min soutenu contrôlé + 70 min longue ; vélo Z2 75–90 min ; natation 2×.','S4 RECOVERY · CAP 3× facile, volume CAP réduit ~20–30 %, longue 55–60 min ; natation technique ; force légère.','S5 BUILD · CAP 3–4× selon récupération : 45 min facile + 4×6 min tempo/seuil bas + 40 min récupération optionnelle + 75–80 min longue.']
        if i==3:
            b['name']='M4 · Base marathon + maintien triathlon';b['objective']='Faire progresser le volume CAP et la durabilité avant le spécifique marathon, sans abandonner natation et vélo';b['focus']='Volume CAP facile / seuil contrôlé / sortie longue / économie de course';b['sessions']='CAP 4×/sem cible si tolérance verte · natation 2× · vélo 1–2× Z2 · force 1×. Environ ≥70 % du temps d’endurance à faible intensité ; une seule séance CAP exigeante structurée la plupart des semaines.'
            b['weeks']=['S1 BASE · CAP 4× : 45 min facile + 50 min avec 8×20 s lignes droites + 45 min facile + longue 80 min ; natation 2× ; vélo Z2 90 min.','S2 BUILD · CAP 4× : 50 min facile + 3×8 min seuil bas/tempo + 40 min récupération + longue 90 min ; natation 2× ; vélo 90 min.','S3 BUILD · CAP 4× : 50 min facile + 5×5 min soutenu contrôlé + 45 min facile + longue 1h40 ; natation 2× ; vélo 1h30–1h45.','S4 RECOVERY · CAP -25 à -30 % : 3 footings faciles, longue 75 min ; test CSS possible ; force légère.','S5 BUILD · CAP 4× : 50 min facile + 3×10 min tempo + 45 min récupération + longue 1h45 ; vélo Z2 1h45 ; natation 2×.','S6 BUILD · CAP 4× : 55 min facile + 2×15 min tempo/seuil bas + 45 min facile + longue 1h50 ; vélo Z2 90 min ; natation 2×.','S7 PEAK · CAP 4× : 50 min facile + 4×8 min tempo + 45 min récupération + longue 1h55–2h00 si hanche/tibias verts ; vélo facile 75–90 min ; natation 2×.','S8 RECOVERY · volume CAP -25 à -30 %, 3 sorties faciles + quelques lignes droites ; transition vers spécifique marathon.']
        if i==4:
            b['focus']='Spécifique marathon / durabilité / allure marathon / nutrition';b['sessions']='CAP 4×/sem cible · natation 1–2× récupération · vélo 0–1× facile · force 1× entretien. Structure dominante pyramidal : beaucoup de facile, une séance spécifique/tempo, une sortie longue, deux footings faciles.'
            b['weeks']=['S1 BUILD · CAP 4× : 50 min facile + 3×10 min allure marathon + 40 min récupération + longue 1h45 ; natation 1–2×.','S2 BUILD · CAP 4× : 55 min facile + 2×15 min allure marathon + 45 min facile + longue 20–22 km ; nutrition testée.','S3 BUILD · CAP 4× : 50 min facile + 3×12 min allure marathon + 45 min récupération + longue 22–24 km dont fin progressive si récupération verte.','S4 RECOVERY · volume -25 à -30 % : 3 CAP faciles + longue 16–18 km ; natation souple ; mobilité.','S5 PEAK · CAP 4× : 55 min facile + 2×20 min allure marathon + 45 min récupération + longue 25–27 km avec stratégie nutrition/hydratation.','S6 PEAK · CAP 4× : 50 min facile + 3×15 min allure marathon + 40 min récupération + longue 27–30 km MAX uniquement si douleur 0–2/10 et récupération correcte.','S7 TAPER · CAP -30 à -40 % : 3–4 sorties courtes, 2×12 min allure marathon, longue 14–16 km facile.','S8 RACE · 2–3 footings 25–40 min + quelques accélérations ; MARATHON AVEIRO.']
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
    wi=st.select_slider('Semaine',options=list(range(len(b['weeks']))),value=0,format_func=lambda i:f'S{i+1}',key='season_week');w=b['weeks'][wi];kind=_week_kind(w);st.markdown(f"<div class='smweek {kind.lower()}'><div class='sphase'>{kind}</div><h3>S{wi+1}</h3><p>{w}</p></div>",unsafe_allow_html=True);st.markdown('#### Lecture Coach');st.caption('Cible, pas emploi du temps figé. La CAP monte progressivement à partir du RESET ; la majorité reste facile. Garde difficile ou nuit → alléger/déplacer ; rugby = charge intense ; danse = charge complémentaire. Avec antécédent de périostite et gêne de hanche, toute hausse de CAP doit être conditionnée par la tolérance : douleur croissante, modification de foulée ou récupération basse = réduction de charge et évaluation adaptée.')

def goals_page():
    st.header('Objectifs');goals=query("SELECT * FROM goals WHERE COALESCE(event_date,'')!='' AND lower(name) NOT LIKE '%triathlon m%' ORDER BY event_date")
    for g in goals:
        try:days=(date.fromisoformat(g['event_date'])-date.today()).days
        except:days=None
        title=f"🏁 {g['name']} · {_fmt_date(g['event_date'])}"+(f" · J-{days}" if days is not None and days>=0 else '')
        with st.expander(title):st.write(f"Priorité **{g.get('priority') or '—'}** · Sport **{g.get('sport') or '—'}**");st.write(g.get('qualitative_goal') or g.get('notes') or 'Objectif à préciser')
