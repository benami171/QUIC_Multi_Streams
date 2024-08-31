import os

def generate_data_file(file_name: str, size_in_mb: int):
    file_path = os.path.join(os.getcwd(), file_name)
    with open(file_path, 'wb') as file:
        file.write(os.urandom(size_in_mb * 1024 * 1024))

if __name__ == "__main__":
    generate_data_file("random_data_file", 10)