import random
import names
import os
import tempfile
from flask import Flask, request, send_file, render_template, Response, stream_with_context
from collections import deque
import time

app = Flask(__name__)

def generate_combo(selected_suffix):
    name = names.get_first_name()
    
    suffix_type = int(selected_suffix)
    suffix = ''
    
    if suffix_type == 1:
        suffix = str(random.randint(1900, 2050))
    elif suffix_type == 2:
        suffix = str(random.randint(0, 1000))
    elif suffix_type == 3:
        suffix = random.choice('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ')
    elif suffix_type == 4:
        prefix = random.choice('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ')
        name = f"{prefix}{name}"
    elif suffix_type == 5:
        prefix = str(random.randint(0, 999)).zfill(3)
        name = f"{prefix}{name}"
    elif suffix_type == 6:
        prefix = str(random.randint(1900, 2050))
        name = f"{prefix}{name}"
    elif suffix_type == 7:
        prefix = str(random.randint(1900, 2050))
        suffix = str(random.randint(0, 999)).zfill(3)
        name = f"{prefix}{name}"
    elif suffix_type == 8:
        prefix = str(random.randint(0, 999)).zfill(3)
        suffix = str(random.randint(1900, 2050))
        name = f"{prefix}{name}"
    elif suffix_type == 9:
        prefix = str(random.randint(0, 999)).zfill(3)
        suffix = str(random.randint(0, 999)).zfill(3)
        name = f"{prefix}{name}"
    elif suffix_type == 10:
        prefix = str(random.randint(123, 123456))
        name = f"{prefix}{name}"
    elif suffix_type == 11:
        suffix = str(random.randint(123, 123456))
    elif suffix_type == 12:
        suffix = '0' * random.randint(1, 4)
    elif suffix_type == 13:  # Mixto
        return generate_combo(random.choice(list(map(str, range(1, 13)))))
    elif suffix_type == 15:  # Sin variación
        pass

    username = f"{name}{suffix}"
    password = names.get_last_name()  # Contraseña aleatoria
    return f"{username}:{password}"

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/generate_stream')
def generate_stream():
    filename = request.args.get('filename', '').strip()
    combo_count = int(request.args.get('combo_count', 0))
    selected_suffix = request.args.get('suffixes')

    if not filename:
        return Response('{"type":"error","value":"El nombre del archivo es obligatorio."}', mimetype='text/event-stream')
    if combo_count <= 0 or combo_count > 100000:
        return Response('{"type":"error","value":"La cantidad de combos debe estar entre 1 y 100,000."}', mimetype='text/event-stream')
    if not selected_suffix or not selected_suffix.isdigit():
        return Response('{"type":"error","value":"Debes seleccionar una variación de nombre de usuario."}', mimetype='text/event-stream')

    selected_suffix = int(selected_suffix)
    temp_file = tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', delete=False, suffix='.txt')
    temp_path = temp_file.name
    app.config['temp_files'] = app.config.get('temp_files', {})
    app.config['temp_files'][filename] = temp_path

    def generate():
        unique_combos = set()
        buffer = deque(maxlen=10000)
        count = 0

        try:
            while count < combo_count:
                combo = generate_combo(selected_suffix)
                if combo not in unique_combos:
                    unique_combos.add(combo)
                    buffer.append(combo + "\n")
                    count += 1
                    yield f'data: {{"type":"combo","value":"{combo}"}}\n\n'
                    if len(buffer) == buffer.maxlen:
                        temp_file.writelines(buffer)
                        buffer.clear()
            if buffer:
                temp_file.writelines(buffer)
            temp_file.close()
            yield f'data: {{"type":"done","value":"Generación completada."}}\n\n'
        except Exception as e:
            yield f'data: {{"type":"error","value":"Error al generar combos: {str(e)}"}}\n\n'
            temp_file.close()

    return Response(stream_with_context(generate()), mimetype='text/event-stream')

@app.route('/download')
def download():
    filename = request.args.get('filename', '').strip()
    temp_path = app.config.get('temp_files', {}).get(filename)

    if temp_path and os.path.exists(temp_path):
        response = send_file(
            temp_path,
            as_attachment=True,
            download_name=f"{filename}.txt",
            mimetype='text/plain'
        )
        return response
    else:
        return render_template('index.html', error="Archivo no encontrado. Por favor, genera los combos nuevamente.")

@app.teardown_request
def cleanup_temp_files(exception=None):
    temp_files = app.config.get('temp_files', {})
    for fname, temp_path in list(temp_files.items()):
        if os.path.exists(temp_path):
            try:
                os.remove(temp_path)
                del temp_files[fname]
            except:
                pass

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
