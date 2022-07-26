import os


parent_folder = "/Users/fryderykkogl/Data/temp/file_names"

# list all .mrb files in the folder and its subfolders
mrb_files = []
for root, dirs, files in os.walk(parent_folder):
    for file in files:
        if file.endswith(".mrb"):
            mrb_files.append(os.path.join(root, file))

#%%
# rename all .mrb files to .zip
for mrb_file in mrb_files:
    os.rename(mrb_file, mrb_file.replace(".mrb", ".zip"))


#%%
# list all .nrrd files
nrrd_files = []
for root, dirs, files in os.walk(parent_folder):
    for file in files:
        if file.endswith(".nrrd"):

            if file.lower() not in nrrd_files:
                nrrd_files.append(file.lower())

#%% wrtie the list of nrrd files to a text file
with open(os.path.join(parent_folder, "segmentations.txt"), "w") as f:
    for nrrd_file in segmentations:
        f.write(nrrd_file + "\n")

#%%
# read file names from previously saved text file
with open(os.path.join(parent_folder, "volumes.txt"), "r") as f:
    volumes = f.readlines()
    volumes = [x.strip() for x in volumes]

#%%
volumes_no_rage = [x for x in volumes if "rage" not in x]
volumes_rage = [x for x in volumes if "rage" in x]


"""
MRI:
{caseXXX}-{3D/2D}-{AX/COR/SAG}-{T1/T2}-*{MPRAGE/MP2RAGE/FLAIR/BLADE/SPACE/}-*{rare_modifiers}-{preop/intraop}
* - optional parameters (rare_modifiers - in case there is something special about a specific volume)

examples:
case001-3D-AX-T1-preop
case042-3D-AX-T1-MPRAGE-preop
case999-2D-COR-T2-BLADE-intraop
case103-3D-SAG-T2-preop

Segmentations:
{caseXXX}-{preop_resection_cavity/cerebrum/ventricles/tumor}-*{target/non-targeted_nodule/residual}-{corresponding_scan_identifier}
* - optional parameter

examples:
case001-preop_resection_cavity-3D-AX-T1-preop
case042-cerebrum-3D-AX-T1-MPRAGE-preop
case999-tumor-2D-COR-T2-BLADE-intraop
case103-tumor-residual-3D-SAG-T2-preop

Ultrasound:
{caseXXX}-{US1-pre-dura/US2-post-dura/US3-pre-imri}

examples:
case001-US1-pre-dura
case042-US2-post-dura
case999-US3-pre-imri

"""