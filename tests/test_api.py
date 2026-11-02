import time
import pytest
from fastapi.testclient import TestClient
from dashboard.app import create_app
from dashboard.domain import Controller


@pytest.fixture
def client(tmp_path):
    with TestClient(create_app(str(tmp_path/"test.sqlite"),demo=False,dashboard_token="ui-secret",device_token="device-secret")) as c:
        yield c


UI={"Authorization":"Bearer ui-secret"}
DEVICE={"Authorization":"Bearer device-secret"}


def telemetry():
    return dict(Controller().tick(0),source="esp32")


def test_telemetry_command_ack_history(client):
    assert client.get("/api/health").json()["status"]=="ok"
    assert client.get("/api/rooms").status_code==401
    assert client.post("/api/devices/classroom-101/telemetry",json=telemetry(),headers=UI).status_code==401
    assert client.post("/api/devices/classroom-101/telemetry",json=telemetry(),headers=DEVICE).json()=={"command":None}
    command=dict(mode="MANUAL",light1=True,fan=True,servo=70)
    r=client.post("/api/rooms/classroom-101/commands",json=command,headers=UI)
    assert r.status_code==200
    version=r.json()["command"]["version"]
    poll=client.post("/api/devices/classroom-101/telemetry",json=telemetry(),headers=DEVICE).json()
    assert poll["command"]["version"]==version and poll["command"]["light1"]
    data=dict(telemetry(),applied_version=version,mode="MANUAL",light1=True,fan=True,servo=70,power_w=80)
    assert client.post("/api/devices/classroom-101/telemetry",json=data,headers=DEVICE).status_code==200
    s=client.get("/api/rooms",headers=UI).json()[0]
    assert s["applied_version"]==s["command"]["version"] and s["online"]
    history=client.get("/api/rooms/classroom-101/history",headers=UI).json()
    assert len(history)==3 and history[-1]["power_w"]==80


def test_validation_and_identity(client):
    bad=dict(telemetry(),temperature=900)
    assert client.post("/api/devices/room/telemetry",json=bad,headers=DEVICE).status_code==422
    assert client.post("/api/devices/demo-101/telemetry",json=telemetry(),headers=DEVICE).status_code==409
    assert client.post("/api/devices/room/telemetry",json=telemetry(),headers=DEVICE).status_code==200
    assert client.post("/api/rooms/room/sensors",json=Controller().sensors,headers=UI).status_code==409
    assert client.post("/api/rooms/room/commands",json={"mode":"MANUAL","servo":181},headers=UI).status_code==422
    assert client.post("/api/rooms/room/commands",json={"mode":"MANUAL","light1":"false"},headers=UI).status_code==422


def test_simulation_controls_and_restart(tmp_path):
    db=str(tmp_path/"demo.sqlite")
    for iteration in range(2):
        with TestClient(create_app(db,demo=True,dashboard_token="",device_token="")) as client:
            sensors=dict(Controller().sensors,occupancy=True,light=10,air_quality=95)
            assert client.post("/api/rooms/demo-101/sensors",json=sensors).status_code==200
            s=client.get("/api/rooms").json()[0]
            assert s["light1"] and s["alarm"] and s["servo"]==180
            assert client.get("/").status_code==200
            assert client.get("/static/app.js").status_code==200
            assert len(client.get("/api/rooms/demo-101/history").json())>=iteration+1


def test_command_persists_across_restart(tmp_path):
    db=str(tmp_path/"persist.sqlite")
    with TestClient(create_app(db,demo=False,dashboard_token="",device_token="")) as client:
        client.post("/api/devices/room/telemetry",json=telemetry())
        r=client.post("/api/rooms/room/commands",json={"mode":"MANUAL","light1":True}).json()
    with TestClient(create_app(db,demo=False,dashboard_token="",device_token="")) as client:
        assert client.post("/api/devices/room/telemetry",json=telemetry()).json()["command"]==r["command"]


def test_public_startup_requires_distinct_credentials(monkeypatch,tmp_path):
    monkeypatch.setenv("PUBLIC_DEPLOYMENT","1")
    with pytest.raises(RuntimeError):
        create_app(str(tmp_path/"x"),dashboard_token="",device_token="")
    with pytest.raises(RuntimeError):
        create_app(str(tmp_path/"x"),dashboard_token="a"*32,device_token="a"*32)
