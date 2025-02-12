import gdown
import pandas as pd
from flask import Flask, render_template_string, request, jsonify
import logging

app = Flask(__name__)
logging.basicConfig(level=logging.DEBUG)

# -------------------------------
# Google Drive Excel File Settings
# -------------------------------
# Shared Google Drive link:
#   https://docs.google.com/spreadsheets/d/1sMiMvKiVaC31dpkbL6vZ9TtNypkTGwuw/edit?usp=drive_link
# The file ID is: 1sMiMvKiVaC31dpkbL6vZ9TtNypkTGwuw
GDRIVE_FILE_ID = "1sMiMvKiVaC31dpkbL6vZ9TtNypkTGwuw"
GDRIVE_DOWNLOAD_URL = f"https://drive.google.com/uc?id={GDRIVE_FILE_ID}&export=download"

def fetch_excel():
    """
    Downloads the Excel file from Google Drive using gdown,
    saves it locally as "temp_data.xlsx", and returns a DataFrame.
    """
    try:
        # Download the file (it will overwrite the existing one)
        gdown.download(GDRIVE_DOWNLOAD_URL, "temp_data.xlsx", quiet=False)
        return pd.read_excel("temp_data.xlsx")
    except Exception as e:
        app.logger.error("Error fetching Excel file from Google Drive: %s", e)
        return pd.DataFrame()

# Load the data once at startup.
df = fetch_excel()

# -------------------------------
# HTML Template with CSS, Bootstrap, and jQuery UI
# -------------------------------
HTML_TEMPLATE = '''
<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <title>Consumer Lookup</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <!-- Bootstrap CSS -->
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <!-- jQuery UI CSS -->
    <link rel="stylesheet" href="https://code.jquery.com/ui/1.13.2/themes/base/jquery-ui.css">
    <style>
      body { 
        background: #f8f9fa; 
      }
      .container { 
        max-width: 90%; 
        margin-top: 50px; 
      }
      .card { 
        box-shadow: 0 4px 8px rgba(0,0,0,0.1); 
        border-radius: 10px; 
      }
      .result-table th { 
        width: 40%; 
      }
      #search-again { 
        display: none; 
      }
      /* Loading animation */
      .loader { 
        display: none; 
        margin: 10px auto; 
        border: 5px solid #f3f3f3; 
        border-radius: 50%; 
        border-top: 5px solid #3498db; 
        width: 30px; 
        height: 30px; 
        animation: spin 1s linear infinite; 
      }
      @keyframes spin { 
        100% { transform: rotate(360deg); } 
      }
      /* Responsive table */
      .table-responsive { 
        overflow-x: auto; 
      }
      @media (max-width: 600px) { 
        .container { max-width: 95%; } 
        h2 { font-size: 22px; }
        .form-label { font-size: 14px; }
        .btn { font-size: 14px; padding: 10px; }
        .result-table th, .result-table td { 
          font-size: 14px; 
          padding: 8px; 
        }
      }
    </style>
  </head>
  <body>
    <div class="container">
      <div class="card p-4">
        <h2 class="card-title text-center mb-3">Consumer Lookup</h2>

        <!-- Search Form Section -->
        <div id="search-section">
          <form method="post" action="/search" id="search-form">
            <div class="mb-3">
              <label for="consumer_id" class="form-label">Enter Consumer ID (ACCT_ID):</label>
              <input type="text" class="form-control" id="consumer_id" name="consumer_id" placeholder="e.g., 12345" required>
            </div>
            <div class="d-grid">
              <button type="submit" class="btn btn-primary">Search</button>
            </div>
            <div class="text-center">
              <div class="loader" id="loading"></div>
            </div>
          </form>
        </div>

        <!-- Search Again Button Section -->
        <div id="search-again" class="text-center">
          <button class="btn btn-secondary mt-3" onclick="showSearch()">Search Again</button>
        </div>

        <!-- Error Message Section -->
        {% if message %}
          <div class="alert alert-danger mt-4" role="alert">
            {{ message }}
          </div>
        {% endif %}

        <!-- Consumer Details Result Section -->
        {% if result %}
          <div id="result-section" class="mt-4">
            <h4 class="text-center">Consumer Details</h4>
            <div class="table-responsive">
              <table class="table table-bordered result-table">
                <tbody>
                  {% for key, value in result.items() %}
                    <tr>
                      <th>{{ key }}</th>
                      <td>{{ value }}</td>
                    </tr>
                  {% endfor %}
                </tbody>
              </table>
            </div>
          </div>
          <!-- Hide search form and display Search Again button -->
          <script>
            document.getElementById("search-section").style.display = "none";
            document.getElementById("search-again").style.display = "block";
          </script>
        {% endif %}
      </div>
    </div>

    <!-- jQuery and jQuery UI -->
    <script src="https://code.jquery.com/jquery-3.6.0.min.js"></script>
    <script src="https://code.jquery.com/ui/1.13.2/jquery-ui.min.js"></script>
    <!-- Bootstrap JS -->
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>

    <script>
      $(document).ready(function(){
        // Enable autocomplete for consumer_id field
        $("#consumer_id").autocomplete({
          source: function(request, response) {
            $.ajax({
              url: "/autocomplete",
              dataType: "json",
              data: { q: request.term },
              success: function(data) {
                response(data);
              }
            });
          },
          minLength: 1
        });

        // Show loading animation when the form is submitted
        $("#search-form").submit(function(){
          $("#loading").show();
        });
      });

      // Function to show the search form again
      function showSearch() {
        document.getElementById("search-section").style.display = "block";
        document.getElementById("search-again").style.display = "none";
        document.getElementById("result-section").style.display = "none";
      }
    </script>
  </body>
</html>
'''

# -------------------------------
# Flask Routes
# -------------------------------

@app.route('/', methods=['GET'])
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/search', methods=['POST'])
def search():
    consumer_id = request.form.get('consumer_id', '').strip()
    if not consumer_id:
        return render_template_string(HTML_TEMPLATE, message="Please enter a Consumer ID.")
    try:
        # Attempt numeric match first; if not, use string matching.
        try:
            consumer_id_int = int(consumer_id)
            matching_rows = df[df['ACCT_ID'] == consumer_id_int]
        except ValueError:
            matching_rows = df[df['ACCT_ID'].astype(str).str.strip() == consumer_id]
        if matching_rows.empty:
            return render_template_string(HTML_TEMPLATE, message="No consumer found with that ID.")
        else:
            result = matching_rows.iloc[0].to_dict()
            return render_template_string(HTML_TEMPLATE, result=result)
    except Exception as e:
        app.logger.error("Error during search: %s", e)
        return render_template_string(HTML_TEMPLATE, message="An error occurred. Please try again.")

@app.route('/autocomplete', methods=['GET'])
def autocomplete():
    query = request.args.get('q', '').strip()
    if not query:
        return jsonify([])
    suggestions = df[df['ACCT_ID'].astype(str).str.startswith(query)]['ACCT_ID'].astype(str).head(10).tolist()
    return jsonify(suggestions)

# -------------------------------
# Run the Flask App
# -------------------------------
if __name__ == '__main__':
    app.run(debug=True)
