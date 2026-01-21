import network
import uasyncio as asyncio
import struct
import hashlib
import binascii
from machine import Pin


class MPCKeys:
    # ---------- FACE BUTTONS ----------
    LFT = "BTN_LFT"
    RGT = "BTN_RGT"
    FWD = "BTN_FWD"
    BWD = "BTN_BWD"

    # ---------- INDICATOR ----------
    IND_R = "IND_R"
    IND_L = "IND_L"
    IND_LR = "IND_LR"

    # ---------- MISSALANIOUS ----------
    LIGHT = "BTN_LIGHT"
    HORN = "BTN_HORN"

    LB1 = "BTN_LB1"
    LB2 = "BTN_LB2"
    LB3 = "BTN_LB3"
    LB4 = "BTN_LB4"


# LED indicating that esp32 is on
led = Pin(2, Pin.OUT)
led.on()

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

HTML = f"""<!DOCTYPE html>
<html>
<head>
<meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=1, user-scalable=no">
<title>ESP32 RC</title>

<style>
:root {{
  --bg: #0b0e14;
  --panel: #121826;
  --btn: #1a2133;
  --accent: #4cc9f0;
  --warn: #f4a261;
  --text: #e5e7eb;
  --border: #2a3558;
}}

* {{
  box-sizing: border-box;
  touch-action: none;
  user-select: none;
}}

html, body {{
  margin: 0;
  width: 100%;
  height: 100%;
  background: var(--bg);
  color: var(--text);
  font-family: system-ui, sans-serif;
}}

.app {{
  height: 100svh;
  display: flex;
  flex-direction: column;
  margin: 20px;
  margin-top: 40px;
  margin-bottom: 40px;
}}

/* ---------- TOP BAR ---------- */
.top {{
  display: flex;
  gap: 12px;
  padding: 12px 16px;
}}

.top button {{
  flex: 1;
  height: 44px;
  background: var(--btn);
  border: 1px solid var(--border);
  color: var(--text);
  font-weight: 600;
  border-radius: 10px;
}}

/* ---------- MAIN ---------- */
.main {{
  flex: 1;
  display: flex;
  justify-content: space-between;
  padding: 16px;
  gap: 16px;
}}

/* ---------- PANELS ---------- */
.panel {{
  background: var(--panel);
  border-radius: 16px;
  padding: 16px;
  display: flex;
  flex-direction: column;
  justify-content: flex-end;
}}

/* ---------- LEFT (STEERING) ---------- */
.left {{
  width: 35%;
  align-items: center;
}}

.indicator {{
  display: flex;
  gap: 8px;
}}

.indicator button {{
  width: 48px;
  height: 36px;
  border-radius: 8px;
  border: 1px solid var(--accent);
  background: transparent;
  color: var(--accent);
}}

.steer {{
  display: flex;
  gap: 14px;
  padding: 16px;
}}

.big {{
  width: 80px;
  height: 80px;
  font-size: 34px;
  border-radius: 14px;
  border: 2px solid var(--accent);
  background: var(--btn);
  color: var(--accent);
}}

/* ---------- CENTER ---------- */
.center {{
  width: 30%;
  align-items: center;
}}

.buttons {{
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 10px;
}}

.circle {{
  width: 56px;
  height: 56px;
  border-radius: 50%;
  border: 2px solid var(--accent);
  background: var(--btn);
  color: var(--accent);
  font-weight: 600;
}}

.motor {{
  display: flex;
  gap: 14px;
  padding: 16px;
}}

.motor button {{
  width: 80px;
  height: 80px;
  font-size: 32px;
  border-radius: 14px;
  border: 2px solid var(--warn);
  background: var(--btn);
  color: var(--warn);
}}

/* ---------- INTERACTION ---------- */
button:active {{
  transform: scale(0.94);
  background: #222b44;
}}

button.pressed {{
  box-shadow: 0 0 12px currentColor;
  background: #2a3a5a;
}}

.big.pressed {{
  background: rgba(76, 201, 240, 0.15);
  box-shadow: inset 0 0 8px rgba(76, 201, 240, 0.3), 0 0 16px rgba(76, 201, 240, 0.4);
}}

.circle.pressed {{
  background: rgba(76, 201, 240, 0.15);
  box-shadow: 0 0 12px rgba(76, 201, 240, 0.6);
}}

.motor button.pressed {{
  background: rgba(244, 162, 97, 0.15);
  box-shadow: inset 0 0 8px rgba(244, 162, 97, 0.3), 0 0 16px rgba(244, 162, 97, 0.4);
}}

.indicator button.pressed {{
  background: rgba(76, 201, 240, 0.2);
  box-shadow: 0 0 10px rgba(76, 201, 240, 0.5);
}}

/* ---------- MOBILE ---------- */
@media (max-width: 700px) {{
  .main {{
    flex-direction: column;
  }}

  .left, .center {{
    width: 100%;
    align-items: center;
  }}

  .steer, .motor {{
    justify-content: center;
  }}
}}
</style>
</head>

<body>
<div class="app">

  <div class="top">
    <button id="btn_{MPCKeys.LIGHT}">LIGHT</button>
    <button id="btn_{MPCKeys.HORN}">HORN</button>
  </div>

  <div class="main">

    <!-- STEERING -->
    <div class="panel left">
      <div class="indicator">
        <button id="btn_{MPCKeys.IND_L}">◀</button>
        <button id="btn_{MPCKeys.IND_LR}">◀▶</button>
        <button id="btn_{MPCKeys.IND_R}">▶</button>
      </div>

      <div class="steer">
        <button id="btn_{MPCKeys.LFT}" class="big">◀</button>
        <button id="btn_{MPCKeys.RGT}" class="big">▶</button>
      </div>
    </div>

    <!-- CENTER -->
    <div class="panel center">
      <div class="buttons">
        <button id="btn_{MPCKeys.LB1}" class="circle">B1</button>
        <button id="btn_{MPCKeys.LB2}" class="circle">B2</button>
        <button id="btn_{MPCKeys.LB3}" class="circle">B3</button>
        <button id="btn_{MPCKeys.LB4}" class="circle">B4</button>
      </div>

      <div class="motor">
        <button id="btn_{MPCKeys.FWD}">▲</button>
        <button id="btn_{MPCKeys.BWD}">▼</button>
      </div>
    </div>

  </div>
</div>

<script>
let ws = new WebSocket("ws://192.168.4.1/ws");

function send(m){{ if(ws.readyState===1) ws.send(m); }}

function bind(id, key){{
  let b=document.getElementById(id);
  b.ontouchstart=e=>{{e.preventDefault();b.classList.add("pressed");send(key+":pressed");}}
  b.ontouchend=e=>{{e.preventDefault();b.classList.remove("pressed");send(key+":released");}}
  b.onmousedown=()=>{{b.classList.add("pressed");send(key+":pressed");}}
  b.onmouseup=()=>{{b.classList.remove("pressed");send(key+":released");}}
  b.onmouseleave=()=>{{b.classList.remove("pressed");send(key+":released");}}
}}

[
 ["{MPCKeys.LFT}","{MPCKeys.LFT}"],["{MPCKeys.RGT}","{MPCKeys.RGT}"],
 ["{MPCKeys.FWD}","{MPCKeys.FWD}"],["{MPCKeys.BWD}","{MPCKeys.BWD}"],
 ["{MPCKeys.LIGHT}","{MPCKeys.LIGHT}"],["{MPCKeys.HORN}","{MPCKeys.HORN}"],
 ["{MPCKeys.IND_L}","{MPCKeys.IND_L}"],["{MPCKeys.IND_R}","{MPCKeys.IND_R}"],["{MPCKeys.IND_LR}","{MPCKeys.IND_LR}"],
 ["{MPCKeys.LB1}","{MPCKeys.LB1}"],["{MPCKeys.LB2}","{MPCKeys.LB2}"],
 ["{MPCKeys.LB3}","{MPCKeys.LB3}"],["{MPCKeys.LB4}","{MPCKeys.LB4}"]
].forEach(([id,key])=>bind("btn_"+id,key));
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


class _ButtonState:
    def __init__(self):
        self.down = False
        self.pressed = False
        self.released = False


class Input:
    def __init__(self):
        self._buttons = {}
        self._axes = {}

    def _btn(self, code):
        if code not in self._buttons:
            self._buttons[code] = _ButtonState()
        return self._buttons[code]

    # called by remote / ws / radio 
    def emit_button(self, code, value):
        b = self._btn(code)
        b.pressed  = value and not b.down
        b.released = (not value) and b.down
        b.down = bool(value)


    

    # ---- user polling API ----
    def is_down(self, code):
        return self._btn(code).down

    def is_pressed(self, code):
        return self._btn(code).pressed

    def is_released(self, code):
        return self._btn(code).released

    #resets pressed and released keys
    def end_frame(self):
        for b in self._buttons.values():
            b.pressed = False
            b.released = False


class RemoteController:
    def __init__(self, port=80):
        self.port = port
        self.input = Input()
        self.server = None
        
    async def start(self):
        """Start the WebSocket server"""
        self.server = await asyncio.start_server(
            self._handle_client, "0.0.0.0", self.port
        )
        print(f"Server started on port {self.port}")
        await self.server.wait_closed()
    
    async def _handle_client(self, reader, writer):
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
                    print("Received:", msg)
                    
                    # Parse key and state
                    if ":" in msg:
                        key, state = msg.split(":")
                    else:
                        key = msg
                        state = "pressed"
                    
                    # Update input state
                    value = 1 if state == "pressed" else 0
                    self.input.emit_button(key, value)
                    
            else:
                await writer.awrite(
                    "HTTP/1.1 200 OK\r\nContent-Type: text/html\r\n\r\n"
                )
                await writer.awrite(HTML)

        except:
            pass
        finally:
            await writer.aclose()
    
    def update(self):
        self.input.end_frame()
    
    def is_pressed(self, key):
        return self.input.is_pressed(key)
    
    def is_released(self, key):
        return self.input.is_released(key)
    
    def is_down(self, key):
        return self.input.is_down(key)