from flask import Flask, render_template
from flask_socketio import SocketIO, emit # type: ignore

app = Flask(__name__)
app.config['SECRET_KEY'] = 'race_secret'
socketio = SocketIO(app)

race_state = {
    "status": "stopped",  # started, safety_car, yellow_flag, red_flag
    "sector": None,
    "penalties": [],
    "raceControl": [],
    "safety_active": False
}

@app.route('/leaderboard')
def leaderboard():
    return render_template('leaderboard.html')

@app.route('/admin')
def admin():
    return render_template('admin.html')

@app.route('/')
def speedometer():
    return render_template('speedometer.html')

# ----- EVENT SOCKET -----
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

@socketio.on('update_lap')
def handle_update_lap(data):
    emit('lap_update', data, broadcast=True)

@socketio.on('update_leaderboard')
def handle_update_leaderboard(data):
    # data = [{pos:1, team_logo:'ferrari.png', name:'LEC', gap:'Leader'}, ...]
    emit('leaderboard_update', data, broadcast=True)
    
@socketio.on('session_change')
def handle_session_change(data):
    # data = { "session": "RACE" }
    emit('session_update', data, broadcast=True)



@socketio.on('flag_event')
def handle_flag(data):
    # data = { type: 'yellow'/'red'/'safety'/'green', sector: 1/2/3 }
    flag_type = data['type']
    race_state["sector"] = data.get('sector')

    if flag_type == "safety":
        # toggle safety car
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

@socketio.on('raceControl')
def handle_raceControl(data):
    race_state["raceControl"].append(data)
    emit('raceControl_update', data, broadcast=True)

if __name__ == '__main__':
    socketio.run(app, debug=True, port=5002, allow_unsafe_werkzeug=True)
