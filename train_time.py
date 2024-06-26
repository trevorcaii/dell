import subprocess
import time

def read_header(bus):
    try:
        bridge_control_output = subprocess.check_output(["setpci", "-s", bus, "0e.w"])
        return f" : {bridge_control_output.decode().strip()}"
    except subprocess.CalledProcessError:
        return f"Error reading Bridge Control for {bus}."
    
def read_link_status(bus):
    try:
        link_status_output = subprocess.check_output(["setpci", "-s", bus, "CAP_EXP+0X12.w"])
        return link_status_output.decode().strip()
    except subprocess.CalledProcessError:
        return None
    
def hex_to_binary(hex_string):
    binary_string = format(int(hex_string, 16), '032b')
    return binary_string

def extract_link_status(hex_string):
    binary_string = hex_to_binary(hex_string)
    current_link_width = int(binary_string[-4:], 2)
    current_link_speed = int(binary_string[-10:-4], 2)
    return current_link_width, current_link_speed
    
def get_train_time(bdf):
    header_type = read_header(bdf)[-2:]
    if header_type == 

def main():
    print(type(read_header("15:00.0")[-2:]))

if __name__ == "__main__":
    main()
