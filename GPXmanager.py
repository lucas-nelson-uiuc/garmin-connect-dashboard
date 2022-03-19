import os
import sys
import warnings
warnings.filterwarnings('ignore')

import GPXcleaner as gc
import DIRhelper as dh


def raw_gpx_to_reuben_gpx(gpx_path):
    
    raw_df = gc.gpx_to_dataframe(gpx_path)
    
    # create copy of dataframe for security
    points_df = raw_df.copy()

    # convert date and time to respective datetime.objects
    points_df['date'] = gc.convert_date(points_df['time'])
    points_df['time'] = gc.convert_time(points_df['time'])

    # change in elevation between measurements
    points_df['elevation_diff'] = gc.get_elevation_diff(points_df['elevation'])
    
    # latitude/longitude of n=1 future observation
    points_df['proj_latitude'] = gc.get_shifted_col(points_df['latitude']).fillna(points_df['latitude'].iloc[0])
    points_df['proj_longitude'] = gc.get_shifted_col(points_df['longitude']).fillna(points_df['longitude'].iloc[0])
    
    # distance between observed point and n=1 future point
    points_df['distance'] = points_df[['latitude', 'longitude', 'proj_latitude', 'proj_longitude']
                                ].apply(gc.calculate_haversine, axis=1)
    
    # convert to local time
    points_df['local_time'] = points_df['time'].apply(gc.convert_timezone)
    
    # get time differences to calculate speeds
    points_df['time_elapsed'] = points_df['local_time'].apply(
        lambda x: (x.hour * 60**2) + (x.minute * 60**1) + (x.second * 60**0)
    )
    points_df['time_between_measure'] = points_df['time_elapsed'].diff(1).fillna(0).astype(int)
    points_df['speed_kmh'] = points_df['speed_kmh'] = points_df[['distance', 'time_between_measure']].apply(lambda x: (x[0]/x[1]) * 3.6, axis=1).fillna(0)
    
    # smooth (using moving average) speed and gradient
    points_df['speed_kmh_ma5'] = gc.get_moving_average_col(points_df['speed_kmh'])
    points_df['gradient'] = gc.calculate_gradient(points_df['elevation_diff'], points_df['distance'])
    points_df['gradient_ma5'] = gc.get_moving_average_col(points_df['gradient'])

    # return the bad boy
    return gc.drop_cols(points_df, 'time_between_measure', 'proj_latitude', 'proj_longitude')

def write_to_id_dir(gpx_path, backup_dir, extension='csv'):

    gpx_df = raw_gpx_to_reuben_gpx(gpx_path)
    gpx_file_id = gpx_path[gpx_path.rfind('_') + 1 : gpx_path.find('.gpx')]
    gpx_file_date = gpx_df['date'].iloc[0].date().strftime('%Y-%m-%d')
    gpx_file_root = f"{gpx_file_date}-{gpx_file_id}.{extension}"
    gpx_id_found = 'no'

    while gpx_id_found == 'no':
        for activity in os.listdir(backup_dir):
            for file in os.listdir(f'{backup_dir}/{activity}'):
                if gpx_file_root in file:
                    gpx_file_dir = activity
                    gpx_id_found = 'yes'

    gpx_file_path = f'{backup_dir}/{gpx_file_dir}/{gpx_file_root}'
    
    if not os.path.isfile(gpx_file_path):
        with open(gpx_file_path, 'w') as f:
            gpx_df.to_csv(f, index=False)
    
    if os.path.isfile(gpx_file_path):
        success += 1; total += 1
        print(
            '\tSuccess {:<12}: {}'.format(
                f'[{success}/{total}]',
                gpx_file_path
            )
        )
    else:
        failure += 1; total += 1
        print(
            '\tFailure {:<12}: {}'.format(
                f'[{failure}/{total}]',
                gpx_file_path
            )
        )
    
    print()


if __name__ == '__main__':
    
    arguments = sys.argv[1:]
    backup_dir = arguments['backup' in arguments[1]]
    gpx_dir = arguments[backup_dir == arguments[0]]

    while not os.path.exists(backup_dir):
        print(f'{backup_dir} is not a valid directory. Please create before running this script.')
        sys.exit()

    while not os.path.exists(gpx_dir):
        print(f'{gpx_dir} is not a valid directory. Please create before running this script.')
        sys.exit()
    
    if '.DS_Store' in os.listdir(backup_dir):
        dh.remove_DS_Store(backup_dir)
    
    gpx_files = map(
        lambda g: f'{gpx_dir}/{g}',
        filter(
            lambda f: f.endswith('.gpx'),
            os.listdir(gpx_dir)
            )
        )
    
    print('>> CHECKING CURRENT BACKUP DIRECTORY STATUS')
    prior_status = dh.prior_backup_directory_status(backup_dir)
    
    print('>> STARTING BACKUP PROCESS')
    for gpx_file in gpx_files:
        write_to_id_dir(gpx_file, backup_dir)
    
    while not os.path.isdir(backup_dir):
        backup_dir = input('|| Enter valid backup directory ||\n> ')
    
    print('>> CHECKING UPDATED BACKUP DIRECTORY STATUS')
    dh.completion_summary_statistics(backup_dir, prior_status)

    print('>> BACKUP PROCESS COMPLETE')
