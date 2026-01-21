import uasyncio as asyncio
from esp32_mpcontroler import RemoteController, MPCKeys


async def main():
    # Initialize the remote controller
    remote = RemoteController(port=80)
    
    # Start the server in background
    server_task = asyncio.create_task(remote.start())
    
    print("Remote Controller started!")
    print("Connect to ESP32_RC WiFi and open http://192.168.4.1")
    print()
    
    # Main loop
    while True:
        remote.update()
        
        # Check all button presses
        if remote.is_pressed(MPCKeys.LFT):
            print("→ BTN_LFT pressed")
        if remote.is_pressed(MPCKeys.RGT):
            print("→ BTN_RGT pressed")
        if remote.is_pressed(MPCKeys.FWD):
            print("→ BTN_FWD pressed")
        if remote.is_pressed(MPCKeys.BWD):
            print("→ BTN_BWD pressed")
        if remote.is_pressed(MPCKeys.LIGHT):
            print("→ BTN_LIGHT pressed")
        if remote.is_pressed(MPCKeys.HORN):
            print("→ BTN_HORN pressed")
        if remote.is_pressed(MPCKeys.IND_L):
            print("→ IND_L pressed")
        if remote.is_pressed(MPCKeys.IND_R):
            print("→ IND_R pressed")
        if remote.is_pressed(MPCKeys.IND_LR):
            print("→ IND_LR pressed")
        
        # Check all button releases
        if remote.is_released(MPCKeys.LFT):
            print("← BTN_LFT released")
        if remote.is_released(MPCKeys.RGT):
            print("← BTN_RGT released")
        if remote.is_released(MPCKeys.FWD):
            print("← BTN_FWD released")
        if remote.is_released(MPCKeys.BWD):
            print("← BTN_BWD released")
        if remote.is_released(MPCKeys.LIGHT):
            print("← BTN_LIGHT released")
        if remote.is_released(MPCKeys.HORN):
            print("← BTN_HORN released")
        if remote.is_released(MPCKeys.IND_L):
            print("← IND_L released")
        if remote.is_released(MPCKeys.IND_R):
            print("← IND_R released")
        if remote.is_released(MPCKeys.IND_LR):
            print("← IND_LR released")
        
        await asyncio.sleep(0.01)


# Start the application
asyncio.run(main())