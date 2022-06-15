import pathlib
def make_blank_webpage(page_name):
    """
    Create a blank webpage directory and boilerplate code.
    """
    page_dir = f"./application/webassets/{page_name}"
    pathlib.Path(page_dir).mkdir(parents=True, exist_ok=False)
    pathlib.Path(page_dir + "/" + page_name + ".txt").touch()
if __name__ == "__main__":
    input_page_name = input("Enter the name of the webpage: ")
    make_blank_webpage(input_page_name)