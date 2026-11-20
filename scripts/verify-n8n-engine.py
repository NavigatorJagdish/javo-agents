"""Actual external n8n import/execute against disposable Javo data and grants.

No installer, paid service, user profile, email or publication. The review driver
acts as the owner only for the exact synthetic workflow/input below.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import secrets
import socket
import subprocess
import sys
import tempfile
import time
from uuid import uuid4

from verification_runtime import ROOT, clean_environment, isolated_runtime


def free_port():
    with socket.socket() as sock:
        sock.bind(('127.0.0.1',0))
        return str(sock.getsockname()[1])


def stop(process):
    if process.poll() is None:
        if sys.platform == 'win32':
            subprocess.run([str(Path(os.environ.get('SystemRoot','C:/Windows'))/'System32/taskkill.exe'),
                '/PID',str(process.pid),'/T','/F'],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,timeout=15,check=False)
        else:
            process.terminate()
        process.wait(timeout=15)


def execution_result(output):
    decoder=json.JSONDecoder()
    for index,char in enumerate(output):
        if char!='{':
            continue
        try:
            value,_=decoder.raw_decode(output[index:])
        except ValueError:
            continue
        if isinstance(value,dict) and isinstance(value.get('data'),dict) and 'resultData' in value['data']:
            return value
    raise ValueError('No actual n8n execution result was returned')


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--node',type=Path,required=True)
    parser.add_argument('--n8n-root',type=Path,required=True,help='External npm prefix, outside the Javo checkout')
    args=parser.parse_args()
    external=args.n8n_root.resolve()
    if external.is_relative_to(ROOT):
        raise ValueError('n8n must remain an external installation')
    package=external/'node_modules/n8n'
    if json.loads((package/'package.json').read_text(encoding='utf-8'))['version']!='2.48.7':
        raise ValueError('Review a changed external n8n version before this acceptance check')
    if 'Sustainable Use License' not in (package/'LICENSE.md').read_text(encoding='utf-8'):
        raise ValueError('Review changed n8n license before execution')
    command=[str(args.node.resolve()),str(package/'bin/n8n')]
    with isolated_runtime() as (base,request), tempfile.TemporaryDirectory(prefix='javo-n8n-acceptance-') as folder:
        data=Path(folder)
        key=secrets.token_urlsafe(48)
        env=clean_environment()
        env['PATH']=str(args.node.resolve().parent)+os.pathsep+env.get('PATH','')
        env.update({'N8N_USER_FOLDER':str(data),'N8N_ENCRYPTION_KEY':key,'N8N_LISTEN_ADDRESS':'127.0.0.1',
            'N8N_HOST':'127.0.0.1','N8N_PORT':free_port(),'N8N_RUNNERS_BROKER_PORT':free_port(),
            'N8N_RUNNERS_MODE':'internal','N8N_RUNNERS_MAX_CONCURRENCY':'1','N8N_PYTHON_ENABLED':'false',
            'N8N_DIAGNOSTICS_ENABLED':'false','N8N_VERSION_NOTIFICATIONS_ENABLED':'false','N8N_TEMPLATES_ENABLED':'false',
            'N8N_COMMUNITY_PACKAGES_ENABLED':'false','N8N_PUBLIC_API_DISABLED':'true','N8N_BLOCK_ENV_ACCESS_IN_NODE':'true',
            'N8N_LICENSE_AUTO_RENEW_ENABLED':'false','N8N_LICENSE_SERVER_URL':'http://127.0.0.1:1',
            # The execute command writes even --rawOutput through logger.info.
            'N8N_LOG_LEVEL':'info','EXECUTIONS_TIMEOUT':'120',
            'NODES_INCLUDE':json.dumps(['n8n-nodes-base.'+name for name in ['manualTrigger','scheduleTrigger','code','httpRequest','wait','if','stopAndError']])})
        grant=request('/api/integrations/grants',{'client':'n8n','label':'Disposable actual n8n acceptance',
            'scopes':['read_status','read_workflows','propose_workflow','read_own_results'],'lifetime_hours':1})
        last=''
        def redact(text):
            return text.replace(grant['token'],'[redacted disposable client grant]').replace(key,'[redacted temporary n8n key]')
        def run_cli(*arguments):
            nonlocal last
            result=subprocess.run([*command,*arguments],env=env,cwd=data,capture_output=True,text=True,timeout=150)
            last=redact(result.stdout+result.stderr)
            if result.returncode:
                raise RuntimeError('External n8n command failed: '+arguments[0])
            return result.stdout
        try:
            version=run_cli('--version').strip()
            assert version.endswith('2.48.7'), 'Unexpected n8n engine version'
            first,end=str(uuid4()),str(uuid4())
            saved=request('/api/workflows/',{'name':'Actual n8n synthetic review acceptance','nodes':[
                {'id':first,'node_type':'trigger','label':'Start','is_entry_point':True},
                {'id':end,'node_type':'end','label':'End'}],
                'edges':[{'source_node_id':first,'target_node_id':end}]})
            request('/api/security/resume',{})
            credential=secrets.token_hex(8)
            credential_file=data/'disposable-credential.json'
            credential_file.write_text(json.dumps([{'id':credential,'name':'Disposable Javo scope','type':'httpHeaderAuth',
                'data':{'name':'Authorization','value':'Bearer '+grant['token']}}]),encoding='utf-8')
            run_cli('import:credentials','--input='+str(credential_file))
            credential_file.unlink()
            workflow=json.loads((ROOT/'integrations/n8n-reviewed-drafting.json').read_text(encoding='utf-8'))
            workflow['id']=secrets.token_hex(8)
            workflow['versionId']=str(uuid4())
            brief='Synthetic known facts for actual n8n protocol acceptance.'
            for node in workflow['nodes']:
                if node['name']=='Set brief':
                    node['parameters']['jsCode']='return [{json:'+json.dumps({'base_url':base,'workflow_id':saved['id'],'brief':brief,'max_polls':30})+'}];'
                if node['type']=='n8n-nodes-base.httpRequest':
                    node['credentials']={'httpHeaderAuth':{'id':credential,'name':'Disposable Javo scope'}}
            workflow_file=data/'inactive-workflow.json'
            workflow_file.write_text(json.dumps(workflow),encoding='utf-8')
            run_cli('import:workflow','--input='+str(workflow_file))
            seen=set()
            for choice in ['approve','reject']:
                log_path=data/('execution-'+choice+'.log')
                with log_path.open('w',encoding='utf-8') as log:
                    process=subprocess.Popen([*command,'execute','--id='+workflow['id'],'--rawOutput'],env=env,cwd=data,
                        stdout=log,stderr=log,**({'creationflags':0x08000000} if sys.platform=='win32' else {}))
                    decided=None
                    observed=None
                    started=time.monotonic()
                    try:
                        while process.poll() is None and time.monotonic()-started<240:
                            for proposal in request('/api/integrations/proposals'):
                                if proposal['id'] in seen or proposal['status']!='pending':
                                    continue
                                assert proposal['grant_id']==grant['id']
                                assert proposal['payload']=={'workflow_id':saved['id'],'expected_revision':saved['revision'],
                                    'fingerprint':saved['fingerprint'],'trigger_data':{'brief':brief}}
                                if observed is None:
                                    observed=time.monotonic()
                                # Ensure a pending status/eligible wait branch actually runs.
                                if time.monotonic()-observed<13:
                                    continue
                                decided=request('/api/integrations/proposals/'+proposal['id']+'/review',
                                    {'expected_revision':proposal['revision'],'decision':choice})
                                seen.add(proposal['id'])
                            time.sleep(0.25)
                        if process.poll() is None:
                            raise TimeoutError('Actual n8n execution exceeded acceptance deadline')
                    finally:
                        stop(process)
                last=redact(log_path.read_text(encoding='utf-8',errors='replace'))
                actual=execution_result(last)
                run_data=actual['data']['resultData']['runData']
                assert decided is not None, 'n8n never submitted a reviewable proposal'
                if choice=='approve':
                    report=run_data['Report verified local result'][-1]['data']['main'][0][0]['json']
                    assert report['status']=='completed' and report['execution_id']==decided['execution_id']
                    receipt=request('/api/workflows/executions/'+report['execution_id'])
                    assert receipt['execution_verified'] and receipt['status']=='completed'
                    assert 'Still eligible to wait?' in run_data
                    print('REAL_N8N_17_NODE_OWNER_REVIEW_RESULT_OK',flush=True)
                else:
                    assert decided['status']=='rejected' and decided['execution_id'] is None
                    assert 'Stop without replay' in run_data and 'Report verified local result' not in run_data
                    print('REAL_N8N_REJECTION_STOPS_WITHOUT_DISPATCH_OK',flush=True)
            assert len(request('/api/workflows/'+saved['id']+'/executions'))==1
            print(json.dumps({'external_n8n':'2.48.7','template_nodes':len(workflow['nodes']),
                'loaded_node_types':7,'owner_profile_used':False,'cloud_model_used':False,'live_action':False}),flush=True)
        except BaseException:
            print(last[-7000:],file=sys.stderr)
            raise
        finally:
            request('/api/integrations/grants/'+grant['id']+'/revoke',{})


if __name__=='__main__':
    main()
