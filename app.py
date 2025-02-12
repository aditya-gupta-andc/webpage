from flask import Flask, request, render_template_string, jsonify
import pandas as pd
import logging

app = Flask(__name__)
logging.basicConfig(level=logging.DEBUG)

# Use the raw URL for the Excel file from GitHub
EXCEL_URL = (
    "https://raw.githubusercontent.com/aditya-gupta-andc/webpage/"
    "7f71424bde7b11e34d9e9c0b61284b126ace26f3/master25.xlsx"
)

# Load the Excel file into a DataFrame at startup.
try:
    df = pd.read_excel(EXCEL_URL)
except Exception as e:
    app.logger.error("Error loading Excel file: %s", e)
    df = pd.DataFrame()

# HTML Template with Bootstrap, custom CSS, and jQuery UI for autocomplete
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
      body { background: #f8f9fa; }
      .container { max-width: 90%; margin-top: 50px; }
      .card { box-shadow: 0 4px 8px rgba(0,0,0,0.1); border-radius: 10px; }
      .result-table th { width: 40%; }
      #search-again { display: none; } /* Hide the "Search Again" button initially */
      
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
      @keyframes spin { 100% { transform: rotate(360deg); } }

      /* Make table scrollable on small screens */
      .table-responsive { overflow-x: auto; }

      /* Improve table layout for small screens */
      @media (max-width: 600px) { 
        .container { max-width: 95%; } 
        h2 { font-size: 22px; }
        .form-label { font-size: 14px; }
        .btn { font-size: 14px; padding: 10px; }

        /* Ensure table adjusts properly */
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

        <div id="search-again" class="text-center">
          <button class="btn btn-secondary mt-3" onclick="showSearch()">Search Again</button>
        </div>

        {% if message %}
          <div class="alert alert-danger mt-4" role="alert">
            {{ message }}
          </div>
        {% endif %}
        
        {% if result %}
          <div id="result-section" class="mt-4">
            <h4 class="text-center">Consumer Details</h4>
            <div class="table-responsive">  <!-- NEW: Scrollable Table Wrapper -->
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
        // Autocomplete feature
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

        // Show loading animation when searching
        $("#search-form").submit(function(){
          $("#loading").show();
        });
      });

      // Show search again form when clicking "Search Again"
      function showSearch() {
        document.getElementById("search-section").style.display = "block";
        document.getElementById("search-again").style.display = "none";
        document.getElementById("result-section").style.display = "none";
      }
    </script>
  </body>
</html>
'''

@app.route('/', methods=['GET'])
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/search', methods=['POST'])
def search():
    consumer_id = request.form.get('consumer_id', '').strip()
    
    if not consumer_id:
        return render_template_string(HTML_TEMPLATE, message="Please enter a Consumer ID.")
    
    try:
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

if __name__ == '__main__':
    app.run(debug=True)
