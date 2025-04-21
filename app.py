from flask import Flask, request, jsonify, send_file
import os
import subprocess
import tempfile
import magic
import uuid

app = Flask(__name__)
TEMP_DIR = '/tmp/conversions'
os.makedirs(TEMP_DIR, exist_ok=True)

@app.route('/convert', methods=['POST'])
def convert_to_pdf():
    if 'file' not in request.files:
        return jsonify({"error": "No file provided"}), 400
    
    input_file = request.files['file']
    temp_id = str(uuid.uuid4())
    input_path = os.path.join(TEMP_DIR, f"{temp_id}_{input_file.filename}")
    output_path = os.path.join(TEMP_DIR, f"{temp_id}_output.pdf")
    
    # Save uploaded file
    input_file.save(input_path)
    
    # Detect file type
    mime = magic.Magic(mime=True)
    file_type = mime.from_file(input_path)
    
    try:
        # Convert based on file type
        if 'pdf' in file_type:
            # Already PDF, just return
            return send_file(input_path, mimetype='application/pdf')
        
        elif 'image' in file_type:
            # Convert image to PDF
            subprocess.run(['img2pdf', input_path, '-o', output_path], check=True)
            
        elif 'officedocument' in file_type or 'msword' in file_type:
            # Convert office document
            subprocess.run([
                'libreoffice', '--headless', '--convert-to', 'pdf',
                '--outdir', TEMP_DIR, input_path
            ], check=True)
            base_name = os.path.splitext(os.path.basename(input_path))[0].split('_', 1)[1]
            temp_output = os.path.join(TEMP_DIR, f"{base_name}.pdf")
            os.rename(temp_output, output_path)
            
        else:
            return jsonify({"error": f"Unsupported file type: {file_type}"}), 400
        
        return send_file(output_path, mimetype='application/pdf')
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
    finally:
        # Cleanup temp files after a delay (allows download to complete)
        def cleanup():
            try:
                if os.path.exists(input_path):
                    os.remove(input_path)
                if os.path.exists(output_path):
                    os.remove(output_path)
            except:
                pass
                
        # Schedule cleanup
        import threading
        t = threading.Timer(300, cleanup)  # 5 minute delay
        t.daemon = True
        t.start()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
