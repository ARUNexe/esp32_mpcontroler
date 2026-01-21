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
* {{
  box-sizing: border-box;
  touch-action: none;
  user-select: none;
}}
html, body {{
  margin: 0;
  padding: 0;
  width: 100%;
  height: 100%;
  background: #000;
  overflow: hidden;
  font-family: sans-serif;
}}

.app {{
  height: 100svh;
  display: flex;
  flex-direction: column;
}}

/* ---------- TOP BAR ---------- */
.top {{
  flex: 0 0 auto;
  display: flex;
  justify-content: center;
  gap: 10px;
  padding: 8px;
}}

.top button {{
  flex: 1;
  max-width: 120px;
  height: 48px;
  font-size: 14px;
  background: #444;
  color: #fff;
  border: 2px solid #888;
}}

/* ---------- MAIN AREA ---------- */
.main {{
  flex: 1;
  display: flex;
}}

/* ---------- COLUMNS ---------- */
.column {{
  flex: 1;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
}}

.label {{
  color: #aaa;
  margin-bottom: 10px;
  font-size: 16px;
}}

/* ---------- BUTTONS ---------- */
.pad {{
  display: flex;
  gap: 12px;
}}

.big {{
  width: min(30vw, 120px);
  height: min(30vw, 120px);
  font-size: 42px;
  background: #222;
  border-radius: 12px;
}}

.steer {{
  color: #0af;
  border: 3px solid #0af;
}}

.motor-fwd {{
  color: #0f0;
  border: 3px solid #f80;
}}

.motor-back {{
  color: #f80;
  border: 3px solid #f80;
}}

.motor-stop {{
  color: #f00;
  border: 3px solid #f00;
}}

button:active {{
  transform: scale(0.95);
  background: #555;
}}

.indicators {{
  display: flex;
  gap: 8px;
  margin-bottom: 12px;
}}

.indicators button {{
  width: 48px;
  height: 36px;
  font-size: 18px;
  background: #111;
  color: #ff0;
  border: 2px solid #ff0;
  border-radius: 6px;
}}
</style>
</head>

<body>
<div class="app">

  <!-- TOP CONTROLS -->
  <div class="top">
    <button id="btn_{MPCKeys.LIGHT}">LIGHT</button>
    <button id="btn_{MPCKeys.HORN}">HORN</button>
  </div>

  <!-- MAIN CONTROLS -->
  <div class="main">

    <div class="column">

      <!-- INDICATOR -->
      <div class="indicators">
        <button id="btn_{MPCKeys.IND_L}">◀</button>
        <button id="btn_{MPCKeys.IND_LR}">◀▶</button>
        <button id="btn_{MPCKeys.IND_R}">▶</button>
      </div>
      <!-- LEFT PAD -->
      <div class="pad">
        <button id="btn_{MPCKeys.LFT}" class="big steer">←</button>
        <button id="btn_{MPCKeys.RGT}" class="big steer">→</button>
      </div>
    </div>

    <!-- RIGHT PAD -->
    <div class="column">
      <div class="pad">
        <button id="btn_{MPCKeys.FWD}" class="big motor-fwd">▲</button>
        <button id="btn_{MPCKeys.BWD}" class="big motor-back">▼</button>
      </div>
    </div>

  </div>
</div>

<script>
let ws = new WebSocket("ws://192.168.4.1/ws");
const KEYS = {{
  LFT: "{MPCKeys.LFT}",
  RGT: "{MPCKeys.RGT}",
  FWD: "{MPCKeys.FWD}",
  BWD: "{MPCKeys.BWD}",
  IND_L: "{MPCKeys.IND_L}",
  IND_R: "{MPCKeys.IND_R}",
  IND_LR: "{MPCKeys.IND_LR}",
  LIGHT: "{MPCKeys.LIGHT}",
  HORN: "{MPCKeys.HORN}",
}};

function send(m){{ if(ws.readyState===1) ws.send(m); }}

function bind(id, key){{
  let b=document.getElementById(id);
  b.ontouchstart=e=>{{e.preventDefault();send(key + ":pressed");}}
  b.ontouchend=e=>{{e.preventDefault();if(key)send(key + ":released");}}
  b.onmousedown=()=>send(key + ":pressed");
  b.onmouseup=()=>{{if(key)send(key + ":released");}}
  b.onmouseleave=()=>{{if(key)send(key + ":released");}}
}}

bind("btn_" + KEYS.LFT, KEYS.LFT);
bind("btn_" + KEYS.RGT, KEYS.RGT);
bind("btn_" + KEYS.FWD, KEYS.FWD);
bind("btn_" + KEYS.BWD, KEYS.BWD);
bind("btn_" + KEYS.LIGHT, KEYS.LIGHT);
bind("btn_" + KEYS.HORN, KEYS.HORN);
bind("btn_" + KEYS.IND_L, KEYS.IND_L);
bind("btn_" + KEYS.IND_R, KEYS.IND_R);
bind("btn_" + KEYS.IND_LR, KEYS.IND_LR);
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