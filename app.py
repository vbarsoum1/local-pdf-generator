from flask import Flask, request, jsonify, send_file
import os
import subprocess
import tempfile
import uuid
import shutil
from werkzeug.utils import secure_filename
import mimetypes

app = Flask(__name__)
TEMP_DIR = '/tmp/conversions'
os.makedirs(TEMP_DIR, exist_ok=True)

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({"status": "healthy"}), 200

@app.route('/convert', methods=['POST'])
def convert_to_pdf():
    if 'file' not in request.files:
        return jsonify({"error": "No file provided"}), 400
    
    input_file = request.files['file']
    original_filename = secure_filename(input_file.filename)
    file_ext = os.path.splitext(original_filename)[1].lower()
    
    # Create unique ID and paths for this conversion
    temp_id = str(uuid.uuid4())
    input_path = os.path.join(TEMP_DIR, f"{temp_id}_{original_filename}")
    output_path = os.path.join(TEMP_DIR, f"{temp_id}_output.pdf")
    
    # Save uploaded file
    input_file.save(input_path)
    
    try:
        # Check if already PDF by extension
        if file_ext == '.pdf':
            return send_file(input_path, mimetype='application/pdf')
        
        # Detect if image by extension
        image_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff']
        if file_ext in image_extensions:
            # Use img2pdf for images
            subprocess.run(['img2pdf', input_path, '-o', output_path], check=True)
        else:
            # Use LibreOffice for documents
            subprocess.run([
                'libreoffice', '--headless', '--convert-to', 'pdf',
                '--outdir', TEMP_DIR, input_path
            ], check=True)
            
            # Locate the output file - LibreOffice keeps original extension
            base_name = os.path.splitext(os.path.basename(input_path))[0]
            temp_output = os.path.join(TEMP_DIR, f"{base_name.split('_', 1)[1]}.pdf")
            
            # If file exists, move it to our standard output path
            if os.path.exists(temp_output):
                shutil.move(temp_output, output_path)
            else:
                return jsonify({"error": "Conversion failed, no output file generated"}), 500
        
        # Return converted PDF
        return send_file(output_path, mimetype='application/pdf')
    
    except subprocess.CalledProcessError as e:
        return jsonify({"error": f"Conversion command failed: {str(e)}"}), 500
    except Exception as e:
        return jsonify({"error": f"Conversion error: {str(e)}"}), 500
    
    finally:
        # Schedule file cleanup (in production, use a proper cleanup task)
        try:
            if os.path.exists(input_path):
                os.remove(input_path)
            if os.path.exists(output_path) and os.path.exists(input_path) != file_ext == '.pdf':
                # Only remove output if we're not using input as output (PDF passthrough)
                os.remove(output_path)
        except Exception as e:
            print(f"Cleanup error: {str(e)}")

if __name__ == '__main__':
    # Print startup message for debugging
    print("Document Conversion Service starting up...")
    print(f"Temporary directory: {TEMP_DIR}")
    
    # List available conversion tools
    try:
        print("LibreOffice version:")
        subprocess.run(['libreoffice', '--version'], check=False)
        
        print("\nimg2pdf version:")
        subprocess.run(['img2pdf', '--version'], check=False)
    except Exception as e:
        print(f"Error checking tools: {str(e)}")
    
    app.run(host='0.0.0.0', port=5000)
