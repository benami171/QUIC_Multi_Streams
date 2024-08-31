import os
import random

def generate_data_file(file_name: str, size_in_mb: int):
    file_path = os.path.join(os.getcwd(), file_name)
    characters = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ'
    data = ''.join(random.choice(characters) for _ in range(size_in_mb * 1024 * 1024))
    with open(file_path, 'w') as file:
        file.write(data)

if __name__ == "__main__":
    generate_data_file("random_data_file.txt", 2)