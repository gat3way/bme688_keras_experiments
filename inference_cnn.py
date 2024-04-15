import json
import os
import sys
import time
import asyncio
from keras import saving
import numpy as np
from bleak import BleakClient
from bleak import BleakScanner

MODEL_NAME = ""
SAMPLES_PER_CYCLE=50
CLASSES = 100
UART_TX_UUID = "6e400002-b5a3-f393-e0a9-e50e24dcca9e"
UART_RX_UUID = "6e400003-b5a3-f393-e0a9-e50e24dcca9e"
flag = False 
recv = ""

async def discover():
    devices = await BleakScanner.discover()
    for d in devices:
        if "BME688" in str(d):
            mac_addr = str(d).split(" ")[0]
            return mac_addr[:-1]
    return None


def notification_handler(sender, data):
    """Simple notification handler which prints the data received."""
    global flag
    global recv
    recv = data.decode('utf-8')
    flag = True


async def run(address, loop):
    global MODEL_NAME,flag,recv

    try:
        model = saving.load_model("{}.keras".format(MODEL_NAME))
    except:
        print("Could not load the model {}.keras".format(MODEL_NAME))
        sys.exit(2)

    buffer = ""
    decoder = json.JSONDecoder()
    lines = [ [-1.0]*SAMPLES_PER_CYCLE for i in range(8)]
    cycles = [-1 for i in range(8)]
    times = [time.time() for i in range(8)]
    saved = 0

    async with BleakClient(address, loop=loop) as client:
        x = await client.is_connected()
        print("Connected to device, please wait for the duty cycle to start...")

        await client.start_notify(UART_RX_UUID, notification_handler)
        while True:
            await asyncio.sleep(0.0)
            if flag:
                buffer += recv
                try:
                    decoded,j_len = decoder.raw_decode(buffer)
                    buffer = buffer[j_len:]
                    j = decoded["bme68x"]
                    gsensor = j["sensor_number"]
                    gres = j["gas_resistance"]
                    gindex = j["gas_index"]
                    flag = False
                except:
                    import traceback
                    traceback.print_exc()
                    continue

                if cycles[gsensor] < 0:
                    if time.time() - times[gsensor] < 10: # max sleep within cycle is ~4s so this is just to make sure
                        continue
                times[gsensor] = time.time()

                if cycles[gsensor] < 0 and gindex == 0:
                    cycles[gsensor] = 0

                if cycles[gsensor] >= 0:
                    lines[gsensor][10*cycles[gsensor]+gindex] = gres
                    if gindex == 9:
                        if cycles[gsensor] == int(SAMPLES_PER_CYCLE / 10)-1:

                            # Evaluate results
                            entry = ""
                            test = np.full([1,SAMPLES_PER_CYCLE],0)
                            for i in range(0,SAMPLES_PER_CYCLE):
                                test[0][i] = lines[gsensor][i]
                            test = test.reshape(test.shape[0], test.shape[1], 1)
                            results = model.predict(test, verbose=0)
                            try:
                                with open("{}.classes".format(MODEL_NAME),"r") as f:
                                    classes = f.readlines()
                            except:
                                print("Cannot open classes file: {}.classes".format(MODEL_NAME))
                                sys.exit(3)

                            res = np.copy(results)
                            print("Results: ")
                            num = 0
                            while num < 5:
                                ind = 0
                                highest = 0
                                for val in range(0,CLASSES):
                                    if res[0][val] > highest:
                                        highest = res[0][val]
                                        ind = val
                                res[0][ind] = 0
                                if highest > 0.05 and ind < len(classes)-1:
                                    print("{}. {} ({:.2f}%)".format(num+1, classes[ind].strip("\n"), highest*100))
                                highest = 0
                                num += 1


                            for i in range(0,SAMPLES_PER_CYCLE):
                                cycles[gsensor] = -1.0
                            cycles[gsensor] = 0
                        else:
                            cycles[gsensor] += 1

                else:
                    recv = ""

def usage():
    print("Usage: {} <model_name>".format(sys.argv[0]))
    sys.exit(1)


def main():
    global MODEL_NAME

    os.environ["KERAS_BACKEND"] = "theano"
    if len(sys.argv) != 2:
        usage()
        sys.exit(1)
    else:
        MODEL_NAME = sys.argv[1]

    address = asyncio.run(discover())
    if address is None:
        print("No BME688 device found!")
        sys.exit(2)
    print("Found BME688 device: {}".format(address))
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(run(address, loop))

if __name__ == "__main__":
    main()
