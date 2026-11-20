"""Builds the list of expected photographs (12 restaurants + 120 dishes) from seed_data.py.

It parses seed_data.py with `ast` so nothing is executed and no database is needed.
"""
import ast
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from image_paths import restaurant_photo_rel, food_photo_rel  # noqa: E402

PER_RESTAURANT = 10  # seed_data.py keeps exactly this many dishes per restaurant


def load_catalog():
    with open(os.path.join(ROOT, 'seed_data.py'), encoding='utf-8') as fh:
        tree = ast.parse(fh.read())
    data = {}
    for node in tree.body:
        if isinstance(node, ast.Assign) and getattr(node.targets[0], 'id', '') in (
                'sample_restaurants', 'sample_foods_by_restaurant', 'extra_foods_by_restaurant'):
            data[node.targets[0].id] = ast.literal_eval(node.value)
    items = []
    for r in data['sample_restaurants']:
        items.append({'kind': 'restaurant', 'restaurant': r['name'], 'name': r['name'],
                      'cuisine': r['cuisine_type'], 'rel': restaurant_photo_rel(r['name'])})
        seen, count = set(), 0
        dishes = list(data['sample_foods_by_restaurant'].get(r['name'], [])) + \
            list(data['extra_foods_by_restaurant'].get(r['name'], []))
        for dish in dishes:
            if dish[0].casefold() in seen:
                continue
            if count >= PER_RESTAURANT:
                break
            seen.add(dish[0].casefold())
            count += 1
            items.append({'kind': 'food', 'restaurant': r['name'], 'name': dish[0],
                          'cuisine': r['cuisine_type'], 'rel': food_photo_rel(r['name'], dish[0])})
    return items


def abs_path(item):
    return os.path.join(ROOT, 'static', *item['rel'].split('/'))


if __name__ == '__main__':
    its = load_catalog()
    print(sum(i['kind'] == 'restaurant' for i in its), 'restaurants,', sum(i['kind'] == 'food' for i in its), 'foods')
