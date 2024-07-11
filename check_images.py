# This script finds all Dockerfiles from the current directory recursively
# then it looks through each one for lines that begin with FROM
# the lines may look like the following:

# FROM ubuntu:latest
# FROM ubuntu:16.04
# FROM ubuntu:16.04 as base
# FROM --platform=arm64 ubuntu:16.04 as base

# the script will output a list of all of the base images used in the Dockerfile
# along with the Dockerfile that uses it
# if the base image is not in the allowed_base_images class, it will be highlighted in yellow
# if there is at least one base image that is not allowed, the script will return an error code 1
# otherwise, it will return 0

import os
import json

class Colors:
    """ ANSI color codes """
    BLACK = "\033[0;30m"
    RED = "\033[0;31m"
    GREEN = "\033[0;32m"
    BROWN = "\033[0;33m"
    BLUE = "\033[0;34m"
    PURPLE = "\033[0;35m"
    CYAN = "\033[0;36m"
    LIGHT_GRAY = "\033[0;37m"
    DARK_GRAY = "\033[1;30m"
    LIGHT_RED = "\033[1;31m"
    LIGHT_GREEN = "\033[1;32m"
    YELLOW = "\033[1;33m"
    LIGHT_BLUE = "\033[1;34m"
    LIGHT_PURPLE = "\033[1;35m"
    LIGHT_CYAN = "\033[1;36m"
    LIGHT_WHITE = "\033[1;37m"
    BOLD = "\033[1m"
    FAINT = "\033[2m"
    ITALIC = "\033[3m"
    UNDERLINE = "\033[4m"
    BLINK = "\033[5m"
    NEGATIVE = "\033[7m"
    CROSSED = "\033[9m"
    END = "\033[0m"


def find_dockerfiles():
    dockerfiles = []
    for root, _, files in os.walk("."):
        for file in files:
            if file == "Dockerfile":
                dockerfiles.append(os.path.join(root, file))
    return dockerfiles

def extract_parts(line):
    platform_part = ""
    as_part = ""
    image_part = ""
    if "--platform=" in line.lower():
        _, platform_part, image_part, as_part = line.split(" ", 3)
        platform_part = f" {platform_part}"
    else:
        if "as " in line.lower():
            _, image_part, as_part = line.split(" ", 2)
        else:
            _, image_part = line.split(" ", 1)
    return platform_part, image_part, as_part

def check_image(image, allowed_base_images):
    if image in allowed_base_images:
        return f" {Colors.GREEN}{image}{Colors.END}", False
    else:
        return f" {Colors.YELLOW}{image}{Colors.END}", True

def process_line(line, line_number, allowed_base_images):
    line = " ".join(line.strip().split())
    has_error = False
    if line.startswith("FROM"):
        platform_part, image, as_part = extract_parts(line)
        formatted_image_part, has_error = check_image(image, allowed_base_images)
        if has_error:
            print(f"{Colors.LIGHT_WHITE}  {line_number}: FROM{platform_part}{formatted_image_part} {Colors.LIGHT_WHITE}{as_part}{Colors.END}")
        else:
            print(f"  {line_number}: FROM{platform_part}{formatted_image_part} {as_part}")
    return has_error

def check_dockerfiles(dockerfiles):
    with open(os.environ['CHAINGUARD_FILE']) as file:
        data = json.load(file)
        allowed_base_images = data["images"]

    number_of_errors = 0
    
    for dockerfile in dockerfiles:
        print(f"{Colors.CYAN}{Colors.UNDERLINE}{dockerfile}{Colors.END}")
        with open(dockerfile, 'r') as file:
            lines = file.readlines()
            for line_number, line in enumerate(lines, start=1):
                error = process_line(line, line_number, allowed_base_images)
                number_of_errors = number_of_errors + 1 if error else number_of_errors
        print()
    return number_of_errors

# main script starts here

print(f"\n⛭ Checking Dockerfiles...\n")
dockerfiles = find_dockerfiles()
errors = check_dockerfiles(dockerfiles)

if errors > 0:
    print(f"{Colors.YELLOW}⚠️ Found {errors} Docker image(s) not in allowed list{Colors.END}")
    print(f"{Colors.BLUE}ℹ {Colors.ITALIC}For more information see: https://github.com/johnschult/check-image-action{Colors.END}\n")
    exit(1)
else:
    print(f"{Colors.GREEN}✓ All base images are OK{Colors.END}\n")
