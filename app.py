import json
import subprocess
from flask import Flask
from flask import request
from json import JSONDecodeError
from pathlib import Path

app = Flask(__name__)

GITLAB_WEBHOOK_KEY = ''
BASE_DIR = app.root_path


@app.route('/deploy', methods=["POST"])
def deploy():
    error = True
    http_status = 400
    detail = None
    command = None
    path_config = Path(BASE_DIR) / 'webhook.json'


    # gitlab
    header_signature = request.headers.get('X_GITLAB_TOKEN')
    if header_signature is None:
        detail = "failure: no signature"
        http_status = 403
    elif not request.json:
        detail = 'failure: {}'.format('no payload data')
    else:
        data = request.json
        repository = data.get('project')
        repository_name = repository.get('name')
        ref = data.get('ref')
        try:
            with open(path_config, encoding='utf8') as f:
                configs = json.loads(f.read())
            for c in configs:
                if repository_name == c.get('repository'):
                    if ref and ref.endswith(c.get('branch')):
                        if header_signature == c.get('token'):
                            command = c.get('shell')
                            break
                        else:
                            detail = "failure: Wrong signature"
                            break
                    else:
                        detail = 'repository: {}, unknown branch: {}'.format(repository_name, ref)
        except FileNotFoundError:
            # 設定ファイルが見つからない場合
            detail = f'{path_config} not exists'
        except JSONDecodeError:
            # 設定ファイルの内容不正の場合
            detail = 'webhook.json format error'

    if command:
        ret_code = subprocess.call(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if ret_code == 0:
            error = False
            http_status = 200
            detail = 'success'
        else:
            detail = 'failure: {}'.format(command)

    return {
        'error': error,
        'detail': detail,
        'command': command
    }, http_status
