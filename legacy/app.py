from main import TrixApp


def run():
    TrixApp().run()


# alias so pyproject.toml can use either app:run or app:main
main = run


if __name__ == "__main__":
    run()
