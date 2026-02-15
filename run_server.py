from __future__ import annotations

from backend.app import create_app


def main() -> None:
    app = create_app()
    print("Iniciando servidor Flask na porta 5000...")
    app.run(debug=True, port=5000)


if __name__ == "__main__":
    main()

