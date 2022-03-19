import os


def prior_backup_directory_status(backup_dir):
    
    print('>> PRIOR BACKUP DIRECTORY STATUS')

    if len(os.listdir(backup_dir)) == 0:
        retr_dict = {}
    
    else:
        retr_dict = {}
        for activity in os.listdir(backup_dir):
            activity_dir = backup_dir + f'/{activity}'
            retr_dict[activity] = {
                'prior_files': len(os.listdir(activity_dir)),
                'prior_size': os.path.getsize(activity_dir)
            }
    
            print(f'''
            -> {activity}
                Files: {retr_dict[activity]['prior_files']}
                Size : {retr_dict[activity]['prior_size']}
            ''')
    
    return retr_dict

def remove_DS_Store(backup_dir):
    os.remove(f'{backup_dir}/.DS_Store')

def completion_summary_statistics(backup_dir, prior_status_dict):
    
    for activity in os.listdir(backup_dir):
        if activity in prior_status_dict:
            old_files = prior_status_dict[activity]['prior_files']
            total_files = len(os.listdir(f'{backup_dir}/{activity}'))
            old_size = prior_status_dict[activity]['prior_size']
            total_size = len(os.listdir(f'{backup_dir}/{activity}'))
        else:
            old_files, old_size = 0, 0
            total_files = len(os.listdir(f'{backup_dir}/{activity}'))
            total_size = os.path.getsize(f'{backup_dir}/{activity}')

        print(f'''
        -> {activity}
            New files: [{total_files - old_files}/{total_files}]
            New size : [{total_size - old_size}/{total_size}]
        ''')
