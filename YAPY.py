#! /usr/bin/python3
import argparse
import concurrent.futures
import subprocess
import sys
from getpass import getpass

import requests
from termcolor import colored

parser = argparse.ArgumentParser(description="'YAPY', Yet Another Python Yaourt :P")
parser.add_argument("package", type=str, help="Package to install")
args = parser.parse_args()


def aur_response():
    if len(args.package) > 1:
        try:
            response = requests.get(f"https://aur.archlinux.org//rpc/?v=5&type=search&by=name-desc&arg={args.package}")
            results_AUR = response.json().get("results")
            return results_AUR
        except:
            print("Could not search for packages, check your network")
            sys.exit()
    else:
        print("Package name is too short")
        sys.exit()


with concurrent.futures.ThreadPoolExecutor() as executor:
    future = executor.submit(aur_response)
    results_AUR = future.result()

response = requests.get(f"https://www.archlinux.org/packages/search/json/?q={args.package}")
results_REPO = response.json().get("results")
if len(results_AUR) != 0 or len(results_REPO) != 0:
    print(len(results_AUR), "packages found in AUR")
    print(len(results_REPO), "packages found in repos")
else:
    print("No packages found, Quitting...")
    sys.exit()


class IterPackage(type):
    def __iter__(cls):
        return iter(cls._allPackages)


class Package(metaclass=IterPackage):
    _allPackages = []

    def __init__(self, ID, Name, Origin):
        self._allPackages.append(self)
        self.ID = ID
        self.Name = Name
        self.Origin = Origin


def get_pack(array, org, name, ver, desc, repo, k):
    j = k + 10
    if len(array) < j:
        j = len(array)
    for i in range(k, j):
        package = Package(i + 1, array[i].get(f"{name}"), f"{org}")
        print(package.ID, colored(package.Name, "red"), colored(array[i].get(f"{ver}"), "yellow"),
              colored(array[i].get(f"{repo}"), "blue"))
        print(colored(array[i].get(f"{desc}"), "magenta"), "\n")
    try:
        if j != len(array):
            while True:
                prompt = input("Do you want to see more ? [Y/n]: ").upper()
                if prompt in ["Y", "N", ""]:
                    break
            print("")
        else:
            prompt = "N"
        if prompt == "N":
            while True:
                try:
                    selected = int(input("Select package number: "))
                    package = [i.Name for i in Package if i.ID == selected and i.Origin == f"{org}"]
                    if len(package) != 0:
                        return package[0]
                    else:
                        print("Invalid Choice")
                except KeyboardInterrupt:
                    sys.exit()
                except ValueError:
                    print("Invalid Choice")
        elif prompt in ["Y", ""]:
            get_pack(array, org, name, ver, desc, repo, k + 10)
        else:
            print("Invalid Choice")
    except KeyboardInterrupt:
        sys.exit()


while True:
    try:
        if len(results_AUR) != 0 and len(results_REPO) != 0:
            choice = input("Use AUR or official repos ? [AUR, OFF]: ").upper()
            if choice in ["AUR", "OFF"]:
                break
        elif len(results_AUR) == 0:
            subprocess.run('read -s -n 1 -p "Indexing Official repos, Press any key...."', shell=True)
            choice = "OFF"
            print("\n")
            break
        else:
            subprocess.run('read -s -n 1 -p "Indexing AUR repo, Press any key...."', shell=True)
            choice = "AUR"
            print("\n")
            break
    except KeyboardInterrupt:
        sys.exit()
if choice == "OFF":
    package = get_pack(results_REPO, "OFF", "pkgname", "pkgver", "pkgdesc", "repo", 0)
    try:
        sudo = getpass()
    except KeyboardInterrupt:
        sys.exit()
    install = subprocess.run(f"echo {sudo} | sudo -S pacman --noconfirm -S {package}", shell=True, text=True,
                             stderr=subprocess.PIPE)
    if install.returncode != 0:
        try:
            response = requests.get("https://www.archlinux.org")
        except:
            print("No network, Quitting...")
            sys.exit()
        print("Password is incorrect")
elif choice == "AUR":
    package = get_pack(results_AUR, "AUR", "Name", "Version", "Description", "Maintainer", 0)
    subprocess.run(f"mkdir {package} && cd {package}", shell=True, capture_output=True)
    wget = subprocess.run(
        f"wget -O {package}/PKGBUILD https://aur.archlinux.org/cgit/aur.git/plain/PKGBUILD?h={package}",
        shell=True,
        capture_output=True, text=True)
    if wget.returncode == 0:
        print("Success! ")
        while True:
            try:
                prompt = input("Do you want to inspect PKGBUILD? [Y/n] ")
            except KeyboardInterrupt:
                sys.exit()
            if prompt.upper() in ["Y", "N", ""]:
                break
            else:
                print("Invalid Choice")
        if prompt.upper() in ["Y", ""]:
            while True:
                try:
                    ed = input("Select your editor: (nano, vim, gedit): ")
                except KeyboardInterrupt:
                    sys.exit()
                editor = subprocess.run(f"{ed} {package}/PKGBUILD", shell=True, capture_output=True, text=True)
                if editor.returncode != 0:
                    print("Editor doesn't exist")
                else:
                    print(editor.stdout)
                    break
        build = subprocess.run(f"cd {package} && makepkg -s", shell=True)
        if build.returncode == 0:
            build = subprocess.run(f"cd {package} && makepkg --install", shell=True)
    else:
        print(wget.stderr)