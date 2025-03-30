document.getElementById('file').addEventListener('change', function() {
    const fileNameDisplay = document.getElementById('file-name');
    const file = this.files[0];
    
    if (file) {
      fileNameDisplay.textContent = `✅ File Selected: ${file.name}`;
      fileNameDisplay.style.color = "#28a745";
    } else {
      fileNameDisplay.textContent = "No file chosen";
      fileNameDisplay.style.color = "#555";
    }
  });
  
  document.getElementById('upload-form').addEventListener('submit', function(e) {
    e.preventDefault();
    
    const processingDiv = document.getElementById('processing');
    const resultDiv = document.getElementById('result');
    const fileInput = document.getElementById('file');
    const summaryLength = document.getElementById('summary-length').value;
  
    processingDiv.classList.remove('hidden');
    resultDiv.classList.add('hidden');
  
    if (!fileInput.files.length) {
      alert('Please select a file before submitting.');
      processingDiv.classList.add('hidden');
      return;
    }
  
    const formData = new FormData();
    formData.append('file', fileInput.files[0]);
    formData.append('summary-length', summaryLength);
  
    fetch('/uploads', {
      method: 'POST',
      body: formData
    })
    .then(response => {
      if (!response.ok) {
        return response.json().then(err => { throw new Error(err.error || 'Unknown error'); });
      }
      return response.json();
    })
    .then(data => {
      processingDiv.classList.add('hidden');
      
      if (data.error) {
        alert(`Error: ${data.error}`);
      } else {
        resultDiv.classList.remove('hidden');
        document.getElementById('summaryType').textContent = summaryLength === 'short' ? 'Short' : 'Long';
        document.getElementById('summaryText').textContent = data.summary;
      }
    })
    .catch(error => {
      processingDiv.classList.add('hidden');
      alert(`Error: ${error.message}`);
      console.error('Error:', error);
    });
  });
  