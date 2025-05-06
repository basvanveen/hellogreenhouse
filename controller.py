import sys
sys.path.insert(1, 'libs/')
import ujson as json
import time
import machine
from bh1750 import BH1750
import bme280_float as bme280
import asyncio

validLightModes = ['manual','lux']
validWaterModes = ['manual','time']
validStates     = ['on','off']

class GreenHouse:

    def __init__(self, name, debugmode):
        self.debugmode = debugmode
        self.currentLux = 0
        self.currentCelsius = 0
        self.coolDown = 1
        self.offset = 0 if debugmode else 2
        print(f"Instantiating GreenHouse: {name}")
        with open('settings/firebeetle2.json', 'r') as f:
            self.controlProfile = json.load(f)
            print(json.dumps(self.controlProfile))
        if not self.debugmode:
            self.i2c = machine.SoftI2C(scl=machine.Pin(self.controlProfile['luxSclPin']),
                                       sda=machine.Pin(self.controlProfile['luxSdaPin']),
                                       freq=400000)
            self.bme = bme280.BME280(i2c=self.i2c)

    def getControlProfile(self):
        return self.controlProfile
    

    def getTemperature(self):
        if self.debugmode:
              return 123456 # running in debug just output a value 
        return self.bme.values[0]

    def getPressure(self):
        if self.debugmode:
              return 123456 # running in debug just output a value 
        return self.bme.values[1]

    def getHumidity(self):
        if self.debugmode:
              return 123456 # running in debug just output a value 
        return self.bme.values[2]

    def getTime(self):
        return f"{(time.localtime()[3]+self.offset)%24:02d}:{time.localtime()[4]:02d}"
    
    def getMetrics(self):
          metrics = self.controlProfile.copy()
          metrics['currentLux']      = self.currentLux
          metrics['currentCelsius']  = self.getTemperature()
          metrics['currentHumidity'] = self.getHumidity()
          metrics['currentPressure'] = self.getPressure()          
          return metrics
    
    def getLux(self):
        if self.debugmode:
              return 123456 # running in debug just output a value 

        light_sensor = BH1750(bus=self.i2c, addr=0x23)
        try:
        # Read lux every 2 seconds
            self.currentLux = light_sensor.luminance(BH1750.CONT_HIRES_1)
            print(f"lux measured: {self.currentLux}")
            return self.currentLux
        except Exception as e:
            # Handle any exceptions during sensor reading
            print("can't read lux")
            return 13371337

    async def waterTimer(self):
          print(f"Water Operations: {self.getTime()} allowedTimes: {self.controlProfile['waterTimes']}")
          if self.getTime() in self.controlProfile['waterTimes'] and (self.coolDown > 0):
                # Resetting coolDown
                self.coolDown = 0
                print("Watering 🪴💧")
                if not self.debugmode:
                    machine.Pin(self.controlProfile['waterValve1Pin'], machine.Pin.OUT).value(0)
                    machine.Pin(self.controlProfile['waterValve2Pin'], machine.Pin.OUT).value(0)
                self.controlProfile['waterValve1'] = "on"
                self.controlProfile['waterValve2'] = "on"
                await asyncio.sleep(self.controlProfile['waterDurationSeconds'])
                self.coolDown -= (60 - self.controlProfile['waterDurationSeconds'])
          else:
                print(f"Not watering 🚱, coolDown timer: {self.coolDown} ")
                if not self.debugmode:
                    machine.Pin(self.controlProfile['waterValve1Pin'], machine.Pin.OUT).value(1)
                    machine.Pin(self.controlProfile['waterValve2Pin'], machine.Pin.OUT).value(1) 
                self.controlProfile['waterValve1'] = "off"
                self.controlProfile['waterValve2'] = "off"
                time.sleep(1)
          # coolDown timer to avoid multiple occurences per minute
          self.coolDown += 1

    def lightLux(self):
          print("lux Operations")
          if self.getLux() < self.controlProfile['ledLuxLevel']:
                if not self.debugmode:
                    machine.Pin(self.controlProfile['ledStrip1Pin'], machine.Pin.OUT).value(0)
                    machine.Pin(self.controlProfile['ledStrip2Pin'], machine.Pin.OUT).value(0)
                self.controlProfile['ledStrip1'] = "on"
                self.controlProfile['ledStrip2'] = "on"
          else:
                if not self.debugmode:
                    machine.Pin(self.controlProfile['ledStrip1Pin'], machine.Pin.OUT).value(1)
                    machine.Pin(self.controlProfile['ledStrip2Pin'], machine.Pin.OUT).value(1)    
                self.controlProfile['ledStrip1'] = "off"
                self.controlProfile['ledStrip2'] = "off"           

    def lightManual(self):
          print("manual Operations")   
    
    def setControlValue(self,name, value):
        """ set parameters for controller I/O
            lots of if statements due to lack of 
            schema validation or using enum or even
            case switch in micropython atm...
        """
        print(f"name: {name} value: {value}")
        if   name   == 'lightMode':
                if value in validLightModes:
                    self.controlProfile['lightMode'] = value
        elif name   == 'temperaturePin':
                self.controlProfile['temperaturePin'] = int(value)
        elif name   == 'waterMode':
                if value in validWaterModes:
                    self.controlProfile['waterMode'] = value
        elif name   == 'waterDurationSeconds':
                self.controlProfile['waterDurationSeconds'] = int(value)
        elif name   == 'waterTimes':
                self.controlProfile['waterTimes'] = value
        elif name   == 'waterValve1':
                if value in validStates:
                    self.controlProfile['waterValve1'] = value
        elif name   == 'waterValve2':
                if value in validStates:
                    self.controlProfile['waterValve2'] = value
        elif name   == 'waterValve1Pin':
                self.controlProfile['waterValve1Pin'] = int(value)
        elif name   == 'waterValve2Pin':
                self.controlProfile['waterValve2Pin'] = int(value)
        elif name   == 'ledLuxLevel':
                self.controlProfile['ledLuxLevel'] = int(value)
        elif name   == 'ledLuxBackoffSeconds':
                self.controlProfile['ledLuxBackoffSeconds'] =int(value)
        elif name   == 'ledStrip1':
                if value in validStates:
                    self.controlProfile['ledStrip1'] = value
        elif name   == 'ledStrip1':
                if value in validStates:
                    self.controlProfile['ledStrip2'] = value
        elif name   == 'ledStrip1Pin':
                self.controlProfile['ledStrip1Pin'] = int(value)
        elif name   == 'ledStrip2Pin':
                self.controlProfile['ledStrip2Pin'] = int(value)
        else:
            return f"{{'message': '{name} unknown parameter'"
        return self.controlProfile