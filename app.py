import hmac
import json
import os
import subprocess
from enum import Enum
from hashlib import sha1

from flask import Flask
from flask import request
from json import JSONDecodeError
from pathlib import Path

app = Flask(__name__)

GITLAB_WEBHOOK_KEY = ''
BASE_DIR = app.root_path


@app.route('/deploy/', methods=["POST"])
def deploy():
    error = True
    http_status = 400
    detail = None
    command = None

    path_config = os.environ.get('CONFIG_PATH', Path(BASE_DIR) / 'webhook.json')
    header_signature = payload = None
    repository_type = RepositoryType.UNKNOWN

    # gitlab
    if 'X_GITLAB_TOKEN' in request.headers:
        repository_type = RepositoryType.GITLAB
        header_signature = request.headers.get('X_GITLAB_TOKEN', None)
        if header_signature is None:
            detail = "failure: no signature"
            http_status = 403
        elif not request.json:
            detail = 'failure: {}'.format('no payload data')
        else:
            payload = request.json
    elif 'X-Hub-Signature' in request.headers:
        repository_type = RepositoryType.GITHUB
        header_signature = request.headers.get('X-Hub-Signature', None)
        if header_signature is None:
            detail = "failure: no signature"
            http_status = 403
        elif not request.json:
            detail = 'failure: {}'.format('no payload data')
        else:
            payload = request.json

    if payload:
        repository_name = get_repository_name(payload, repository_type)
        branch_name = get_branch_name(payload)
        try:
            with open(path_config, encoding='utf8') as f:
                configs = json.loads(f.read())
            for c in configs:
                if repository_name == c.get('repository'):
                    if branch_name == c.get('branch'):
                        if validate_token(header_signature, c.get('token'), repository_type):
                            command = c.get('shell')
                            break
                        else:
                            detail = "failure: Wrong signature"
                            break
                    else:
                        detail = 'repository: {}, unknown branch: {}'.format(repository_name, branch_name)
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


class RepositoryType(Enum):
    UNKNOWN = 0
    GITLAB = 1
    GITHUB = 2


def get_repository_name(payload: dict, repository_type: RepositoryType) -> (str, None):
    if repository_type == RepositoryType.GITLAB:
        repository = payload.get('project')
        return repository.get('name')
    elif repository_type == RepositoryType.GITHUB:
        repository = payload.get('repository')
        return repository.get('name')
    else:
        return None


def get_branch_name(payload: dict) -> (str, None):
    if 'ref' in payload:
        return payload.get('ref').replace('refs/heads/', '')
    else:
        return None


def validate_token(header_signature: str, token: str, repository_type: RepositoryType) -> bool:
    encoding = 'utf-8'
    if repository_type == RepositoryType.GITLAB:
        return header_signature == token
    elif repository_type == RepositoryType.GITHUB:
        sha_name, signature = header_signature.split('=')
        if sha_name != 'sha1':
            return False
        mac = hmac.new(token.encode(encoding), msg=request.data, digestmod=sha1)
        if not hmac.compare_digest(mac.hexdigest().encode(encoding), signature.encode(encoding)):
            return False
        return True
    else:
        return False
