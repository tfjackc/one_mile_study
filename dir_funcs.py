import os


def create_folder(one_mile_dir, folder_name):
    study_dir = os.path.join(one_mile_dir, folder_name)
    if os.path.exists(study_dir):
        print(f"Already Exists: {study_dir}")
    else:
        print(f"Creating Directory: {study_dir}")
        os.mkdir(study_dir)
    return study_dir


def delete_folder(target_property):
    one_mile_dir = os.getcwd()
    taxlot_dir = target_property
    study_dir = os.path.join(one_mile_dir, taxlot_dir)
    if os.path.exists(study_dir):
        print(f"deleting: {study_dir}")
    else:
        print(f"{study_dir} Does not exist")
