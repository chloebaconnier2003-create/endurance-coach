"""Athlete-confirmed coaching baseline, updated 2026-10-10.

These are initial planning constraints, not clinical thresholds or guaranteed targets.
"""
BASELINE = {
    "weekly_tolerated_hours_min": 6,
    "weekly_tolerated_hours_max": 9,
    "availability": "variable",
    "current_running_hours_per_week_min": 2,
    "current_running_hours_per_week_max": 3,
    "current_typical_long_run_km": 13,
    "current_typical_long_run_minutes_approx": 90,
    "occasional_discomfort": ["hip", "shins"],
    "goal_strategy": "Optimize marathon and intermediate races while building toward LeMan Full Distance",
    "equipment": ["gps_hr_watch", "hr_chest_strap", "indoor_trainer", "pool", "garmin_strava_data"],
    "power_meter_confirmed": False,
    "weekly_hours_include_rugby_dance": True,
    "planning_principles": [
        "Do not automatically treat 9h as a mandatory weekly minimum.",
        "Reduce training during 24h shifts, intense training-work days and rugby matches.",
        "Use heart-rate, RPE and duration until individual zones are calibrated.",
        "Prioritize gradual running exposure with hip/shin symptom checks.",
        "Treat long-range schedules as provisional; adapt near-term workouts using recovery data.",
    ],
}
