import json
import sys
import time
import asyncio
from bleak import BleakClient
from bleak import BleakScanner

SAMPLES_PER_CYCLE=50
SAMPLES = 100
WORK_DIR = "./"
CLASS_NAME = "test"
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



def get_progress_string(lst, ind):
    num = 0
    for i in range(0,SAMPLES_PER_CYCLE):
        if lst[ind][i] > 0.0:
            num += 1
    coef = int((num*10) / SAMPLES_PER_CYCLE)
    line = "Sensor {}: ".format(ind+1)
    for i in range(0,coef):
        line+="+"
    for i in range(coef,10):
        line+="="
    return line

def num_logging(lst):
    num = 0
    for i in range(0,8):
        if lst[i] > 0:
            num+=1
    return num


def print_progress(saved_samples,lst,cycles):
    print("\033[F\033[F\033[F\033[F\033[F\033[F\033[F\033[F\033[F", end="")
    print("\rCollected samples: {}/{} | Sensors logging: {}/8".format(saved_samples, SAMPLES, num_logging(cycles)))
    sys.stdout.flush()
    for i in range(0,8):
        print(get_progress_string(lst,i))
    sys.stdout.flush()


def notification_handler(sender, data):
    """Simple notification handler which prints the data received."""
    global flag
    global recv
    recv = data.decode('utf-8')
    flag = True


async def run(address, loop):
    global flag, recv, WORK_DIR, SAMPLES,CLASS_NAME
    buffer = ""
    decoder = json.JSONDecoder()
    lines = [ [-1.0]*SAMPLES_PER_CYCLE for i in range(8)]
    cycles = [-1 for i in range(8)]
    times = [time.time() for i in range(8)]
    saved = 0

    async with BleakClient(address, loop=loop) as client:
        x = await client.is_connected()
        print("Connected to device, please wait for the duty cycle to start")
        print("\n\n\n\n\n\n\n\n")

        await client.start_notify(UART_RX_UUID, notification_handler)
        with open("{}/{}.csv".format(WORK_DIR, CLASS_NAME),"a") as out:
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
                                # Write results
                                entry = ""
                                for i in range(0,SAMPLES_PER_CYCLE):
                                    entry += str(lines[gsensor][i])
                                    entry += ","
                                entry = entry[:-1] + "\n"
                                out.write(entry)
                                saved += 1
                                if saved == SAMPLES:
                                    return
                                for i in range(0,SAMPLES_PER_CYCLE):
                                    lines[gsensor][i] = -1.0
                                cycles[gsensor] = 0
                            else:
                                cycles[gsensor] += 1

                    print_progress(saved,lines,cycles)

                else:
                    recv = ""

def usage():
    print("Usage: {} <work_dir> <class_name> <samples>".format(sys.argv[0]))
    sys.exit(1)


def main():
    global WORK_DIR, CLASS_NAME, SAMPLES

    if len(sys.argv) != 4:
        usage()
        sys.exit(1)
    else:
        WORK_DIR = sys.argv[1]
        CLASS_NAME = sys.argv[2]
        SAMPLES = int(sys.argv[3])

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
