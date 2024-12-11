from flask import Flask, request, send_file, render_template, url_for
from bs4 import BeautifulSoup
import pdfkit
import os

app = Flask(__name__)

UPLOAD_FOLDER = "uploads"
OUTPUT_FOLDER = "static/output"

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['OUTPUT_FOLDER'] = OUTPUT_FOLDER

# Ensure folders exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/process', methods=['POST'])
def process():
    try:
        html_file = request.files['html_file']
        images = request.files.getlist('images')

        # Validate file types
        if not html_file.filename.endswith('.html'):
            return "Invalid file type for HTML file.", 400
        for image in images:
            if not image.filename.lower().endswith(('.jpg', '.jpeg', '.png')):
                return "Invalid file type for images.", 400

        # Save HTML file
        html_path = os.path.join(app.config['UPLOAD_FOLDER'], html_file.filename)
        html_file.save(html_path)

        # Save images
        image_paths = {}
        for image in images:
            image_path = os.path.join(app.config['UPLOAD_FOLDER'], image.filename)
            image.save(image_path)
            image_paths[image.filename] = image_path

        # Modify HTML to insert absolute paths for images
        with open(html_path, 'r', encoding='utf-8') as file:
            soup = BeautifulSoup(file, 'html.parser')

        for img_tag in soup.find_all('img'):
            img_name = os.path.basename(img_tag['src'])
            if img_name in image_paths:
                img_tag['src'] = 'file://' + os.path.abspath(image_paths[img_name])

        # Save the modified HTML
        output_html_path = os.path.join(app.config['OUTPUT_FOLDER'], 'processed.html')
        with open(output_html_path, 'w', encoding='utf-8') as file:
            file.write(str(soup))

        # Convert the HTML to PDF
        wkhtmltopdf_path = r'c:\\Program Files\\wkhtmltopdf\\bin\\wkhtmltopdf.exe'
        config = pdfkit.configuration(wkhtmltopdf=wkhtmltopdf_path)
        output_pdf_path = os.path.join(app.config['OUTPUT_FOLDER'], 'processed.pdf')

        options = {
            'quiet': '',
            'enable-local-file-access': ''
        }
        pdfkit.from_file(output_html_path, output_pdf_path, configuration=config, options=options)

        # Generate URLs for processed files
        html_url = url_for('static', filename='output/processed.html', _external=True)
        pdf_url = url_for('static', filename='output/processed.pdf', _external=True)

        # Render the result page
        return render_template('result.html', html_url=html_url, pdf_url=pdf_url)

    except Exception as e:
        return f"An error occurred: {str(e)}", 500

if __name__ == '__main__':
    app.run(debug=True, use_reloader=False)
