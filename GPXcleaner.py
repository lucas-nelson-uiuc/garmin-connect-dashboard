import pandas as pd
from datetime import datetime
import gpxpy
import pytz
from haversine import haversine, Unit


def read_gpx_file(file_path):
    gpx_file = open(file_path)
    return gpxpy.parse(gpx_file)

def gpx_to_dataframe(file_path):

    points_skeleton = [
        [point.latitude, point.longitude, point.elevation, point.time]
        for track in read_gpx_file(file_path).tracks
        for segment in track.segments
        for point in segment.points
    ]

    points_df =  pd.DataFrame(
        points_skeleton,
        columns=['latitude', 'longitude', 'elevation', 'time']
    )
    
    return points_df

def convert_date(time_col):
    return pd.to_datetime(time_col.dt.date)

def convert_time(time_col):
    return time_col.dt.time

def get_elevation_diff(elev_col):
    return elev_col.diff(1).fillna(0)

def get_shifted_col(col):
    return col.shift(1)

def calculate_haversine(list_de_lat_lon):
    lat1, lon1, lat2, lon2 = list_de_lat_lon
    return haversine(
        (lat1, lon1), (lat2, lon2),
        unit=Unit.METERS
    )

def get_moving_average_col(col, ma=5):
    return col.rolling(window=ma).mean().fillna(method='bfill')

def calculate_gradient(elev_diff_col, dist_col):
    elev_diff_ma5 = get_moving_average_col(elev_diff_col)
    dist_col_ma5 = get_moving_average_col(dist_col)
    return elev_diff_ma5 / dist_col_ma5 * 100

def drop_cols(df, *args):
    return df.drop(columns=list(args))

def time_to_tz_native(t, tz_in, tz_out):
    return tz_in.localize(datetime.combine(datetime.today(), t)).astimezone(tz_out).time()
    
def raw_to_reuben(raw_df):
    # create copy of dataframe for security
    points_df = raw_df.copy()

    # convert date and time to respective datetime.objects
    points_df['date'] = convert_date(points_df['time'])
    points_df['time'] = convert_time(points_df['time'])

    # change in elevation between measurements
    points_df['elevation_diff'] = get_elevation_diff(points_df['elevation'])
    
    # latitude/longitude of n=1 future observation
    points_df['proj_latitude'] = get_shifted_col(points_df['latitude']).fillna(points_df['latitude'].iloc[0])
    points_df['proj_longitude'] = get_shifted_col(points_df['longitude']).fillna(points_df['longitude'].iloc[0])
    
    # distance between observed point and n=1 future point
    points_df['distance'] = points_df[['latitude', 'longitude', 'proj_latitude', 'proj_longitude']
                                ].apply(calculate_haversine, axis=1)
    
    # convert to local time
    points_df['local_time'] = points_df['time'].apply(
        lambda t: time_to_tz_native(t, pytz.utc, pytz.timezone(pytz.all_timezones[pytz.all_timezones.index('America/Chicago')]))
        )
    
    # get time differences to calculate speeds
    points_df['time_elapsed'] = points_df['local_time'].apply(
        lambda x: (x.hour * 60**2) + (x.minute * 60**1) + (x.second * 60**0)
    )
    points_df['time_between_measure'] = points_df['time_elapsed'].diff(1).fillna(0).astype(int)
    points_df['speed_kmh'] = points_df['speed_kmh'] = points_df[['distance', 'time_between_measure']].apply(lambda x: (x[0]/x[1]) * 3.6, axis=1).fillna(0)
    
    # smooth (using moving average) speed and gradient
    points_df['speed_kmh_ma5'] = get_moving_average_col(points_df['speed_kmh'])
    points_df['gradient'] = calculate_gradient(points_df['elevation_diff'], points_df['distance'])
    points_df['gradient_ma5'] = get_moving_average_col(points_df['gradient'])

    # return the bad boy
    return drop_cols(points_df, 'time_between_measure', 'proj_latitude', 'proj_longitude')
