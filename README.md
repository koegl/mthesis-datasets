# mthesis Datasets

To rund DICOM ultrasound de-identification run deidentify_dcm_start.py (without any parameters).
- this will open a GUI with further explanations

To inspect images (e.g. if cropping was correct) run main.py in inspect_cropping. First change the path to the json
containing the paths to the folders in the main().
The json should look like this:

```
{
    "paths": [
        "path/to/folder1/containing/images",
        "path/to/folder2/containing/images",
        "path/to/folder3/containing/images"
    ]
}
```

Then press enter to accept an image or q and then enter to reject an image. to stop press s and enter. a text file
'rejected.txt' will be created in the folder above the first folder containing the paths to all the rejected images and
the path to the last file that was not rejected (so in the next run you can remove the checked paths form the json).
The rejected paths get appended to the text file, so old data is not lost.