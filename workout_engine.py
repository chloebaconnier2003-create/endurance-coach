"""Session detail templates: durations and efforts adapt to each generated workout."""
import re

def detailed_workout(sport,intensity,duration,objective='',title=''):
    sport=(sport or '').lower(); intensity=(intensity or 'easy').lower()
    duration=max(15,int(duration or 45)); t=(title or '').lower()
    hard=intensity not in ('easy','recovery')
    warm=min(15,max(5,duration//5)); cool=min(10,max(5,duration//8))
    main_minutes=duration-warm-cool
    target='RPE 3–4/10, conversation possible' if not hard else 'RPE 5–7/10, jamais à bloc'
    nutrition='Hydratation selon conditions et soif.'
    if duration>=90:nutrition='Tester 30–60 g glucides/h en course ou 40–90 g/h à vélo, selon tolérance; hydratation individualisée.'
    if sport in ('running','trail'):
        if 'brick' in t:
            main=f'{main_minutes} min de transition très facile après vélo; aucune recherche de vitesse.'
            target='RPE 2–3/10'
        elif 'strides' in t or 'lignes droites' in t:
            main=f'{max(5,main_minutes-8)} min faciles puis 4–6 × 15–20 s de foulée relâchée, récupération complète.'
        elif 'côtes' in t:
            n=min(6,max(2,main_minutes//8))
            main=f'{n} × 45–60 s en côte à effort maîtrisé, récupération en marchant; compléter en endurance facile.'
        elif hard and any(k in t for k in ('tempo','marathon','seuil','spécifique')):
            found=re.search(r'(\d+)\s*[×x]\s*(\d+)',t)
            n,block=(int(found.group(1)),int(found.group(2))) if found else (3,6)
            recovery=2 if block<=10 else 3
            while n>1 and n*block+(n-1)*recovery>main_minutes:n-=1
            block=min(block,max(3,(main_minutes-(n-1)*recovery)//n))
            main=f'{n} × {block} min à allure marathon ressentie/tempo contrôlé, {recovery} min trot entre répétitions; temps restant facile.'
            target='RPE 5–6/10; allure à individualiser par tests, ne pas forcer une vitesse théorique'
        elif sport=='trail':
            main=f'{main_minutes} min sur terrain vallonné, marche active en montée, descentes prudentes.'
        else:
            main=f'{main_minutes} min en endurance fondamentale, aisance respiratoire; rester facile jusqu’au bout.'
        return dict(summary=f'{duration} min · '+('séance spécifique' if hard else 'endurance facile'),warmup=f'{warm} min faciles et progressives.',main=main,cooldown=f'{cool} min faciles ou marche.',intensity_target=target,nutrition=nutrition,coach_note=objective or 'Respecter la tolérance mécanique et la récupération.')
    if sport=='cycling':
        if 'force-endurance' in t or 'montée' in t:
            n=min(4,max(2,main_minutes//20))
            main=f'{n} × 6 min en montée ou résistance modérée, RPE 5–6/10, récupération 4 min souples; reste Z2.'
        elif hard:
            n=min(4,max(2,main_minutes//18))
            main=f'{n} × 8 min tempo RPE 5–6/10, récupération 4 min; reste en endurance.'
        else:
            main=f'{main_minutes} min en Z2 conversationnelle, cadence confortable; en home-trainer, ventilation et hydratation.'
        return dict(summary=f'{duration} min vélo',warmup=f'{warm} min très souples.',main=main,cooldown=f'{cool} min souples.',intensity_target=target,nutrition=nutrition,coach_note=objective or 'Endurance cycliste.')
    if sport=='swimming':
        if 'css' in t or hard:
            main='6 × 100 m réguliers avec 20–30 s de repos; compléter en nage facile selon le temps restant.'
        elif 'technique' in t:
            main='6–8 × 50 m éducatifs avec 20 s de repos, puis 4 × 100 m souples; réduire les répétitions si nécessaire.'
        else:
            main='4 × 200 m en aisance avec 20–30 s de repos, puis 4 × 50 m techniques; adapter le nombre de répétitions.'
        return dict(summary=f'{duration} min natation',warmup='200 m très faciles.',main=main,cooldown='100 m souples.',intensity_target='RPE 3–5/10; priorité à la technique.',nutrition='Boire selon besoin.',coach_note=objective or 'Endurance et économie de nage.')
    if sport=='strength':
        return dict(summary=f'{duration} min renforcement',warmup='8 min mobilité et activation hanches/tronc.',main='2–3 séries de squat ou fente tolérés, charnière de hanche, mollets, tirage, poussée et gainage; 6–12 répétitions, 2–3 répétitions en réserve.',cooldown='5 min retour au calme.',intensity_target='RPE 5–7/10; aucun exercice douloureux, aucune série à échec.',nutrition='Apports énergétiques et protéiques suffisants.',coach_note=objective or 'Robustesse musculaire.')
    return dict(summary=f'{duration} min',warmup=f'{warm} min progressives.',main=f'{main_minutes} min contrôlées.',cooldown=f'{cool} min faciles.',intensity_target=target,nutrition=nutrition,coach_note=objective or 'Entraînement général.')
