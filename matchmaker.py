from flask import Flask, request, render_template, redirect, url_for, g,\
    session, escape, flash
from flask.ext.openid import OpenID
from openid.extensions import pape
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.ext.declarative import declarative_base
import logging
import math
import unicodedata
from models import db, User, Match, Pair, Conversation, Message, ExtinctCombo,\
    get_pair_list, get_user_list, \
    clear_all_users, clear_all_pairs, get_user_from_user_id, \
    get_pair_from_pair_id, get_match_from_match_id, \
    get_user_conversations_in_match, get_conversation_from_conversation_id
db.drop_all()
db.create_all()

log = logging.getLogger(__name__)
logging.basicConfig(filename="logs/main.log", level=logging.DEBUG)
app = Flask(__name__)

app.config.update(
    DATABASE_URI='sqlite:////tmp/flask-openid.db',
    SECRET_KEY='development key',
    DEBUG=True)

oid = OpenID(app, safe_roots=[], extension_responses=[pape.Response])

engine = create_engine(app.config['DATABASE_URI'])
db_session = scoped_session(sessionmaker(autocommit=False,
                                         autoflush=False,
                                         bind=engine))
Base = declarative_base()
Base.query = db_session.query_property()


def init_db():
    Base.metadata.create_all(bind=engine)


#class User(Base):
#    __tablename__ = 'users'
#    id = Column(Integer, primary_key=True)
#    name = Column(String(60))
#    email = Column(String(200))
#    openid = Column(String(200))

#    def __init__(self, name, email, openid):
#        self.name = name
#        self.email = email
#        self.openid = openid


@app.before_request
def before_request():
    g.user = None
    if 'openid' in session:
        g.user = User.query.filter_by(openid=session['openid']).first()


@app.after_request
def after_request(response):
    db_session.remove()
    return response


@app.route('/index')
def index():
    if 'email' in session:
        return 'Logged in as %s' % escape(session['username'])
        # EVENTUALLY WILL HAVE here link to username
    else:
        return 'You are not logged in'


@app.route('/', methods=['GET', 'POST'])
def base():
    return render_template("base.html")

@app.route('/facebook', methods=['GET', 'POST'])
def facebook():
    return render_template("facebook.html")

@app.route('/login', methods=['GET', 'POST'])
@oid.loginhandler
def login():
    if g.user is not None:
        return redirect(oid.get_next_url())
    if request.method == 'POST':
        openid = request.form.get('openid')
        if openid:
            pape_req = pape.Request([])
            return oid.try_login(openid, ask_for=['email', 'nickname'],
                                 ask_for_optional=['fullname'],
                                 extensions=[pape_req])
    return render_template('login.html', next=oid.get_next_url(),
                           error=oid.fetch_error())


@oid.after_login
def create_or_login(resp):
    session['openid'] = resp.identity_url
    if 'pape' in resp.extensions:
        pape_resp = resp.extensions['pape']
        session['auth_time'] = pape_resp.auth_time
    user = User.query.filter_by(openid=resp.identity_url).first()
    if user is not None:
        flash(u'Successfully signed in')
        g.user = user
        return redirect(oid.get_next_url())
    return redirect(url_for('create_profile', next=oid.get_next_url(),
                            name=resp.fullname or resp.nickname,
                            email=resp.email))


@app.route('/create-profile', methods=['GET', 'POST'])
def create_profile():
    # if g.user is not None or 'openid' not in session:
    #     return redirect(url_for('home'))
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        if not name:
            flash(u'Error: you have to provide a name')
        elif '@' not in email:
            flash(u'Error: you have to enter a valid email address')
        else:
            flash(u'Profile successfully created')
            db_session.add(User(name, email, session['openid']))
            db_session.commit()
            return redirect(oid.get_next_url())
    return render_template('create_profile.html', next_url=oid.get_next_url())


@app.route('/logout')
def logout():
    session.pop('openid', None)
    flash(u'You have been signed out')
#    return redirect(oid.get_next_url())
    return render_template("base.html")


@app.route("/signup")
def signup():
    return render_template("signup.html")


@app.route('/profile/<user_id>', methods=['POST', 'GET'])
def edit_profile(user_id):
    user_id = request.form['user_id']
    user = get_user_from_user_id(user_id)
    return render_template("profile.html", user=user)


@app.route("/matchmake/<user_id>", methods=['GET', 'POST'])
def matchmake(user_id):
    user_id = request.form['user_id']
    user = get_user_from_user_id(user_id)
    log.debug("MATCHMAKE {}".format(user.username))
    try:
        next_pair = user.get_next_pair()
        log.debug("Offering {} for user {}".format(next_pair, user))
        error = None
        descriptions = next_pair.get_descriptions()
    except Exception:
        next_pair = None
        descriptions = ["nothing", "nothing"]
        error = "no pairs"
    return render_template("matchmake.html",
                           user=user,
                           next_pair=next_pair,
                           error=error,
                           descriptions=descriptions)


@app.route("/matches/<user_id>", methods=['POST', 'GET'])
def matches(user_id):
    user_id = request.form['user_id']
    user = get_user_from_user_id(user_id)
    match_list = user.get_match_list()
    log.debug("USER {} HAS MATCH LIST {}".format(user, match_list))
    return render_template("matches.html", user=user)


@app.route("/match/<match_id>", methods=['POST', 'GET'])
def match(match_id):
    match_id = request.form['match_id']
    user_id = request.form['user_id']
    user = get_user_from_user_id(user_id)
    match = get_match_from_match_id(match_id)
    print " user_id is {}".format(user_id)
    print " match user ids are {}".format(match.get_user_ids())
    if int(user_id) is int(match.get_user_ids()[1]):
        otheruser_id = match.get_user_ids()[0]
        x = ""
    elif int(user_id) is int(match.get_user_ids()[0]):
        otheruser_id = match.get_user_ids()[1]
        x = ""
    else:
        user_id = match.get_user_ids()[1]
        otheruser_id = match.get_user_ids()[0]
        x = "to start wingmanning"
    print "match user ids are {} and {}, ids I'm using are {} and {}".format(match.get_user_ids()[0], match.get_user_ids()[1], user_id, otheruser_id)
    conversation = get_user_conversations_in_match(match_id, user_id, otheruser_id)
    conversation_messages = conversation.get_message_strings_list()
    conversation_length = len(conversation_messages)
    print "FIRST type of conv_messages is {} ".format(type(conversation_messages))
    return render_template("match.html", user=user, match=match,
                           conversation=conversation,
                           conversation_messages=conversation_messages,
                           conversation_length=conversation_length, x=x)


@app.route("/addingmessage", methods=['POST', 'GET'])
def addingmessage():
    conversation_id = request.form['conversation_id']
    conversation = get_conversation_from_conversation_id(conversation_id)
    print "conversation is: ", conversation
    match_id = request.form['match_id']
    user_id = request.form['user_id']
    user = get_user_from_user_id(user_id)
    match = get_match_from_match_id(match_id)
    newmessage = request.form['newmessage']
    print "New message is :", newmessage
    conversation.add_message(newmessage, user_id)
    conversation_messages = conversation.get_message_strings_list()
    conversation_length = len(conversation_messages)
    return render_template("match.html", user=user, match=match,
                           conversation=conversation,
                           conversation_messages=conversation_messages,
                           conversation_length=conversation_length,
                           x="")


@app.route('/intermediate', methods=['POST', 'GET'])
def intermediate():
    name = request.form['name']
    email = request.form['email']
    description = request.form['user_description']
    user = User(name, email, description)
    user.start()
    return render_template("continue.html", user=user)


@app.route('/home/<user_id>', methods=['POST', 'GET'])
def home(user_id):
    user_id = request.form['user_id']
    user = get_user_from_user_id(user_id)
    return render_template("home.html", user=user)


@app.route('/happy/<user_id>', methods=['POST', 'GET'])
def happy(user_id):
    pair_id = request.form['pair_shown_id']
    pair_matched = get_pair_from_pair_id(pair_id)
    user_id = request.form['user_id']
    user = get_user_from_user_id(user_id)
    user.make_pair_match(pair_matched)
    return render_template("happy.html", user=user,
                           pair_matched=pair_matched)


@app.route('/sad/<user_id>', methods=['POST', 'GET'])
def sad(user_id):
    pair_id = request.form['pair_shown_id']
    pair_shown = get_pair_from_pair_id(pair_id)
    user_id = request.form['user_id']
    user = get_user_from_user_id(user_id)
    pair_shown.decline_this_pair(user_id)
    log.debug("Pair: {} declined by: {}".format(pair_shown, user))
    return render_template("sad.html", user=user,
                           pair_shown=pair_shown)


@app.route('/user/<username>')
def show_user_profile(username):
    # show the user profile for that user
    return 'User %s' % username


@app.route('/post/<int:post_id>')
def show_post(post_id):
    # show the post with the given id, the id is an integer
    return 'Post %d' % post_id


if __name__ == "__main__":

    app.run(host='0.0.0.0', port=5000)
