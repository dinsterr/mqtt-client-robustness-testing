# Partially sourced from: https://julienharbulot.com/python-dynamical-import.html
from importlib import import_module
from inspect import isclass
from pathlib import Path
from pkgutil import iter_modules
import logging

from broker.message_generators.message_generator import MessageGenerator as BaseClass

# iterate through the modules in the current package
# and import all subclasses of MessageGenerator in the current directory

found_generators = []
package_dir = Path(__file__).resolve().parent
for (parent_path, module_name, is_package) in iter_modules([str(package_dir)]):
    if is_package:
        continue

    # import the module and iterate through its attributes to validate that it is a subclass of the MessageGenerator
    module = import_module(f"{__name__}.{module_name}")
    for attribute_name in dir(module):
        attribute = getattr(module, attribute_name)

        if isclass(attribute) \
                and attribute is not BaseClass \
                and issubclass(attribute, BaseClass):
            # Add the class to this package's variables
            globals()[attribute_name] = attribute
            found_generators.append(attribute._GENERATOR_TYPE)

logging.info(f"Found available message generators: {', '.join(found_generators)}\n")
