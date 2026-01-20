import network
import uasyncio as asyncio
import struct
import hashlib
import binascii
import time
from machine import Pin, PWM

# ================= LED =================
led = Pin(2, Pin.OUT)
led.on()

# ================= SERVO =================
servo = PWM(Pin(18), freq=50)

SERVO_MIN_US = 700
SERVO_MAX_US = 2300

LEFT_POS   = 45
CENTER_POS = 90
RIGHT_POS  = 135

STEP_DEG = 3
STEP_DELAY_MS = 20
SERVO_IDLE_TIMEOUT = 1.2

current_angle = CENTER_POS
target_angle = CENTER_POS
last_move_time = time.time()
servo_active = False

def angle_to_duty(angle):
    angle = max(LEFT_POS, min(RIGHT_POS, angle))
    us = SERVO_MIN_US + (SERVO_MAX_US - SERVO_MIN_US) * \
         (angle - LEFT_POS) / (RIGHT_POS - LEFT_POS)
    return int(us * 1023 / 20000)

def servo_write(angle):
    global servo_active
    servo.duty(angle_to_duty(angle))
    servo_active = True

def servo_off():
    global servo_active
    servo.duty(0)
    servo_active = False

servo_write(CENTER_POS)

# ================= INDICATOR LEDS =================
ind_left = Pin(16, Pin.OUT)
ind_right = Pin(17, Pin.OUT)

ind_left.off()
ind_right.off()

indicator_task = None

# ================= WIFI AP =================
ap = network.WLAN(network.AP_IF)
ap.active(True)
ap.config(
    essid="ESP32_RC",
    password="12345678",
    authmode=network.AUTH_WPA_WPA2_PSK
)

while not ap.active():
    pass

print("AP IP:", ap.ifconfig()[0])

HTML = """<!DOCTYPE html>
<html>
<head>
<meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=1, user-scalable=no">
<title>ESP32 RC</title>
<style>
* {
  box-sizing: border-box;
  touch-action: none;
  user-select: none;
}
html, body {
  margin: 0;
  padding: 0;
  width: 100%;
  height: 100%;
  background: #000;
  overflow: hidden;
  font-family: sans-serif;
}

.app {
  height: 100svh;
  display: flex;
  flex-direction: column;
}

/* ---------- TOP BAR ---------- */
.top {
  flex: 0 0 auto;
  display: flex;
  justify-content: center;
  gap: 10px;
  padding: 8px;
}

.top button {
  flex: 1;
  max-width: 120px;
  height: 48px;
  font-size: 14px;
  background: #444;
  color: #fff;
  border: 2px solid #888;
}

/* ---------- MAIN AREA ---------- */
.main {
  flex: 1;
  display: flex;
}

/* ---------- COLUMNS ---------- */
.column {
  flex: 1;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
}

.label {
  color: #aaa;
  margin-bottom: 10px;
  font-size: 16px;
}

/* ---------- BUTTONS ---------- */
.pad {
  display: flex;
  gap: 12px;
}

.big {
  width: min(30vw, 120px);
  height: min(30vw, 120px);
  font-size: 42px;
  background: #222;
  border-radius: 12px;
}

.steer {
  color: #0af;
  border: 3px solid #0af;
}

.motor-fwd {
  color: #0f0;
  border: 3px solid #f80;
}

.motor-back {
  color: #f80;
  border: 3px solid #f80;
}

.motor-stop {
  color: #f00;
  border: 3px solid #f00;
}

button:active {
  transform: scale(0.95);
  background: #555;
}

.indicators {
  display: flex;
  gap: 8px;
  margin-bottom: 12px;
}

.indicators button {
  width: 48px;
  height: 36px;
  font-size: 18px;
  background: #111;
  color: #ff0;
  border: 2px solid #ff0;
  border-radius: 6px;
}
</style>
</head>

<body>
<div class="app">

  <!-- TOP CONTROLS -->
  <div class="top">
    <button id="light">LIGHT</button>
    <button id="horn">HORN</button>
  </div>

  <!-- MAIN CONTROLS -->
  <div class="main">

    <!-- STEERING -->
    
    <!-- INDICATORS -->
    <div class="column">

      <div class="indicators">
        <button id="ind_left">◀</button>
        <button id="ind_both">◀▶</button>
        <button id="ind_right">▶</button>
      </div>
      <div class="pad">
        <button id="left" class="big steer">←</button>
        <button id="right" class="big steer">→</button>
      </div>
    </div>

    <!-- MOTOR -->
    <div class="column">
      <div class="pad">
        <button id="forward" class="big motor-fwd">▲</button>
        <button id="back" class="big motor-back">▼</button>
      </div>
    </div>

  </div>
</div>

<script>
let ws = new WebSocket("ws://192.168.4.1/ws");

function send(m){ if(ws.readyState===1) ws.send(m); }

function bind(id, press, release=null){
  let b=document.getElementById(id);
  b.ontouchstart=e=>{e.preventDefault();send(press);}
  b.ontouchend=e=>{e.preventDefault();if(release)send(release);}
  b.onmousedown=()=>send(press);
  b.onmouseup=()=>{if(release)send(release);}
  b.onmouseleave=()=>{if(release)send(release);}
}

bind("left","LEFT","CENTER");
bind("right","RIGHT","CENTER");
bind("forward","FORWARD","STOP");
bind("back","BACK","STOP");
bind("light","LIGHT");
bind("horn","HORN");
bind("ind_left","IND_LEFT");
bind("ind_right","IND_RIGHT");
bind("ind_both","IND_BOTH");
</script>
</body>
</html>
"""


# ================= WEBSOCKET =================
def ws_accept(key):
    GUID = "258EAFA5-E914-47DA-95CA-C5AB0DC85B11"
    sha1 = hashlib.sha1((key + GUID).encode()).digest()
    return binascii.b2a_base64(sha1).strip().decode()

async def ws_recv(reader):
    hdr = await reader.readexactly(2)
    length = hdr[1] & 0x7F
    if length == 126:
        length = struct.unpack(">H", await reader.readexactly(2))[0]
    mask = await reader.readexactly(4)
    data = bytearray(await reader.readexactly(length))
    for i in range(length):
        data[i] ^= mask[i % 4]
    return data.decode()

# ================= SERVO TASK =================
async def servo_task():
    global current_angle, last_move_time
    while True:
        if current_angle != target_angle:
            last_move_time = time.time()
            current_angle += STEP_DEG if current_angle < target_angle else -STEP_DEG
            servo_write(current_angle)
        else:
            if servo_active and time.time() - last_move_time > SERVO_IDLE_TIMEOUT:
                servo_off()
        await asyncio.sleep_ms(STEP_DELAY_MS)

# ================= INDICATOR TASK =================

async def blink_indicator(left=False, right=False, duration=5):
    end_time = time.time() + duration
    state = False
    while time.time() < end_time:
        state = not state
        if left:
            ind_left.value(state)
        if right:
            ind_right.value(state)
        await asyncio.sleep_ms(400)

    # turn OFF after timeout
    ind_left.off()
    ind_right.off()

def start_indicator(left=False, right=False, duration=5):
    global indicator_task
    if indicator_task:
        indicator_task.cancel()
    ind_left.off()
    ind_right.off()
    indicator_task = asyncio.create_task(
        blink_indicator(left, right, duration)
    )

# ================= SERVER =================
async def handle_client(reader, writer):
    global target_angle
    try:
        req = await reader.readline()
        is_ws = b"GET /ws" in req

        headers = {}
        while True:
            line = await reader.readline()
            if line == b"\r\n":
                break
            k, v = line.decode().split(":", 1)
            headers[k.strip()] = v.strip()

        if is_ws:
            accept = ws_accept(headers["Sec-WebSocket-Key"])
            await writer.awrite(
                "HTTP/1.1 101 Switching Protocols\r\n"
                "Upgrade: websocket\r\n"
                "Connection: Upgrade\r\n"
                f"Sec-WebSocket-Accept: {accept}\r\n\r\n"
            )

            while True:
                msg = await ws_recv(reader)
                print("Received:", msg)  # Debug print
                if msg == "LEFT":
                    target_angle = LEFT_POS
                elif msg == "RIGHT":
                    target_angle = RIGHT_POS
                elif msg == "CENTER":
                    target_angle = CENTER_POS
                # Filler buttons - add your logic here
                elif msg == "FORWARD":
                    print("Forward pressed")
                elif msg == "BACK":
                    print("Back pressed")
                elif msg == "STOP":
                    print("Stop pressed")
                elif msg == "LIGHT":
                    print("Light pressed")
                elif msg == "HORN":
                    print("Horn pressed")
                elif msg == "TURBO":
                    print("Turbo pressed")
                elif msg == "IND_LEFT":
                    print("Left indicator pressed")
                    start_indicator(left=True, duration=5)
                elif msg == "IND_RIGHT":
                    print("Right indicator pressed")
                    start_indicator(right=True, duration=5)
                elif msg == "IND_BOTH":
                    print("Both indicator pressed")
                    start_indicator(left=True, right=True, duration=6)
        else:
            await writer.awrite(
                "HTTP/1.1 200 OK\r\nContent-Type: text/html\r\n\r\n"
            )
            await writer.awrite(HTML)

    except:
        pass
    finally:
        await writer.aclose()

# ================= MAIN =================
async def main():
    asyncio.create_task(servo_task())
    server = await asyncio.start_server(handle_client, "0.0.0.0", 80)
    print("Server running")
    await server.wait_closed()

asyncio.run(main())