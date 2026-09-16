import json
import time
from typing import Any

import requests


def batch(func, ids: list[str]) -> dict[str, dict[str, Any]]:
    CHUNK_SIZE = 0x100
    result = {}
    for i in range(0, len(ids), CHUNK_SIZE):
        slice = ids[i:i+CHUNK_SIZE]
        result.update(func(slice))
    return result


def get_content_items(ids: list[str]) -> dict[str, dict[str, Any]]:
    while True:
        try:
            response = requests.get(
                f'https://instrument-api.splice.com/api/v2/content/content-items?ids={','.join(ids)}',
                headers={'X-Client-Id': '69'},
            )
            return {
                item['content_id']: item
                for item in response.json()['items']
            }
        except Exception:
            time.sleep(2)


def get_assets(ids: list[str]) -> dict[str, dict[str, Any]]:
    while True:
        try:
            response = requests.get(
                f'https://instrument-api.splice.com/api/v2/content/content-assets?ids={','.join(ids)}',
                headers={'X-Client-Id': '69'},
            )
            return {
                asset['asset_id']: asset
                for asset in response.json()['assets']
            }
        except Exception:
            time.sleep(2)


def search() -> dict[str, dict[str, Any]]:
    page = 1
    max_page = 0xfff
    result = {}
    while page <= max_page:
        json_response = requests.get(
            f'https://instrument-api.splice.com/api/v2/content/content-items/search?type=library&page={page}',
            headers={'X-Client-Id': '69'},
        ).json()
        max_page = json_response['pagination']['last_page']
        result.update({i['content_id']: i for i in json_response['items']})
        page += 1

    return result


def get_info(ids: list[str]):
    assets = batch(get_assets, ids)
    content_items = batch(get_content_items, ids)
    keys = set([*assets.keys(), *content_items.keys()])
    return {
        k: assets.get(k, {}) | content_items.get(k, {})
        for k in keys
    }


def process_items(data: dict[str, dict[str, Any]], cache_set: set[str]):
    # Note that `data` is mutable.

    if len(data) == 0:
        return

    # Pass 1: generate nested dicts in each of `data`, which will be populated by the next pass.
    replacement_keys = {}
    for iden, item in data.items():
        for k, v in list(item.items()):
            cache_set.add(iden)

            if k in {
                'content_id',
                'asset_id',
            }:
                continue

            split = k.rsplit('_', 1)
            if len(split) == 1:
                continue
            (base, suffix) = split

            # For example, when a key is `"image_id"`
            if suffix == 'id' and isinstance(v, str):
                replacement_keys.update({
                    v: (item, f'{base}_item')
                })

            # For example, when a key is `"item_ids"`
            if suffix == 'ids' and isinstance(v, list):
                rep_dict = item[f'{base}_items'] = {}
                replacement_keys.update({
                    i: (rep_dict, i)
                    for i in v
                })

    # Pass 2: populate nested dicts.
    replacement_key_keys = set(replacement_keys).difference(cache_set)
    replacement = get_info(list(replacement_key_keys))
    process_items(replacement, cache_set)
    for k, item in replacement.items():
        (dict_to_add, key_to_add) = replacement_keys[k]
        dict_to_add[key_to_add] = item


def main():
    data = search()
    process_items(data, set())
    json.dump(data, open('result.json', 'w'), indent='\t')


if __name__ == '__main__':
    main()
