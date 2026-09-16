from datetime import date,datetime,timedelta

def coach_brief(readiness_score,status,next_session,next_goal,recent_shift=None,load=None):
    messages=[]
    if recent_shift and recent_shift.get('shift_type') in {'24h','12h_nuit'} and float(recent_shift.get('hours_since') or 999)<24:
        messages.append("La récupération post-garde est prioritaire aujourd'hui.")
    if readiness_score<45: messages.append("Les signaux de récupération sont faibles : évite l'intensité et réduis le volume.")
    elif readiness_score<60: messages.append("Journée à charge contrôlée : conserve l'entraînement seulement s'il reste facile.")
    else: messages.append("Les indicateurs du jour permettent de suivre le plan prévu.")
    if load and load.get('ratio'):
        r=load['ratio']
        if r>1.35: messages.append("Ta charge des 7 derniers jours est nettement au-dessus de ta moyenne récente : évite d'ajouter une séance dure.")
        elif r<0.65: messages.append("La charge récente est basse par rapport aux quatre dernières semaines; la progression peut rester graduelle.")
    if next_session: messages.append(f"Prochaine séance : {next_session.get('title')} ({next_session.get('duration_min') or '?'} min).")
    if next_goal: messages.append(f"Cap actuel : {next_goal.get('name')} le {next_goal.get('event_date')}.")
    return messages

def explain_plan_day(session,day_events=None):
    if not session:return "Aucune séance d'endurance imposée : cette journée peut servir à récupérer ou absorber les autres contraintes."
    context=', '.join(day_events or [])
    base=f"Cette séance de {session.get('sport','sport')} vise : {session.get('objective') or 'développer la qualité nécessaire à la phase actuelle'}."
    return base+(f" Elle a été placée ici en tenant compte de : {context}." if context else " Elle est placée dans une fenêtre disponible pour espacer les charges importantes.")

def adaptation_options(session,reason):
    if not session:return ['Repos','Mobilité 15–20 min','Activité très facile selon envie']
    sport=str(session.get('sport') or '')
    if sport in {'running','trail'}: return ['Réduire la durée de 30 %','Remplacer par vélo facile','Remplacer par natation technique','Déplacer de 24 h']
    return ['Réduire la durée de 25–30 %','Passer en endurance facile','Déplacer de 24 h','Annuler si fatigue persistante']
