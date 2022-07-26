from Resources.Logic.nifti_exporting_logic import NiftiExportingLogic
from Resources.Logic.dicom_exporting_logic import DicomExportingLogic


class ExportWrapper:
    """
    Class to wrap around the exporting classes
    """

    def __init__(self,
                 output_folder,
                 export_type='NIFTI'):

        self.output_folder = output_folder
        self.export_type = export_type

        if self.export_type.lower() == 'nifti':
            self.exporting_logic = NiftiExportingLogic(output_folder)
        elif self.export_type.lower() == 'dicom':
            self.exporting_logic = DicomExportingLogic(output_folder)
        else:
            raise ValueError('Export type not supported')

    def export(self, parent_identity=False, resample_spacing=False, deidentify=False, case='000'):
        self.exporting_logic.full_export(parent_identity, resample_spacing, deidentify, case)


