import asyncio
from contextlib import asynccontextmanager, suppress
import json
import os
from pathlib import Path
import re
import secrets
import sqlite3
import time
from typing import Literal
from fastapi import FastAPI, HTTPException, Request, Depends
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, ConfigDict, Field, StrictBool
from .domain import Controller

ROOT = Path(__file__).resolve().parent


class Sensors(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)
    temperature: float = Field(ge=-40, le=80)
    humidity: float = Field(ge=0, le=100)
    light: float = Field(ge=0, le=100)
    air_quality: float = Field(ge=0, le=100)
    occupancy: StrictBool
    sensor_valid: StrictBool = True


class Telemetry(Sensors):
    source: Literal["esp32", "simulator"] = "esp32"
    mode: Literal["AUTO", "MANUAL"]
    light1: StrictBool
    light2: StrictBool
    fan: StrictBool
    servo: int = Field(ge=0, le=180, strict=True)
    alarm: StrictBool
    power_w: float = Field(ge=0, le=1000)
    energy_wh: float = Field(ge=0)
    auto_wh: float = Field(ge=0)
    baseline_wh: float = Field(ge=0)
    ml_class: Literal["EMPTY", "OCCUPIED_NORMAL", "HIGH_ENERGY_USAGE", "POOR_ENVIRONMENT", "ABNORMAL_CONDITION", "UNAVAILABLE"]
    confidence: float = Field(ge=0, le=1)
    alert: Literal["INFO", "WARNING", "CRITICAL"]
    applied_version: int = Field(ge=0, strict=True)


class Command(BaseModel):
    model_config = ConfigDict(extra="forbid")
    mode: Literal["AUTO", "MANUAL"]
    light1: StrictBool = False
    light2: StrictBool = False
    fan: StrictBool = False
    servo: int = Field(default=0, ge=0, le=180, strict=True)
    reset_alarm: StrictBool = False


def create_app(db_path=None, demo=None, dashboard_token=None, device_token=None):
    db_path = db_path or os.getenv("DATABASE_PATH", "runtime/classrooms.sqlite3")
    demo = os.getenv("SIMULATOR_ENABLED", "1") == "1" if demo is None else demo
    ui_token = os.getenv("DASHBOARD_TOKEN", "") if dashboard_token is None else dashboard_token
    node_token = os.getenv("DEVICE_TOKEN", "") if device_token is None else device_token
    if os.getenv("PUBLIC_DEPLOYMENT", "0") == "1" and (len(ui_token) < 32 or len(node_token) < 32 or ui_token == node_token):
        raise RuntimeError("Public deployment requires distinct random DASHBOARD_TOKEN and DEVICE_TOKEN (32+ characters).")
    controllers = {"demo-101": Controller()} if demo else {}

    def auth(expected):
        async def check(request: Request):
            if expected:
                header = request.headers.get("authorization", "")
                if not secrets.compare_digest(header, "Bearer " + expected):
                    raise HTTPException(401, "Access token required")
            elif request.client is None or request.client.host not in {"127.0.0.1", "::1", "testclient"}:
                raise HTTPException(403, "Unconfigured server permits loopback clients only")
        return check

    ui_auth, device_auth = auth(ui_token), auth(node_token)

    def validate_id(room):
        if not re.fullmatch(r"[a-zA-Z0-9][a-zA-Z0-9_-]{0,47}", room):
            raise HTTPException(422, "Invalid classroom ID")

    def store(room, data):
        validate_id(room)
        db = app.state.db
        db.execute("INSERT INTO telemetry(room,at,payload) VALUES(?,?,?)", (room, time.time(), json.dumps(data)))
        # Bounded retained history, including across restarts.
        db.execute("DELETE FROM telemetry WHERE room=? AND id NOT IN (SELECT id FROM telemetry WHERE room=? ORDER BY id DESC LIMIT 1000)", (room, room))
        db.commit()

    def desired(room):
        row = app.state.db.execute("SELECT payload FROM commands WHERE room=?", (room,)).fetchone()
        return json.loads(row[0]) if row else None

    async def simulate():
        while True:
            for room, controller in controllers.items():
                cmd = desired(room)
                if cmd and cmd["version"] > controller.version:
                    controller.command(cmd, time.monotonic())
                store(room, controller.tick(time.monotonic()))
            await asyncio.sleep(2)

    @asynccontextmanager
    async def lifespan(app):
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        app.state.db = sqlite3.connect(db_path, check_same_thread=False)
        app.state.db.execute("PRAGMA journal_mode=WAL")
        app.state.db.executescript("CREATE TABLE IF NOT EXISTS telemetry(id INTEGER PRIMARY KEY,room TEXT,at REAL,payload TEXT); CREATE INDEX IF NOT EXISTS room_history ON telemetry(room,id); CREATE TABLE IF NOT EXISTS commands(room TEXT PRIMARY KEY,payload TEXT);")
        # Restore simulation counters; downtime is not counted as energy use.
        for room, controller in controllers.items():
            previous = app.state.db.execute("SELECT payload FROM telemetry WHERE room=? ORDER BY id DESC LIMIT 1", (room,)).fetchone()
            if previous:
                p = json.loads(previous[0])
                controller.energy, controller.auto, controller.baseline = p["energy_wh"], p["auto_wh"], p["baseline_wh"]
                controller.sensors = {k: p[k] for k in controller.sensors}
        task = asyncio.create_task(simulate()) if demo else None
        yield
        if task:
            task.cancel()
            with suppress(asyncio.CancelledError):
                await task
        app.state.db.close()

    app = FastAPI(title="Smart Campus Classroom API", lifespan=lifespan, docs_url=None, redoc_url=None)
    app.mount("/static", StaticFiles(directory=ROOT / "static"), name="static")

    @app.get("/")
    async def index():
        return FileResponse(ROOT / "static/index.html")

    @app.get("/api/health")
    async def health():
        app.state.db.execute("SELECT 1").fetchone()
        return {"status": "ok", "simulator": demo}

    @app.get("/api/rooms", dependencies=[Depends(ui_auth)])
    async def rooms():
        rows = app.state.db.execute("SELECT room,at,payload FROM telemetry WHERE id IN (SELECT MAX(id) FROM telemetry GROUP BY room) ORDER BY room").fetchall()
        return [dict(json.loads(p), id=room, received_at=at, online=time.time()-at<12, command=desired(room)) for room, at, p in rows]

    @app.get("/api/rooms/{room}/history", dependencies=[Depends(ui_auth)])
    async def history(room: str):
        validate_id(room)
        rows = app.state.db.execute("SELECT at,payload FROM telemetry WHERE room=? ORDER BY id DESC LIMIT 120", (room,)).fetchall()
        return [dict(json.loads(p), at=at) for at, p in reversed(rows)]

    @app.post("/api/rooms/{room}/commands", dependencies=[Depends(ui_auth)])
    async def command(room: str, command: Command):
        validate_id(room)
        if not app.state.db.execute("SELECT 1 FROM telemetry WHERE room=? LIMIT 1", (room,)).fetchone():
            raise HTTPException(404, "Classroom has not connected")
        # Wall-clock microseconds survive device reboot; persisted prior versions handle clock rollback.
        old = desired(room)
        version = max(time.time_ns()//1000, (old["version"]+1) if old else 1)
        data = dict(command.model_dump(), version=version)
        app.state.db.execute("INSERT OR REPLACE INTO commands VALUES(?,?)", (room, json.dumps(data)))
        app.state.db.commit()
        return {"command": data, "status": "pending"}

    @app.post("/api/rooms/{room}/sensors", dependencies=[Depends(ui_auth)])
    async def sensors(room: str, sensors: Sensors):
        if room not in controllers:
            raise HTTPException(409, "Change real ESP32 sensors in Wokwi")
        controller = controllers[room]
        controller.integrate(time.monotonic())
        controller.sensors = sensors.model_dump()
        store(room, controller.tick(time.monotonic()))
        return {"status": "applied"}

    @app.post("/api/devices/{room}/telemetry", dependencies=[Depends(device_auth)])
    async def telemetry(room: str, telemetry: Telemetry):
        validate_id(room)
        if room.startswith("demo-") or telemetry.source != "esp32":
            raise HTTPException(409, "Reserved simulator identity")
        store(room, telemetry.model_dump())
        return {"command": desired(room)}

    return app


app = create_app()
