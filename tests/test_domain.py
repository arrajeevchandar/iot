import pytest
from dashboard.domain import Controller, Classifier


@pytest.mark.parametrize("changes,expected", [
    ({"occupancy":False}, {"light1":False,"light2":False,"fan":False}),
    ({"occupancy":True,"light":10}, {"light1":True,"light2":True}),
    ({"occupancy":True,"temperature":35}, {"fan":True}),
    ({"air_quality":70}, {"servo":90,"alert":"WARNING"}),
    ({"air_quality":95}, {"servo":180,"alarm":True,"alert":"CRITICAL"}),
    ({"temperature":46}, {"servo":180,"alarm":True}),
    ({"sensor_valid":False}, {"servo":180,"ml_class":"UNAVAILABLE","alert":"WARNING"}),
])
def test_scenarios(changes, expected):
    c=Controller()
    c.sensors.update(changes)
    result=c.tick(0)
    for k,v in expected.items():
        assert result[k]==v


def test_manual_emergency_and_return_auto():
    c=Controller()
    c.command(dict(mode="MANUAL",light1=True,light2=False,fan=True,servo=20,version=1),0)
    assert c.tick(1)["light1"]
    assert c.tick(2)["servo"]==20
    c.sensors["air_quality"]=95
    assert c.tick(3)["servo"]==180 and c.tick(4)["alarm"]
    c.sensors["air_quality"]=20
    assert not c.tick(5)["alarm"]
    c.mode="AUTO"
    assert c.tick(6)["power_w"]==0


def test_elapsed_energy_and_mode_accounting():
    c=Controller()
    c.sensors.update(occupancy=True,light=10,temperature=30)
    c.tick(0)
    s=c.tick(3600)
    assert s["energy_wh"]==100 and s["auto_wh"]==100 and s["baseline_wh"]==100
    c.command(dict(mode="MANUAL",light1=True,light2=False,fan=False,servo=0,version=1),3600)
    c.tick(3600)
    s=c.tick(7200)
    assert s["energy_wh"]==120 and s["auto_wh"]==100 and s["baseline_wh"]==200


@pytest.mark.parametrize("features,power,label", [
    ([24,50,50,20,False],0,"EMPTY"),
    ([24,50,50,20,True],0,"OCCUPIED_NORMAL"),
    ([24,50,80,20,False],100,"HIGH_ENERGY_USAGE"),
    ([35,50,50,70,True],60,"POOR_ENVIRONMENT"),
    ([48,50,50,95,True],60,"ABNORMAL_CONDITION"),
])
def test_trained_model(features,power,label):
    sensors=dict(zip(["temperature","humidity","light","air_quality","occupancy"],features))
    predicted,confidence=Classifier().predict(sensors,power)
    assert predicted==label
    assert 0<=confidence<=1


def test_missing_ml_keeps_rules(tmp_path):
    c=Controller(classifier=Classifier(tmp_path/"absent.npz"))
    c.sensors.update(occupancy=True,light=10,air_quality=95)
    s=c.tick(0)
    assert s["ml_class"]=="UNAVAILABLE" and s["light1"] and s["alarm"]
