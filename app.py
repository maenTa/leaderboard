from flask import Flask, render_template
from flask_socketio import SocketIO, emit
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'race_secret'
socketio = SocketIO(app, async_mode='eventlet')

race_state = {
    "status": "stopped",  # started, safety_car, yellow_flag, red_flag
    "sector": None,
    "penalties": [],
    "safety_active": False
}

@app.route('/')
def leaderboard():
    return render_template('leaderboard.html')

@app.route('/admin')
def admin():
    return render_template('admin.html')

# ----- SOCKET EVENTS -----
@socketio.on('start_lights')
def handle_start_lights():
    emit('lights_start', broadcast=True)

@socketio.on('race_start')
def handle_race_start():
    race_state["status"] = "started"
    emit('race_started', broadcast=True)

@socketio.on('start_formation_lap')
def handle_formation_lap():
    emit('formation_lap', broadcast=True)

@socketio.on('flag_event')
def handle_flag(data):
    flag_type = data['type']
    race_state["sector"] = data.get('sector')

    if flag_type == "safety":
        race_state["safety_active"] = not race_state["safety_active"]
        if race_state["safety_active"]:
            race_state["status"] = "safety_car"
            emit('flag_update', {"type": "safety"}, broadcast=True)
        else:
            race_state["status"] = "safety_ending"
            emit('flag_update', {"type": "safety_end"}, broadcast=True)
    elif flag_type == "green":
        race_state["status"] = "green_flag"
        race_state["safety_active"] = False
        emit('flag_update', {"type": "green"}, broadcast=True)
    else:
        race_state["status"] = flag_type
        emit('flag_update', data, broadcast=True)

@socketio.on('penalty')
def handle_penalty(data):
    race_state["penalties"].append(data)
    emit('penalty_update', data, broadcast=True)

if __name__ == '__main__':
    # Railway automatically sets the PORT environment variable
    port = int(os.environ.get("PORT", 8080))
    socketio.run(app, host="0.0.0.0", port=port, debug=True, allow_unsafe_werkzeug=True)
