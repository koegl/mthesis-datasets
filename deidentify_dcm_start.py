# command to compile everything into one executable (the argument at the front is to handle pydicom errors)
# pyinstaller --collect-submodules pydicom.encoders deidentify_dcm_start.py --name=deidentify_dcm_m1 --onefile

from deidentify_dcm.main_func import main

if __name__ == "__main__":
    main()
