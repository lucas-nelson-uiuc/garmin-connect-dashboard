from GPXfile import GPXfile
import GPXcleaner
from file_manager import FileManager
import pandas as pd


class Aggregator:
    
    def __init__(self):
        self.file_manager = FileManager()
    
    def clean_single_files(self):
        clean_dfs = []
        gpx_dict = self.file_manager.return_file_type_export_dir()
        gpx_paths = gpx_paths = list(
            map(
                lambda sub_dir: list(
                map(
                    lambda file: f'{self.export_dir}/{sub_dir}/{file}',
                    gpx_dict[sub_dir])),
                gpx_dict
                )
            )

        for file in gpx_paths:
            clean_dfs.append(GPXcleaner(file))