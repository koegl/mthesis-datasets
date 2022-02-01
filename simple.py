import json

# file = open("C:\\Users\\fryde\\Documents\\university\\master\\thesis\\code\\available_data_read.json")

# data = json.load(file)

# print(4)


d = {
    "patient_zero": {
        "Pre-op Imaging": [],
        "Intra-op Imaging": {
            "Ultrasounds": [],
            "rest": []
        },
        "Continuous Tracking Data": {
            "Pre-iMRI Tracking": [],
            "Post-iMRI Tracking": []
        },
        "Segmentations": {
            "Pre-op fMRI Segmentations": [],
            "Pre-op Brainlab Manual DTI Tractography Segmentations": [],
            "rest": []
        }
    },
}

f = open("C:\\Users\\fryde\\Documents\\university\\master\\thesis\\code\\available_data_write.json", "w")
json.dump(d, f)
f.close()
