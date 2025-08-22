from flask import Flask, render_template, request, session, redirect, url_for
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'your-secret-key-here'

currency_rates = {
    "USD": 1.0,
    "EUR": 1.09,
    "GBP": 1.28,
    "CAD": 0.73,
    "DKK": 0.15,
    "JPY": 0.0064,
    "CNY": 0.14,
    "ARS": 0.0011,
    "BRL": 0.19,
    "INR": 0.012,
}

def calculate_rate_per_second(rate_usd, rate_type, hours_per_day):
    """Convert a USD rate to rate per second based on rate_type and hours/day"""
    if rate_type == "hourly":
        return rate_usd / 3600
    elif rate_type == "daily":
        return rate_usd / (hours_per_day * 3600)
    elif rate_type == "weekly":
        return rate_usd / (hours_per_day * 5 * 3600)
    elif rate_type == "biweekly":
        return rate_usd / (hours_per_day * 10 * 3600)
    elif rate_type == "monthly":
        return rate_usd / (hours_per_day * 22 * 3600)
    elif rate_type == "yearly":
        return rate_usd / (hours_per_day * 252 * 3600)
    return 0

@app.route('/')
def index():
    session.clear()
    return render_template('index.html')

@app.route('/add_participant', methods=['POST'])
def add_participant():
    data = request.get_json()
    if 'batch' in data:
        session['participants'] = data['batch']
    if 'meetingName' in data:
        session['meeting_name'] = data['meetingName']
    if 'meetingEmail' in data:
        session['meeting_email'] = data['meetingEmail']
    session.modified = True
    return {'success': True}

@app.route('/meeting')
def meeting():
    if 'participants' not in session or not session['participants']:
        return redirect(url_for('index'))

    total_cost_per_second = 0
    # DEBUG: Print for troubleshooting
    # print("Participants", session['participants'])

    for p in session['participants']:
        rate = float(p.get('rate', 0))
        rate_type = p.get('rateType') or p.get('rate_type')
        currency = p.get('currency', 'USD')
        currency_mult = currency_rates.get(currency, 1.0)
        rate_usd = rate * currency_mult  # <--- CONVERSION TO USD
        if rate_type == 'hourly':
            hours_per_day = 8
        else:
            hours_per_day = float(p.get('hoursPerDay', p.get('hours_per_day', 8)))
        count = int(p.get('count', 1))
        rate_per_second = calculate_rate_per_second(rate_usd, rate_type, hours_per_day)
        total_cost_per_second += rate_per_second * count

    session['meeting_start'] = datetime.now().isoformat()
    session['total_cost_per_second'] = total_cost_per_second
    session.modified = True

    meeting_name = session.get('meeting_name', 'Untitled Meeting')
    return render_template('meeting.html', cost_per_second=total_cost_per_second, meeting_name=meeting_name)

@app.route('/stop_meeting', methods=['POST'])
def stop_meeting():
    if 'meeting_start' not in session:
        return redirect(url_for('index'))
    meeting_end = datetime.now()
    meeting_start = datetime.fromisoformat(session['meeting_start'])
    duration_seconds = (meeting_end - meeting_start).total_seconds()
    total_cost = session['total_cost_per_second'] * duration_seconds
    session['meeting_duration'] = duration_seconds
    session['total_cost'] = total_cost
    session['meeting_end'] = meeting_end.isoformat()
    session.modified = True
    return redirect(url_for('summary'))

@app.route('/summary')
def summary():
    if 'meeting_duration' not in session:
        return redirect(url_for('index'))

    duration_seconds = session['meeting_duration']
    duration_minutes = int(duration_seconds // 60)
    duration_secs = int(duration_seconds % 60)
    meeting_start = datetime.fromisoformat(session['meeting_start']).strftime('%Y-%m-%d %H:%M:%S')
    meeting_end = datetime.fromisoformat(session['meeting_end']).strftime('%Y-%m-%d %H:%M:%S')
    meeting_name = session.get('meeting_name', 'Untitled Meeting')
    meeting_email = session.get('meeting_email', '')
    cost_per_second = session.get('total_cost_per_second', 0)

    return render_template(
        'summary.html',
        duration_minutes=duration_minutes,
        duration_seconds=duration_secs,
        total_cost=session['total_cost'],
        meeting_start=meeting_start,
        meeting_end=meeting_end,
        meeting_name=meeting_name,
        meeting_email=meeting_email,
        cost_per_second=cost_per_second,
        participant_table=session['participants']
    )

if __name__ == '__main__':
    app.run(debug=True)
