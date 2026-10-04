import time
from fastapi.testclient import TestClient
from work2030.api import create_app


def wait_idle(client, sid):
    end = time.monotonic() + 30
    while time.monotonic() < end:
        g = client.get(f"/api/sessions/{sid}").json()
        if not g["active"]:
            return g
        time.sleep(.05)
    raise AssertionError("Mission timed out")


def test_api_full_mission_refusal_approval_pause_reset_export(store, monkeypatch):
    monkeypatch.setenv("ANIMATOR_TOKEN", "test-secret")
    headers = {"Authorization": "Bearer test-secret"}
    with TestClient(create_app(store)) as c:
        groups = c.get('/api/sessions').json()
        assert len(groups) == 5
        sid = groups[0]["id"]
        base = f"/api/sessions/{sid}"
        assert c.get('/api/admin/sessions').status_code == 401
        assert c.get('/api/health').json()['status'] == 'ok'
        c.post(base+'/actions', json={"action":"context","data":{"id":"m-access"}}).raise_for_status()
        c.post(base+'/mission', json={"goal":"Préparer HORIZON","provider":"demo"}).raise_for_status()
        p = wait_idle(c,sid)['state']['proposal']
        assert p
        c.post(base+'/decision',json={'proposal_id':p['id'],'accept':False}).raise_for_status()
        assert c.get(base).json()['state']['documents'] == []
        c.post(base+'/mission',json={'goal':'Préparer HORIZON'}).raise_for_status()
        p = wait_idle(c,sid)['state']['proposal']
        c.post(base+'/decision',json={'proposal_id':p['id'],'accept':True}).raise_for_status()
        g=wait_idle(c,sid)
        assert g['state']['proposal']['status']=='completed'
        exported=c.get(base+'/export')
        assert 'decision.approved' in exported.text
        assert 'Plan' in exported.text and 'HORIZON' in exported.text
        c.post(f'/api/admin/{sid}/control',headers=headers,json={'action':'pause','data':{'paused':True}}).raise_for_status()
        assert c.post(base+'/actions',json={'action':'roles'}).status_code==409
        c.post(f'/api/admin/{sid}/control',headers=headers,json={'action':'reset'}).raise_for_status()
        assert c.get(base).json()['state']['documents']==[]
        c.post('/api/admin/all/control',headers=headers,json={'action':'reset'}).raise_for_status()
        assert len(c.get('/api/admin/sessions',headers=headers).json())==5


def test_missing_memory_prevents_approval(store):
    with TestClient(create_app(store)) as c:
        sid=c.get('/api/sessions').json()[0]['id']; base=f'/api/sessions/{sid}'
        c.post(base+'/mission',json={'goal':'Préparer HORIZON'}).raise_for_status()
        p=wait_idle(c,sid)['state']['proposal']
        assert p['warnings']
        assert c.post(base+'/decision',json={'proposal_id':p['id'],'accept':True}).status_code==409
        assert c.get(base).json()['state']['documents']==[]


def test_restart_restores_interrupted_execution_even_when_paused(store, services):
    from work2030.services import fingerprint
    sid = store.create('Interrupted')['id']
    services.interact(sid, 'context', {'id': 'm-access'})
    plan = {'space_id':'pavillon', 'resource_ids':['led','audio','table-a','table-b','quiet','signs'], 'occupancy':{'scene':70,'atelier':38,'calme':12}}
    p = services.workspace(sid, {'operation':'preview','plan':plan})
    def approve(s):
        s['proposal']['status']='executing'
    store.mutate(sid,'decision.approved',approve)
    services.workspace(sid, {'operation':'apply','proposal_id':p['id']})
    store.mutate(sid,'facilitator.pause',lambda s:s.update(paused=True),snapshot=False)
    with TestClient(create_app(store)) as c:
        state=c.get('/api/sessions/'+sid).json()['state']
        assert not state['assignments'] and state['paused'] and state['proposal'] is None


def test_invalid_action_is_explained_and_printable_cards_served(store):
    with TestClient(create_app(store)) as c:
        sid=c.get('/api/sessions').json()[0]['id']
        result=c.post(f'/api/sessions/{sid}/actions',json={'action':'assign','data':{}})
        assert result.status_code==409 and 'Paramètres' in result.json()['detail']
        cards=c.get('/cartes')
        assert cards.status_code==200 and cards.text.count('<article>')==15
