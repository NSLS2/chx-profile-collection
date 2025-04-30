macro_list = ["optional_startup/lutz_macros/collection_uid.py",
              "usermacros/printing_macros_03012025.py",
             "optional_startup/30-SAXS_WAXS.py",
             "optional_startup/lutz_macros/3D_printing_setup.py"]

macro_dir = '/nsls2/data/chx/shared/config/bluesky/profile_collection/'
from termcolor import colored
for m in macro_list:
    try:
        exec(open(m).read())
        print(colored('successfully loaded %s'%m,'green'))
    except:
        print(colored('failed to load %s'%m,'red'))