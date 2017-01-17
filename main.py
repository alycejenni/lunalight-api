from flask import Flask
from flask import jsonify, request, abort
import json
from models import *

app = Flask(__name__)

@app.route('/')
def simple():
    npixels = request.args.get("npixels", default=None)
    if not npixels:
        abort(404)
    else:
        npixels = int(npixels)
        moon = LunarData()
        tides = TidalData()
        data = {}
        normal_led = NormalLED(tides=tides, moon=moon)
        data["normal"] = {"r": normal_led.r, "g": normal_led.g, "b": normal_led.b, "tuple": normal_led.tuple}
        if (npixels * moon.pc_complete) % 1 != 0:
            partial = (npixels * moon.pc_complete) - int(npixels * moon.pc_complete)
            partial_led = PartialLED(tides=tides, moon=moon, partial=partial)
            data["partial"] = {"r": partial_led.r, "g": partial_led.g, "b": partial_led.b, "tuple": partial_led.tuple}
        data["moonpc"] = moon.pc_complete
        data["moonstage"] = moon.stage
        return json.dumps(data)

if __name__ == '__main__':
    app.run()