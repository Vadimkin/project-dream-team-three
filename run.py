from app.utils import get_current_app

app = get_current_app()

if __name__ == '__main__':
    app.run(host='0.0.0.0')
