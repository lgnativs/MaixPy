#
# @file from https://github.com/Neutree/c_cpp_project_framework
# @author neucrack
#

import argparse
import os, sys, time, re, shutil
import subprocess
from multiprocessing import cpu_count

if not os.path.exists("CMakeLists.txt") or  not os.path.exists("main"):
    print("please run me at project folder!")
    exit(1)

try:
    sdk_path = sdk_path
except Exception:
    sdk_path = os.path.abspath("../../")
project_path = sys.path[0]
project_name = ""
project_cmake_path = project_path+"/CMakeLists.txt"
project_cmake_content = ""
with open(project_cmake_path) as f:
    project_cmake_content = f.read()
match = re.findall(r"{}(.*){}".format(r"project\(", r"\)"), project_cmake_content, re.MULTILINE|re.DOTALL)
if len(match) != 0:
    project_name = match[0]
    print(project_name)
if project_name == "":
    print("[ERROR] Can not find project name in {}".format(project_cmake_path))
    exit(1)


flash_dir = sdk_path+"/tools/flash"
if os.path.exists(flash_dir):
    sys.path.insert(1, flash_dir)
    from flash import parser as flash_parser
project_parser = argparse.ArgumentParser(description='build tool, e.g. `python project.py build`', prog="project.py", parents=[flash_parser])

project_parser.add_argument('--toolchain',
                        help='toolchain path ( absolute path )',
                        metavar='PATH',
                        default="")

project_parser.add_argument('--toolchain-prefix',
                        help='toolchain prefix(e.g. mips-elf-',
                        metavar='PREFIX',
                        default="")
project_parser.add_argument('--verbose',
                        help='for build command, execute `make VERBOSE=1` to compile',
                        action="store_true",
                        default=False)
cmd_help ='''project command'''
project_parser.add_argument("cmd",
                    help=cmd_help,
                    choices=["config", "build", "rebuild", "menuconfig", "clean", "distclean", "clean_conf", "flash"]
                    )

project_args = project_parser.parse_args()

cwd = sys.path[0]
os.chdir(cwd)

config_filename = ".config.mk"
gen_project_type = "Unix Makefiles"


config_content_old = ""


if os.path.exists(config_filename):
    with open(config_filename) as f:
        config_content_old = f.read()
header = "# Generated by config.py, DO NOT edit!\n\n"
config_content = header
update_config = False
if project_args.toolchain.strip() != "":
    if not os.path.exists(project_args.toolchain):
        print("config toolchain path error:", project_args.toolchain)
        exit(1)
    update_config = True
    project_args.toolchain = project_args.toolchain.strip().replace("\\","/")
    config_content += 'CONFIG_TOOLCHAIN_PATH="'+project_args.toolchain+'"\n'
if project_args.toolchain_prefix.strip() != "":
    update_config = True
    project_args.toolchain_prefix = project_args.toolchain_prefix.strip().replace("\\","/")
    config_content += 'CONFIG_TOOLCHAIN_PREFIX="'+project_args.toolchain_prefix+'"\n'
config_content += '\n'
if update_config and config_content != config_content_old:
    with open(config_filename, "w") as f:
        f.write(config_content)
    if os.path.exists("build/config/global_config.mk"):
        os.remove("build/config/global_config.mk")
    print("generate config file at: {}".format(config_filename))

# config
if project_args.cmd == "config":
    print("config complete")
# rebuild / build
elif project_args.cmd == "build" or project_args.cmd == "rebuild":
    print("build now")
    time_start = time.time()
    if not os.path.exists("build"):
        os.mkdir("build")
    os.chdir("build")
    if not os.path.exists("Makefile") or project_args.cmd == "rebuild":
        res = subprocess.call(["cmake", "-G", gen_project_type, ".."])
        if res != 0:
            exit(1)
    if project_args.verbose:
        res = subprocess.call(["make", "VERBOSE=1"])
    else:
        res = subprocess.call(["make", "-j{}".format(cpu_count())])
    if res != 0:
        exit(1)

    time_end = time.time()
    print("==================================")
    print("build end, time last:%.2fs" %(time_end-time_start))
    print("==================================")
# clean
elif project_args.cmd == "clean":
    print("clean now")
    if os.path.exists("build"):
        os.chdir("build")
        res =subprocess.call(["make", "clean"])
        if res != 0:
            exit(1)
    print("clean complete")
# distclean    
elif project_args.cmd == "distclean":
    print("clean now")
    if os.path.exists("build"):
        os.chdir("build")
        subprocess.call(["make", "clean"])
        os.chdir("..")
        shutil.rmtree("build")
    print("clean complete")
# menuconfig
elif project_args.cmd == "menuconfig":
    time_start = time.time()
    if not os.path.exists("build"):
        os.mkdir("build")
    os.chdir("build")
    if not os.path.exists("build/Makefile"):
        res = subprocess.call(["cmake", "-G", gen_project_type, ".."])
        if res != 0:
            exit(1)
    res = subprocess.call(["make", "menuconfig"])
    if res != 0:
        exit(1)
# flash
elif project_args.cmd == "flash":
    flash_file_path = os.path.abspath(sdk_path+"/tools/flash/flash.py")
    with open(flash_file_path) as f:
        exec(f.read())
# clean_conf
elif project_args.cmd == "clean_conf":
    print("clean now")
    # clean cmake config files
    if os.path.exists(config_filename):
        os.remove(config_filename)
    if os.path.exists("build/config/"):
        shutil.rmtree("build/config")
    # clean flash config file
    flash_file_path = os.path.abspath(sdk_path+"/tools/flash/flash.py")
    with open(flash_file_path) as f:
        exec(f.read())
    print("clean complete")
else:
    print("Error: Unknown command")
    exit(1)

