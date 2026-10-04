import os

def remove_empty_folders(path):
    """
    Recursively removes all empty folders and subfolders within the given path.
    A folder is considered empty if it contains no files or only other empty folders.
    """
    if not os.path.isdir(path):
        print(f"Error: '{path}' is not a valid directory.")
        return

    cnt = 1
    loop_cnt = 1
    while cnt > 0:
        print(f"Loop {loop_cnt}")
        loop_cnt += 1
        cnt = 0
        for dirpath, dirnames, filenames in os.walk(path, topdown=False):
            # topdown=False ensures that subfolders are processed before their parents,
            # allowing for deletion of empty subfolders before checking their parent.
            if not dirnames and not filenames:
                try:
                    cnt += 1
                    os.rmdir(dirpath)
                    print(f"Removed empty directory: {dirpath}")
                except OSError as e:
                    print(f"Error removing directory {dirpath}: {e}")

if __name__ == "__main__":
    target_directory = input("Enter the path of the directory to clean: ")
    remove_empty_folders(target_directory)
    input("Empty folder cleanup complete.")