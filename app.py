import sqlite3
from dataclasses import dataclass
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
/* Прогресс турнира */
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
        "ruleset": "Формат соревнований",
        "create_tournament": "Создать турнир",
        "pick_or_create": "Выберите турнир слева или создайте новый",

        # Навигация
        "nav_overview": "📊 Обзор",
        "nav_participants": "👥 Участники",
        "nav_groups": "🎯 Группы",
        "nav_group_stage": "✏️ Групповой этап",
        "nav_playoff": "🔥 Плей-офф",
        "nav_bracket": "🏆 Сетка",

        # Обзор
        "overview_title": "Обзор турнира",
        "total_participants": "Всего участников",
        "expected_participants": "Требуется",
        "current_stage": "Текущий этап",
        "no_stage": "Этап не создан",
        "tournament_progress": "Прогресс турнира",
        "stage_completed": "Завершён",
        "stage_active": "Активный",
        "stage_pending": "Ожидает",

        # Участники
        "participants_title": "Список участников",
        "add_participant": "Добавить участника",
        "pilot_name": "Имя пилота",
        "seed": "Посев (место в квалификации)",
        "add": "Добавить",
        "seed_unique": "Этот номер посева уже занят",
        "demo_fill": "Тестовое заполнение",
        "demo_hint": "Быстро добавить тестовых участников",
        "demo_count": "Количество",
        "demo_prefix": "Префикс имени",
        "demo_add": "Добавить тестовых",
        "demo_already": "Участники уже добавлены",
        "demo_added": "Добавлено участников",

        # Группы
        "groups_title": "Группы этапа",
        "create_stage": "Сформировать группы",
        "cannot_create": "Недостаточно участников",
        "stage_created": "Группы сформированы!",
        "group": "Группа",
        "no_groups": "Группы ещё не сформированы",
        "qualifies": "проходит",
        "download_csv": "📥 Скачать CSV",

        # Групповой этап
        "group_stage_title": "Групповой этап — ввод результатов",
        "group_stage_info": "Здесь вводятся результаты вылетов группового этапа",
        "select_group": "Выберите группу",
        "heat_number": "Номер вылета",
        
        # Плей-офф
        "playoff_title": "Плей-офф — ввод результатов",
        "playoff_not_started": "Плей-офф ещё не начался. Завершите групповой этап и нажмите 'Начать плей-офф' на вкладке Сетка.",
        "playoff_round": "Раунд",
        "start_playoff": "🚀 Начать плей-офф",
        "group_stage_active": "⚡ Идёт групповой этап",
        "playoff_active": "🔥 Идёт плей-офф",
        "waiting_for_groups": "Ожидает завершения групп",
        "dnf_pilots": "DNF (не финишировали)",
        "finish_order": "Порядок финиша",
        "place": "место",
        "save_results": "💾 Сохранить результаты",
        "saved": "Сохранено!",
        "autofill": "Автозаполнить по посеву",
        "clear": "Очистить",
        "heat_results": "Результаты вылета",
        "points": "Очки",
        "total_points": "Всего очков",
        "wins": "Победы",
        "rank": "Место",

        # Сетка
        "bracket_title": "Турнирная сетка",
        "advance_stage": "Перейти к следующему этапу",
        "last_stage": "Это финал! Турнир завершён",
        "tie_warning": "⚠️ Обнаружено равенство очков! Может потребоваться дополнительный вылет",
        "next_stage": "Следующий этап",
        "transition_map": "Схема перехода",
        "from_group": "из группы",
        "place_short": "м.",
        "final": "ФИНАЛ",
        "semifinal": "Полуфинал",
        "quarterfinal": "Четвертьфинал",
        "round_of_16": "1/8 финала",

        # Общее
        "saved_msg": "✅ Сохранено",
        "error": "Ошибка",
    },
    "EN": {
        "app_title": "🏁 Drone Racing Tournament",
        "language": "Language",
        "tournament": "Tournament",
        "select_tournament": "Select tournament",
        "create_new": "➕ Create new",
        "create_new_header": "New tournament",
        "tournament_name": "Tournament name",
        "ruleset": "Competition format",
        "create_tournament": "Create tournament",
        "pick_or_create": "Select a tournament on the left or create a new one",

        "nav_overview": "📊 Overview",
        "nav_participants": "👥 Pilots",
        "nav_groups": "🎯 Groups",
        "nav_group_stage": "✏️ Group Stage",
        "nav_playoff": "🔥 Playoff",
        "nav_bracket": "🏆 Bracket",

        "overview_title": "Tournament Overview",
        "total_participants": "Total pilots",
        "expected_participants": "Required",
        "current_stage": "Current stage",
        "no_stage": "No stage created",
        "tournament_progress": "Tournament progress",
        "stage_completed": "Completed",
        "stage_active": "Active",
        "stage_pending": "Pending",

        "participants_title": "Pilots list",
        "add_participant": "Add pilot",
        "pilot_name": "Pilot name",
        "seed": "Seed (qualification rank)",
        "add": "Add",
        "seed_unique": "This seed number is already taken",
        "demo_fill": "Test data",
        "demo_hint": "Quickly add test participants",
        "demo_count": "Count",
        "demo_prefix": "Name prefix",
        "demo_add": "Add test pilots",
        "demo_already": "Pilots already added",
        "demo_added": "Pilots added",

        "groups_title": "Stage groups",
        "create_stage": "Create groups",
        "cannot_create": "Not enough participants",
        "stage_created": "Groups created!",
        "group": "Group",
        "no_groups": "Groups not yet created",
        "qualifies": "qualify",
        "download_csv": "📥 Download CSV",

        # Group stage
        "group_stage_title": "Group Stage — Enter Results",
        "group_stage_info": "Enter heat results for the group stage here",
        "select_group": "Select group",
        "heat_number": "Heat number",
        "dnf_pilots": "DNF (did not finish)",
        "finish_order": "Finish order",
        "place": "place",
        "save_results": "💾 Save results",
        "saved": "Saved!",
        
        # Playoff
        "playoff_title": "Playoff — Enter Results",
        "playoff_not_started": "Playoff not started yet. Finish the group stage and click 'Start Playoff' on the Bracket tab.",
        "playoff_round": "Round",
        "start_playoff": "🚀 Start Playoff",
        "group_stage_active": "⚡ Group Stage Active",
        "playoff_active": "🔥 Playoff Active",
        "waiting_for_groups": "Waiting for groups to finish",
        "autofill": "Auto-fill by seed",
        "clear": "Clear",
        "heat_results": "Heat results",
        "points": "Points",
        "total_points": "Total points",
        "wins": "Wins",
        "rank": "Rank",

        "bracket_title": "Tournament bracket",
        "advance_stage": "Advance to next stage",
        "last_stage": "This is the final! Tournament completed",
        "tie_warning": "⚠️ Tie detected! An extra heat may be required",
        "next_stage": "Next stage",
        "transition_map": "Transition map",
        "from_group": "from group",
        "place_short": "pl.",
        "final": "FINAL",
        "semifinal": "Semifinal",
        "quarterfinal": "Quarterfinal",
        "round_of_16": "Round of 16",

        "saved_msg": "✅ Saved",
        "error": "Error",
    },
}

def T(key: str) -> str:
    lang = st.session_state.get("lang", "RU")
    return I18N.get(lang, I18N["RU"]).get(key, key)

# ============================================================
# ПРАВИЛА (таблицы посева и пересева)
# ============================================================

# Посев 32 → 1/8 (Таблица №3)
SEEDING_1_8_32: Dict[int, List[int]] = {
    1: [1, 9, 24, 32],
    2: [8, 16, 17, 25],
    3: [7, 15, 18, 26],
    4: [6, 14, 19, 27],
    5: [5, 13, 20, 28],
    6: [4, 12, 21, 29],
    7: [3, 11, 22, 30],
    8: [2, 10, 23, 31],
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

# Посев 16 → 1/4 (Таблица №4)
SEEDING_1_4_16: Dict[int, List[int]] = {
    1: [1, 5, 12, 16],
    2: [3, 7, 10, 14],
    3: [2, 6, 11, 15],
    4: [4, 8, 9, 13],
}

# Посев 32 → 1/4 по 8 человек (Таблица №6)
SEEDING_1_4_32_8P: Dict[int, List[int]] = {
    1: [1, 5, 9, 13, 17, 21, 25, 29],
    2: [2, 6, 10, 14, 18, 22, 26, 30],
    3: [3, 7, 11, 15, 19, 23, 27, 31],
    4: [4, 8, 12, 16, 20, 24, 28, 32],
}

# Пересев 1/4(8) → 1/2(8)
PROGRESS_1_4_TO_1_2_8P: Dict[int, List[Tuple[int, int]]] = {
    1: [(1, 1), (2, 1), (3, 4), (4, 4), (1, 2), (2, 2), (3, 3), (4, 3)],
    2: [(1, 3), (2, 3), (3, 2), (4, 2), (1, 4), (2, 4), (3, 1), (4, 1)],
}

# Пересев 1/2(8) → Финал(8)
PROGRESS_1_2_TO_FINAL_8P: Dict[int, List[Tuple[int, int]]] = {
    1: [(1, 1), (2, 1), (3, 1), (4, 1), (1, 2), (2, 2), (3, 2), (4, 2)]
}

# Схемы начисления очков
SCORING = {
    "group4": {1: 4, 2: 3, 3: 2, 4: 1},
    "group8": {1: 4, 2: 3, 3: 2, 4: 1, 5: 0, 6: 0, 7: 0, 8: 0},
    "final4": {1: 3, 2: 2, 3: 1, 4: 0},
}

@dataclass
class StageDef:
    code: str
    display_name: Dict[str, str]
    group_size: int
    group_count: int
    qualifiers: int  # сколько проходит из группы
    scoring: str
    bonus_two_wins: bool
    seeding_map: Optional[Dict[int, List[int]]] = None
    progress_map: Optional[Dict[int, List[Tuple[int, int]]]] = None

RULESETS: Dict[str, Dict] = {
    "32_classic": {
        "name": {
            "RU": "32 пилота: 1/8 → 1/4 → 1/2 → Финал",
            "EN": "32 pilots: 1/8 → 1/4 → 1/2 → Final",
        },
        "stages": [
            StageDef("1/8", {"RU": "1/8 финала", "EN": "Round of 16"}, 4, 8, 2, "group4", False, seeding_map=SEEDING_1_8_32),
            StageDef("1/4", {"RU": "Четвертьфинал", "EN": "Quarterfinal"}, 4, 4, 2, "group4", False, progress_map=PROGRESS_1_8_TO_1_4),
            StageDef("1/2", {"RU": "Полуфинал", "EN": "Semifinal"}, 4, 2, 2, "group4", False, progress_map=PROGRESS_1_4_TO_1_2),
            StageDef("F", {"RU": "ФИНАЛ", "EN": "FINAL"}, 4, 1, 0, "final4", True, progress_map=PROGRESS_1_2_TO_FINAL),
        ],
    },
    "16_classic": {
        "name": {
            "RU": "16 пилотов: 1/4 → 1/2 → Финал",
            "EN": "16 pilots: 1/4 → 1/2 → Final",
        },
        "stages": [
            StageDef("1/4", {"RU": "Четвертьфинал", "EN": "Quarterfinal"}, 4, 4, 2, "group4", False, seeding_map=SEEDING_1_4_16),
            StageDef("1/2", {"RU": "Полуфинал", "EN": "Semifinal"}, 4, 2, 2, "group4", False, progress_map=PROGRESS_1_4_TO_1_2),
            StageDef("F", {"RU": "ФИНАЛ", "EN": "FINAL"}, 4, 1, 0, "final4", True, progress_map=PROGRESS_1_2_TO_FINAL),
        ],
    },
    "32_8pilots": {
        "name": {
            "RU": "32 пилота (группы по 8): 1/4 → 1/2 → Финал",
            "EN": "32 pilots (groups of 8): 1/4 → 1/2 → Final",
        },
        "stages": [
            StageDef("1/4", {"RU": "Четвертьфинал", "EN": "Quarterfinal"}, 8, 4, 4, "group8", False, seeding_map=SEEDING_1_4_32_8P),
            StageDef("1/2", {"RU": "Полуфинал", "EN": "Semifinal"}, 8, 2, 4, "group8", False, progress_map=PROGRESS_1_4_TO_1_2_8P),
            StageDef("F", {"RU": "ФИНАЛ", "EN": "FINAL"}, 8, 1, 0, "group8", False, progress_map=PROGRESS_1_2_TO_FINAL_8P),
        ],
    },
}

# ============================================================
# База данных
# ============================================================

def db() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn

def init_db():
    conn = db()
    conn.executescript("""
    CREATE TABLE IF NOT EXISTS tournaments(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        ruleset_key TEXT NOT NULL,
        created_at TEXT NOT NULL
    );

    CREATE TABLE IF NOT EXISTS participants(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        tournament_id INTEGER NOT NULL,
        name TEXT NOT NULL,
        seed INTEGER NOT NULL,
        UNIQUE(tournament_id, seed),
        FOREIGN KEY(tournament_id) REFERENCES tournaments(id) ON DELETE CASCADE
    );

    CREATE TABLE IF NOT EXISTS stages(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        tournament_id INTEGER NOT NULL,
        stage_idx INTEGER NOT NULL,
        code TEXT NOT NULL,
        group_size INTEGER NOT NULL,
        group_count INTEGER NOT NULL,
        qualifiers INTEGER NOT NULL,
        scoring TEXT NOT NULL,
        bonus_two_wins INTEGER NOT NULL DEFAULT 0,
        status TEXT NOT NULL DEFAULT 'active',
        UNIQUE(tournament_id, stage_idx),
        FOREIGN KEY(tournament_id) REFERENCES tournaments(id) ON DELETE CASCADE
    );

    CREATE TABLE IF NOT EXISTS groups(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        stage_id INTEGER NOT NULL,
        group_no INTEGER NOT NULL,
        UNIQUE(stage_id, group_no),
        FOREIGN KEY(stage_id) REFERENCES stages(id) ON DELETE CASCADE
    );

    CREATE TABLE IF NOT EXISTS group_members(
        group_id INTEGER NOT NULL,
        participant_id INTEGER NOT NULL,
        PRIMARY KEY(group_id, participant_id),
        FOREIGN KEY(group_id) REFERENCES groups(id) ON DELETE CASCADE,
        FOREIGN KEY(participant_id) REFERENCES participants(id) ON DELETE CASCADE
    );

    CREATE TABLE IF NOT EXISTS heats(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        group_id INTEGER NOT NULL,
        heat_no INTEGER NOT NULL,
        UNIQUE(group_id, heat_no),
        FOREIGN KEY(group_id) REFERENCES groups(id) ON DELETE CASCADE
    );

    CREATE TABLE IF NOT EXISTS heat_results(
        heat_id INTEGER NOT NULL,
        participant_id INTEGER NOT NULL,
        place INTEGER,
        dnf INTEGER NOT NULL DEFAULT 0,
        points INTEGER NOT NULL DEFAULT 0,
        PRIMARY KEY(heat_id, participant_id),
        FOREIGN KEY(heat_id) REFERENCES heats(id) ON DELETE CASCADE,
        FOREIGN KEY(participant_id) REFERENCES participants(id) ON DELETE CASCADE
    );
    """)
    conn.commit()
    conn.close()

def qdf(sql: str, params=()) -> pd.DataFrame:
    conn = db()
    df = pd.read_sql_query(sql, conn, params=params)
    conn.close()
    return df

def exec_sql(sql: str, params=()):
    conn = db()
    conn.execute(sql, params)
    conn.commit()
    conn.close()

def exec_many(sql: str, rows: List[tuple]):
    conn = db()
    conn.executemany(sql, rows)
    conn.commit()
    conn.close()

# ============================================================
# Бизнес-логика
# ============================================================

def get_ruleset(tournament_id: int) -> Dict:
    t = qdf("SELECT ruleset_key FROM tournaments WHERE id=?", (tournament_id,)).iloc[0]
    return RULESETS[str(t["ruleset_key"])]

def expected_participants(ruleset_key: str) -> int:
    rs = RULESETS[ruleset_key]
    sd0: StageDef = rs["stages"][0]
    return sd0.group_size * sd0.group_count

def participant_count(tournament_id: int) -> int:
    df = qdf("SELECT COUNT(*) as c FROM participants WHERE tournament_id=?", (tournament_id,))
    return int(df.iloc[0]["c"]) if not df.empty else 0

def get_active_stage(tournament_id: int) -> Optional[pd.Series]:
    df = qdf(
        "SELECT * FROM stages WHERE tournament_id=? AND status='active' ORDER BY stage_idx DESC LIMIT 1",
        (tournament_id,)
    )
    return df.iloc[0] if not df.empty else None

def get_all_stages(tournament_id: int) -> pd.DataFrame:
    return qdf("SELECT * FROM stages WHERE tournament_id=? ORDER BY stage_idx", (tournament_id,))

def points_for_place(scoring: str, place: Optional[int], dnf: bool) -> int:
    if dnf or place is None:
        return 0
    return SCORING.get(scoring, {}).get(int(place), 0)

def create_stage(tournament_id: int, stage_idx: int) -> int:
    ruleset = get_ruleset(tournament_id)
    sd: StageDef = ruleset["stages"][stage_idx]

    exec_sql("""
        INSERT OR IGNORE INTO stages(
            tournament_id, stage_idx, code, group_size, group_count,
            qualifiers, scoring, bonus_two_wins, status
        )
        VALUES(?,?,?,?,?,?,?,?, 'active')
    """, (tournament_id, stage_idx, sd.code, sd.group_size, sd.group_count,
          sd.qualifiers, sd.scoring, int(sd.bonus_two_wins)))

    stage_id = int(qdf(
        "SELECT id FROM stages WHERE tournament_id=? AND stage_idx=?",
        (tournament_id, stage_idx)
    ).iloc[0]["id"])

    existing = qdf("SELECT COUNT(*) as c FROM groups WHERE stage_id=?", (stage_id,)).iloc[0]["c"]
    if int(existing) == 0:
        exec_many(
            "INSERT INTO groups(stage_id, group_no) VALUES(?,?)",
            [(stage_id, gno) for gno in range(1, sd.group_count + 1)]
        )
    return stage_id

def seed_groups(tournament_id: int, stage_id: int, seeding_map: Dict[int, List[int]]):
    groups_df = qdf("SELECT id, group_no FROM groups WHERE stage_id=?", (stage_id,))
    gid_by_no = {int(r["group_no"]): int(r["id"]) for _, r in groups_df.iterrows()}

    inserts = []
    for gno, seeds in seeding_map.items():
        for seed in seeds:
            pid_df = qdf("SELECT id FROM participants WHERE tournament_id=? AND seed=?", (tournament_id, seed))
            if not pid_df.empty:
                inserts.append((gid_by_no[gno], int(pid_df.iloc[0]["id"])))

    exec_many("INSERT OR IGNORE INTO group_members(group_id, participant_id) VALUES(?,?)", inserts)

def get_group_members(stage_id: int, group_no: int) -> pd.DataFrame:
    return qdf("""
        SELECT p.id as pid, p.seed, p.name
        FROM groups g
        JOIN group_members gm ON gm.group_id=g.id
        JOIN participants p ON p.id=gm.participant_id
        WHERE g.stage_id=? AND g.group_no=?
        ORDER BY p.seed
    """, (stage_id, int(group_no)))

def get_all_groups(stage_id: int) -> Dict[int, pd.DataFrame]:
    groups = qdf("SELECT group_no FROM groups WHERE stage_id=? ORDER BY group_no", (stage_id,))
    return {int(g["group_no"]): get_group_members(stage_id, int(g["group_no"])) for _, g in groups.iterrows()}

def save_heat(stage_id: int, group_no: int, heat_no: int, results: List[Dict]):
    group_id = int(qdf("SELECT id FROM groups WHERE stage_id=? AND group_no=?", (stage_id, group_no)).iloc[0]["id"])
    exec_sql("INSERT OR IGNORE INTO heats(group_id, heat_no) VALUES(?,?)", (group_id, heat_no))
    heat_id = int(qdf("SELECT id FROM heats WHERE group_id=? AND heat_no=?", (group_id, heat_no)).iloc[0]["id"])

    stage = qdf("SELECT scoring FROM stages WHERE id=?", (stage_id,)).iloc[0]
    scoring = str(stage["scoring"])

    rows = []
    for r in results:
        pts = points_for_place(scoring, r.get("place"), r.get("dnf", False))
        rows.append((heat_id, r["pid"], r.get("place"), int(r.get("dnf", False)), pts))

    exec_many("""
        INSERT OR REPLACE INTO heat_results(heat_id, participant_id, place, dnf, points)
        VALUES(?,?,?,?,?)
    """, rows)

def get_heat_results(stage_id: int, group_no: int, heat_no: int) -> Dict[int, Dict]:
    group_id_df = qdf("SELECT id FROM groups WHERE stage_id=? AND group_no=?", (stage_id, group_no))
    if group_id_df.empty:
        return {}
    group_id = int(group_id_df.iloc[0]["id"])
    heat_df = qdf("SELECT id FROM heats WHERE group_id=? AND heat_no=?", (group_id, heat_no))
    if heat_df.empty:
        return {}
    heat_id = int(heat_df.iloc[0]["id"])
    df = qdf("SELECT participant_id, place, dnf FROM heat_results WHERE heat_id=?", (heat_id,))
    return {int(r["participant_id"]): {"place": None if pd.isna(r["place"]) else int(r["place"]), "dnf": bool(int(r["dnf"]))} for _, r in df.iterrows()}

def compute_standings(stage_id: int) -> pd.DataFrame:
    df = qdf("""
        SELECT
            g.group_no,
            p.id as pid,
            p.seed,
            p.name,
            COALESCE(SUM(hr.points), 0) as points,
            COALESCE(SUM(CASE WHEN hr.place=1 AND hr.dnf=0 THEN 1 ELSE 0 END), 0) as wins
        FROM groups g
        JOIN group_members gm ON gm.group_id=g.id
        JOIN participants p ON p.id=gm.participant_id
        LEFT JOIN heats h ON h.group_id=g.id
        LEFT JOIN heat_results hr ON hr.heat_id=h.id AND hr.participant_id=p.id
        WHERE g.stage_id=?
        GROUP BY g.group_no, p.id
        ORDER BY g.group_no, points DESC, wins DESC, p.seed ASC
    """, (stage_id,))

    stage = qdf("SELECT bonus_two_wins FROM stages WHERE id=?", (stage_id,)).iloc[0]
    if int(stage["bonus_two_wins"]) == 1:
        df["bonus"] = (df["wins"] >= 2).astype(int)
        df["total"] = df["points"] + df["bonus"]
    else:
        df["bonus"] = 0
        df["total"] = df["points"]

    df = df.sort_values(["group_no", "total", "wins", "seed"], ascending=[True, False, False, True])
    df["rank"] = df.groupby("group_no").cumcount() + 1
    return df

def advance_to_next_stage(tournament_id: int):
    cur = get_active_stage(tournament_id)
    if cur is None:
        return
    ruleset = get_ruleset(tournament_id)
    cur_idx = int(cur["stage_idx"])
    if cur_idx + 1 >= len(ruleset["stages"]):
        return

    next_idx = cur_idx + 1
    next_sd: StageDef = ruleset["stages"][next_idx]
    next_stage_id = create_stage(tournament_id, next_idx)

    standings = compute_standings(int(cur["id"]))

    if next_sd.progress_map:
        groups_df = qdf("SELECT id, group_no FROM groups WHERE stage_id=?", (next_stage_id,))
        gid_by_no = {int(r["group_no"]): int(r["id"]) for _, r in groups_df.iterrows()}

        rows = []
        for target_gno, refs in next_sd.progress_map.items():
            for (place, src_gno) in refs:
                gdf = standings[standings["group_no"] == src_gno].copy()
                gdf = gdf.sort_values(["total", "wins", "seed"], ascending=[False, False, True])
                if len(gdf) >= place:
                    pid = int(gdf.iloc[place - 1]["pid"])
                    rows.append((gid_by_no[target_gno], pid))

        exec_many("INSERT OR IGNORE INTO group_members(group_id, participant_id) VALUES(?,?)", rows)

    exec_sql("UPDATE stages SET status='done' WHERE id=?", (int(cur["id"]),))

# ============================================================
# Визуальные компоненты (Streamlit native)
# ============================================================

def style_standings_table(df: pd.DataFrame, qualifiers: int):
    """Стилизует таблицу: зелёный фон для проходящих, красный для не проходящих"""
    def highlight_row(row):
        rank = row["М"]
        if qualifiers > 0:
            if rank <= qualifiers:
                return ["background-color: #1a472a; color: #90EE90"] * len(row)  # Тёмно-зелёный
            else:
                return ["background-color: #4a1a1a; color: #FFB6B6"] * len(row)  # Тёмно-красный
        return [""] * len(row)
    
    return df.style.apply(highlight_row, axis=1)


def render_group_card_native(group_no: int, standings: pd.DataFrame, qualifiers: int):
    """Рендерит карточку группы — компактная таблица"""
    group_standings = standings[standings["group_no"] == group_no].sort_values("rank")
    
    st.markdown(f"#### Группа {group_no}")
    
    # Создаём данные для таблицы
    table_data = []
    for _, row in group_standings.iterrows():
        rank = int(row["rank"])
        seed = int(row["seed"])
        name = row["name"]
        total = int(row["total"])
        
        table_data.append({
            "М": rank,
            "Пилот": f"#{seed} {name}",
            "Очки": total,
        })
    
    df = pd.DataFrame(table_data)
    styled_df = style_standings_table(df, qualifiers)
    st.dataframe(styled_df, use_container_width=True, hide_index=True, height=35 + 35*len(table_data))
    
    if qualifiers > 0:
        st.caption(f"🟢 Проходят: первые {qualifiers} | 🔴 Не проходят")


def render_bracket_visual(tournament_id: int, lang: str):
    """Рендерит визуальную турнирную сетку — компактные таблицы"""
    ruleset = get_ruleset(tournament_id)
    stages_df = get_all_stages(tournament_id)
    
    # Определяем статус группового этапа
    group_stage_row = stages_df[stages_df["stage_idx"] == 0]
    group_stage_active = not group_stage_row.empty and group_stage_row.iloc[0]["status"] == "active"
    group_stage_done = not group_stage_row.empty and group_stage_row.iloc[0]["status"] == "done"
    
    # Показываем общий статус турнира
    if group_stage_active:
        st.info("⚡ **Сейчас идёт: ГРУППОВОЙ ЭТАП** — вводите результаты на вкладке 'Групповой этап'")
    elif group_stage_done:
        # Проверяем есть ли активный плей-офф этап
        playoff_active = stages_df[(stages_df["stage_idx"] > 0) & (stages_df["status"] == "active")]
        if not playoff_active.empty:
            active_sd = ruleset["stages"][int(playoff_active.iloc[0]["stage_idx"])]
            st.success(f"🔥 **Сейчас идёт: {active_sd.display_name.get(lang, active_sd.code)}** — вводите результаты на вкладке 'Плей-офф'")
        else:
            # Все завершены?
            all_done = all(stages_df["status"] == "done") if not stages_df.empty else False
            if all_done and len(stages_df) == len(ruleset["stages"]):
                st.success("🏆 **ТУРНИР ЗАВЕРШЁН!**")
    
    st.divider()
    
    # Создаем колонки для каждого этапа
    num_stages = len(ruleset["stages"])
    stage_cols = st.columns(num_stages)
    
    for idx, sd in enumerate(ruleset["stages"]):
        stage_row = stages_df[stages_df["stage_idx"] == idx]
        stage_name = sd.display_name.get(lang, sd.code)
        is_final = sd.code == "F"
        is_group_stage = (idx == 0)
        
        with stage_cols[idx]:
            # Заголовок этапа
            if is_final:
                st.markdown(f"### 🏆 {stage_name}")
            elif is_group_stage:
                st.markdown(f"### 📊 {stage_name}")
            else:
                st.markdown(f"### {stage_name}")
            
            if not stage_row.empty:
                stage_id = int(stage_row.iloc[0]["id"])
                status = stage_row.iloc[0]["status"]
                standings = compute_standings(stage_id)
                all_groups = get_all_groups(stage_id)
                
                # Статус этапа — показываем только для текущего
                if status == "active":
                    if is_group_stage:
                        st.success("⚡ Идёт")
                    else:
                        st.success("🔥 Идёт")
                elif status == "done":
                    st.caption("✓ Завершён")
                
                # Группы — компактные таблицы с подсветкой
                for gno in sorted(all_groups.keys()):
                    gdf = standings[standings["group_no"] == gno].sort_values("rank")
                    
                    st.markdown(f"**Группа {gno}**")
                    
                    table_data = []
                    for _, row in gdf.iterrows():
                        rank = int(row["rank"])
                        seed = int(row["seed"])
                        name = row["name"]
                        total = int(row["total"])
                        
                        table_data.append({
                            "М": rank,
                            "Пилот": f"#{seed} {name}",
                            "Оч": total,
                        })
                    
                    df_display = pd.DataFrame(table_data)
                    styled_df = style_standings_table(df_display, sd.qualifiers)
                    st.dataframe(styled_df, use_container_width=True, hide_index=True, height=35 + 35*len(table_data))
                    
            else:
                # Этап ещё не создан — показываем "ожидает"
                if is_group_stage:
                    st.caption("⏳ Создайте группы")
                elif group_stage_active:
                    st.caption("⏳ Ожидает окончания групп")
                else:
                    st.caption("⏳ Ожидает")
                
                for gno in range(1, sd.group_count + 1):
                    st.markdown(f"**Группа {gno}**")
                    placeholder_data = [{"М": i+1, "Пилот": "—", "Оч": 0} for i in range(sd.group_size)]
                    st.dataframe(pd.DataFrame(placeholder_data), use_container_width=True, hide_index=True, height=35 + 35*sd.group_size)
    
    # Примечание о цветах
    st.divider()
    st.caption("🟢 Зелёный = проходит дальше | 🔴 Красный = выбывает")


def render_transition_table(tournament_id: int, cur_stage: pd.Series, next_stage_idx: int, lang: str):
    """Рендерит таблицу перехода на следующий этап"""
    ruleset = get_ruleset(tournament_id)
    next_sd: StageDef = ruleset["stages"][next_stage_idx]
    pm = next_sd.progress_map

    if not pm:
        return

    standings = compute_standings(int(cur_stage["id"]))
    
    st.markdown(f"### 🔀 {T('transition_map')} → {next_sd.display_name.get(lang, next_sd.code)}")
    
    rows = []
    for target_gno, refs in pm.items():
        for place, src_gno in refs:
            gdf = standings[standings["group_no"] == src_gno].sort_values(["total", "wins", "seed"], ascending=[False, False, True])
            pilot_name = "—"
            pilot_seed = "?"
            if len(gdf) >= place:
                pilot_name = gdf.iloc[place - 1]["name"]
                pilot_seed = int(gdf.iloc[place - 1]["seed"])
            
            rows.append({
                "В группу": f"{T('group')} {target_gno}",
                "Откуда": f"{place} {T('place_short')} {T('group')} {src_gno}",
                "Пилот": f"#{pilot_seed} {pilot_name}",
            })
    
    df = pd.DataFrame(rows)
    st.dataframe(df, use_container_width=True, hide_index=True)

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
# Пароль берём из Streamlit Secrets (настраивается в Streamlit Cloud)
import os
APP_PASSWORD = st.secrets.get("APP_PASSWORD", os.environ.get("APP_PASSWORD", ""))

def check_password():
    """Проверяет пароль и возвращает True если авторизован"""
    
    # Проверяем что пароль настроен
    if not APP_PASSWORD:
        st.error("⚠️ Пароль не настроен! Добавьте APP_PASSWORD в Streamlit Secrets.")
        st.stop()
    
    if "authenticated" not in st.session_state:
        st.session_state["authenticated"] = False
    
    if st.session_state["authenticated"]:
        return True
    
    # Показываем форму входа
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

# Проверяем авторизацию
if not check_password():
    st.stop()

# ============================================================

init_db()

# Базовые стили
st.markdown(BASE_CSS, unsafe_allow_html=True)

# --- Сайдбар: язык + турнир
with st.sidebar:
    # Язык — русский по умолчанию
    lang_options = ["RU", "EN"]
    lang_idx = lang_options.index(st.session_state.get("lang", "RU")) if st.session_state.get("lang", "RU") in lang_options else 0
    lang = st.selectbox("🌐 " + I18N["RU"]["language"], lang_options, index=lang_idx, key="lang")

    st.divider()
    
    # Кнопка выхода
    if st.button("🚪 Выйти", use_container_width=True):
        st.session_state["authenticated"] = False
        st.rerun()
    
    st.divider()

    st.header("🏁 " + T("tournament"))

    tdf = qdf("SELECT * FROM tournaments ORDER BY id DESC")
    t_map = {f'{r["name"]}': int(r["id"]) for _, r in tdf.iterrows()} if not tdf.empty else {}
    id_to_name = {v: k for k, v in t_map.items()}

    options = [T("create_new")] + list(t_map.keys())
    
    # Определяем начальный индекс (если есть сохранённый турнир)
    default_idx = 0
    if "selected_tournament" in st.session_state:
        saved_id = st.session_state["selected_tournament"]
        if saved_id in id_to_name:
            saved_name = id_to_name[saved_id]
            if saved_name in options:
                default_idx = options.index(saved_name)
        del st.session_state["selected_tournament"]
    
    sel = st.selectbox(T("select_tournament"), options, index=default_idx)

    if sel == T("create_new"):
        st.subheader(T("create_new_header"))
        name = st.text_input(T("tournament_name"), value=f"Турнир {datetime.now().strftime('%d.%m.%Y')}")
        ruleset_key = st.selectbox(
            T("ruleset"),
            list(RULESETS.keys()),
            format_func=lambda k: RULESETS[k]["name"][lang],
        )
        if st.button(T("create_tournament"), type="primary"):
            exec_sql(
                "INSERT INTO tournaments(name, ruleset_key, created_at) VALUES(?,?,?)",
                (name, ruleset_key, datetime.now().isoformat(timespec="seconds")),
            )
            # Получаем ID созданного турнира и сохраняем для автовыбора
            new_id = qdf("SELECT id FROM tournaments ORDER BY id DESC LIMIT 1").iloc[0]["id"]
            st.session_state["selected_tournament"] = int(new_id)
            st.rerun()
        tournament_id = None
    else:
        tournament_id = t_map[sel]
        tr = qdf("SELECT * FROM tournaments WHERE id=?", (tournament_id,)).iloc[0]
        st.caption(f"📋 {RULESETS[str(tr['ruleset_key'])]['name'][lang]}")

if tournament_id is None:
    st.title(T("app_title"))
    st.info(T("pick_or_create"))
    st.stop()

# --- Основная часть
st.title(T("app_title"))

ruleset = get_ruleset(tournament_id)
ruleset_key = qdf("SELECT ruleset_key FROM tournaments WHERE id=?", (tournament_id,)).iloc[0]["ruleset_key"]
exp_n = expected_participants(ruleset_key)
p_count = participant_count(tournament_id)
active_stage = get_active_stage(tournament_id)

# Навигация tabs
tabs = st.tabs([
    T("nav_overview"),
    T("nav_participants"),
    T("nav_groups"),
    T("nav_group_stage"),
    T("nav_playoff"),
    T("nav_bracket"),
])

# ============================================================
# TAB 0: Обзор
# ============================================================
with tabs[0]:
    st.header(T("overview_title"))

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric(T("total_participants"), f"{p_count} / {exp_n}")
    with col2:
        stage_name = "—"
        if active_stage is not None:
            sd = ruleset["stages"][int(active_stage["stage_idx"])]
            stage_name = sd.display_name.get(lang, sd.code)
        st.metric(T("current_stage"), stage_name)
    with col3:
        all_stages = get_all_stages(tournament_id)
        completed = len(all_stages[all_stages["status"] == "done"])
        st.metric(T("tournament_progress"), f"{completed} / {len(ruleset['stages'])}")

    # Прогресс-бар этапов
    st.markdown(f"**{T('tournament_progress')}**")
    progress_html = '<div class="tournament-progress">'
    for idx, sd in enumerate(ruleset["stages"]):
        stage_row = all_stages[all_stages["stage_idx"] == idx]
        if not stage_row.empty:
            status = stage_row.iloc[0]["status"]
            css = "completed" if status == "done" else "active"
        else:
            css = "pending"
        progress_html += f'<span class="progress-stage {css}">{sd.display_name.get(lang, sd.code)}</span>'
    progress_html += '</div>'
    st.markdown(progress_html, unsafe_allow_html=True)

# ============================================================
# TAB 1: Участники
# ============================================================
with tabs[1]:
    st.header(T("participants_title"))

    col1, col2 = st.columns([1, 2])

    with col1:
        st.subheader(T("add_participant"))
        with st.form("add_pilot", clear_on_submit=True):
            name = st.text_input(T("pilot_name"))
            seed = st.number_input(T("seed"), min_value=1, step=1)
            if st.form_submit_button(T("add"), type="primary"):
                try:
                    exec_sql(
                        "INSERT INTO participants(tournament_id, name, seed) VALUES(?,?,?)",
                        (tournament_id, name.strip(), int(seed)),
                    )
                    st.success(T("saved"))
                    st.rerun()
                except sqlite3.IntegrityError:
                    st.error(T("seed_unique"))

        st.divider()
        st.subheader(T("demo_fill"))
        st.caption(T("demo_hint"))
        n = st.number_input(T("demo_count"), min_value=4, max_value=128, value=int(exp_n), step=1)
        prefix = st.text_input(T("demo_prefix"), value="Пилот")

        if st.button(T("demo_add")):
            if participant_count(tournament_id) > 0:
                st.warning(T("demo_already"))
            else:
                rows = [(tournament_id, f"{prefix} {i}", i) for i in range(1, int(n) + 1)]
                exec_many("INSERT INTO participants(tournament_id, name, seed) VALUES(?,?,?)", rows)
                st.success(f'{T("demo_added")}: {n}')
                st.rerun()

    with col2:
        pdf = qdf(
            "SELECT seed as '№', name as 'Пилот' FROM participants WHERE tournament_id=? ORDER BY seed",
            (tournament_id,),
        )
        st.dataframe(pdf, use_container_width=True, hide_index=True, height=500)

# ============================================================
# TAB 2: Группы
# ============================================================
with tabs[2]:
    st.header(T("groups_title"))

    if active_stage is None:
        st.info(T("no_groups"))

        can_create = p_count >= exp_n
        if not can_create:
            st.warning(f'{T("cannot_create")}: {p_count}/{exp_n}')

        if st.button(T("create_stage"), type="primary", disabled=not can_create):
            sd0 = ruleset["stages"][0]
            stage_id = create_stage(tournament_id, 0)
            if sd0.seeding_map:
                seed_groups(tournament_id, stage_id, sd0.seeding_map)
            st.success(T("stage_created"))
            st.rerun()
    else:
        stage_id = int(active_stage["id"])
        sd = ruleset["stages"][int(active_stage["stage_idx"])]
        standings = compute_standings(stage_id)
        all_groups = get_all_groups(stage_id)

        # Отображаем группы в сетке
        cols = st.columns(min(4, len(all_groups)))
        for idx, gno in enumerate(sorted(all_groups.keys())):
            with cols[idx % len(cols)]:
                render_group_card_native(gno, standings, sd.qualifiers)

        # Кнопка экспорта
        st.divider()
        groups_df = qdf("""
            SELECT g.group_no as 'Группа', p.seed as 'Посев', p.name as 'Пилот'
            FROM groups g
            JOIN group_members gm ON gm.group_id = g.id
            JOIN participants p ON p.id = gm.participant_id
            WHERE g.stage_id = ?
            ORDER BY g.group_no, p.seed
        """, (stage_id,))
        csv = groups_df.to_csv(index=False).encode("utf-8-sig")
        st.download_button(T("download_csv"), data=csv, file_name=f"groups_{sd.code}.csv", mime="text/csv")

# ============================================================
# TAB 3: Групповой этап (ввод результатов)
# ============================================================
with tabs[3]:
    st.header(T("group_stage_title"))
    
    # Проверяем что активный этап - это групповой (stage_idx == 0)
    if active_stage is None:
        st.info("Сначала создайте группы на вкладке 'Группы'")
    elif int(active_stage["stage_idx"]) != 0:
        st.success("✅ Групповой этап завершён! Результаты плей-офф вводятся на вкладке 'Плей-офф'.")
    else:
        stage_id = int(active_stage["id"])
        sd = ruleset["stages"][int(active_stage["stage_idx"])]
        all_groups = get_all_groups(stage_id)
        scoring = SCORING.get(sd.scoring, {})
        
        st.info(f"⚡ Сейчас идёт: **{sd.display_name.get(lang, sd.code)}** (групповой этап)")
        
        col1, col2, col3 = st.columns([2, 2, 3])
        with col1:
            group_no = st.selectbox("Группа", list(all_groups.keys()), format_func=lambda x: f"Группа {x}")
        with col2:
            heat_no = st.number_input("Вылет №", min_value=1, step=1, value=1)
        with col3:
            st.markdown(f"""
            **Очки за места:**  
            🥇 1 место = **{scoring.get(1,0)}** оч. | 🥈 2 место = **{scoring.get(2,0)}** оч.  
            🥉 3 место = **{scoring.get(3,0)}** оч. | 4 место = **{scoring.get(4,0)}** оч.
            """)
        
        st.divider()
        
        members = all_groups[group_no]
        if members.empty:
            st.warning("В группе нет участников")
        else:
            existing = get_heat_results(stage_id, group_no, heat_no)
            pid_map = {int(r["pid"]): {"seed": int(r["seed"]), "name": str(r["name"])} for _, r in members.iterrows()}
            all_pids = list(pid_map.keys())
            
            state_key = f"res_{stage_id}_{group_no}_{heat_no}"
            
            # Инициализация
            if state_key not in st.session_state:
                st.session_state[state_key] = []
                # Загружаем существующие результаты
                if existing:
                    place_to_pid = {}
                    dnf_list = []
                    for pid, data in existing.items():
                        if data.get("dnf"):
                            dnf_list.append(("DNF", pid))
                        elif data.get("place"):
                            place_to_pid[data["place"]] = pid
                    # Сортируем по местам
                    for place in sorted(place_to_pid.keys()):
                        st.session_state[state_key].append(("PLACE", place_to_pid[place]))
                    for item in dnf_list:
                        st.session_state[state_key].append(item)
            
            results_list = st.session_state[state_key]  # [("PLACE", pid), ("DNF", pid), ...]
            assigned_pids = {item[1] for item in results_list}
            free_pids = [pid for pid in all_pids if pid not in assigned_pids]
            
            # Текущее место для назначения
            current_place = sum(1 for item in results_list if item[0] == "PLACE") + 1
            
            # === ГЛАВНАЯ СЕКЦИЯ ===
            left_col, right_col = st.columns([3, 2])
            
            with left_col:
                st.markdown("### 👆 Нажмите на пилота в порядке финиша")
                
                if free_pids:
                    st.markdown(f"**Сейчас выбираем: {current_place} место** (+{scoring.get(current_place, 0)} очков)")
                    
                    # Большие кнопки для каждого пилота
                    for pid in free_pids:
                        info = pid_map[pid]
                        col_btn, col_dnf = st.columns([4, 1])
                        with col_btn:
                            if st.button(f"🏁  #{info['seed']} {info['name']}", key=f"p_{state_key}_{pid}", use_container_width=True):
                                st.session_state[state_key].append(("PLACE", pid))
                                st.rerun()
                        with col_dnf:
                            if st.button("❌", key=f"dnf_{state_key}_{pid}", help="Не финишировал (DNF)"):
                                st.session_state[state_key].append(("DNF", pid))
                                st.rerun()
                else:
                    st.success("✅ Все пилоты распределены!")
            
            with right_col:
                st.markdown("### 📋 Результаты вылета")
                
                if results_list:
                    place_counter = 1
                    for idx, (status, pid) in enumerate(results_list):
                        info = pid_map[pid]
                        
                        if status == "PLACE":
                            pts = scoring.get(place_counter, 0)
                            if place_counter == 1:
                                icon = "🥇"
                            elif place_counter == 2:
                                icon = "🥈"
                            elif place_counter == 3:
                                icon = "🥉"
                            else:
                                icon = f"{place_counter}."
                            
                            c1, c2 = st.columns([5, 1])
                            c1.markdown(f"{icon} **{info['name']}** (+{pts})")
                            if c2.button("↩", key=f"undo_{state_key}_{idx}"):
                                st.session_state[state_key].pop(idx)
                                st.rerun()
                            place_counter += 1
                        else:
                            c1, c2 = st.columns([5, 1])
                            c1.markdown(f"❌ ~~{info['name']}~~ (DNF)")
                            if c2.button("↩", key=f"undo_{state_key}_{idx}"):
                                st.session_state[state_key].pop(idx)
                                st.rerun()
                else:
                    st.info("Пусто. Нажмите на пилота слева.")
            
            # === КНОПКИ ДЕЙСТВИЙ ===
            st.divider()
            
            all_done = len(results_list) == len(all_pids)
            
            btn_col1, btn_col2, btn_col3 = st.columns([2, 1, 1])
            
            with btn_col1:
                if st.button("💾 СОХРАНИТЬ", type="primary", disabled=not all_done, use_container_width=True):
                    results = []
                    place_counter = 1
                    for status, pid in results_list:
                        if status == "PLACE":
                            results.append({"pid": pid, "place": place_counter, "dnf": False})
                            place_counter += 1
                        else:
                            results.append({"pid": pid, "place": None, "dnf": True})
                    
                    save_heat(stage_id, group_no, heat_no, results)
                    del st.session_state[state_key]
                    st.success("✅ Сохранено!")
                    st.balloons()
                    st.rerun()
            
            with btn_col2:
                if st.button("🔄 Сбросить", use_container_width=True):
                    st.session_state[state_key] = []
                    st.rerun()
            
            with btn_col3:
                # Автозаполнение по посеву
                if st.button("⚡ По посеву", use_container_width=True, help="Заполнить по номерам посева"):
                    st.session_state[state_key] = []
                    for pid in sorted(all_pids, key=lambda p: pid_map[p]["seed"]):
                        st.session_state[state_key].append(("PLACE", pid))
                    st.rerun()
            
            if not all_done:
                st.warning(f"⏳ Осталось: {len(all_pids) - len(results_list)} пилот(ов)")
        
        # === ТАБЛИЦА ОЧКОВ ===
        st.divider()
        st.markdown("### 🏆 Таблица очков этапа")
        st.caption("🟢 Зелёный = проходит в плей-офф | 🔴 Красный = выбывает")
        
        standings = compute_standings(stage_id)
        
        for gno in sorted(standings["group_no"].unique()):
            gdf = standings[standings["group_no"] == gno].sort_values("rank")
            
            with st.expander(f"Группа {gno}" + (" ← текущая" if gno == group_no else ""), expanded=(gno == group_no)):
                table_rows = []
                for _, row in gdf.iterrows():
                    rank = int(row["rank"])
                    table_rows.append({
                        "М": rank,
                        "Пилот": f"#{int(row['seed'])} {row['name']}",
                        "Очки": int(row["total"]),
                        "Побед": int(row["wins"]),
                    })
                df = pd.DataFrame(table_rows)
                styled_df = style_standings_table(df, sd.qualifiers)
                st.dataframe(styled_df, use_container_width=True, hide_index=True)

# ============================================================
# TAB 4: Плей-офф (ввод результатов)
# ============================================================
with tabs[4]:
    st.header(T("playoff_title"))
    
    # Определяем текущий этап плей-офф
    all_stages_df = get_all_stages(tournament_id)
    
    # Групповой этап - это stage_idx == 0
    group_stage = all_stages_df[all_stages_df["stage_idx"] == 0]
    group_stage_done = not group_stage.empty and group_stage.iloc[0]["status"] == "done"
    
    if not group_stage_done:
        st.warning(T("playoff_not_started"))
        st.info("👉 Завершите групповой этап и нажмите 'Начать плей-офф' на вкладке **Сетка**")
    else:
        # Найдём активный этап плей-офф (stage_idx > 0)
        playoff_stages = all_stages_df[all_stages_df["stage_idx"] > 0]
        active_playoff = playoff_stages[playoff_stages["status"] == "active"]
        
        if active_playoff.empty:
            # Проверяем есть ли вообще плей-офф этапы
            if playoff_stages.empty:
                st.info("⏳ Плей-офф этапы ещё не созданы. Нажмите 'Перейти к следующему этапу' на вкладке Сетка.")
            else:
                st.success("🏆 Плей-офф завершён!")
        else:
            playoff_stage = active_playoff.iloc[0]
            stage_id = int(playoff_stage["id"])
            stage_idx = int(playoff_stage["stage_idx"])
            sd = ruleset["stages"][stage_idx]
            stage_name = sd.display_name.get(lang, sd.code)
            
            st.success(f"🔥 Сейчас идёт: **{stage_name}**")
            
            all_groups = get_all_groups(stage_id)
            scoring = SCORING.get(sd.scoring, {})
            
            # === ВЫБОР ГРУППЫ ===
            col1, col2, col3 = st.columns([2, 2, 3])
            with col1:
                group_options = list(all_groups.keys())
                if group_options:
                    group_no = st.selectbox("Группа", group_options, format_func=lambda x: f"Группа {x}", key="playoff_group")
                else:
                    group_no = 1
                    st.warning("Нет групп")
            with col2:
                heat_no = st.number_input("Вылет №", min_value=1, step=1, value=1, key="playoff_heat")
            with col3:
                st.markdown(f"""
                **Очки за места:**  
                🥇 1м = **{scoring.get(1,0)}** | 🥈 2м = **{scoring.get(2,0)}** | 🥉 3м = **{scoring.get(3,0)}** | 4м = **{scoring.get(4,0)}**
                """)
            
            st.divider()
            
            if group_no in all_groups:
                members = all_groups[group_no]
                if members.empty:
                    st.warning("В группе нет участников")
                else:
                    existing = get_heat_results(stage_id, group_no, heat_no)
                    pid_map = {int(r["pid"]): {"seed": int(r["seed"]), "name": str(r["name"])} for _, r in members.iterrows()}
                    all_pids = list(pid_map.keys())
                    
                    state_key = f"playoff_{stage_id}_{group_no}_{heat_no}"
                    
                    # Инициализация
                    if state_key not in st.session_state:
                        st.session_state[state_key] = []
                        if existing:
                            place_to_pid = {}
                            dnf_list = []
                            for pid, data in existing.items():
                                if data.get("dnf"):
                                    dnf_list.append(("DNF", pid))
                                elif data.get("place"):
                                    place_to_pid[data["place"]] = pid
                            for place in sorted(place_to_pid.keys()):
                                st.session_state[state_key].append(("PLACE", place_to_pid[place]))
                            for item in dnf_list:
                                st.session_state[state_key].append(item)
                    
                    results_list = st.session_state[state_key]
                    assigned_pids = {item[1] for item in results_list}
                    free_pids = [pid for pid in all_pids if pid not in assigned_pids]
                    current_place = sum(1 for item in results_list if item[0] == "PLACE") + 1
                    
                    # === UI ввода ===
                    left_col, right_col = st.columns([3, 2])
                    
                    with left_col:
                        st.markdown("### 👆 Нажмите на пилота в порядке финиша")
                        
                        if free_pids:
                            st.markdown(f"**Сейчас: {current_place} место** (+{scoring.get(current_place, 0)} очков)")
                            
                            for pid in free_pids:
                                info = pid_map[pid]
                                c1, c2 = st.columns([4, 1])
                                with c1:
                                    if st.button(f"🏁 #{info['seed']} {info['name']}", key=f"pp_{state_key}_{pid}", use_container_width=True):
                                        st.session_state[state_key].append(("PLACE", pid))
                                        st.rerun()
                                with c2:
                                    if st.button("❌", key=f"pd_{state_key}_{pid}", help="DNF"):
                                        st.session_state[state_key].append(("DNF", pid))
                                        st.rerun()
                        else:
                            st.success("✅ Все распределены!")
                    
                    with right_col:
                        st.markdown("### 📋 Результаты")
                        
                        if results_list:
                            place_counter = 1
                            for idx, (status, pid) in enumerate(results_list):
                                info = pid_map[pid]
                                if status == "PLACE":
                                    pts = scoring.get(place_counter, 0)
                                    icon = "🥇" if place_counter == 1 else ("🥈" if place_counter == 2 else ("🥉" if place_counter == 3 else f"{place_counter}."))
                                    c1, c2 = st.columns([5, 1])
                                    c1.markdown(f"{icon} **{info['name']}** (+{pts})")
                                    if c2.button("↩", key=f"pu_{state_key}_{idx}"):
                                        st.session_state[state_key].pop(idx)
                                        st.rerun()
                                    place_counter += 1
                                else:
                                    c1, c2 = st.columns([5, 1])
                                    c1.markdown(f"❌ ~~{info['name']}~~ (DNF)")
                                    if c2.button("↩", key=f"pu_{state_key}_{idx}"):
                                        st.session_state[state_key].pop(idx)
                                        st.rerun()
                        else:
                            st.info("Пусто")
                    
                    # === КНОПКИ ===
                    st.divider()
                    all_done = len(results_list) == len(all_pids)
                    
                    c1, c2 = st.columns([2, 1])
                    with c1:
                        if st.button("💾 СОХРАНИТЬ", type="primary", disabled=not all_done, use_container_width=True, key="playoff_save"):
                            results = []
                            place_counter = 1
                            for status, pid in results_list:
                                if status == "PLACE":
                                    results.append({"pid": pid, "place": place_counter, "dnf": False})
                                    place_counter += 1
                                else:
                                    results.append({"pid": pid, "place": None, "dnf": True})
                            save_heat(stage_id, group_no, heat_no, results)
                            del st.session_state[state_key]
                            st.success("✅ Сохранено!")
                            st.balloons()
                            st.rerun()
                    with c2:
                        if st.button("🔄 Сбросить", use_container_width=True, key="playoff_reset"):
                            st.session_state[state_key] = []
                            st.rerun()
                    
                    if not all_done:
                        st.warning(f"⏳ Осталось: {len(all_pids) - len(results_list)}")
            
            # === Таблица текущего этапа ===
            st.divider()
            st.markdown(f"### 🏆 Таблица {stage_name}")
            if sd.qualifiers > 0:
                st.caption("🟢 Зелёный = проходит дальше | 🔴 Красный = выбывает")
            
            standings = compute_standings(stage_id)
            
            for gno in sorted(standings["group_no"].unique()):
                gdf = standings[standings["group_no"] == gno].sort_values("rank")
                with st.expander(f"Группа {gno}", expanded=True):
                    rows = []
                    for _, row in gdf.iterrows():
                        rank = int(row["rank"])
                        rows.append({
                            "М": rank,
                            "Пилот": f"#{int(row['seed'])} {row['name']}",
                            "Оч": int(row["total"]),
                        })
                    df = pd.DataFrame(rows)
                    styled_df = style_standings_table(df, sd.qualifiers)
                    st.dataframe(styled_df, use_container_width=True, hide_index=True)

# ============================================================
# TAB 5: Сетка турнира
# ============================================================
with tabs[5]:
    st.header(T("bracket_title"))

    # Визуальная сетка
    render_bracket_visual(tournament_id, lang)

    # Переход на следующий этап
    if active_stage is not None:
        cur_idx = int(active_stage["stage_idx"])
        is_group_stage = (cur_idx == 0)

        if cur_idx + 1 >= len(ruleset["stages"]):
            st.success(f"🏆 {T('last_stage')}")
        else:
            st.divider()
            
            # Схема перехода
            next_sd = ruleset["stages"][cur_idx + 1]
            
            if is_group_stage:
                st.markdown("### 🚀 Переход к плей-офф")
                st.info(f"После завершения группового этапа, нажмите кнопку ниже чтобы начать **{next_sd.display_name.get(lang, next_sd.code)}**")
            else:
                st.markdown(f"### ➡️ Переход к {next_sd.display_name.get(lang, next_sd.code)}")
            
            render_transition_table(tournament_id, active_stage, cur_idx + 1, lang)

            # Проверка на равенство очков
            standings = compute_standings(int(active_stage["id"]))
            stage_info = qdf("SELECT qualifiers FROM stages WHERE id=?", (int(active_stage["id"]),)).iloc[0]
            q = int(stage_info["qualifiers"])

            tie_detected = False
            if q > 0:
                for gno in standings["group_no"].unique():
                    gdf = standings[standings["group_no"] == gno].sort_values(["total", "wins", "seed"], ascending=[False, False, True]).reset_index(drop=True)
                    if len(gdf) > q:
                        if gdf.iloc[q - 1]["total"] == gdf.iloc[q]["total"]:
                            tie_detected = True
                            break

            if tie_detected:
                st.warning(T("tie_warning"))

            st.divider()
            
            # Разные кнопки для группового и плей-офф
            if is_group_stage:
                btn_label = "🚀 НАЧАТЬ ПЛЕЙ-ОФФ"
            else:
                btn_label = f"➡️ Перейти к {next_sd.display_name.get(lang, next_sd.code)}"
            
            if st.button(btn_label, type="primary", use_container_width=True):
                try:
                    advance_to_next_stage(tournament_id)
                    st.success(T("saved"))
                    st.rerun()
                except Exception as e:
                    st.error(str(e))
