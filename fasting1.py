import pandas as pd
import os
from flask import Flask, render_template_string, request

app = Flask(__name__)

# Load data from CSV
csv_file = 'C:/Users/Shiva/Desktop/New folder/fast/data.csv'
if not os.path.exists(csv_file):
    print(f"{csv_file} not found")
    exit()

data = pd.read_csv(csv_file)

# Convert gender to numbers (Female=1, Male=0)
data['gender'] = data['gender'].map({'Female': 1, 'Male': 0})

# Define features for patient input (excluding diet flags for now)
base_features = ['age', 'gender', 'weight', 'bmi', 'basal fasting glucose (mmol/l)', 
                 'basal fasting insulin (pmol/l)', 'HOMA-IR diff']

# Diet flags in the data
diet_flags = ['Diet Hi Carb', 'Diet Hi Mono', 'CER', 'IER', 'DMF', 'FESD', 'IECR', 
              'IECR + PF', 'IF100', 'IF70', 'DR70', 'CCR', 'ICR']

# Check if all required columns are present
missing_cols = [col for col in base_features + diet_flags + ['fasting glucose after (mmol/l)'] if col not in data.columns]
if missing_cols:
    print(f"Missing columns in the data: {missing_cols}")
    exit()

# Diet plan templates based on IF types from study
diet_plans = {
    'CER': {
        'Name': 'Continuous Energy Restriction (CER)',
        'Description': 'Daily 25% calorie reduction with balanced meals.',
        'Timings': 'Breakfast: 8:00 AM, Lunch: 1:00 PM, Dinner: 6:00 PM',
        'Foods': 'Vegetables (spinach, broccoli), Fruits (berries, apples), Lean protein (chicken), Whole grains (quinoa)',
        'Fasting': 'No fasting periods, consistent intake daily.'
    },
    'IER': {
        'Name': 'Intermittent Energy Restriction (5:2 Diet)',
        'Description': 'Two days of very low calories (500-600 kcal), five days normal eating.',
        'Timings': 'Fasting Days: One meal at 12:00 PM; Normal Days: Breakfast 8:00 AM, Lunch 1:00 PM, Dinner 6:00 PM',
        'Foods': 'Fasting Days: Vegetables (kale, carrots), Fruits (orange); Normal Days: Add lean protein (fish), nuts',
        'Fasting': 'Two consecutive days (e.g., Mon, Tue) with 500-600 kcal.'
    },
    'DMF': {
        'Name': 'Daily Morning Fasting (DMF)',
        'Description': 'Skip breakfast, eat within a 6-8 hour window later in the day.',
        'Timings': 'First Meal: 12:00 PM, Last Meal: 8:00 PM',
        'Foods': 'Vegetables (zucchini, peppers), Fruits (banana, grapefruit), Protein (eggs), Healthy fats (avocado)',
        'Fasting': 'Fast from 8:00 PM to 12:00 PM daily (16-hour fast).'
    },
    'FESD': {
        'Name': 'Fasting Every Second Day (FESD)',
        'Description': 'Alternate fasting (20 hours) and normal eating days.',
        'Timings': 'Fasting Day: One meal at 6:00 PM; Normal Day: Breakfast 8:00 AM, Lunch 1:00 PM, Dinner 6:00 PM',
        'Foods': 'Fasting Day: Vegetables (cucumber, leafy greens); Normal Day: Fruits (peach), Protein (turkey)',
        'Fasting': 'Fast 20 hours every other day (e.g., 10:00 PM to 6:00 PM next day).'
    }
}

# Function to suggest diet plan based on patient data
def suggest_diet_plan(patient_data):
    glucose = patient_data['basal fasting glucose (mmol/l)']
    insulin = patient_data['basal fasting insulin (pmol/l)']
    bmi = patient_data['bmi']
    age = patient_data['age']
    gender = 'Female' if patient_data['gender'] == 1 else 'Male'

    # Print patient data for debugging
    print(f"Patient Data: {patient_data}")

    # Simple rule-based logic based on study insights and patient profile
    if glucose > 5.6 or insulin > 100:  # High glucose/insulin, suggesting stricter IF
        if age > 45:  # Older patients may benefit from milder IF
            diet = 'CER' if gender == 'Female' else 'FESD'
        else:  # Younger, stricter IF
            diet = 'IER' if gender == 'Female' else 'FESD'
    elif bmi > 30:  # Overweight, moderate IF
        diet = 'DMF' if gender == 'Female' else 'CER'
    else:  # Milder IF for lower risk
        diet = 'CER' if gender == 'Female' else 'DMF'

    plan = diet_plans[diet]
    return {
        'Diet Name': plan['Name'],
        'Description': plan['Description'],
        'Meal Timings': plan['Timings'],
        'Recommended Foods': plan['Foods'],
        'Fasting Schedule': plan['Fasting']
    }

@app.route('/', methods=['GET', 'POST'])
def index():
    patient_diet_plans = []
    selected_patient = None
    diet_suggestion = None
    error_message = None  # Variable to store error message

    if request.method == 'POST':
        try:
            selected_patient = int(request.form['patient'])
            if selected_patient == 0:  # Check if "Select Patient" is chosen
                error_message = "No patient selected. Please select a patient."
            else:
                patient_data = data.iloc[selected_patient - 1][base_features].to_dict()
                patient_name = data.iloc[selected_patient - 1]['name']  # Get the patient's name
                
                # Print selected patient and patient data for debugging
                print(f"Selected Patient: {selected_patient}")
                print(f"Patient Data: {patient_data}")
                
                diet_suggestion = suggest_diet_plan(patient_data)
                patient_diet_plans.append({
                    'Patient Name': patient_name,  # Use the patient's name
                    'Diet Name': diet_suggestion['Diet Name'],
                    'Description': diet_suggestion['Description'],
                    'Meal Timings': diet_suggestion['Meal Timings'],
                    'Recommended Foods': diet_suggestion['Recommended Foods'],
                    'Fasting Schedule': diet_suggestion['Fasting Schedule']
                })
        except ValueError:
            error_message = "Invalid selection. Please select a valid patient."

    # HTML template to display the diet plans
    html_template = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Intermittent Fasting</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                margin: 0;
                padding: 0;
                background-color: #f4f4f9;
                color: #333;
                display: flex;
                justify-content: center;
                align-items: center;
                height: 100vh;
            }
            .container {
                width: 80%;
                max-width: 800px;
                background-color: white;
                padding: 20px;
                border-radius: 8px;
                box-shadow: 0 0 10px rgba(0, 0, 0, 0.1);
            }
            h1 {
                color: #4CAF50;
                text-align: center;
            }
            form {
                margin-bottom: 20px;
                text-align: center;
            }
            label {
                font-weight: bold;
            }
            select, button {
                padding: 10px;
                margin: 10px 0;
                border: 1px solid #ccc;
                border-radius: 4px;
                width: 100%;
                max-width: 300px;
            }
            button {
                background-color: #4CAF50;
                color: white;
                cursor: pointer;
            }
            button:hover {
                background-color: #45a049;
            }
            table {
                width: 100%;
                border-collapse: collapse;
                margin-bottom: 20px;
            }
            th, td {
                border: 1px solid #ddd;
                padding: 8px;
                text-align: left;
            }
            th {
                background-color: #4CAF50;
                color: white;
            }
            tr:nth-child(even) {
                background-color: #f2f2f2;
            }
            .error {
                color: red;
                text-align: center;
                margin-bottom: 20px;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Suggested Diet Plans for Patients</h1>
            <form method="post">
                <label for="patient">Select Patient:</label>
                <select name="patient" id="patient">
                    <option value="0">Select Patient</option> <!-- Default option -->
                    {% for i in range(data.shape[0]) %}
                        <option value="{{ i + 1 }}" {% if selected_patient == i + 1 %}selected{% endif %}>{{ data.iloc[i]['name'] }}</option>
                    {% endfor %}
                </select>
                <button type="submit">Submit</button>
            </form>
            {% if error_message %}
                <p class="error">{{ error_message }}</p>
            {% endif %}
            {% if patient_diet_plans %}
                {% for plan in patient_diet_plans %}
                    <h2>Patient: {{ plan['Patient Name'] }}</h2> <!-- Display the patient's name -->
                    <table>
                        <tr><th>Category</th><th>Details</th></tr>
                        <tr><td>Diet Name</td><td>{{ plan['Diet Name'] }}</td></tr>
                        <tr><td>Description</td><td>{{ plan['Description'] }}</td></tr>
                        <tr><td>Meal Timings</td><td>{{ plan['Meal Timings'] }}</td></tr>
                        <tr><td>Recommended Foods</td><td>{{ plan['Recommended Foods'] }}</td></tr>
                        <tr><td>Fasting Schedule</td><td>{{ plan['Fasting Schedule'] }}</td></tr>
                    </table>
                {% endfor %}
            {% endif %}
        </div>
    </body>
    </html>
    """
    return render_template_string(html_template, patient_diet_plans=patient_diet_plans, data=data, selected_patient=selected_patient, error_message=error_message)

if __name__ == '__main__':
    app.run(debug=True)