from flask import Flask, request
import os
from flask_cors import CORS
from tasksv2 import resize_image, crop_image
from celery.result import AsyncResult
from celery_workerv2 import celery
from flask import send_from_directory
import threading
import uuid
import time

app = Flask(__name__)
CORS(app)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'images_v2')
PROCESSED_FOLDER = os.path.join(BASE_DIR, 'image_outv2')

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(PROCESSED_FOLDER, exist_ok=True)

# In-memory database to store task results for the thread fallback
tasks_db = {}

def run_crop_task_in_thread(task_id, filepath, output_path):
    tasks_db[task_id] = {"state": "PENDING", "result": None}
    try:
        # Sleep for a short duration to mimic asynchronous execution countdown
        time.sleep(2)
        # Call the underlying function of the celery task
        res = crop_image(filepath, output_path, (1080, 1080))
        tasks_db[task_id] = {"state": "SUCCESS", "result": res}
    except Exception as e:
        tasks_db[task_id] = {"state": "FAILURE", "result": str(e)}

@app.route('/upload', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        f = request.files.getlist('image[]')
        task_ids = []      
        for file in f:
            filepath = os.path.join(UPLOAD_FOLDER, file.filename)
            file.save(filepath)
            output_path = os.path.join(PROCESSED_FOLDER, f'resized_{file.filename}')
            
            task_id = str(uuid.uuid4())
            task_ids.append(task_id)
            
            # Start background thread to process the image without requiring Redis/Celery
            threading.Thread(target=run_crop_task_in_thread, args=(task_id, filepath, output_path)).start()

        return {"task_ids": task_ids}, 202
    else:
        return "no-no-no mister fish"


@app.route('/status/<task_id>')
def task_status(task_id):
    # Check in-memory database first
    if task_id in tasks_db:
        return tasks_db[task_id]
        
    # Fallback to Celery if not found locally
    try:
        result = AsyncResult(task_id, app=celery)
        return {"state": result.state, "result": result.result}
    except Exception:
        return {"state": "PENDING", "result": None}

@app.route('/download/<filename>')
def download_file(filename):
    return send_from_directory(PROCESSED_FOLDER, filename)

if __name__ == '__main__':
    app.run(debug=True)