from flask import Flask, render_template, request, jsonify
import os
import torch
from transformers import pipeline, AutoTokenizer, AutoModelForSeq2SeqLM
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader
import pdf2image
import easyocr

app = Flask(__name__)

# Model loading
checkpoint = "facebook/bart-large-cnn"
tokenizer = AutoTokenizer.from_pretrained(checkpoint)
base_model = AutoModelForSeq2SeqLM.from_pretrained(checkpoint, device_map="auto", torch_dtype=torch.float32)

# EasyOCR reader
reader = easyocr.Reader(['en'])

# Extract text from images using OCR
def extract_text_from_image(image_path):
    result = reader.readtext(image_path, detail=0)
    return " ".join(result)

# Convert PDF pages to images and extract text
def extract_text_from_pdf_images(pdf_path):
    images = pdf2image.convert_from_path(pdf_path)
    extracted_text = ""
    for i, image in enumerate(images):
        temp_image_path = f"temp_page_{i}.jpg"
        image.save(temp_image_path, "JPEG")
        extracted_text += extract_text_from_image(temp_image_path) + "\n"
        os.remove(temp_image_path)
    return extracted_text

# Extract text from file
def extract_text_from_file(file_path):
    if file_path.lower().endswith('.pdf'):
        loader = PyPDFLoader(file_path)
        pages = loader.load_and_split()
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=200, chunk_overlap=50)
        texts = text_splitter.split_documents(pages)
        extracted_text = "\n".join([text.page_content for text in texts])

        if not extracted_text.strip():
            extracted_text = extract_text_from_pdf_images(file_path)

    elif file_path.lower().endswith(('.jpg', '.jpeg', '.png')):
        extracted_text = extract_text_from_image(file_path)

    else:
        raise ValueError("Unsupported file format.")
    
    return extracted_text

# Summarization pipeline
def generate_summary(text, max_length, min_length):
    summarization_pipeline = pipeline('summarization', model=base_model, tokenizer=tokenizer, max_length=max_length, min_length=min_length)
    result = summarization_pipeline(text)
    return result[0]['summary_text']

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/uploads', methods=['POST'])
def summarize():
    try:
        # Check if the request has a file
        if 'file' not in request.files:
            return jsonify({"error": "No file part in the request"}), 400
        
        file = request.files['file']

        if file.filename == '':
            return jsonify({"error": "No file selected"}), 400

        summary_type = request.form.get('summary-length')
        if not summary_type:
            return jsonify({"error": "Missing summary length"}), 400

        max_length, min_length = (150, 60) if summary_type == "short" else (500, 200)

        filepath = os.path.join('uploads', file.filename)
        file.save(filepath)
        extracted_text = extract_text_from_file(filepath)

        if not extracted_text.strip():
            return jsonify({"error": "No readable text found in the document."})

        summary = generate_summary(extracted_text, max_length, min_length)
        return jsonify({"summary": summary})
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    os.makedirs("uploads", exist_ok=True)
    app.run(debug=True)
