# Sourced from: https://julienharbulot.com/python-dynamical-import.html

from importlib import import_module
from inspect import isclass
from pathlib import Path
from pkgutil import iter_modules

from broker.message_generators.message_generator import MessageGenerator as BaseClass

# iterate through the modules in the current package
# import all subclasses of MessageGenerator

package_dir = Path(__file__).resolve().parent
for (_, module_name, _) in iter_modules([package_dir]):
    # import the module and iterate through its attributes
    module = import_module(f"{__name__}.{module_name}")
    for attribute_name in dir(module):
        attribute = getattr(module, attribute_name)

        if isclass(attribute) \
                and attribute is not BaseClass \
                and issubclass(attribute, BaseClass):
            # Add the class to this package's variables
            globals()[attribute_name] = attribute
