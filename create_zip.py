import zipfile
import os

def create_zip():
    # Change to script directory
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    
    files_to_zip = [
        'requirements.txt',
        'Procfile',
        'flask_app.py',
        'set_webhook.py',
        'PYTHONANYWHERE_GUIDE.md',
        'vodiy_express.db'
    ]
    folders_to_zip = ['bot', 'core']
    
    zip_filename = 'jonlitaxi_deploy.zip'
    
    with zipfile.ZipFile(zip_filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
        # Add individual files
        for file in files_to_zip:
            if os.path.exists(file):
                print(f"Adding {file}...")
                zipf.write(file)
            else:
                print(f"Warning: {file} not found")
        
        # Add folders
        for folder in folders_to_zip:
            if os.path.exists(folder):
                print(f"Adding folder {folder}...")
                for root, dirs, files in os.walk(folder):
                    # Filter out __pycache__
                    dirs[:] = [d for d in dirs if d != '__pycache__']
                    for file in files:
                        if file.endswith('.pyc'):
                            continue
                        file_path = os.path.join(root, file)
                        print(f"Adding {file_path}...")
                        zipf.write(file_path)
            else:
                 print(f"Warning: {folder} not found")
                 
    print(f"Successfully created {zip_filename}")

if __name__ == "__main__":
    create_zip()
