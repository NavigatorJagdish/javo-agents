"""Explicit external-only test setup; no upstream lifecycle scripts or owner data."""
import argparse
import hashlib
import io
import json
from pathlib import Path
import platform
import shutil
import subprocess
import tarfile
from urllib.request import Request, urlopen

from verification_runtime import ROOT, clean_environment


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--prefix',type=Path,required=True)
    args=parser.parse_args()
    prefix=args.prefix.resolve()
    if prefix.is_relative_to(ROOT):
        raise ValueError('External n8n must remain outside the checkout/distribution')
    prefix.mkdir(parents=True,exist_ok=True)
    source=(ROOT/'integrations/n8n-acceptance-package.json').read_bytes()
    package=prefix/'package.json'
    if package.exists() and package.read_bytes()!=source:
        raise ValueError('Existing external package configuration differs; retained for review')
    package.write_bytes(source)
    node=shutil.which('node')
    npm=shutil.which('npm.cmd' if platform.system()=='Windows' else 'npm')
    if not node or not npm:
        raise ValueError('Install the reviewed Node24 runtime explicitly first')
    npm_cli=Path(npm).parent/'node_modules/npm/bin/npm-cli.js' if platform.system()=='Windows' else Path(npm).resolve()
    if not npm_cli.is_file():
        raise ValueError('Reviewed npm JavaScript entry point is unavailable')
    npm_command=[node,str(npm_cli)]
    env=clean_environment()
    version=subprocess.check_output([node,'--version'],env=env,text=True).strip()
    if version!='v24.22.3':
        raise ValueError('This acceptance setup requires reviewed Node24.22.3')
    empty_config=prefix/'empty-user-npmrc'
    empty_config.write_text('',encoding='utf-8')
    # A conflicting peer graph belongs to unused upstream AI nodes. This test
    # loads seven core types only; no claim of compatibility for all n8n nodes.
    command=[*npm_command,'install','--legacy-peer-deps','--ignore-scripts','--no-audit','--no-fund',
             '--prefer-offline','--maxsockets=5','--fetch-retries=1','--fetch-timeout=30000',
             '--registry=https://registry.npmjs.org','--userconfig='+str(empty_config)]
    subprocess.run(command,cwd=prefix,env=env,check=True,timeout=900)
    installed=prefix/'node_modules/n8n'
    if json.loads((installed/'package.json').read_text(encoding='utf-8'))['version']!='2.48.7':
        raise ValueError('External n8n version changed')
    if 'Sustainable Use License' not in (installed/'LICENSE.md').read_text(encoding='utf-8'):
        raise ValueError('Review changed external license')
    sqlite=prefix/'node_modules/sqlite3'
    if json.loads((sqlite/'package.json').read_text(encoding='utf-8'))['version']!='5.1.7':
        raise ValueError('Review changed native SQLite dependency')
    target='win32' if platform.system()=='Windows' else 'linux' if platform.system()=='Linux' else None
    if not target or platform.machine().lower() not in {'amd64','x86_64'}:
        raise ValueError('Native acceptance currently supports Windows/Linux x64 only')
    name='sqlite3-v5.1.7-napi-v6-'+target+'-x64.tar.gz'
    api='https://api.github.com/repos/TryGhost/node-sqlite3/releases/tags/v5.1.7'
    with urlopen(Request(api,headers={'User-Agent':'Javo-external-acceptance'}),timeout=30) as response:
        release=json.load(response)
    asset=next(a for a in release['assets'] if a['name']==name)
    url='https://github.com/TryGhost/node-sqlite3/releases/download/v5.1.7/'+name
    if asset['browser_download_url']!=url or not 0<asset['size']<3*1024*1024:
        raise ValueError('Unexpected official native release asset')
    with urlopen(url,timeout=60) as response:
        data=response.read(asset['size']+1)
    digest=hashlib.sha256(data).hexdigest()
    if len(data)!=asset['size'] or (asset.get('digest') and asset['digest']!='sha256:'+digest):
        raise ValueError('Native archive differs from official release metadata')
    with tarfile.open(fileobj=io.BytesIO(data),mode='r:gz') as archive:
        members=archive.getmembers()
        if len(members)!=1 or not members[0].isfile() or members[0].name!='build/Release/node_sqlite3.node' or members[0].size>8*1024*1024:
            raise ValueError('Unexpected native archive member')
        content=archive.extractfile(members[0]).read()
    binary=sqlite/'build/Release/node_sqlite3.node'
    binary.parent.mkdir(parents=True,exist_ok=True)
    if binary.exists() and binary.read_bytes()!=content:
        raise ValueError('Existing native binding differs; retained for review')
    binary.write_bytes(content)
    subprocess.run([node,'-e',"require('sqlite3');console.log('EXTERNAL_SQLITE_IMPORT_OK')"],cwd=prefix,env=env,check=True,timeout=30)
    audit=subprocess.run([*npm_command,'audit','--json','--registry=https://registry.npmjs.org','--userconfig='+str(empty_config)],
                         cwd=prefix,env=env,capture_output=True,text=True,timeout=120)
    report=json.loads(audit.stdout)
    counts=report.get('metadata',{}).get('vulnerabilities')
    if not isinstance(counts,dict):
        raise ValueError('No completed external dependency audit')
    (prefix/'dependency-audit.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    (prefix/'native-provenance.json').write_text(json.dumps({'url':url,'sha256':digest,
        'vendor_digest_available':bool(asset.get('digest')),'scripts_executed':False,'bundled_with_javo':False},indent=2),encoding='utf-8')
    print('EXTERNAL_N8N_AUDIT_COUNTS '+json.dumps(counts),flush=True)
    if counts.get('critical',0):
        raise ValueError('Critical dependency findings remain; refuse engine acceptance')
    print('EXTERNAL_N8N_PREPARED_FOR_ISOLATED_ACCEPTANCE; remaining audit findings are not cleared',flush=True)


if __name__=='__main__':
    main()
