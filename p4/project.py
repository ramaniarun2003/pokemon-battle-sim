"""
Loads data from pokemon_attributes.csv and type_effectiveness_stats.csv.
Provides public functions for interacting with this data without
needing to know how to open csv data or how to index into a dict/list.
"""

import os
import functools
import csv

_ATTRIBUTES_CSV_FILE_NAME = "pokemon_attributes.csv"
_EFFECTIVENESS_CSV_FILE_NAME = "type_effectiveness.csv"


_CSV_NOT_FOUND_MSG_FORMAT = """We expected to find a file named
{} in the same folder containing your notebook, but it doees not
exist there. Please do not change the names of any of the provided
files within the assignment zip after extracting it."""

if not os.path.isfile(_ATTRIBUTES_CSV_FILE_NAME):
    raise FileNotFoundError(_CSV_NOT_FOUND_MSG_FORMAT.format(_ATTRIBUTES_CSV_FILE_NAME))

if not os.path.isfile(_EFFECTIVENESS_CSV_FILE_NAME):
    raise FileNotFoundError(
        _CSV_NOT_FOUND_MSG_FORMAT.format(_EFFECTIVENESS_CSV_FILE_NAME)
    )


_pokemon: dict[str, dict[str, int]] = {}
_effectiveness: dict[str, dict[str, float]] = {}
_integer_attributes = ["Attack", "Defense", "HP", "Sp. Atk", "Sp. Def", "Speed"]

with open(_ATTRIBUTES_CSV_FILE_NAME, encoding="utf-8") as f:
    raw_pkmn_data = list(csv.reader(f))
attributes_headers = raw_pkmn_data[0]
attributes_rows = raw_pkmn_data[1:]
for attribute_row in attributes_rows:
    pkmn = {}
    for i, attributes_header in enumerate(attributes_headers):
        if attributes_header in _integer_attributes:
            pkmn[attributes_headers[i]] = int(attribute_row[i])
        else:
            pkmn[attributes_headers[i]] = attribute_row[i]
    _pokemon[pkmn["Name"]] = pkmn


with open(_EFFECTIVENESS_CSV_FILE_NAME, encoding="utf-8") as f:
    raw_type_data = list(csv.reader(f))
attacking_types = raw_type_data[0][1:]
defending_effectiveness_rows = raw_type_data[1:]
for attacking_type in attacking_types:
    _effectiveness[attacking_type] = {}
for defending_effectiveness_row in defending_effectiveness_rows:
    defending_type = defending_effectiveness_row[0]
    for i, effectiveness in enumerate(defending_effectiveness_row[1:]):
        attacking_type = attacking_types[i]
        _effectiveness[attacking_type][defending_type] = float(effectiveness)


def handle_key_error(func):
    """Wrapper for neatly handling KeyErrors

    This is nice because students tend to make a lot of spelling mistakes in this
    assignment since Pokemon names aren't real words.
    """

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except KeyError as e:
            print(f"{args[0]} not found. Please check your spelling.")
            raise e

    return wrapper


@handle_key_error
def print_attributes(pkmn_name: str) -> None:
    """Prints all the attributes for a Pokemon"""

    for attribute in _pokemon[pkmn_name]:
        print(attribute, ": ", _pokemon[pkmn_name][attribute])


@handle_key_error
def get_region(pkmn_name: str) -> str:
    """Where the Pokemon was first discovered"""

    return _pokemon[pkmn_name]["Region"]


def get_type1(pkmn_name: str) -> str:
    """The Pokemon's primary type"""

    return _pokemon[pkmn_name]["Type 1"]


def get_type2(pkmn_name: str) -> str:
    """The Pokemon's secondary type"""

    return _pokemon[pkmn_name]["Type 2"]


def get_hp(pkmn_name: str) -> int:
    """The Pokemon's amount of Hit Points, HP for short"""

    return _pokemon[pkmn_name]["HP"]


def get_attack(pkmn_name: str) -> int:
    """The Pokemon's attack stat, affects how much physical damage a Pokemon can do"""

    return _pokemon[pkmn_name]["Attack"]


def get_defense(pkmn_name: str) -> int:
    """The Pokemon's defense stat, affects how much physical damage a Pokemon can take before fainting"""

    return _pokemon[pkmn_name]["Defense"]


def get_special_attack(pkmn_name: str) -> int:
    """The Pokemon's special attack stat, affects how much special damage a Pokemon can do"""

    return _pokemon[pkmn_name]["Sp. Atk"]


def get_special_defense(pkmn_name: str) -> int:
    """The Pokemon's special defense stat, affects how much special damage a Pokemon can take before fainting"""

    return _pokemon[pkmn_name]["Sp. Def"]


def get_speed(pkmn_name: str) -> int:
    """The Pokemon's speed stat, determines which Pokemon can attack first in a battle"""

    return _pokemon[pkmn_name]["Speed"]


def get_type_effectiveness(attacker_type: str, defender_type: str) -> float:
    """The effectiveness of attacker's type against defender's type"""

    return _effectiveness[attacker_type][defender_type]
