from pathlib import Path

from streamlit.web import cli as stcli


def main() -> None:
    stcli.main_run([str(Path(__file__).with_name("app.py"))])


if __name__ == "__main__":
    main()
