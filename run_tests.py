def test_process_file():
    from processor import process_file
    # Empty bytes – extract_text returns "", no API call, so it's safe without key
    result = process_file(b"")
    assert isinstance(result, list), "Result should be a list"
    print("test_process_file passed.")

if __name__ == "__main__":
    test_process_file()
    print("All tests passed.")
