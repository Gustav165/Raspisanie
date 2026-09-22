from flask import Flask, render_template, jsonify, request
import os
import json
import uuid

app = Flask(__name__)
SAVES_DIR = os.path.join(os.path.dirname(__file__), 'saves')
SCHEDULE_TEMPLATE = 'lol2.json'


def read_table(filename):
    filepath = os.path.join(SAVES_DIR, filename)
    with open(filepath, 'r', encoding='utf-8') as file:
        table = json.load(file)
    table['id'] = filename[:-5]
    return table


def write_table(table_id, table):
    filepath = os.path.join(SAVES_DIR, f'{table_id}.json')
    with open(filepath, 'w', encoding='utf-8') as file:
        json.dump({
            'name': table.get('name', table_id),
            'headers': table.get('headers', []),
            'data': table.get('data', [])
        }, file, ensure_ascii=False, indent=2)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/tables')
def get_tables():
    os.makedirs(SAVES_DIR, exist_ok=True)
    tables_data = []
    for filename in os.listdir(SAVES_DIR):
        is_schedule = filename == SCHEDULE_TEMPLATE or filename.startswith('raspisanie-')
        if not is_schedule or not filename.endswith('.json'):
            continue
        try:
            tables_data.append(read_table(filename))
        except (OSError, ValueError) as error:
            print(f'Ошибка чтения {filename}: {error}')
    return jsonify(tables_data)


@app.post('/api/tables')
def add_table():
    os.makedirs(SAVES_DIR, exist_ok=True)
    template = read_table(SCHEDULE_TEMPLATE)
    table_id = f'raspisanie-{uuid.uuid4().hex[:8]}'
    payload = request.get_json(silent=True) or {}
    table = {
        'name': payload.get('name') or f"{template.get('name', 'Расписание')} (новое)",
        'headers': payload.get('headers', template.get('headers', [])),
        'data': payload.get('data', template.get('data', []))
    }
    write_table(table_id, table)
    table['id'] = table_id
    return jsonify(table), 201


@app.put('/api/tables/<table_id>')
def update_table(table_id):
    if table_id == SCHEDULE_TEMPLATE[:-5]:
        return jsonify({'error': 'Пример нельзя изменить'}), 400
    if '/' in table_id or '\\' in table_id:
        return jsonify({'error': 'Некорректное имя таблицы'}), 400
    filepath = os.path.join(SAVES_DIR, f'{table_id}.json')
    if not os.path.isfile(filepath):
        return jsonify({'error': 'Таблица не найдена'}), 404
    payload = request.get_json(silent=True) or {}
    if not isinstance(payload.get('headers'), list) or not isinstance(payload.get('data'), list):
        return jsonify({'error': 'Некорректные данные таблицы'}), 400
    table = {
        'name': payload.get('name') or 'Расписание',
        'headers': payload['headers'],
        'data': payload['data']
    }
    write_table(table_id, table)
    table['id'] = table_id
    return jsonify(table)


@app.delete('/api/tables/<table_id>')
def delete_table(table_id):
    if table_id == SCHEDULE_TEMPLATE[:-5]:
        return jsonify({'error': 'Пример нельзя удалить'}), 400
    if '/' in table_id or '\\' in table_id:
        return jsonify({'error': 'Некорректное имя таблицы'}), 400
    filepath = os.path.join(SAVES_DIR, f'{table_id}.json')
    if not os.path.isfile(filepath):
        return jsonify({'error': 'Таблица не найдена'}), 404
    os.remove(filepath)
    return jsonify({'success': True})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)