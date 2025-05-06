import sys
# adding microdot path for simpler import
sys.path.insert(1, 'microdot/')
import asyncio
from microdot import Microdot
from controller import GreenHouse
import time
import sys

debugmode = False

app = Microdot()
controller = GreenHouse("kaskas", debugmode )

@app.route('/')
async def index(request):
    return 'Hello, Greenhouse! 🌱'

@app.get('/metrics')
async def index(request):
    return controller.getMetrics()

@app.post('/control')
async def control(request):
    # logic to set parameters go here
    for item, value in request.json.items():
        print(f"key:{item}, value:{value}")
        controller.setControlValue(item,value)
    return controller.getControlProfile()

async def lightLoop():
    while True:
        if controller.getControlProfile()['lightMode'] == 'lux':
              controller.lightLux()
              print(f"temp: {controller.getTemperature()}, humidity: {controller.getHumidity()}")
              await asyncio.sleep(1)
        else:
              controller.lightManual()
              await asyncio.sleep(1)

async def waterLoop():
    while True:
        if controller.getControlProfile()['waterMode'] == 'time':
              await controller.waterTimer()
              await asyncio.sleep(1)
        else:
              print("manual watering")
              await asyncio.sleep(1)

async def main():
    light = asyncio.create_task(lightLoop())
    water = asyncio.create_task(waterLoop())
    server = asyncio.create_task(app.run(port=80))

    # cleanup
    await asyncio.sleep(10)

asyncio.run(main())
