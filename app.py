import random
import names
import os
from flask import Flask, request, send_file, render_template, Response
from collections import deque
import time
import tempfile
import json
import uuid

app = Flask(__name__)

# Variable global para rastrear el progreso y archivo generado
progress_data = {'progress': 0, 'total': 0, 'filename': None, 'file_id': None, 'temp_path': None}

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

@app.route('/generate', methods=['POST'])
def generate():
    global progress_data
    try:
        filename = request.form.get('filename', '').strip()
        if not filename:
            return render_template('index.html', error="El nombre del archivo es obligatorio.")

        combo_count = int(request.form.get('combo_count', 0))
        if combo_count <= 0 or combo_count > 100000:
            return render_template('index.html', error="La cantidad de combos debe estar entre 1 y 100,000.")

        selected_suffix = request.form.get('suffixes')
        if not selected_suffix or not selected_suffix.isdigit():
            return render_template('index.html', error="Debes seleccionar una variación de nombre de usuario.")

        selected_suffix = int(selected_suffix)

        # Generar un ID único para el archivo
        file_id = str(uuid.uuid4())
        # Inicializar el progreso
        progress_data['progress'] = 0
        progress_data['total'] = combo_count
        progress_data['filename'] = filename
        progress_data['file_id'] = file_id

        # Crear un archivo temporal en modo texto
        temp_path = tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', delete=False, suffix='.txt').name
        progress_data['temp_path'] = temp_path
        unique_combos = set()
        buffer = deque(maxlen=10000)
        count = 0

        with open(temp_path, 'w', encoding='utf-8') as temp_file:
            start_time = time.time()
            while count < combo_count:
                combo = generate_combo(selected_suffix)
                if combo not in unique_combos:
                    unique_combos.add(combo)
                    buffer.append(combo + "\n")
                    count += 1
                    progress_data['progress'] = count
                    if len(buffer) == buffer.maxlen:
                        temp_file.writelines(buffer)
                        buffer.clear()
            
            if buffer:
                temp_file.writelines(buffer)

        # Enviar el file_id como respuesta para que el cliente lo use en la descarga
        return json.dumps({'file_id': file_id})

    except Exception as e:
        return render_template('index.html', error=f"Error al generar combos: {str(e)}")

@app.route('/progress')
def progress():
    def generate_progress():
        global progress_data
        last_progress = -1
        while True:
            current_progress = progress_data['progress']
            if current_progress != last_progress:
                percentage = (current_progress / progress_data['total'] * 100) if progress_data['total'] > 0 else 0
                yield f"data: {json.dumps({'progress': percentage})}\n\n"
                last_progress = current_progress
            if current_progress >= progress_data['total']:
                break
            time.sleep(0.1)  # Esper Entomol: 09:54 PM AST on Friday, October 10, 2025
ar brevemente para evitar uso excesivo de CPU
    return Response(generate_progress(), mimetype='text/event-stream')

@app.route('/download/<file_id>')
def download(file_id):
    global progress_data
    if progress_data.get('file_id') == file_id and progress_data.get('temp_path'):
        temp_path = progress_data['temp_path']
        filename = progress_data['filename']
        if os.path.exists(temp_path):
            return send_file(
                temp_path,
                as_attachment=True,
                download_name=f"{filename}.txt",
                mimetype='text/plain'
            )
    return render_template('index.html', error="Archivo no encontrado o solicitud inválida.")

@app.teardown_request
def cleanup_temp_files(exception=None):
    # Limpiar archivos temporales
    global progress_data
    temp_dir = tempfile.gettempdir()
    for fname in os.listdir(temp_dir):
        if fname.endswith('.txt'):
            try:
                os.remove(os.path.join(temp_dir, fname))
            except:
                pass
    progress_data = {'progress': 0, 'total': 0, 'filename': None, 'file_id': None, 'temp_path': None}

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
