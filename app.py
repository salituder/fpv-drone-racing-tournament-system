import sqlite3
import random
import math
import os
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Tuple, Optional

import pandas as pd
import streamlit as st

DB_PATH = "tournament.db"

# ============================================================
# БАЗОВЫЕ СТИЛИ CSS
# ============================================================

BASE_CSS = """
<style>
.tournament-progress {
    display: flex;
    gap: 10px;
    margin: 15px 0;
    flex-wrap: wrap;
}
.progress-stage {
    padding: 8px 16px;
    border-radius: 20px;
    font-weight: 500;
    font-size: 0.9em;
}
.progress-stage.completed {
    background: #4CAF50;
    color: white;
}
.progress-stage.active {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
}
.progress-stage.pending {
    background: #e0e0e0;
    color: #666;
}
</style>
"""

# ============================================================
# i18n — Русский по умолчанию
# ============================================================

I18N = {
    "RU": {
        "app_title": "🏁 Турнир по дрон-рейсингу",
        "language": "Язык",
        "tournament": "Турнир",
        "select_tournament": "Выбрать турнир",
        "create_new": "➕ Создать новый",
        "create_new_header": "Новый турнир",
        "tournament_name": "Название турнира",
        "discipline": "Дисциплина",
        "create_tournament": "Создать турнир",
        "time_limit": "Лимит времени (сек)",
        "total_laps": "Кол-во кругов (по регламенту)",

        # Дисциплины
        "drone_individual": "Дроны: Личный зачёт",
        "sim_individual": "Симулятор: Личный зачёт",
        "sim_team": "Симулятор: Командный зачёт",
        "coming_soon": "В разработке...",

        # Навигация
        "nav_overview": "📊 Обзор",
        "nav_participants": "👥 Участники",
        "nav_qualification": "⏱️ Квалификация",
        "nav_bracket": "🏆 Сетка",
        "nav_playoff": "🔥 Плей-офф",
        "nav_final": "🥇 Финал",

        # Обзор
        "overview_title": "Обзор турнира",
        "total_participants": "Участников",
        "tournament_status": "Статус",
        "status_setup": "Подготовка",
        "status_qualification": "Квалификация",
        "status_bracket": "Плей-офф",
        "status_finished": "Завершён",

        # Участники
        "participants_title": "Список участников",
        "add_participant": "Добавить участника",
        "pilot_name": "Имя пилота",
        "add": "Добавить",
        "random_draw": "🎲 Жеребьёвка (случайные номера)",
        "draw_done": "Жеребьёвка проведена!",
        "draw_already": "Жеребьёвка уже проведена",
        "start_number": "Стартовый №",
        "demo_fill": "Тестовое заполнение",
        "demo_hint": "Быстро добавить тестовых участников",
        "demo_count": "Количество",
        "demo_prefix": "Префикс имени",
        "demo_add": "Добавить тестовых",
        "demo_already": "Участники уже добавлены",
        "demo_added": "Добавлено участников",

        # Квалификация
        "qual_title": "Квалификационный этап",
        "qual_info": "Введите результаты каждого пилота. Система автоматически определит кто проходит дальше.",
        "time_seconds": "Время (сек)",
        "laps_completed": "Круги.Препятствия",
        "completed_all": "Все 3 круга",
        "projected_time": "Расчётное время (3 кр.)",
        "qual_rank": "Место",
        "qual_cutoff": "Проходят: {} из {}",
        "qual_finish": "✅ Завершить квалификацию → Сформировать сетку",
        "qual_not_all": "Не все результаты введены!",
        "qual_done": "Квалификация завершена!",

        # Сетка
        "bracket_title": "Турнирная сетка",
        "group": "Группа",
        "advance_stage": "➡️ Перейти к следующему этапу",
        "start_playoff": "🚀 Начать плей-офф",
        "last_stage": "Это финальный этап",
        "tie_warning": "⚠️ Обнаружено равенство очков! Возможно потребуется доп. вылет.",
        "waiting_for_qual": "Ожидание завершения квалификации",

        # Плей-офф
        "playoff_title": "Плей-офф — ввод результатов",
        "playoff_not_started": "Плей-офф ещё не начался",
        "select_round": "Выберите раунд",
        "select_group": "Группа",

        # Финал
        "final_title": "ФИНАЛ",
        "heat_n": "Вылет {}",
        "final_standings": "Итоговая таблица финала",
        "champion": "🏆 ЧЕМПИОН",
        "bonus_note": "Бонус +1 за 2 и более побед в вылетах",

        # Общее
        "saved": "✅ Сохранено!",
        "error": "Ошибка",
        "download_csv": "📥 Скачать CSV",
        "place_short": "м.",
        "points": "Очки",
        "pilot": "Пилот",
        "time": "Время",
        "laps": "Круги",
        "place": "Место",
    },
    "EN": {
        "app_title": "🏁 Drone Racing Tournament",
        "language": "Language",
        "tournament": "Tournament",
        "select_tournament": "Select tournament",
        "create_new": "➕ Create new",
        "create_new_header": "New tournament",
        "tournament_name": "Tournament name",
        "discipline": "Discipline",
        "create_tournament": "Create tournament",
        "time_limit": "Time limit (sec)",
        "total_laps": "Laps count (regulation)",

        "drone_individual": "Drones: Individual",
        "sim_individual": "Simulator: Individual",
        "sim_team": "Simulator: Team",
        "coming_soon": "Coming soon...",

        "nav_overview": "📊 Overview",
        "nav_participants": "👥 Participants",
        "nav_qualification": "⏱️ Qualification",
        "nav_bracket": "🏆 Bracket",
        "nav_playoff": "🔥 Playoff",
        "nav_final": "🥇 Final",

        "overview_title": "Tournament Overview",
        "total_participants": "Participants",
        "tournament_status": "Status",
        "status_setup": "Setup",
        "status_qualification": "Qualification",
        "status_bracket": "Playoff",
        "status_finished": "Finished",

        "participants_title": "Participants",
        "add_participant": "Add participant",
        "pilot_name": "Pilot name",
        "add": "Add",
        "random_draw": "🎲 Random draw",
        "draw_done": "Draw completed!",
        "draw_already": "Draw already done",
        "start_number": "Start #",
        "demo_fill": "Test fill",
        "demo_hint": "Quick add test participants",
        "demo_count": "Count",
        "demo_prefix": "Name prefix",
        "demo_add": "Add test",
        "demo_already": "Participants already added",
        "demo_added": "Added participants",

        "qual_title": "Qualification",
        "qual_info": "Enter results for each pilot. System auto-determines who advances.",
        "time_seconds": "Time (sec)",
        "laps_completed": "Laps.Obstacles",
        "completed_all": "All 3 laps",
        "projected_time": "Projected time (3 laps)",
        "qual_rank": "Rank",
        "qual_cutoff": "Advancing: {} of {}",
        "qual_finish": "✅ Finish Qualification → Generate Bracket",
        "qual_not_all": "Not all results entered!",
        "qual_done": "Qualification complete!",

        "bracket_title": "Tournament Bracket",
        "group": "Group",
        "advance_stage": "➡️ Advance to next stage",
        "start_playoff": "🚀 Start Playoff",
        "last_stage": "This is the final stage",
        "tie_warning": "⚠️ Tie detected! Extra heat may be required.",
        "waiting_for_qual": "Waiting for qualification",

        "playoff_title": "Playoff — Enter Results",
        "playoff_not_started": "Playoff not started yet",
        "select_round": "Select round",
        "select_group": "Group",

        "final_title": "FINAL",
        "heat_n": "Heat {}",
        "final_standings": "Final Standings",
        "champion": "🏆 CHAMPION",
        "bonus_note": "Bonus +1 for 2+ first-place finishes",

        "saved": "✅ Saved!",
        "error": "Error",
        "download_csv": "📥 Download CSV",
        "place_short": "pl.",
        "points": "Points",
        "pilot": "Pilot",
        "time": "Time",
        "laps": "Laps",
        "place": "Place",
    }
}


def T(key: str) -> str:
    lang = st.session_state.get("lang", "RU")
    return I18N.get(lang, I18N["RU"]).get(key, I18N["RU"].get(key, key))


# ============================================================
# ТАБЛИЦЫ ПОСЕВА И ПРОГРЕССА (из официального регламента)
# ============================================================

# Посев 32 → 1/8 (Таблица №3)
SEEDING_1_8_32: Dict[int, List[int]] = {
    1: [1, 9, 24, 32], 2: [8, 16, 17, 25], 3: [7, 15, 18, 26], 4: [6, 14, 19, 27],
    5: [5, 13, 20, 28], 6: [4, 12, 21, 29], 7: [3, 11, 22, 30], 8: [2, 10, 23, 31],
}

# Посев 16 → 1/4 (Таблица №4)
SEEDING_1_4_16: Dict[int, List[int]] = {
    1: [1, 5, 12, 16], 2: [3, 7, 10, 14], 3: [2, 6, 11, 15], 4: [4, 8, 9, 13],
}

# Посев 8 → 1/2 (аналогичная схема змейкой)
SEEDING_1_2_8: Dict[int, List[int]] = {
    1: [1, 4, 5, 8], 2: [2, 3, 6, 7],
}

# Посев 4 → Финал
SEEDING_FINAL_4: Dict[int, List[int]] = {
    1: [1, 2, 3, 4],
}

# Пересев 1/8 → 1/4
PROGRESS_1_8_TO_1_4: Dict[int, List[Tuple[int, int]]] = {
    1: [(1, 1), (1, 5), (2, 6), (2, 2)],
    2: [(1, 7), (1, 3), (2, 8), (2, 4)],
    3: [(1, 8), (1, 4), (2, 7), (2, 3)],
    4: [(1, 6), (1, 2), (2, 1), (2, 5)],
}

# Пересев 1/4 → 1/2
PROGRESS_1_4_TO_1_2: Dict[int, List[Tuple[int, int]]] = {
    1: [(1, 1), (1, 2), (2, 3), (2, 4)],
    2: [(1, 3), (1, 4), (2, 1), (2, 2)],
}

# Пересев 1/2 → Финал
PROGRESS_1_2_TO_FINAL: Dict[int, List[Tuple[int, int]]] = {
    1: [(1, 1), (1, 2), (2, 1), (2, 2)]
}

# Очки финала
FINAL_SCORING = {1: 3, 2: 2, 3: 1, 4: 0}


# ============================================================
# StageDef + динамическая генерация сетки
# ============================================================

@dataclass
class StageDef:
    code: str
    display_name: Dict[str, str]
    group_size: int
    group_count: int
    qualifiers: int
    heats_count: int = 1  # 3 для финала
    seeding_map: Optional[Dict[int, List[int]]] = None
    progress_map: Optional[Dict[int, List[Tuple[int, int]]]] = None


def compute_bracket_size(n: int) -> int:
    """Наибольшая степень 2 <= n (минимум 4)."""
    for s in [32, 16, 8, 4]:
        if n >= s:
            return s
    return 4


def generate_bracket(advancing: int) -> List[StageDef]:
    """Генерирует список этапов плей-офф по количеству прошедших."""
    stages: List[StageDef] = []
    if advancing >= 32:
        stages.append(StageDef("1/8", {"RU": "1/8 финала", "EN": "Round of 16"}, 4, 8, 2, 1,
                                seeding_map=SEEDING_1_8_32))
        stages.append(StageDef("1/4", {"RU": "Четвертьфинал", "EN": "Quarterfinal"}, 4, 4, 2, 1,
                                progress_map=PROGRESS_1_8_TO_1_4))
        stages.append(StageDef("1/2", {"RU": "Полуфинал", "EN": "Semifinal"}, 4, 2, 2, 1,
                                progress_map=PROGRESS_1_4_TO_1_2))
        stages.append(StageDef("F", {"RU": "ФИНАЛ", "EN": "FINAL"}, 4, 1, 0, 3,
                                progress_map=PROGRESS_1_2_TO_FINAL))
    elif advancing >= 16:
        stages.append(StageDef("1/4", {"RU": "Четвертьфинал", "EN": "Quarterfinal"}, 4, 4, 2, 1,
                                seeding_map=SEEDING_1_4_16))
        stages.append(StageDef("1/2", {"RU": "Полуфинал", "EN": "Semifinal"}, 4, 2, 2, 1,
                                progress_map=PROGRESS_1_4_TO_1_2))
        stages.append(StageDef("F", {"RU": "ФИНАЛ", "EN": "FINAL"}, 4, 1, 0, 3,
                                progress_map=PROGRESS_1_2_TO_FINAL))
    elif advancing >= 8:
        stages.append(StageDef("1/2", {"RU": "Полуфинал", "EN": "Semifinal"}, 4, 2, 2, 1,
                                seeding_map=SEEDING_1_2_8))
        stages.append(StageDef("F", {"RU": "ФИНАЛ", "EN": "FINAL"}, 4, 1, 0, 3,
                                progress_map=PROGRESS_1_2_TO_FINAL))
    else:  # 4
        stages.append(StageDef("F", {"RU": "ФИНАЛ", "EN": "FINAL"}, 4, 1, 0, 3,
                                seeding_map=SEEDING_FINAL_4))
    return stages


# ============================================================
# База данных
# ============================================================

def db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    conn = db()
    c = conn.cursor()

    c.execute("""CREATE TABLE IF NOT EXISTS tournaments(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        discipline TEXT NOT NULL DEFAULT 'drone_individual',
        time_limit_seconds REAL NOT NULL DEFAULT 90.0,
        total_laps INTEGER NOT NULL DEFAULT 3,
        status TEXT NOT NULL DEFAULT 'setup',
        created_at TEXT NOT NULL
    )""")

    c.execute("""CREATE TABLE IF NOT EXISTS participants(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        tournament_id INTEGER NOT NULL,
        name TEXT NOT NULL,
        start_number INTEGER,
        FOREIGN KEY(tournament_id) REFERENCES tournaments(id) ON DELETE CASCADE
    )""")

    c.execute("""CREATE TABLE IF NOT EXISTS qualification_results(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        tournament_id INTEGER NOT NULL,
        participant_id INTEGER NOT NULL,
        time_seconds REAL,
        laps_completed REAL,
        completed_all_laps INTEGER DEFAULT 0,
        projected_time REAL,
        UNIQUE(tournament_id, participant_id),
        FOREIGN KEY(tournament_id) REFERENCES tournaments(id) ON DELETE CASCADE,
        FOREIGN KEY(participant_id) REFERENCES participants(id) ON DELETE CASCADE
    )""")

    c.execute("""CREATE TABLE IF NOT EXISTS stages(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        tournament_id INTEGER NOT NULL,
        stage_idx INTEGER NOT NULL,
        code TEXT NOT NULL,
        group_size INTEGER NOT NULL,
        group_count INTEGER NOT NULL,
        qualifiers INTEGER NOT NULL,
        heats_count INTEGER NOT NULL DEFAULT 1,
        status TEXT NOT NULL DEFAULT 'active',
        UNIQUE(tournament_id, stage_idx),
        FOREIGN KEY(tournament_id) REFERENCES tournaments(id) ON DELETE CASCADE
    )""")

    c.execute("""CREATE TABLE IF NOT EXISTS groups(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        stage_id INTEGER NOT NULL,
        group_no INTEGER NOT NULL,
        UNIQUE(stage_id, group_no),
        FOREIGN KEY(stage_id) REFERENCES stages(id) ON DELETE CASCADE
    )""")

    c.execute("""CREATE TABLE IF NOT EXISTS group_members(
        group_id INTEGER NOT NULL,
        participant_id INTEGER NOT NULL,
        PRIMARY KEY(group_id, participant_id),
        FOREIGN KEY(group_id) REFERENCES groups(id) ON DELETE CASCADE,
        FOREIGN KEY(participant_id) REFERENCES participants(id) ON DELETE CASCADE
    )""")

    c.execute("""CREATE TABLE IF NOT EXISTS heats(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        group_id INTEGER NOT NULL,
        heat_no INTEGER NOT NULL,
        UNIQUE(group_id, heat_no),
        FOREIGN KEY(group_id) REFERENCES groups(id) ON DELETE CASCADE
    )""")

    c.execute("""CREATE TABLE IF NOT EXISTS heat_results(
        heat_id INTEGER NOT NULL,
        participant_id INTEGER NOT NULL,
        time_seconds REAL,
        laps_completed REAL,
        completed_all_laps INTEGER DEFAULT 0,
        projected_time REAL,
        place INTEGER,
        points INTEGER DEFAULT 0,
        PRIMARY KEY(heat_id, participant_id),
        FOREIGN KEY(heat_id) REFERENCES heats(id) ON DELETE CASCADE,
        FOREIGN KEY(participant_id) REFERENCES participants(id) ON DELETE CASCADE
    )""")

    conn.commit()
    conn.close()


def qdf(sql, params=()) -> pd.DataFrame:
    conn = db()
    df = pd.read_sql_query(sql, conn, params=params)
    conn.close()
    return df


def exec_sql(sql, params=()):
    conn = db()
    conn.execute(sql, params)
    conn.commit()
    conn.close()


def exec_many(sql, rows):
    conn = db()
    conn.executemany(sql, rows)
    conn.commit()
    conn.close()


# ============================================================
# Бизнес-логика: квалификация
# ============================================================

def calc_projected_time(time_seconds: float, laps_completed: float, total_laps: int = 3) -> Optional[float]:
    """Рассчитать теоретическое время на total_laps кругов."""
    if laps_completed and laps_completed > 0:
        return round(time_seconds * (total_laps / laps_completed), 2)
    return None


def rank_results(results: List[Dict]) -> List[Dict]:
    """
    Ранжирование по времени:
    1. Пролетели все круги → по time_seconds ASC
    2. Не долетели → по laps_completed DESC
    """
    completed = [r for r in results if r.get("completed_all_laps")]
    incomplete = [r for r in results if not r.get("completed_all_laps")]
    completed.sort(key=lambda r: r.get("time_seconds") or 9999)
    incomplete.sort(key=lambda r: -(r.get("laps_completed") or 0))
    ranked = completed + incomplete
    for i, r in enumerate(ranked):
        r["place"] = i + 1
    return ranked


def get_qualification_results(tournament_id: int) -> pd.DataFrame:
    """Получить результаты квалификации с ранжированием."""
    df = qdf("""
        SELECT p.id as pid, p.name, p.start_number,
               qr.time_seconds, qr.laps_completed, qr.completed_all_laps, qr.projected_time
        FROM participants p
        LEFT JOIN qualification_results qr ON qr.participant_id = p.id AND qr.tournament_id = ?
        WHERE p.tournament_id = ?
        ORDER BY p.start_number
    """, (tournament_id, tournament_id))
    return df


def get_qual_ranking(tournament_id: int) -> pd.DataFrame:
    """Ранжированный список квалификации."""
    df = qdf("""
        SELECT p.id as pid, p.name, p.start_number,
               qr.time_seconds, qr.laps_completed, qr.completed_all_laps, qr.projected_time
        FROM participants p
        JOIN qualification_results qr ON qr.participant_id = p.id AND qr.tournament_id = ?
        WHERE p.tournament_id = ? AND qr.time_seconds IS NOT NULL
    """, (tournament_id, tournament_id))

    if df.empty:
        return df

    # Ранжируем
    results = df.to_dict("records")
    ranked = rank_results(results)
    ranked_df = pd.DataFrame(ranked)
    return ranked_df


def save_qual_result(tournament_id: int, participant_id: int, time_seconds: float,
                     laps_completed: float, completed_all_laps: bool, total_laps: int = 3):
    projected = calc_projected_time(time_seconds, laps_completed, total_laps) if not completed_all_laps else time_seconds
    exec_sql("""
        INSERT OR REPLACE INTO qualification_results(tournament_id, participant_id,
            time_seconds, laps_completed, completed_all_laps, projected_time)
        VALUES(?, ?, ?, ?, ?, ?)
    """, (tournament_id, participant_id, time_seconds, laps_completed,
          int(completed_all_laps), projected))


def participant_count(tournament_id: int) -> int:
    df = qdf("SELECT COUNT(*) as c FROM participants WHERE tournament_id=?", (tournament_id,))
    return int(df.iloc[0]["c"]) if not df.empty else 0


# ============================================================
# Бизнес-логика: сетка и плей-офф
# ============================================================

def get_tournament(tournament_id: int) -> pd.Series:
    return qdf("SELECT * FROM tournaments WHERE id=?", (tournament_id,)).iloc[0]


def get_all_stages(tournament_id: int) -> pd.DataFrame:
    return qdf("SELECT * FROM stages WHERE tournament_id=? ORDER BY stage_idx", (tournament_id,))


def get_active_stage(tournament_id: int) -> Optional[pd.Series]:
    df = qdf("SELECT * FROM stages WHERE tournament_id=? AND status='active' ORDER BY stage_idx DESC LIMIT 1",
             (tournament_id,))
    return df.iloc[0] if not df.empty else None


def create_stage(tournament_id: int, stage_idx: int, sd: StageDef) -> int:
    exec_sql("""INSERT OR IGNORE INTO stages(tournament_id, stage_idx, code, group_size,
                group_count, qualifiers, heats_count, status)
                VALUES(?,?,?,?,?,?,?,'active')""",
             (tournament_id, stage_idx, sd.code, sd.group_size, sd.group_count,
              sd.qualifiers, sd.heats_count))
    stage_id = int(qdf("SELECT id FROM stages WHERE tournament_id=? AND stage_idx=?",
                        (tournament_id, stage_idx)).iloc[0]["id"])
    existing = int(qdf("SELECT COUNT(*) as c FROM groups WHERE stage_id=?", (stage_id,)).iloc[0]["c"])
    if existing == 0:
        exec_many("INSERT INTO groups(stage_id, group_no) VALUES(?,?)",
                  [(stage_id, gno) for gno in range(1, sd.group_count + 1)])
    return stage_id


def seed_groups_from_qual(tournament_id: int, stage_id: int, seeding_map: Dict[int, List[int]], advancing: int):
    """Посев из квалификации в первый этап плей-офф."""
    ranking = get_qual_ranking(tournament_id)
    if ranking.empty:
        return
    # Берём только прошедших
    ranking = ranking.head(advancing)

    groups_df = qdf("SELECT id, group_no FROM groups WHERE stage_id=?", (stage_id,))
    gid_by_no = {int(r["group_no"]): int(r["id"]) for _, r in groups_df.iterrows()}

    inserts = []
    for gno, seeds in seeding_map.items():
        for qual_rank in seeds:
            if qual_rank <= len(ranking):
                pid = int(ranking.iloc[qual_rank - 1]["pid"])
                inserts.append((gid_by_no[gno], pid))

    exec_many("INSERT OR IGNORE INTO group_members(group_id, participant_id) VALUES(?,?)", inserts)


def get_group_members(stage_id: int, group_no: int) -> pd.DataFrame:
    return qdf("""
        SELECT p.id as pid, p.name, p.start_number
        FROM groups g
        JOIN group_members gm ON gm.group_id=g.id
        JOIN participants p ON p.id=gm.participant_id
        WHERE g.stage_id=? AND g.group_no=?
        ORDER BY p.start_number
    """, (stage_id, int(group_no)))


def get_all_groups(stage_id: int) -> Dict[int, pd.DataFrame]:
    groups = qdf("SELECT group_no FROM groups WHERE stage_id=? ORDER BY group_no", (stage_id,))
    return {int(g["group_no"]): get_group_members(stage_id, int(g["group_no"])) for _, g in groups.iterrows()}


def save_heat(stage_id: int, group_no: int, heat_no: int, results: List[Dict], is_final: bool = False):
    """Сохранить результаты вылета. results = [{pid, time_seconds, laps_completed, completed_all_laps}]"""
    group_id = int(qdf("SELECT id FROM groups WHERE stage_id=? AND group_no=?",
                        (stage_id, group_no)).iloc[0]["id"])
    exec_sql("INSERT OR IGNORE INTO heats(group_id, heat_no) VALUES(?,?)", (group_id, heat_no))
    heat_id = int(qdf("SELECT id FROM heats WHERE group_id=? AND heat_no=?",
                       (group_id, heat_no)).iloc[0]["id"])

    # Ранжируем
    ranked = rank_results(results)

    tournament = qdf("SELECT t.total_laps FROM stages s JOIN tournaments t ON t.id=s.tournament_id WHERE s.id=?",
                      (stage_id,))
    total_laps = int(tournament.iloc[0]["total_laps"]) if not tournament.empty else 3

    rows = []
    for r in ranked:
        projected = calc_projected_time(r["time_seconds"], r["laps_completed"], total_laps) \
            if not r["completed_all_laps"] else r["time_seconds"]
        pts = FINAL_SCORING.get(r["place"], 0) if is_final else 0
        rows.append((heat_id, r["pid"], r["time_seconds"], r["laps_completed"],
                      int(r["completed_all_laps"]), projected, r["place"], pts))

    exec_sql("DELETE FROM heat_results WHERE heat_id=?", (heat_id,))
    exec_many("""INSERT INTO heat_results(heat_id, participant_id, time_seconds, laps_completed,
                 completed_all_laps, projected_time, place, points) VALUES(?,?,?,?,?,?,?,?)""", rows)


def get_heat_results(stage_id: int, group_no: int, heat_no: int) -> List[Dict]:
    gid_df = qdf("SELECT id FROM groups WHERE stage_id=? AND group_no=?", (stage_id, group_no))
    if gid_df.empty:
        return []
    group_id = int(gid_df.iloc[0]["id"])
    heat_df = qdf("SELECT id FROM heats WHERE group_id=? AND heat_no=?", (group_id, heat_no))
    if heat_df.empty:
        return []
    heat_id = int(heat_df.iloc[0]["id"])
    df = qdf("""SELECT hr.*, p.name, p.start_number FROM heat_results hr
                JOIN participants p ON p.id=hr.participant_id
                WHERE hr.heat_id=? ORDER BY hr.place""", (heat_id,))
    return df.to_dict("records") if not df.empty else []


def compute_group_ranking(stage_id: int, group_no: int) -> pd.DataFrame:
    """Ранжирование в группе по результату одного вылета (для плей-офф)."""
    results = get_heat_results(stage_id, group_no, 1)
    if not results:
        return pd.DataFrame()
    return pd.DataFrame(results)


def compute_final_standings(stage_id: int) -> pd.DataFrame:
    """Итоги финала: сумма очков за 3 вылета + бонус."""
    group_id_df = qdf("SELECT id FROM groups WHERE stage_id=? AND group_no=1", (stage_id,))
    if group_id_df.empty:
        return pd.DataFrame()
    group_id = int(group_id_df.iloc[0]["id"])

    df = qdf("""
        SELECT p.id as pid, p.name, p.start_number,
               COALESCE(SUM(hr.points), 0) as total_points,
               COALESCE(SUM(CASE WHEN hr.place=1 THEN 1 ELSE 0 END), 0) as wins,
               COUNT(hr.heat_id) as heats_played
        FROM group_members gm
        JOIN participants p ON p.id=gm.participant_id
        LEFT JOIN heats h ON h.group_id=gm.group_id
        LEFT JOIN heat_results hr ON hr.heat_id=h.id AND hr.participant_id=p.id
        WHERE gm.group_id=?
        GROUP BY p.id
    """, (group_id,))

    if df.empty:
        return df

    # Бонус +1 за 2+ побед
    df["bonus"] = (df["wins"] >= 2).astype(int)
    df["total"] = df["total_points"] + df["bonus"]
    df = df.sort_values(["total", "wins"], ascending=[False, False]).reset_index(drop=True)
    df["rank"] = range(1, len(df) + 1)
    return df


def check_stage_results_complete(stage_id: int, stage_def: StageDef) -> Tuple[bool, str]:
    """Проверяет, все ли результаты заполнены для текущего этапа.
    Возвращает (ok, message)."""
    all_groups = get_all_groups(stage_id)
    if not all_groups:
        return False, "Нет групп в этом этапе"

    heats_needed = stage_def.heats_count  # 1 для плей-офф, 3 для финала
    missing = []
    for gno, members in all_groups.items():
        if members.empty:
            missing.append(f"Группа {gno}: нет участников")
            continue
        for h in range(1, heats_needed + 1):
            results = get_heat_results(stage_id, gno, h)
            if not results:
                if heats_needed > 1:
                    missing.append(f"Группа {gno}, вылет {h}: нет результатов")
                else:
                    missing.append(f"Группа {gno}: нет результатов")
    if missing:
        return False, "Не все результаты заполнены:\n" + "\n".join(missing)
    return True, ""


def advance_to_next_stage(tournament_id: int, bracket: List[StageDef]):
    """Переход к следующему этапу плей-офф."""
    stages_df = get_all_stages(tournament_id)
    active = stages_df[stages_df["status"] == "active"]
    if active.empty:
        return
    cur = active.iloc[0]
    cur_idx = int(cur["stage_idx"])
    next_idx = cur_idx + 1
    if next_idx >= len(bracket):
        return

    # Валидация: проверить, что все результаты текущего этапа заполнены
    cur_sd = bracket[cur_idx]
    ok, msg = check_stage_results_complete(int(cur["id"]), cur_sd)
    if not ok:
        raise ValueError(msg)

    next_sd = bracket[next_idx]
    next_stage_id = create_stage(tournament_id, next_idx, next_sd)

    if next_sd.progress_map:
        groups_df = qdf("SELECT id, group_no FROM groups WHERE stage_id=?", (next_stage_id,))
        gid_by_no = {int(r["group_no"]): int(r["id"]) for _, r in groups_df.iterrows()}

        rows = []
        for target_gno, refs in next_sd.progress_map.items():
            for (place, src_gno) in refs:
                ranking = compute_group_ranking(int(cur["id"]), src_gno)
                if not ranking.empty and len(ranking) >= place:
                    pid = int(ranking.iloc[place - 1]["participant_id"])
                    rows.append((gid_by_no[target_gno], pid))

        exec_many("INSERT OR IGNORE INTO group_members(group_id, participant_id) VALUES(?,?)", rows)

    exec_sql("UPDATE stages SET status='done' WHERE id=?", (int(cur["id"]),))


def start_bracket(tournament_id: int):
    """Завершить квалификацию и создать первый этап плей-офф."""
    ranking = get_qual_ranking(tournament_id)
    n = len(ranking)
    advancing = compute_bracket_size(n)
    bracket = generate_bracket(advancing)

    # Сохраняем bracket info
    exec_sql("UPDATE tournaments SET status='bracket' WHERE id=?", (tournament_id,))

    # Создаём первый этап
    first_sd = bracket[0]
    stage_id = create_stage(tournament_id, 0, first_sd)

    # Посев
    if first_sd.seeding_map:
        seed_groups_from_qual(tournament_id, stage_id, first_sd.seeding_map, advancing)


def get_bracket_for_tournament(tournament_id: int) -> List[StageDef]:
    """Определяет сетку по количеству прошедших квалификацию."""
    ranking = get_qual_ranking(tournament_id)
    n = len(ranking)
    if n == 0:
        # Проверяем если уже есть этапы — восстанавливаем по кол-ву участников первого этапа
        stages = get_all_stages(tournament_id)
        if not stages.empty:
            first = stages.iloc[0]
            total = int(first["group_size"]) * int(first["group_count"])
            return generate_bracket(total)
        return []
    advancing = compute_bracket_size(n)
    return generate_bracket(advancing)


# ============================================================
# UI-хелперы
# ============================================================

def style_qual_table(df: pd.DataFrame, cutoff: int):
    """Подсветка: зелёный для проходящих, красный для отсечённых."""
    def highlight(row):
        rank = row.name + 1  # 0-based index
        if rank <= cutoff:
            return ["background-color: #1a472a; color: #90EE90"] * len(row)
        else:
            return ["background-color: #4a1a1a; color: #FFB6B6"] * len(row)
    return df.style.apply(highlight, axis=1)


def style_standings_table(df: pd.DataFrame, qualifiers: int):
    """Подсветка для плей-офф таблиц."""
    def highlight_row(row):
        rank = row["М"]
        if qualifiers > 0:
            if rank <= qualifiers:
                return ["background-color: #1a472a; color: #90EE90"] * len(row)
            else:
                return ["background-color: #4a1a1a; color: #FFB6B6"] * len(row)
        return [""] * len(row)
    return df.style.apply(highlight_row, axis=1)


def download_csv_button(df: pd.DataFrame, label: str, filename: str):
    csv = df.to_csv(index=False).encode("utf-8-sig")
    st.download_button(label, data=csv, file_name=filename, mime="text/csv")


def format_time(seconds: Optional[float]) -> str:
    """Форматирует секунды в мм:сс.мс"""
    if seconds is None:
        return "—"
    m = int(seconds) // 60
    s = seconds - m * 60
    return f"{m}:{s:06.3f}"


def parse_time(time_str: str) -> Optional[float]:
    """Парсит время из строки (поддержка форматов: 90.5, 1:30.5)"""
    if not time_str or time_str.strip() == "":
        return None
    time_str = time_str.strip().replace(",", ".")
    if ":" in time_str:
        parts = time_str.split(":")
        try:
            return float(parts[0]) * 60 + float(parts[1])
        except ValueError:
            return None
    try:
        return float(time_str)
    except ValueError:
        return None


# ============================================================
# ПРИЛОЖЕНИЕ
# ============================================================

st.set_page_config(
    page_title="Дрон-рейсинг Турнир",
    page_icon="🏁",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================
# ЗАЩИТА ПАРОЛЕМ
# ============================================================
APP_PASSWORD = st.secrets.get("APP_PASSWORD", os.environ.get("APP_PASSWORD", ""))


def check_password():
    if not APP_PASSWORD:
        st.error("⚠️ Пароль не настроен! Добавьте APP_PASSWORD в Streamlit Secrets.")
        st.stop()
    if "authenticated" not in st.session_state:
        st.session_state["authenticated"] = False
    if st.session_state["authenticated"]:
        return True
    st.markdown("## 🔐 Вход в систему")
    st.markdown("Для доступа к системе управления турнирами введите пароль.")
    password = st.text_input("Пароль", type="password", key="password_input")
    if st.button("Войти", type="primary"):
        if password == APP_PASSWORD:
            st.session_state["authenticated"] = True
            st.rerun()
        else:
            st.error("❌ Неверный пароль")
    return False


if not check_password():
    st.stop()

init_db()
st.markdown(BASE_CSS, unsafe_allow_html=True)

# --- Сайдбар ---
with st.sidebar:
    lang_options = ["RU", "EN"]
    lang_idx = lang_options.index(st.session_state.get("lang", "RU")) if st.session_state.get("lang", "RU") in lang_options else 0
    lang = st.selectbox("🌐 " + I18N["RU"]["language"], lang_options, index=lang_idx, key="lang")
    st.divider()
    if st.button("🚪 Выйти", use_container_width=True):
        st.session_state["authenticated"] = False
        st.rerun()
    st.divider()

    st.header("🏁 " + T("tournament"))
    tdf = qdf("SELECT * FROM tournaments ORDER BY id DESC")
    t_map = {f'{r["name"]}': int(r["id"]) for _, r in tdf.iterrows()} if not tdf.empty else {}
    id_to_name = {v: k for k, v in t_map.items()}
    options = [T("create_new")] + list(t_map.keys())

    default_idx = 0
    if "selected_tournament" in st.session_state:
        saved_id = st.session_state["selected_tournament"]
        if saved_id in id_to_name and id_to_name[saved_id] in options:
            default_idx = options.index(id_to_name[saved_id])
        del st.session_state["selected_tournament"]

    sel = st.selectbox(T("select_tournament"), options, index=default_idx)

    DISCIPLINES = {
        "drone_individual": T("drone_individual"),
        "sim_individual": T("sim_individual"),
        "sim_team": T("sim_team"),
    }

    if sel == T("create_new"):
        st.subheader(T("create_new_header"))
        name = st.text_input(T("tournament_name"), value=f"Турнир {datetime.now().strftime('%d.%m.%Y')}")
        disc_key = st.selectbox(T("discipline"), list(DISCIPLINES.keys()),
                                format_func=lambda k: DISCIPLINES[k])
        time_limit = st.number_input(T("time_limit"), value=90.0, min_value=10.0, step=5.0)
        total_laps = st.number_input(T("total_laps"), value=3, min_value=1, step=1)

        if st.button(T("create_tournament"), type="primary"):
            exec_sql("""INSERT INTO tournaments(name, discipline, time_limit_seconds, total_laps, status, created_at)
                        VALUES(?,?,?,?,?,?)""",
                     (name, disc_key, time_limit, int(total_laps), "setup",
                      datetime.now().isoformat(timespec="seconds")))
            new_id = int(qdf("SELECT id FROM tournaments ORDER BY id DESC LIMIT 1").iloc[0]["id"])
            st.session_state["selected_tournament"] = new_id
            st.rerun()
        tournament_id = None
    else:
        tournament_id = t_map[sel]

if tournament_id is None:
    st.header(T("app_title"))
    st.info("Выберите турнир или создайте новый.")
    st.stop()

# --- Данные турнира ---
tourn = get_tournament(tournament_id)
discipline = str(tourn["discipline"])
t_status = str(tourn["status"])
time_limit = float(tourn["time_limit_seconds"])
total_laps = int(tourn["total_laps"])
p_count = participant_count(tournament_id)

with st.sidebar:
    st.caption(f"📋 {DISCIPLINES.get(discipline, discipline)}")
    st.caption(f"⏱️ {time_limit}с / {total_laps} кр.")
    st.caption(f"👥 {p_count} участников")

# Проверка дисциплины
if discipline != "drone_individual":
    st.header(T("app_title"))
    st.warning(T("coming_soon"))
    st.stop()

st.header(T("app_title"))

# --- Навигация ---
tabs = st.tabs([
    T("nav_overview"),
    T("nav_participants"),
    T("nav_qualification"),
    T("nav_bracket"),
    T("nav_playoff"),
    T("nav_final"),
])

# ============================================================
# TAB 0: Обзор
# ============================================================
with tabs[0]:
    st.subheader(T("overview_title"))
    c1, c2, c3 = st.columns(3)
    with c1:
        st.metric(T("total_participants"), p_count)
    with c2:
        status_labels = {"setup": T("status_setup"), "qualification": T("status_qualification"),
                         "bracket": T("status_bracket"), "finished": T("status_finished")}
        st.metric(T("tournament_status"), status_labels.get(t_status, t_status))
    with c3:
        bracket = get_bracket_for_tournament(tournament_id)
        all_stages = get_all_stages(tournament_id)
        done_count = len(all_stages[all_stages["status"] == "done"]) if not all_stages.empty else 0
        total_stages = len(bracket) if bracket else 0
        st.metric("Этапов", f"{done_count} / {total_stages}")

    # Прогресс
    if bracket:
        st.markdown("**Прогресс турнира:**")
        progress_html = '<div class="tournament-progress">'
        progress_html += f'<span class="progress-stage {"completed" if t_status != "setup" else "active"}">Квалификация</span>'
        for idx, sd in enumerate(bracket):
            stage_row = all_stages[all_stages["stage_idx"] == idx] if not all_stages.empty else pd.DataFrame()
            if not stage_row.empty:
                s = stage_row.iloc[0]["status"]
                css = "completed" if s == "done" else "active"
            else:
                css = "pending"
            sname = sd.display_name.get(lang, sd.code)
            progress_html += f'<span class="progress-stage {css}">{sname}</span>'
        progress_html += '</div>'
        st.markdown(progress_html, unsafe_allow_html=True)

# ============================================================
# TAB 1: Участники
# ============================================================
with tabs[1]:
    st.subheader(T("participants_title"))

    col1, col2 = st.columns([1, 2])

    with col1:
        st.markdown(f"### {T('add_participant')}")
        with st.form("add_pilot", clear_on_submit=True):
            pname = st.text_input(T("pilot_name"))
            if st.form_submit_button(T("add"), type="primary"):
                if pname.strip():
                    exec_sql("INSERT INTO participants(tournament_id, name) VALUES(?,?)",
                             (tournament_id, pname.strip()))
                    st.success(T("saved"))
                    st.rerun()

        st.divider()
        st.markdown(f"### {T('random_draw')}")

        # Проверяем, была ли уже проведена жеребьёвка
        has_numbers = int(qdf("SELECT COUNT(*) as c FROM participants WHERE tournament_id=? AND start_number IS NOT NULL",
                              (tournament_id,)).iloc[0]["c"])
        draw_done = has_numbers > 0

        if not draw_done:
            # Первая жеребьёвка — простая кнопка
            if st.button(T("random_draw"), type="primary"):
                pdf = qdf("SELECT id FROM participants WHERE tournament_id=?", (tournament_id,))
                if pdf.empty:
                    st.warning("Нет участников")
                else:
                    ids = pdf["id"].tolist()
                    random.shuffle(ids)
                    for idx, pid in enumerate(ids):
                        exec_sql("UPDATE participants SET start_number=? WHERE id=?", (idx + 1, pid))
                    exec_sql("UPDATE tournaments SET status='qualification' WHERE id=?", (tournament_id,))
                    st.success(T("draw_done"))
                    st.balloons()
                    st.rerun()
        else:
            st.success("✅ Жеребьёвка проведена")
            # Повторная жеребьёвка — с двойным подтверждением
            redraw_key = "confirm_redraw"
            if not st.session_state.get(redraw_key, False):
                if st.button("🔄 Провести жеребьёвку ещё раз"):
                    st.session_state[redraw_key] = True
                    st.rerun()
            else:
                st.warning("⚠️ Вы уверены? Все текущие стартовые номера будут перемешаны заново.")
                cc1, cc2 = st.columns(2)
                with cc1:
                    if st.button("✅ Да, перемешать", type="primary", use_container_width=True):
                        pdf = qdf("SELECT id FROM participants WHERE tournament_id=?", (tournament_id,))
                        ids = pdf["id"].tolist()
                        random.shuffle(ids)
                        for idx, pid in enumerate(ids):
                            exec_sql("UPDATE participants SET start_number=? WHERE id=?", (idx + 1, pid))
                        st.session_state[redraw_key] = False
                        st.success(T("draw_done"))
                        st.balloons()
                        st.rerun()
                with cc2:
                    if st.button("❌ Отмена", use_container_width=True):
                        st.session_state[redraw_key] = False
                        st.rerun()

        # --- Инструменты разработчика (скрыты) ---
        st.divider()
        with st.expander("🛠️ Инструменты разработчика", expanded=False):
            st.caption(T("demo_hint"))
            n_demo = st.number_input(T("demo_count"), min_value=4, max_value=64, value=16, step=1)
            prefix = st.text_input(T("demo_prefix"), value="Пилот")
            if st.button(T("demo_add")):
                if participant_count(tournament_id) > 0:
                    st.warning(T("demo_already"))
                else:
                    rows = [(tournament_id, f"{prefix} {i}") for i in range(1, int(n_demo) + 1)]
                    exec_many("INSERT INTO participants(tournament_id, name) VALUES(?,?)", rows)
                    st.success(f'{T("demo_added")}: {n_demo}')
                    st.rerun()

    with col2:
        participants_raw = qdf("""SELECT id, start_number, name
                                  FROM participants WHERE tournament_id=?
                                  ORDER BY COALESCE(start_number, 9999), name""", (tournament_id,))

        if participants_raw.empty:
            st.info("Пока нет участников. Добавьте слева.")
        else:
            st.markdown(f"**Всего: {len(participants_raw)} участников**")

            for _, row in participants_raw.iterrows():
                pid = int(row["id"])
                pname = row["name"]
                sn = f"#{int(row['start_number'])}" if pd.notna(row["start_number"]) else ""

                with st.container(border=True):
                    c1, c2, c3 = st.columns([1, 5, 2])
                    with c1:
                        st.markdown(f"**{sn}**" if sn else "—")
                    with c2:
                        # Inline edit
                        edit_key = f"edit_mode_{pid}"
                        if st.session_state.get(edit_key, False):
                            new_name = st.text_input("Имя", value=pname, key=f"edit_name_{pid}", label_visibility="collapsed")
                            ec1, ec2 = st.columns(2)
                            with ec1:
                                if st.button("✅", key=f"save_edit_{pid}", use_container_width=True):
                                    if new_name.strip():
                                        exec_sql("UPDATE participants SET name=? WHERE id=?", (new_name.strip(), pid))
                                    st.session_state[edit_key] = False
                                    st.rerun()
                            with ec2:
                                if st.button("❌", key=f"cancel_edit_{pid}", use_container_width=True):
                                    st.session_state[edit_key] = False
                                    st.rerun()
                        else:
                            st.markdown(pname)
                    with c3:
                        bc1, bc2 = st.columns(2)
                        with bc1:
                            if st.button("✏️", key=f"btn_edit_{pid}", use_container_width=True):
                                st.session_state[f"edit_mode_{pid}"] = True
                                st.rerun()
                        with bc2:
                            if st.button("🗑️", key=f"btn_del_{pid}", use_container_width=True):
                                exec_sql("DELETE FROM participants WHERE id=?", (pid,))
                                # Также удаляем квалификацию если есть
                                exec_sql("DELETE FROM qualification_results WHERE participant_id=?", (pid,))
                                st.rerun()

# ============================================================
# TAB 2: Квалификация
# ============================================================
with tabs[2]:
    st.subheader(T("qual_title"))

    if t_status == "setup":
        st.info("Сначала добавьте участников и проведите жеребьёвку на вкладке 'Участники'")
    elif t_status in ("bracket", "finished"):
        st.success("✅ Квалификация завершена!")
        ranking = get_qual_ranking(tournament_id)
        if not ranking.empty:
            advancing = compute_bracket_size(len(ranking))
            st.info(T("qual_cutoff").format(advancing, len(ranking)))
            display = ranking[["place", "name", "start_number", "time_seconds",
                               "laps_completed", "completed_all_laps", "projected_time"]].copy()
            display.columns = [T("place"), T("pilot"), "№", T("time_seconds"),
                               T("laps_completed"), T("completed_all"), T("projected_time")]
            styled = style_qual_table(display, advancing)
            st.dataframe(styled, use_container_width=True, hide_index=True)
            st.caption("🟢 Зелёный = проходит | 🔴 Красный = не проходит")
    else:
        st.info(T("qual_info"))
        st.caption(f"⏱️ Лимит: {time_limit} сек | 🔄 Кругов: {total_laps}")

        all_participants = qdf("""
            SELECT p.id as pid, p.name, p.start_number,
                   qr.time_seconds, qr.laps_completed, qr.completed_all_laps
            FROM participants p
            LEFT JOIN qualification_results qr ON qr.participant_id=p.id AND qr.tournament_id=?
            WHERE p.tournament_id=? AND p.start_number IS NOT NULL
            ORDER BY p.start_number
        """, (tournament_id, tournament_id))

        if all_participants.empty:
            st.warning("Проведите жеребьёвку на вкладке 'Участники'")
        else:
            st.markdown("### Ввод результатов")

            for _, row in all_participants.iterrows():
                pid = int(row["pid"])
                sn = int(row["start_number"])
                name = row["name"]

                with st.expander(f"**#{sn} {name}**" + (" ✅" if pd.notna(row["time_seconds"]) else " ⏳"), expanded=pd.isna(row["time_seconds"])):
                    c1, c2, c3, c4 = st.columns([2, 2, 1, 2])
                    with c1:
                        existing_time = float(row["time_seconds"]) if pd.notna(row["time_seconds"]) else 0.0
                        time_val = st.number_input(
                            f"Время (сек)", min_value=0.0, max_value=999.0,
                            value=existing_time, step=0.001, key=f"qt_{pid}", format="%.3f")
                    with c2:
                        existing_laps = float(row["laps_completed"]) if pd.notna(row["laps_completed"]) else 0.0
                        laps_val = st.number_input(
                            "Круги.Препятствия", min_value=0.0, max_value=99.0,
                            value=existing_laps, step=0.1, key=f"ql_{pid}", format="%.1f")
                    with c3:
                        existing_all = bool(int(row["completed_all_laps"])) if pd.notna(row["completed_all_laps"]) else False
                        all_laps = st.checkbox("Все круги", value=existing_all, key=f"qa_{pid}",
                                               help="Отметьте, если пилот прошёл все круги за отведённое время")
                    with c4:
                        if time_val > 0 and laps_val > 0:
                            proj = time_val if all_laps else calc_projected_time(time_val, laps_val, total_laps)
                            st.metric("Расчётное", format_time(proj))

                    if st.button("💾 Сохранить", key=f"qs_{pid}"):
                        if time_val > 0:
                            save_qual_result(tournament_id, pid, time_val, laps_val, all_laps, total_laps)
                            st.success(T("saved"))
                            st.rerun()
                        else:
                            st.error("Введите время!")

            # --- Таблица результатов ---
            st.divider()
            st.markdown("### 📊 Текущая таблица квалификации")

            ranking = get_qual_ranking(tournament_id)
            if not ranking.empty:
                advancing = compute_bracket_size(len(ranking))
                total_p = participant_count(tournament_id)
                st.info(T("qual_cutoff").format(advancing, total_p))

                display = ranking[["place", "name", "start_number", "time_seconds",
                                   "laps_completed", "completed_all_laps", "projected_time"]].copy()
                display.columns = ["Место", "Пилот", "№", "Время (сек)", "Круги", "Все 3", "Расчётное"]
                styled = style_qual_table(display, advancing)
                st.dataframe(styled, use_container_width=True, hide_index=True)
                st.caption("🟢 Зелёный = проходит | 🔴 Красный = не проходит")

                download_csv_button(display, T("download_csv"), f"qualification_{tournament_id}.csv")

                # Кнопка завершения
                st.divider()
                filled = int(qdf("SELECT COUNT(*) as c FROM qualification_results WHERE tournament_id=? AND time_seconds IS NOT NULL",
                                  (tournament_id,)).iloc[0]["c"])
                if filled < total_p:
                    st.warning(f"Результаты введены: {filled} из {total_p}")

                if filled < total_p:
                    # Не все результаты — нужно двойное подтверждение
                    confirm_qual_key = "confirm_qual_finish"
                    if not st.session_state.get(confirm_qual_key, False):
                        if st.button(T("qual_finish"), type="primary", use_container_width=True):
                            if filled == 0:
                                st.error(T("qual_not_all"))
                            else:
                                st.session_state[confirm_qual_key] = True
                                st.rerun()
                    else:
                        st.warning(f"⚠️ Заполнено {filled} из {total_p} результатов. Продолжить?")
                        qc1, qc2 = st.columns(2)
                        with qc1:
                            if st.button("✅ Да, завершить квалификацию", type="primary", use_container_width=True):
                                st.session_state[confirm_qual_key] = False
                                start_bracket(tournament_id)
                                st.success(T("qual_done"))
                                st.balloons()
                                st.rerun()
                        with qc2:
                            if st.button("❌ Отмена", use_container_width=True):
                                st.session_state[confirm_qual_key] = False
                                st.rerun()
                else:
                    if st.button(T("qual_finish"), type="primary", use_container_width=True):
                        start_bracket(tournament_id)
                        st.success(T("qual_done"))
                        st.balloons()
                        st.rerun()
            else:
                st.info("Введите результаты выше")

# ============================================================
# TAB 3: Сетка
# ============================================================
with tabs[3]:
    st.subheader(T("bracket_title"))

    bracket = get_bracket_for_tournament(tournament_id)
    all_stages = get_all_stages(tournament_id)

    if not bracket:
        st.info(T("waiting_for_qual"))
    else:
        # Статус
        if t_status == "qualification":
            st.info("⚡ Идёт квалификация — сетка сформируется после её завершения")
        elif t_status == "bracket":
            active = get_active_stage(tournament_id)
            if active is not None:
                active_idx = int(active["stage_idx"])
                active_sd = bracket[active_idx]
                sname = active_sd.display_name.get(lang, active_sd.code)
                if active_sd.code == "F":
                    st.success(f"🏆 Идёт: **{sname}**")
                else:
                    st.success(f"🔥 Идёт: **{sname}**")
        elif t_status == "finished":
            st.success("🏆 **ТУРНИР ЗАВЕРШЁН!**")

        st.divider()

        # Колонки для этапов
        cols = st.columns(len(bracket))
        for idx, sd in enumerate(bracket):
            with cols[idx]:
                sname = sd.display_name.get(lang, sd.code)
                if sd.code == "F":
                    st.markdown(f"### 🏆 {sname}")
                else:
                    st.markdown(f"### {sname}")

                stage_row = all_stages[all_stages["stage_idx"] == idx] if not all_stages.empty else pd.DataFrame()
                if not stage_row.empty:
                    stage_id = int(stage_row.iloc[0]["id"])
                    status = stage_row.iloc[0]["status"]

                    if status == "active":
                        st.success("▶ Идёт")
                    elif status == "done":
                        st.caption("✓ Завершён")

                    all_groups = get_all_groups(stage_id)
                    for gno in sorted(all_groups.keys()):
                        members = all_groups[gno]
                        st.markdown(f"**{T('group')} {gno}**")

                        # Если есть результаты — показываем ранжирование
                        results = get_heat_results(stage_id, gno, 1)
                        if results:
                            tdata = []
                            for r in results:
                                tdata.append({
                                    "М": r["place"],
                                    "Пилот": r["name"],
                                    "Время": format_time(r.get("time_seconds")),
                                    "Круги": r.get("laps_completed", "—"),
                                    "Все": "✅" if r.get("completed_all_laps") else "—",
                                    "Расч.": format_time(r.get("projected_time")),
                                })
                            df_d = pd.DataFrame(tdata)
                            styled = style_standings_table(df_d, sd.qualifiers)
                            st.dataframe(styled, use_container_width=True, hide_index=True,
                                         height=35 + 35 * len(tdata))
                        elif not members.empty:
                            tdata = [{"М": i + 1, "Пилот": r["name"], "Время": "—", "Круги": "—", "Все": "—", "Расч.": "—"}
                                     for i, (_, r) in enumerate(members.iterrows())]
                            st.dataframe(pd.DataFrame(tdata), use_container_width=True,
                                         hide_index=True, height=35 + 35 * len(tdata))
                        else:
                            st.caption("⏳ Ожидает")
                else:
                    st.caption("⏳ Ожидает")
                    for gno in range(1, sd.group_count + 1):
                        st.markdown(f"**{T('group')} {gno}**")
                        tdata = [{"М": i + 1, "Пилот": "—", "Время": "—", "Круги": "—", "Все": "—", "Расч.": "—"}
                                 for i in range(sd.group_size)]
                        st.dataframe(pd.DataFrame(tdata), use_container_width=True,
                                     hide_index=True, height=35 + 35 * sd.group_size)

        # Кнопка перехода
        if t_status == "bracket":
            active = get_active_stage(tournament_id)
            if active is not None:
                cur_idx = int(active["stage_idx"])
                if cur_idx + 1 < len(bracket):
                    st.divider()
                    next_sd = bracket[cur_idx + 1]
                    nname = next_sd.display_name.get(lang, next_sd.code)
                    if st.button(f"➡️ Перейти к {nname}", type="primary", use_container_width=True):
                        try:
                            advance_to_next_stage(tournament_id, bracket)
                            st.success(T("saved"))
                            st.rerun()
                        except Exception as e:
                            st.error(str(e))
                elif bracket[cur_idx].code == "F":
                    # Финал завершён?
                    final_sd = bracket[cur_idx]
                    final_ok, final_msg = check_stage_results_complete(int(active["id"]), final_sd)
                    if final_ok:
                        st.divider()
                        if st.button("🏆 Завершить турнир", type="primary", use_container_width=True):
                            exec_sql("UPDATE stages SET status='done' WHERE id=?", (int(active["id"]),))
                            exec_sql("UPDATE tournaments SET status='finished' WHERE id=?", (tournament_id,))
                            st.success("🏆 Турнир завершён!")
                            st.balloons()
                            st.rerun()

        if not all_stages.empty:
            st.caption("🟢 Зелёный = проходит | 🔴 Красный = выбывает")

# ============================================================
# TAB 4: Плей-офф (ввод результатов)
# ============================================================
with tabs[4]:
    st.subheader(T("playoff_title"))

    bracket = get_bracket_for_tournament(tournament_id)
    all_stages = get_all_stages(tournament_id)

    if t_status != "bracket" or all_stages.empty:
        st.info(T("playoff_not_started"))
    else:
        # Найдём активный этап (не финал)
        active = get_active_stage(tournament_id)
        if active is None:
            st.success("Все этапы плей-офф завершены!")
        else:
            stage_id = int(active["id"])
            stage_idx = int(active["stage_idx"])
            sd = bracket[stage_idx]
            sname = sd.display_name.get(lang, sd.code)

            # Если это финал — направляем на вкладку Финал
            if sd.code == "F":
                st.info("🏆 Сейчас идёт ФИНАЛ — вводите результаты на вкладке 'Финал'")
            else:
                st.success(f"🔥 Сейчас: **{sname}**")

                all_groups = get_all_groups(stage_id)

                col1, col2 = st.columns([2, 3])
                with col1:
                    group_options = list(all_groups.keys())
                    if group_options:
                        group_no = st.selectbox(T("select_group"), group_options,
                                                format_func=lambda x: f"{T('group')} {x}", key="po_group")
                    else:
                        group_no = None

                if group_no and group_no in all_groups:
                    members = all_groups[group_no]
                    existing = get_heat_results(stage_id, group_no, 1)
                    existing_map = {r["participant_id"]: r for r in existing}

                    st.divider()
                    st.markdown(f"### {T('group')} {group_no} — Вылет")
                    st.caption(f"⏱️ Лимит: {time_limit} сек | 4 пилота, проходят 2 лучших")

                    results_to_save = []
                    for _, m in members.iterrows():
                        pid = int(m["pid"])
                        pname = m["name"]
                        ex = existing_map.get(pid, {})

                        with st.container(border=True):
                            c1, c2, c3, c4 = st.columns([3, 2, 2, 1])
                            with c1:
                                st.markdown(f"**{pname}**")
                            with c2:
                                ex_time = float(ex["time_seconds"]) if ex.get("time_seconds") else 0.0
                                tval = st.number_input("Время (сек)", min_value=0.0, max_value=999.0,
                                                       value=ex_time, step=0.1, key=f"po_t_{group_no}_{pid}", format="%.2f")
                            with c3:
                                ex_laps = float(ex["laps_completed"]) if ex.get("laps_completed") else 0.0
                                lval = st.number_input("Круги", min_value=0.0, max_value=99.0,
                                                       value=ex_laps, step=0.1, key=f"po_l_{group_no}_{pid}", format="%.1f")
                            with c4:
                                ex_all = bool(ex.get("completed_all_laps", 0))
                                aval = st.checkbox("Все", value=ex_all, key=f"po_a_{group_no}_{pid}")

                            if tval > 0:
                                results_to_save.append({
                                    "pid": pid, "time_seconds": tval,
                                    "laps_completed": lval, "completed_all_laps": aval
                                })

                    st.divider()
                    c1, c2 = st.columns([2, 1])
                    with c1:
                        if st.button("💾 СОХРАНИТЬ РЕЗУЛЬТАТЫ", type="primary", use_container_width=True, key="po_save"):
                            if len(results_to_save) == len(members):
                                save_heat(stage_id, group_no, 1, results_to_save, is_final=False)
                                st.success(T("saved"))
                                st.balloons()
                                st.rerun()
                            else:
                                st.error("Введите результаты для всех пилотов!")

                    # Таблица результатов группы
                    results = get_heat_results(stage_id, group_no, 1)
                    if results:
                        st.markdown("### 📊 Результаты")
                        tdata = []
                        for r in results:
                            tdata.append({
                                "М": r["place"], "Пилот": r["name"],
                                "Время": format_time(r["time_seconds"]),
                                "Круги": r["laps_completed"],
                                "Расч.": format_time(r["projected_time"]),
                            })
                        df_r = pd.DataFrame(tdata)
                        styled = style_standings_table(df_r, sd.qualifiers)
                        st.dataframe(styled, use_container_width=True, hide_index=True)
                        st.caption("🟢 Проходит | 🔴 Выбывает")

# ============================================================
# TAB 5: Финал
# ============================================================
with tabs[5]:
    st.subheader(f"🏆 {T('final_title')}")

    bracket = get_bracket_for_tournament(tournament_id)
    all_stages = get_all_stages(tournament_id)

    # Найдём финальный этап
    final_stage = None
    if not all_stages.empty:
        for idx, sd in enumerate(bracket):
            if sd.code == "F":
                row = all_stages[all_stages["stage_idx"] == idx]
                if not row.empty:
                    final_stage = row.iloc[0]
                break

    if final_stage is None:
        st.info("Финал ещё не начался. Завершите предыдущие этапы.")
    else:
        stage_id = int(final_stage["id"])
        members = get_group_members(stage_id, 1)

        if members.empty:
            st.warning("Финалисты не определены")
        else:
            st.success(f"🏆 Финалисты: {', '.join(members['name'].tolist())}")
            st.caption(T("bonus_note"))

            # 3 вылета
            for heat_no in range(1, 4):
                st.divider()
                st.markdown(f"### {T('heat_n').format(heat_no)}")

                existing = get_heat_results(stage_id, 1, heat_no)
                existing_map = {r["participant_id"]: r for r in existing}

                results_to_save = []
                for _, m in members.iterrows():
                    pid = int(m["pid"])
                    pname = m["name"]
                    ex = existing_map.get(pid, {})

                    c1, c2, c3, c4 = st.columns([3, 2, 2, 1])
                    with c1:
                        st.markdown(f"**{pname}**")
                    with c2:
                        ex_time = float(ex["time_seconds"]) if ex.get("time_seconds") else 0.0
                        tval = st.number_input("Время", min_value=0.0, max_value=999.0,
                                               value=ex_time, step=0.1,
                                               key=f"fn_t_{heat_no}_{pid}", format="%.2f")
                    with c3:
                        ex_laps = float(ex["laps_completed"]) if ex.get("laps_completed") else 0.0
                        lval = st.number_input("Круги", min_value=0.0, max_value=99.0,
                                               value=ex_laps, step=0.1,
                                               key=f"fn_l_{heat_no}_{pid}", format="%.1f")
                    with c4:
                        ex_all = bool(ex.get("completed_all_laps", 0))
                        aval = st.checkbox("Все", value=ex_all, key=f"fn_a_{heat_no}_{pid}")

                    if tval > 0:
                        results_to_save.append({
                            "pid": pid, "time_seconds": tval,
                            "laps_completed": lval, "completed_all_laps": aval
                        })

                if st.button(f"💾 Сохранить вылет {heat_no}", type="primary", key=f"fn_save_{heat_no}"):
                    if len(results_to_save) == len(members):
                        save_heat(stage_id, 1, heat_no, results_to_save, is_final=True)
                        st.success(T("saved"))
                        st.rerun()
                    else:
                        st.error("Введите результаты для всех!")

                # Показываем результаты вылета
                results = get_heat_results(stage_id, 1, heat_no)
                if results:
                    tdata = [{"М": r["place"], "Пилот": r["name"],
                              "Время": format_time(r["time_seconds"]),
                              "Очки": f"+{r['points']}"} for r in results]
                    st.dataframe(pd.DataFrame(tdata), use_container_width=True, hide_index=True)

            # Итоговая таблица
            st.divider()
            st.markdown(f"### 🏆 {T('final_standings')}")

            standings = compute_final_standings(stage_id)
            if not standings.empty:
                for _, row in standings.iterrows():
                    rank = int(row["rank"])
                    name = row["name"]
                    total = int(row["total"])
                    pts = int(row["total_points"])
                    wins = int(row["wins"])
                    bonus = int(row["bonus"])

                    if rank == 1:
                        icon = "🥇"
                    elif rank == 2:
                        icon = "🥈"
                    elif rank == 3:
                        icon = "🥉"
                    else:
                        icon = f"{rank}."

                    bonus_str = " (+1 бонус)" if bonus > 0 else ""
                    if rank == 1:
                        st.success(f"{icon} **{name}** — {total} оч. ({pts} + {bonus} бонус, {wins} поб.) {T('champion')}")
                    else:
                        st.write(f"{icon} **{name}** — {total} оч. ({pts}{bonus_str}, {wins} поб.)")

                # Завершение турнира
                if int(standings.iloc[0].get("heats_played", 0)) >= 3:
                    st.divider()
                    if t_status != "finished":
                        if st.button("🏆 Завершить турнир", type="primary", use_container_width=True, key="finish_tournament"):
                            exec_sql("UPDATE stages SET status='done' WHERE id=?", (stage_id,))
                            exec_sql("UPDATE tournaments SET status='finished' WHERE id=?", (tournament_id,))
                            st.success("🏆 Турнир завершён!")
                            st.balloons()
                            st.rerun()
            else:
                st.info("Введите результаты вылетов выше")
