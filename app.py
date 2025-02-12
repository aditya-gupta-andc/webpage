from flask import Flask, request, render_template_string
import pandas as pd
import logging

app = Flask(__name__)
logging.basicConfig(level=logging.DEBUG)

# Use the raw URL for the Excel file on GitHub
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

# HTML Template with Bootstrap styling
HTML_TEMPLATE = '''
<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <title>Consumer Lookup</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <!-- Bootstrap CSS CDN -->
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
      body {
        background-color: #f8f9fa;
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
    <!-- Bootstrap JS Bundle -->
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
  </body>
</html>
'''

@app.route('/', methods=['GET'])
def index():
    """Render the home page with the search form."""
    return render_template_string(HTML_TEMPLATE)

@app.route('/search', methods=['POST'])
def search():
    """Handle the search for a consumer by ACCT_ID."""
    consumer_id = request.form.get('consumer_id', '').strip()
    
    if not consumer_id:
        return render_template_string(HTML_TEMPLATE, message="Please enter a Consumer ID.")
    
    try:
        # Attempt to convert the input to an integer.
        try:
            consumer_id_int = int(consumer_id)
            matching_rows = df[df['ACCT_ID'] == consumer_id_int]
        except ValueError:
            # If conversion fails, compare as string.
            matching_rows = df[df['ACCT_ID'].astype(str).str.strip() == consumer_id]
    
        if matching_rows.empty:
            return render_template_string(HTML_TEMPLATE, message="No consumer found with that ID.")
        else:
            # Display the first matching result.
            result = matching_rows.iloc[0].to_dict()
            return render_template_string(HTML_TEMPLATE, result=result)
    except Exception as e:
        app.logger.error("Error during search: %s", e)
        return render_template_string(HTML_TEMPLATE, message="An error occurred while processing your request. Please try again later.")

# Custom 404 error page for undefined routes.
@app.errorhandler(404)
def page_not_found(e):
    return render_template_string('''
    <!doctype html>
    <html lang="en">
      <head>
        <meta charset="utf-8">
        <title>Page Not Found</title>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
      </head>
      <body class="bg-light">
        <div class="container text-center mt-5">
          <h1 class="display-4">404</h1>
          <p class="lead">Page Not Found</p>
          <a href="/" class="btn btn-primary">Go Home</a>
        </div>
      </body>
    </html>
    ''', 404)

if __name__ == '__main__':
    app.run(debug=True)
