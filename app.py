from flask import Flask, request, render_template_string, jsonify
import pandas as pd
import logging

app = Flask(__name__)
logging.basicConfig(level=logging.DEBUG)

# Use the raw URL for the Excel file from GitHub
EXCEL_URL = (
    "https://raw.githubusercontent.com/aditya-gupta-andc/Securepin/"
    "6d06d3f715f14b8ec34c5d98d8f511f7b99ca702/Ghosi_IDF_Jan.xlsx"
)

# Load the Excel file into a DataFrame at startup.
try:
    df = pd.read_excel(EXCEL_URL)
except Exception as e:
    app.logger.error("Error loading Excel file: %s", e)
    df = pd.DataFrame()  # Fallback to an empty DataFrame

# HTML Template with Bootstrap, custom CSS, and jQuery UI for autocomplete
HTML_TEMPLATE = '''
<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <title>Consumer Lookup</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <!-- Bootstrap CSS CDN -->
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <!-- jQuery UI CSS -->
    <link rel="stylesheet" href="https://code.jquery.com/ui/1.13.2/themes/base/jquery-ui.css">
    <style>
      body {
        background: #f8f9fa;
      }
      .container {
        max-width: 600px;
        margin-top: 50px;
      }
      .card {
        box-shadow: 0 4px 8px rgba(0,0,0,0.1);
      }
      .result-table th {
        width: 40%;
      }
    </style>
  </head>
  <body>
    <div class="container">
      <div class="card p-4">
        <h2 class="card-title text-center mb-4">Consumer Lookup</h2>
        <form method="post" action="/search">
          <div class="mb-3">
            <label for="consumer_id" class="form-label">Enter Consumer ID (ACCT_ID):</label>
            <input type="text" class="form-control" id="consumer_id" name="consumer_id" placeholder="e.g., 12345" required>
          </div>
          <div class="d-grid">
            <button type="submit" class="btn btn-primary">Search</button>
          </div>
        </form>
        
        {% if message %}
          <div class="alert alert-danger mt-4" role="alert">
            {{ message }}
          </div>
        {% endif %}
        
        {% if result %}
          <div class="mt-4">
            <h4>Consumer Details</h4>
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
        {% endif %}
      </div>
    </div>
    
    <!-- jQuery and jQuery UI -->
    <script src="https://code.jquery.com/jquery-3.6.0.min.js"></script>
    <script src="https://code.jquery.com/ui/1.13.2/jquery-ui.min.js"></script>
    <!-- Bootstrap JS Bundle -->
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
    <script>
      // Initialize jQuery UI Autocomplete on the consumer_id input field.
      $(document).ready(function(){
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
      });
    </script>
  </body>
</html>
'''

@app.route('/', methods=['GET'])
def index():
    """Render the home page with the search form."""
    return render_template_string(HTML_TEMPLATE)

@app.route('/search', methods=['POST'])
def search():
    """Search for a consumer based on the provided Consumer ID."""
    consumer_id = request.form.get('consumer_id', '').strip()
    
    if not consumer_id:
        return render_template_string(HTML_TEMPLATE, message="Please enter a Consumer ID.")
    
    try:
        # Attempt to match numerically first; if that fails, compare as string.
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
        return render_template_string(HTML_TEMPLATE, message="An error occurred while processing your request. Please try again later.")

@app.route('/autocomplete', methods=['GET'])
def autocomplete():
    """Return a list of up to 10 Consumer IDs that start with the user's input."""
    query = request.args.get('q', '').strip()
    if not query:
        return jsonify([])
    
    suggestions = df[df['ACCT_ID'].astype(str).str.startswith(query)]['ACCT_ID'].astype(str).head(10).tolist()
    return jsonify(suggestions)

if __name__ == '__main__':
    app.run(debug=True)
