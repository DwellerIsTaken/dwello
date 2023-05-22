from __future__ import annotations

import pkg_resources
import discord
import PIL
import sys

from typing import Optional
from io import BytesIO

# MODIFY | FIX
# DO WE NEED THIS?

def apostrophize(word: str) -> str:
    if word[-1] == 's':
        return word + "'"
    else:
        return word + "'s"
    
async def get_avatar_dominant_color(member: Optional[discord.Member]) -> Optional[discord.Colour]:
    image = PIL.Image.open(BytesIO(await member.display_avatar.read()))
    colours = [
        colour
        for colour in sorted(
            image.getcolors(image.size[0] * image.size[1]),
            key=lambda c: c[0],  # Sorts by most amount of pixels
            reverse=True,
        )
        if colour[-1][-1] != 0  # Ignores transparent pixels
    ]

    most_used_colour = colours[0][1]  # This will be a tuple of the format (RRR, GGG, BBB, AAA)
    r, g, b = most_used_colour[0], most_used_colour[1], most_used_colour[2]
    return discord.Colour.from_rgb(r, g, b)

def add_requirements(*packages) -> None:
    try:
        with open('requirements.txt', 'x') as file:
            for package in packages:
                version = get_package_version(package)
                file.write(f"{package.__name__}=={version}\n")

    except FileExistsError:
        with open('requirements.txt', 'r') as file:
            lines = file.readlines()

        updated_lines = []
        package_names = [line.split('==')[0].strip() for line in lines]

        for package in packages:
            package_name = package.__name__
            version = get_package_version(package)
            if not version:
                continue

            updated = False

            for i, line in enumerate(lines):
                if line.startswith(package_name):
                    installed_version = pkg_resources.parse_version(line.split('==')[1].strip())
                    new_version = pkg_resources.parse_version(version)
                    if installed_version < new_version:
                        lines[i] = f"{package_name}=={new_version}\n"
                        updated = True
                    break

            if not updated and package_name not in package_names:
                updated_lines.append(f"{package_name}=={version}\n")
                package_names.append(package_name)

        lines.extend(updated_lines)

        with open('requirements.txt', 'w') as file:
            file.writelines(lines)

def get_package_version(package):
    try:
        version = package.__version__
    
    except AttributeError:
        try:
            version = pkg_resources.get_distribution(package.__name__).version

        except pkg_resources.DistributionNotFound:
            if package.__name__ in sys.builtin_module_names or f"_{package.__name__}" in sys.builtin_module_names:
                print(f"{package.__name__} is a built-in module and doesn't need to be added.")
            else:
                print(f"{package.__name__} is not installed or could be a built-in Python package.")
            return

    return version

'''async def add_requirements(*packages) -> None:
    try:
        with open('requirements.txt', 'x') as file:
            for package in packages:
                package_name = package.__name__
                version = await get_package_version(package)
                file.write(f"{package_name}=={version}\n")

    except FileExistsError:
        with open('requirements.txt', 'r') as file:
            lines = file.readlines()

        updated_lines = []

        for package in packages:
            package_name = package.__name__
            version = await get_package_version(package)

            for i, line in enumerate(lines):
                if line.startswith(package_name):
                    installed_version = pkg_resources.parse_version(
                        line.strip().split('==')[1])
                    new_version = pkg_resources.parse_version(version)

                    if installed_version < new_version:
                        lines[i] = f"{package_name}=={version}\n"
                    break
            else:
                updated_lines.append(f"{package_name}=={version}\n")

        lines.extend(updated_lines)

        with open('requirements.txt', 'w') as file:
            file.writelines(lines)

async def get_package_version(package):
    try:
        version = package.__version__
    
    except AttributeError:
        try:
            version =  pkg_resources.get_distribution(package.__name__).version
        
        except pkg_resources.DistributionNotFound:
            print(f"{package.__name__} is not installed. Installing...")
            await install_package(package.__name__)
            version = await get_package_version(package)

    return version

async def install_package(package_name):
    subprocess.check_call(['pip', 'install', package_name])'''

