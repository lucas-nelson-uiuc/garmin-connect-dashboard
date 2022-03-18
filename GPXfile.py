import os
from GPXcleaner import gpx_to_dataframe, raw_to_reuben

class GPXfile:

    def __init__(self, file_path):
        self.file_path = file_path
        # self.gc = GPXcleaner()
        self.parent_dir = self.get_parent_dir()
        self.raw_df = gpx_to_dataframe(self.file_path)
        self.reuben_df = raw_to_reuben(self.raw_df.copy())
    
    def get_parent_dir(self):
        parent_dir = self.file_path.split('/')[1]
        return parent_dir if os.path.isdir(parent_dir) else None
    
if __name__ == '__main__':
    path = '../exports-garmin-connect/2022-03-16_garmin_connect_export/activity_8469420143.gpx'
    f = GPXfile(path)
    print(f.reuben_df)
