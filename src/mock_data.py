"""
Mock data for FIT CRM Dashboard Demo
Simulovane data pre demonstraciu dashboardu
"""
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from typing import List, Optional
import random


@dataclass
class CheckIn:
    """Weekly check-in data"""
    date: datetime
    weight_kg: float
    mood: str  # excellent, good, ok, bad
    adherence_percent: int  # 0-100
    workouts_completed: int
    workouts_planned: int
    notes: str = ""


@dataclass
class Exercise:
    """Exercise progress tracking"""
    name: str
    initial_weight_kg: float
    current_weight_kg: float
    initial_reps: int
    current_reps: int


@dataclass
class ClientData:
    """Full client data for dashboard"""
    id: str
    name: str
    email: str
    age: int
    gender: str

    # Physical stats
    height_cm: float
    initial_weight_kg: float
    current_weight_kg: float
    goal_weight_kg: float

    # Status
    status: str  # active, stagnating, problem, inactive
    goal: str
    experience_level: str

    # Dates
    start_date: datetime
    last_checkin: datetime

    # Progress data
    checkins: List[CheckIn] = field(default_factory=list)
    exercises: List[Exercise] = field(default_factory=list)

    @property
    def weight_change(self) -> float:
        """Total weight change since start"""
        return self.current_weight_kg - self.initial_weight_kg

    @property
    def progress_percent(self) -> float:
        """Progress towards goal (0-100)"""
        total_to_lose = self.initial_weight_kg - self.goal_weight_kg
        if total_to_lose == 0:
            return 100
        lost = self.initial_weight_kg - self.current_weight_kg
        return min(100, max(0, (lost / total_to_lose) * 100))

    @property
    def days_since_checkin(self) -> int:
        """Days since last check-in"""
        return (datetime.now() - self.last_checkin).days

    @property
    def bmi(self) -> float:
        """Current BMI"""
        height_m = self.height_cm / 100
        return self.current_weight_kg / (height_m ** 2)

    @property
    def weekly_avg_loss(self) -> float:
        """Average weekly weight change"""
        weeks = max(1, (datetime.now() - self.start_date).days / 7)
        return self.weight_change / weeks


def generate_checkins(
    initial_weight: float,
    current_weight: float,
    weeks: int,
    trend: str = "losing"  # losing, gaining, stagnating
) -> List[CheckIn]:
    """Generate realistic check-in history"""
    checkins = []
    weight = initial_weight

    weight_diff = current_weight - initial_weight
    weekly_change = weight_diff / max(1, weeks)

    for week in range(weeks):
        date = datetime.now() - timedelta(weeks=weeks-week)

        # Add some randomness
        variation = random.uniform(-0.3, 0.3)
        weight += weekly_change + variation

        mood = random.choice(["excellent", "good", "good", "ok", "ok"])
        if trend == "stagnating":
            mood = random.choice(["ok", "ok", "bad"])

        adherence = random.randint(70, 100)
        if trend == "problem":
            adherence = random.randint(40, 70)

        workouts_planned = 3
        workouts_completed = min(workouts_planned, random.randint(2, 4))
        if trend == "problem":
            workouts_completed = random.randint(0, 2)

        checkins.append(CheckIn(
            date=date,
            weight_kg=round(weight, 1),
            mood=mood,
            adherence_percent=adherence,
            workouts_completed=workouts_completed,
            workouts_planned=workouts_planned,
            notes=""
        ))

    return checkins


def generate_exercises(experience: str, trend: str = "improving") -> List[Exercise]:
    """Generate exercise progress data"""

    base_exercises = [
        ("Drep (Squat)", 40, 60, 8, 12),
        ("Bench Press", 30, 45, 8, 10),
        ("Mŕtvy ťah (Deadlift)", 50, 80, 6, 8),
        ("Tlaky na ramená", 15, 22, 10, 12),
        ("Veslovanie", 25, 35, 10, 12),
        ("Bicepsový zdvih", 8, 12, 10, 12),
    ]

    exercises = []
    for name, init_w, curr_w, init_r, curr_r in base_exercises:
        if experience == "beginner":
            init_w *= 0.5
            curr_w *= 0.6
        elif experience == "advanced":
            init_w *= 1.3
            curr_w *= 1.4

        if trend == "stagnating":
            curr_w = init_w * 1.05
            curr_r = init_r

        exercises.append(Exercise(
            name=name,
            initial_weight_kg=round(init_w, 1),
            current_weight_kg=round(curr_w, 1),
            initial_reps=init_r,
            current_reps=curr_r
        ))

    return exercises


def get_mock_clients() -> List[ClientData]:
    """Generate mock client data for demo"""

    clients = [
        # Active - good progress
        ClientData(
            id="c1",
            name="Anna Nováková",
            email="anna.novakova@example.com",
            age=32,
            gender="female",
            height_cm=165,
            initial_weight_kg=75.0,
            current_weight_kg=72.0,
            goal_weight_kg=65.0,
            status="active",
            goal="Schudnúť 10kg",
            experience_level="beginner",
            start_date=datetime.now() - timedelta(weeks=4),
            last_checkin=datetime.now() - timedelta(days=2),
            checkins=generate_checkins(75.0, 72.0, 4, "losing"),
            exercises=generate_exercises("beginner", "improving")
        ),

        # Active - excellent progress
        ClientData(
            id="c2",
            name="Peter Horvát",
            email="peter.horvat@example.com",
            age=28,
            gender="male",
            height_cm=182,
            initial_weight_kg=78.0,
            current_weight_kg=82.0,
            goal_weight_kg=85.0,
            status="active",
            goal="Nabrať svalovú hmotu",
            experience_level="intermediate",
            start_date=datetime.now() - timedelta(weeks=6),
            last_checkin=datetime.now() - timedelta(days=1),
            checkins=generate_checkins(78.0, 82.0, 6, "gaining"),
            exercises=generate_exercises("intermediate", "improving")
        ),

        # Stagnating
        ClientData(
            id="c3",
            name="Mária Kováčová",
            email="maria.kovacova@example.com",
            age=45,
            gender="female",
            height_cm=160,
            initial_weight_kg=88.0,
            current_weight_kg=87.0,
            goal_weight_kg=72.0,
            status="stagnating",
            goal="Schudnúť 15kg",
            experience_level="beginner",
            start_date=datetime.now() - timedelta(weeks=8),
            last_checkin=datetime.now() - timedelta(days=14),
            checkins=generate_checkins(88.0, 87.0, 8, "stagnating"),
            exercises=generate_exercises("beginner", "stagnating")
        ),

        # Problem - needs attention
        ClientData(
            id="c4",
            name="Tomáš Szabó",
            email="tomas.szabo@example.com",
            age=35,
            gender="male",
            height_cm=175,
            initial_weight_kg=95.0,
            current_weight_kg=96.5,
            goal_weight_kg=82.0,
            status="problem",
            goal="Schudnúť a zlepšiť kondíciu",
            experience_level="beginner",
            start_date=datetime.now() - timedelta(weeks=5),
            last_checkin=datetime.now() - timedelta(days=21),
            checkins=generate_checkins(95.0, 96.5, 5, "problem"),
            exercises=generate_exercises("beginner", "stagnating")
        ),

        # Active - good progress
        ClientData(
            id="c5",
            name="Lucia Demeterová",
            email="lucia.demeterova@example.com",
            age=26,
            gender="female",
            height_cm=170,
            initial_weight_kg=68.0,
            current_weight_kg=65.5,
            goal_weight_kg=62.0,
            status="active",
            goal="Spevniť postavu",
            experience_level="intermediate",
            start_date=datetime.now() - timedelta(weeks=6),
            last_checkin=datetime.now() - timedelta(days=3),
            checkins=generate_checkins(68.0, 65.5, 6, "losing"),
            exercises=generate_exercises("intermediate", "improving")
        ),

        # Active - new client
        ClientData(
            id="c6",
            name="Martin Kučera",
            email="martin.kucera@example.com",
            age=30,
            gender="male",
            height_cm=180,
            initial_weight_kg=92.0,
            current_weight_kg=90.5,
            goal_weight_kg=85.0,
            status="active",
            goal="Schudnúť tuk, nabrať svaly",
            experience_level="beginner",
            start_date=datetime.now() - timedelta(weeks=2),
            last_checkin=datetime.now() - timedelta(days=1),
            checkins=generate_checkins(92.0, 90.5, 2, "losing"),
            exercises=generate_exercises("beginner", "improving")
        ),
    ]

    return clients


def get_dashboard_stats(clients: List[ClientData]) -> dict:
    """Calculate dashboard statistics"""

    active = [c for c in clients if c.status in ["active", "stagnating"]]
    new_this_week = [c for c in clients if (datetime.now() - c.start_date).days <= 7]
    problem_clients = [c for c in clients if c.status == "problem" or c.days_since_checkin > 14]

    # Calculate retention (mock)
    retention = 95 - len([c for c in clients if c.status == "problem"]) * 5

    # Calculate MRR (mock - €30 per active client)
    mrr = len(active) * 30

    # Progress distribution
    progressing = len([c for c in active if c.weekly_avg_loss < -0.3 or (c.goal_weight_kg > c.initial_weight_kg and c.weekly_avg_loss > 0.2)])
    stagnating = len([c for c in active if abs(c.weekly_avg_loss) < 0.3])
    regressing = len([c for c in active if (c.goal_weight_kg < c.initial_weight_kg and c.weekly_avg_loss > 0) or (c.goal_weight_kg > c.initial_weight_kg and c.weekly_avg_loss < 0)])

    return {
        "total_clients": len(clients),
        "active_clients": len(active),
        "new_this_week": len(new_this_week),
        "retention_percent": retention,
        "mrr_eur": mrr,
        "problem_clients": problem_clients,
        "progressing": progressing,
        "stagnating": stagnating,
        "regressing": regressing,
        "avg_adherence": sum(c.checkins[-1].adherence_percent if c.checkins else 0 for c in active) / max(1, len(active))
    }
