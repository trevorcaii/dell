import functions
import subprocess

def main():
    functions.run_command("sudo modprobe -r nvidia_uvm")
    functions.run_command("sudo modprobe -r nvidia_drm")
    diag_process = subprocess.run(['./fieldiag'], cwd="/home/dell/Downloads/629-INT16-UNIV-ALL")

if __name__ == "__main__":
    main()
