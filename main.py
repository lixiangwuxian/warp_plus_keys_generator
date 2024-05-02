import json
import logging
import random
import sys
from typing import Tuple

import httpx
import time
import os

from httpx import Client

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s ' '- %(message)s',
    stream=sys.stdout,
)

keys=[]
def read_keys():
    pre_keys_file_name='keys.json'
    try:
        with open(pre_keys_file_name,'r')as file:
            data=file.read()
            global keys
            keys=json.loads(data)
            print(keys)
    except Exception as e:
        logging.error(f'获取初始key失败: {e}')

def save_key_to_file(key_info: dict) -> None:
    file_name = 'GeneratedKeys.json'
    try:
        if not os.path.exists(file_name):
            with open(file_name, 'w') as file:
                json.dump([], file)

        with open(file_name, 'r+') as file:
            data = json.load(file)
            data.append(key_info)
            file.seek(0)
            json.dump(data, file, indent=4)
        logging.info(f"成功保存了key: {key_info['license']}")
    except Exception as e:
        logging.error(f'文件保存失败: {e}')


def register_user(client: Client) -> Tuple[int, str, str]:
    response = client.post('/reg')
    user_info = response.json()
    logging.info('成功注册了用户')
    return user_info['id'], user_info['account']['license'], user_info['token']


def register_referral_user(client: Client) -> Tuple[int, str]:
    response = client.post('/reg')
    referral_info = response.json()
    logging.info('成功注册了被邀请的用户')
    return referral_info['id'], referral_info['token']


def add_referral_and_delete(
        client: Client,
        user_id: int,
        user_token: str,
        referral_id: int,
        referral_token: str,
) -> None:
    client.patch(
        f'/reg/{user_id}',
        headers={
            'Authorization': f'Bearer {user_token}',
            'Content-Type': 'application/json; charset=UTF-8',
        },
        json={'referrer': f'{referral_id}'},
    )
    logging.info('添加了邀请。')
    client.delete(
        f'/reg/{referral_id}',
        headers={'Authorization': f'Bearer {referral_token}'},
    )
    logging.info('删除了新建的邀请账户')


def swap_license_keys(
        client: Client, user_id: int, initial_license: str, user_token: str
) -> None:
    selected_key = random.choice(keys)
    client.put(
        f'/reg/{user_id}/account',
        headers={
            'Authorization': f'Bearer {user_token}',
            'Content-Type': 'application/json; charset=UTF-8',
        },
        json={'license': f'{selected_key}'},
    )
    client.put(
        f'/reg/{user_id}/account',
        headers={
            'Authorization': f'Bearer {user_token}',
            'Content-Type': 'application/json; charset=UTF-8',
        },
        json={'license': f'{initial_license}'},
    )
    logging.info('License key已被应用并恢复')


def get_updated_user_info(
        client: Client, user_id: int, user_token: str
) -> Tuple[int, str, bool, int]:
    response = client.get(
        f'/reg/{user_id}/account',
        headers={'Authorization': f'Bearer {user_token}'},
    )
    user_info = response.json()
    logging.info(f'获取到了更新后的用户信息')
    return (
        user_info['referral_count'],
        user_info['license'],
        user_info['warp_plus'],
        user_info['quota'],
    )


def delete_user(client: Client, user_id: int, user_token: str) -> None:
    client.delete(
        f'/reg/{user_id}', headers={'Authorization': f'Bearer {user_token}'}
    )
    logging.info('获取流量后删除了用户')


def generate_and_save_key(client: Client,GBs:int) -> None:
    try:
        user_id, initial_license, user_token = register_user(client)
        (
            _,
            final_license,
            _,
            _,
        ) = get_updated_user_info(client, user_id, user_token)
        logging.info(f'要进行刷流的key: {final_license}')
        i=0
        while i<GBs:
            try:
                referral_id, referral_token = register_referral_user(client)
                add_referral_and_delete(
                    client, user_id, user_token, referral_id, referral_token
                )
                i+=1
            except Exception as error:
                logging.error(f'邀请时出错，信息: {error}')
                time.sleep(1)
                continue                
        swap_license_keys(client, user_id, initial_license, user_token)
        
        (
            referral_count,
            final_license,
            warp_plus,
            quota,
        ) = get_updated_user_info(client, user_id, user_token)
        delete_user(client, user_id, user_token)

        if warp_plus and quota != 0:
            save_key_to_file({'Quota': quota, 'license': final_license})

    except Exception as error:
        logging.error(f'出现错误: {error}')
        logging.info(f'已获取的key: {final_license}')


def create_http_client() -> Client:
    return httpx.Client(
        base_url='https://api.cloudflareclient.com/v0a2223',
        headers={
            'CF-Client-Version': 'a-6.11-2223',
            'Host': 'api.cloudflareclient.com',
            'Connection': 'Keep-Alive',
            'Accept-Encoding': 'gzip',
            'User-Agent': 'okhttp/3.12.1',
            'Content-Type': 'application/json; charset=UTF-8',
        },
        timeout=35,
    )


def apply_delay_if_needed(current_index: int, total_count: int) -> None:
    if current_index != total_count - 1:
        time.sleep(45)


def main(number_of_keys_to_generate: int) -> None:
    read_keys()
    logging.info('欢迎使用Warp+刷key脚本')
    with create_http_client() as client:
        for i in range(number_of_keys_to_generate):
            logging.info(f'正在生成第{i + 1}个key...')
            try:
                generate_and_save_key(client,10)#generate 10GB
            except:
                time.sleep(70)
            apply_delay_if_needed(i, number_of_keys_to_generate)
if __name__ == '__main__':
    main(1)
