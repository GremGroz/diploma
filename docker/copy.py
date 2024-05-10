import os
import shutil

def create_and_copy_file(filename, volume_path):

    # Копируем файл в volume
    destination_path = os.path.join(volume_path, filename)
    shutil.copy(filename, destination_path)


print("Запуск копирую...")
# Example usage
create_and_copy_file("grade.json", "/data")