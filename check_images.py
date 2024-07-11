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

class colors:
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    UNDERLINE = '\033[4m'

with open(os.environ['CHAINGUARD_FILE']) as file:
    data = json.load(file)
    allowed_base_images = data["images"]

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
        return f" {colors.BLUE}{image}{colors.ENDC}", False
    else:
        return f" {colors.WARNING}{image}{colors.ENDC}", True

def process_line(line, line_number, allowed_base_images):
    line = " ".join(line.strip().split())
    has_error = False
    if line.startswith("FROM"):
        platform_part, image, as_part = extract_parts(line)
        formatted_image_part, has_error = check_image(image, allowed_base_images)
        print(f" {line_number}: FROM{platform_part}{formatted_image_part} {as_part}")
    return has_error

def check_dockerfiles(dockerfiles, allowed_base_images):
    number_of_errors = 0
    for dockerfile in dockerfiles:
        print(f"{colors.UNDERLINE}{dockerfile}{colors.ENDC}")
        with open(dockerfile, 'r') as file:
            lines = file.readlines()
            for line_number, line in enumerate(lines, start=1):
                error = process_line(line, line_number, allowed_base_images)
                number_of_errors = number_of_errors + 1 if error else number_of_errors
        print()
    return number_of_errors

dockerfiles = find_dockerfiles()
errors = check_dockerfiles(dockerfiles, allowed_base_images)
if errors > 0:
    print(f"{colors.FAIL} !! Found {errors} Docker image(s) that are not allowed{colors.ENDC}\n")
    print(f"{colors.BLUE}For more information see: https://github.com/johnschult/check-image-action{colors.ENDC}")
    exit(1)
else:
    print(f"{colors.GREEN}✓ All base images are OK{colors.ENDC}\n")
    exit(0)
