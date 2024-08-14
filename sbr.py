import subprocess
import time
from datetime import datetime
from train_time import get_train_time  # Import the get_train_time function
import functions

def read_header(bus):
    try:
        bridge_control_output = subprocess.check_output(["setpci", "-s", bus, "0e.w"])
        return f" : {bridge_control_output.decode().strip()}"
    except subprocess.CalledProcessError:
        return f"Error reading Bridge Control for {bus}."

def read_slot_capabilities(bus):
    try:
        slot_capabilities_output = subprocess.check_output(["setpci", "-s", bus, "CAP_EXP+0X14.l"])
        return slot_capabilities_output.decode().strip()
    except subprocess.CalledProcessError:
        return None

def execute_shell_command(command):
    try:
        result = subprocess.run(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
        if result.returncode == 0:
            return result.stdout.strip()
        else:
            return f"Error: {result.stderr.strip()}"
    except Exception as e:
        return f"Error: {str(e)}"

def hex_to_binary(hex_string):
    binary_string = format(int(hex_string, 16), '032b')
    return binary_string

def read_secondary_bus_number(bus):
    try:
        secondary_bus_output = subprocess.check_output(["setpci", "-s", bus, "19.b"])
        return secondary_bus_output.decode().strip()
    except subprocess.CalledProcessError:
        return None

def read_bridge_control(bus):
    try:
        bridge_control_output = subprocess.check_output(["setpci", "-s", bus, "3e.w"])
        return bridge_control_output.decode().strip()
    except subprocess.CalledProcessError:
        return None

def read_link_status(bus):
    try:
        link_status_output = subprocess.check_output(["setpci", "-s", bus, "CAP_EXP+0X12.w"])
        return link_status_output.decode().strip()
    except subprocess.CalledProcessError:
        return None

def read_link_capabilities17(bus):
    try:
        link_capabilities_output = subprocess.check_output(["setpci", "-s", bus, "CAP_EXP+0X0c.l"])
        return link_capabilities_output.decode().strip()
    except subprocess.CalledProcessError:
        print("error")
        return None

def read_link_capabilities18(bus):
    try:
        link_capabilities_output = subprocess.check_output(["setpci", "-s", bus, "CAP_EXP+0X0c.l"])
        return link_capabilities_output.decode().strip()
    except subprocess.CalledProcessError:
        print("error")
        return None

def set_bridge_control(bus, value, password):
    try:
        subprocess.run(["sudo", "-S", "setpci", "-s", bus, "3e.w=" + value], input=password.encode(), check=True)
    except subprocess.CalledProcessError:
        print(f"Error setting Bridge Control for {bus}.")

def format_bdf(bus):
    bus_number = bus.split(":")[0]
    return f"{bus_number}:0.0"

def convert_hex_to_binary(hex_string):
    decimal_value = int(hex_string, 16)
    binary_string = bin(decimal_value)[2:].zfill(32)  # Ensure 32-bit binary representation
    return binary_string

def extract_link_capabilities(hex_string):
    binary_string = hex_to_binary(hex_string)
    max_link_width = int(binary_string[-3:], 2)
    max_link_speed = int(binary_string[-9:-4], 2)
    return max_link_width, max_link_speed

def read_and_extract_link_capabilities(bus, read_func):
    link_capabilities_hex = read_func(bus)
    return extract_link_capabilities(link_capabilities_hex)

def extract_link_status(hex_string):
    binary_string = hex_to_binary(hex_string)
    current_link_width = int(binary_string[-4:], 2)
    current_link_speed = int(binary_string[-10:-4], 2)
    return current_link_width, current_link_speed

def get_slot_numbers():
    command_output = execute_shell_command("lspci | cut -d ' ' -f 1")
    split_numbers = [num for num in command_output.split('\n') if num]

    slotnumbers = []
    listbdf = []
    for i in range(len(split_numbers)):
        header = read_header(split_numbers[i])
        if header[-1] == '1':
            a = read_slot_capabilities(split_numbers[i])
            b = hex_to_binary(a)
            c = b[0:13]
            d = int(c, 2)
            if d > 0:
                listbdf.append(split_numbers[i])
                slotnumbers.append(d)
    return [f"{slotnumbers[i]} : {listbdf[i]}" for i in range(len(slotnumbers))]

def display_slot_numbers():
    slot_numbers = get_slot_numbers()
    print("Available slot numbers:")
    for slot in slot_numbers:
        print(slot)

def log_dmidecode_info(log_file):
    try:
        dmidecode_output = subprocess.check_output(["sudo", "dmidecode", "-t", "1"]).decode().strip()
        with open(log_file, 'a') as log:
            log.write(f"\nDMIDecode Output:\n{dmidecode_output}\n")
    except subprocess.CalledProcessError as e:
        with open(log_file, 'a') as log:
            log.write(f"\nError running dmidecode: {str(e)}\n")

def sbr(user_password, bdf_list, secondary_bdf_list, loops, kill):
    bridge_control_list = []
    link_capabilities = {"upstream": [], "downstream": []}
    expected_negotiated_link = []

    max_train_time = 0
    for index, bdf in enumerate(bdf_list):
        bridge_control_list.append(read_bridge_control(bdf))
        bdf_link_capabilities = read_and_extract_link_capabilities(bdf, read_link_capabilities17)
        secondary_bdf_link_capabilities = read_and_extract_link_capabilities(secondary_bdf_list[index], read_link_capabilities18)
        print(bdf_link_capabilities)
        print(secondary_bdf_link_capabilities)
        train_time = get_train_time(bdf)
        if train_time > max_train_time:
            max_train_time = train_time

    print(bridge_control_list)
    print(link_capabilities)

    for i in range(loops):
        for bdf in bdf_list:
            set_bridge_control(bdf, "0043", user_password)
        for index, bdf in enumerate(bdf_list):
            set_bridge_control(bdf, bridge_control_list[index], user_password)
        time.sleep(max_train_time)

        for index, bdf in enumerate(bdf_list):
            current_link_status_hex = read_link_status(bdf)
            current_link_status = extract_link_status(current_link_status_hex)
            print(link_capabilities["downstream"])


def run_test(user_password, inputnum_loops, kill, bdf_list, window, window_offset_y, window_offset_x, window_height, window_width, pad_pos):
    pad_pos = functions.output_print(window, window_offset_y, window_offset_x, window_height, window_width, pad_pos, "Running the test...")
    # Initialize variables
    output_lines = []
    start_time = datetime.now()
    output_lines.append(f"Start Time: {start_time}")

    # Gather initial data
    command_output = execute_shell_command("lspci | cut -d ' ' -f 1")
    split_numbers = [num for num in command_output.split('\n') if num]

    slotnumbers = []
    listbdf = []
    for i in range(len(split_numbers)):
        header = read_header(split_numbers[i])
        if header[-1] == '1':
            a = read_slot_capabilities(split_numbers[i])
            b = hex_to_binary(a)
            c = b[0:13]
            d = int(c, 2)
            if d > 0:
                listbdf.append(split_numbers[i])
                slotnumbers.append(d)
    listbdfdown = []
    for i in range(len(listbdf)):
        downstream = listbdf[i]
        secondary_bus = read_secondary_bus_number(downstream)
        a = int(downstream[0:2], 16)
        b = str(hex(a + 1)[2:4])
        c = f"{secondary_bus}:00.0"
        listbdfdown.append(c)
    output_lines.append(f"Tested BDFs: {listbdf}")
    output_lines.append(f"Downstream BDFs: {listbdfdown}")
    output_lines.append(f"Slot Numbers: {slotnumbers}")

    indexlist = []
    bridgecontrollist = []
    link_capabilities = {"upstream": [], "downstream": []}

    tested_bdf_info = {}

    # Get maximum train time for selected slots
    max_train_time = 0
    for slot in slotlist:
        idx = slotnumbers.index(slot)
        indexlist.append(idx)
        bridgecontrollist.append(read_bridge_control(listbdf[idx]))
        link_capabilities["upstream"].append(read_and_extract_link_capabilities(listbdf[idx], read_link_capabilities17))
        link_capabilities["downstream"].append(read_and_extract_link_capabilities(listbdfdown[idx], read_link_capabilities18))
        train_time = get_train_time(listbdf[idx])
        if train_time > max_train_time:
            max_train_time = train_time

    num_loops = 2 * inputnum_loops + 1
    total_operations = num_loops * len(indexlist)
    slot_test_count = {slot: 0 for slot in slotlist}

    operation_count = 0
    
    for i in range(num_loops):
        if i % 2 == 0: time.sleep(max_train_time)
        for j in indexlist:
            operation_count += 1
            slot_test_count[slotnumbers[j]] += 1
            pad_pos = functions.progress_bar(operation_count, total_operations, 'Progress', 'Complete', 1, window_width-31, '█', window, window_offset_y, window_offset_x, window_height, window_width, pad_pos)
            specific_bus_bridge = listbdf[j]
            specific_bus_link = listbdfdown[j]
            desired_values = [bridgecontrollist[indexlist.index(j)], "0043"]
            desired_value = desired_values[i % len(desired_values)]
            set_bridge_control(specific_bus_bridge, desired_value, user_password)
              # Use the maximum train time as sleep duration
            if i % 2 == 0:
                # print(specific_bus_bridge)
                current_link_status_hex = read_link_status(specific_bus_bridge)
                # print(current_link_status_hex)
                # time.sleep(0)
                current_link_status = extract_link_status(current_link_status_hex)
                
                if current_link_status != link_capabilities["downstream"][indexlist.index(j)]:
                    error_time = datetime.now()
                    error_info = {
                        "reset_count": i,
                        "link_status": current_link_status,
                        "link_capabilities": link_capabilities["downstream"][indexlist.index(j)],
                        "error_time": error_time,
                    }
                    if slotnumbers[j] in tested_bdf_info:
                        tested_bdf_info[slotnumbers[j]]["errors"].append(error_info)
                    else:
                        tested_bdf_info[slotnumbers[j]] = {
                            "specific_bus_link": specific_bus_link,
                            "errors": [error_info],
                        }
                    if kill == "y":
                        with open("output.txt", "w") as file:
                            for line in output_lines:
                                file.write(line + "\n")
                        pad_pos = functions.output_print(window, window_offset_y, window_offset_x, window_height, window_width, pad_pos, "")
                        pad_pos = functions.output_print(window, window_offset_y, window_offset_x, window_height, window_width, pad_pos, "Link status does not match capabilities. Killing the program.")
                        return tested_bdf_info

    end_time = datetime.now()
    output_lines.append(f"End Time: {end_time}")
    output_lines.append(f"Slot Test Counts: {inputnum_loops}")

    with open("output.txt", "w") as file:
        for line in output_lines:
            file.write(line + "\n")

    pad_pos = functions.output_print(window, window_offset_y, window_offset_x, window_height, window_width, pad_pos, "Test completed. Check the output.txt file for results.")

    return tested_bdf_info
