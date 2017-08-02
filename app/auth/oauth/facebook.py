from flask_oauth import OAuth

from app.utils import get_current_app

with get_current_app().app_context():
    current_app = get_current_app()

    oauth = OAuth()

    consumer_key = current_app.config.get('FACEBOOK_CONSUMER_KEY')
    consumer_secret = current_app.config.get('FACEBOOK_CONSUMER_SECRET')

    facebook = oauth.remote_app(
        name='facebook',
        base_url='https://graph.facebook.com/',
        request_token_url=None,
        access_token_url='/oauth/access_token',
        authorize_url='https://www.facebook.com/dialog/oauth',
        consumer_key=consumer_key,
        consumer_secret=consumer_secret,
        request_token_params={'scope': 'email'},
    )