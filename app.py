from flask import Flask, request, render_template_string
import pandas as pd

app = Flask(__name__)

# Use the raw URL from GitHub for the Excel file
EXCEL_URL = ("https://raw.githubusercontent.com/aditya-gupta-andc/Securepin/"
             "6d06d3f715f14b8ec34c5d98d8f511f7b99ca702/Ghosi_IDF_Jan.xlsx")

# Load the Excel file into a DataFrame (this will load once when the server starts)
try:
    df = pd.read_excel(EXCEL_URL)
    # Uncomment the next line if you want to see the columns
    # print("Columns in Excel:", df.columns)
except Exception as e:
    print("Error loading Excel file:", e)
    df = pd.DataFrame()  # fallback to an empty DataFrame

# Basic HTML template using Flask’s render_template_string
HTML_TEMPLATE = '''
<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <title>Consumer Search</title>
    <style>
      body { font-family: Arial, sans-serif; margin: 20px; }
      input[type="text"] { padding: 5px; }
      input[type="submit"] { padding: 5px 10px; }
      table { border-collapse: collapse; margin-top: 20px; }
      table, th, td { border: 1px solid #ccc; padding: 8px; }
    </style>
  </head>
  <body>
    <h1>Search for a Consumer</h1>
    <form method="post" action="/search">
      <label for="consumer_id">Enter Consumer ID (ACCT_ID):</label>
      <input type="text" id="consumer_id" name="consumer_id" required>
      <input type="submit" value="Search">
    </form>
    
    {% if message %}
      <p style="color:red;">{{ message }}</p>
    {% endif %}
    
    {% if result %}
      <h2>Consumer Details:</h2>
      <table>
        {% for key, value in result.items() %}
          <tr>
            <th>{{ key }}</th>
            <td>{{ value }}</td>
          </tr>
        {% endfor %}
      </table>
    {% endif %}
  </body>
</html>
'''

@app.route('/', methods=['GET'])
def index():
    # Render the main page with the search form.
    return render_template_string(HTML_TEMPLATE)

@app.route('/search', methods=['POST'])
def search():
    consumer_id = request.form.get('consumer_id')
    
    if not consumer_id:
        return render_template_string(HTML_TEMPLATE, message="Please enter a Consumer ID.")
    
    # Since the Consumer_ID is stored as ACCT_ID in the Excel,
    # and it might be numeric, we try to match accordingly.
    try:
        # Try converting the input to an integer.
        consumer_id_int = int(consumer_id)
        matching_rows = df[df['ACCT_ID'] == consumer_id_int]
    except ValueError:
        # If conversion fails, compare as strings.
        matching_rows = df[df['ACCT_ID'].astype(str) == consumer_id]
    
    if matching_rows.empty:
        # No matching consumer found.
        return render_template_string(HTML_TEMPLATE, message="No consumer found with that ID.")
    else:
        # For this example, we display the first match.
        result = matching_rows.iloc[0].to_dict()
        return render_template_string(HTML_TEMPLATE, result=result)

if __name__ == '__main__':
    # Run the Flask app on localhost (default port 5000).
    app.run(debug=True)
