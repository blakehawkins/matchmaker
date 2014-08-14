from flask import Flask
from flask.ext.sqlalchemy import SQLAlchemy
from random import shuffle
import math
import logging

log = logging.getLogger(__name__)
logging.basicConfig(filename="logs/main.log", level=logging.DEBUG)
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////tmp/test.db'
db = SQLAlchemy(app)


def is_combo_extinct(user_id, pair_id):
    extinct_combos = ExtinctCombo.query.filter_by(user_id=user_id).all()
    for extinct_combo in extinct_combos:
        if extinct_combo in ExtinctCombo.query.filter_by(pair_id=pair_id).all():
            print "Combo is extinct: ", extinct_combo
            return extinct_combo
        else:
            print "Combo is not extinct."
            return False
    return False


def get_pair_list():
    list_of_pairs = Pair.query.all()
    return list_of_pairs


def get_user_list():
    list_of_users = User.query.all()
    return list_of_users


def clear_all_users():
    list_of_users = get_user_list()
    for user in list_of_users:
        db.session.delete(user)

    db.session.commit()
    print "Deleted all users!"


def clear_all_pairs():
    list_of_pairs = get_pair_list()
    for pair in list_of_pairs:
        db.session.delete(pair)

    db.session.commit()
    print "Deleted all pairs!"


def get_user_from_user_id(user_id):
    user = User.query.filter_by(id=user_id).first_or_404()
    return user


def get_message_from_message_id(message_id):
    message = Message.query.filter_by(id=message_id).first_or_404()
    return message


def get_pair_from_pair_id(pair_id):
    pair = Pair.query.filter_by(id=pair_id).first_or_404()
    return pair


def get_match_from_match_id(match_id):
    match = Match.query.filter_by(id=match_id).first_or_404()
    return match


def get_conversation_from_conversation_id(conversation_id):
    conversation = Conversation.query.filter_by(id=conversation_id).first_or_404()
    return conversation


def get_user_conversations_in_match(match_id, user_id1, user_id2):
    all_conversations = Conversation.query.filter_by(match_id=match_id).all()
    print "All conversations: ", all_conversations
    print "user1 and user2: ", user_id1, user_id2
    user_id1 = int(user_id1)
    user_id2 = int(user_id2)
    for convo in all_conversations:
        print "convo.user_ids", convo.user_ids
        if user_id1 in convo.user_ids:
            print "user1 in convo"
            if user_id2 in convo.user_ids:
                print "user2 in convo", convo
                return convo
        else: 
            print "users not in this convo"


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True)
    email = db.Column(db.String(120), unique=True)
    user_description = db.Column(db.String(140))

    def __init__(self, username, email, description=""):
        self.username = username
        self.email = email
        default_description = "I have nothing to say about myself."
        if description == "":
            description = default_description

        self.user_description = description

    def __repr__(self):
        return "<User {}>".format(self.username)

    def make_pairs_for_new_user(self):
        existing_users = get_user_list()
        for user in existing_users:
            if self.id != user.id:
                pair = Pair([user.id, self.id])
                pair.start()

    def start(self):
        # Must be called just after new user is made
        db.session.add(self)
        db.session.commit()
        self.make_pairs_for_new_user()
        log.debug("Starting User {}".format(self))

    def get_next_pair(self):
        pair_list = get_pair_list()
        error_string = None
        shuffle(pair_list)
        for pair in pair_list:
            i_am_in_pair = self.id in pair.get_user_ids()
            # print "Am I in pair: ", i_am_in_pair
            pair_is_a_match = pair.is_match()
            # print "Is this pair a match?", pair_is_a_match
            extinct_combo = is_combo_extinct(self.id, pair.id)
            if extinct_combo is not False:
                pair_seen_by_me = True
            else:
                pair_seen_by_me = False
            # print "Pair seen by me?", pair_seen_by_me

            if i_am_in_pair or pair_seen_by_me or pair_is_a_match:
            #    print "Shouldn't be offered as a pair."
                pass
            else:
            #    print "Offering pair: ", pair
                break
        else:
            error_string = "No pairs available."

        if error_string is None:
            return pair
        else:
            Exception(error_string)

    def get_description(self):
        return self.user_description

    def edit_description(self, new_text):
        self.user_description = new_text
        db.session.commit()

    def make_pair_match(self, pair):
        log.debug("{} calling make_pair_match on pair: {}".format(self, pair))
        match = pair.pair_to_match(self.id)
        return match

    def get_match_list(self):
        list_of_matches = Match.query.all()
        print "{}.get_match_list - list of matches is: {}".format(
            self, list_of_matches)
        list_my_matches = []
        for match in list_of_matches:
            match_user_ids = match.get_user_ids()
            if self.id in match_user_ids:
                list_my_matches.append(match)
        return list_my_matches

    def matches_as_wingman(self):
        list_of_matches = Match.query.all()
        print "list of matches is: {}".format(list_of_matches)
        wingman_matches = []
        for match in list_of_matches:
            match_user_ids = match.get_user_ids()
            if self.id is match.wingman_id:
                wingman_matches.append(match)
        return wingman_matches

    def get_username(self):
        return self.username


class Pair(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_ids = db.Column(db.PickleType)
    seen_by = db.Column(db.PickleType)
    is_this_a_match = db.Column(db.Boolean)

    def __init__(self, user_ids):
        # user_ids is a list of user ids
        self.user_ids = user_ids
        self.seen_by = []
        self.is_this_a_match = False

    def __repr__(self):
        user1_id = self.user_ids[0]
        user2_id = self.user_ids[1]
        return "<Pair {}, {}>".format(user1_id, user2_id)

    def start(self):
        db.session.add(self)
        db.session.commit()
        log.debug("Starting pair: {}".format(self))
        
    def is_match(self):
        return self.is_this_a_match

    def get_user_ids(self):
        return self.user_ids

    def get_usernames(self):
        user_ids = self.user_ids
        usernames = []
        for user_id in user_ids:
            user = get_user_from_user_id(user_id)
            usernames.append(user.username)

        return usernames

    def get_descriptions(self):
        user_ids = self.user_ids
        descriptions = []
        for user_id in user_ids:
            user = get_user_from_user_id(user_id)
            descriptions.append(user.user_description)

        return descriptions

    def get_seen_by(self):
        log.debug("get_seen_by called on {}".format(self))
        return self.seen_by

    def add_seen_by(self, user_id):
        self.seen_by.append(user_id)
        db.session.commit()

    def pair_to_match(self, wingman_id):
        log.debug("User {} matching {}".format(wingman_id, self))
        match = Match(self, wingman_id)
        self.is_this_a_match = True
        db.session.commit()
        match.start()
        return match

    def decline_this_pair(self, user_id):
        extinct_combo = ExtinctCombo(user_id, self.id)
        extinct_combo.start()
        return extinct_combo


class Match(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    pair_id = db.Column(db.Integer, unique=True)
    user_ids = db.Column(db.PickleType)
    conversaton_id = db.Column(db.Integer, unique=True)
    wingman_conversation_id = db.Column(db.Integer, unique=True)
    wingman_id = db.Column(db.Integer)

    def __init__(self, pair, wingman_id):
        print "Pair.get_user_ids: ", pair.get_user_ids()
        self.pair_id = pair.id
        print "Making new match with pair: ", self.pair_id
        self.user_ids = [pair.get_user_ids()[0], pair.get_user_ids()[1]]
        self.wingman_id = wingman_id
        self.yes_list = []

    def __repr__(self):
        return "<Match {}, {}>".format(self.user_ids[0], self.user_ids[1])

    def start(self):
        db.session.add(self)
        # print "Added ", self, "to db"
        db.session.commit()
        # print "Committed ", self, "to db"
        # print ("<Making Conversation between: {} and" +
        #       " {}>").format(self.user_ids[0], self.user_ids[1])
        conversation = Conversation(self, self.user_ids)
        conversation.start()
        self.conversation_id = conversation.id
        db.session.commit()
        convo_ids_1 = [self.wingman_id, self.user_ids[0]]
        # print "<Making Conversation between: {} and {}>".format(convo_ids_1[0],
        #                                                        convo_ids_1[1])
        wingman_conversation = Conversation(self, convo_ids_1)
        wingman_conversation.start()
        self.wingman_conversation_id = wingman_conversation.id
        db.session.commit()
        convo_ids_2 = [self.wingman_id, self.user_ids[1]]
        log.debug("<Making Conversation between: {} and {}>".format(
            convo_ids_2[0],
            convo_ids_2[1]))
        wingman_conversation = Conversation(self, convo_ids_2)
        wingman_conversation.start()
        self.wingman_conversation_id = wingman_conversation.id
        db.session.commit()

    def both_say_yes(self):
        length = len(self.yes_list)
        if length == 2:
            return True
        else:
            return False

    def get_user_ids(self):
        return self.user_ids

    def get_usernames(self):
        user_ids = self.user_ids
        usernames = []
        for user_id in user_ids:
            user = get_user_from_user_id(user_id)
            usernames.append(user.username)
        return usernames

    def say_yes(self, user_id):
        if user_id not in self.yes_list:
            self.yes_list.append(user_id)


class Conversation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    match_id = db.Column(db.Integer)
    user_ids = db.Column(db.PickleType)

    def __init__(self, match, user_ids):
        self.match_id = match.id
        self.user_ids = user_ids
        print "user_ids in conversation set as {}".format(self.user_ids)

    def __repr__(self):
        return "<Conversation between: {} and {}>".format(self.user_ids[0],
                                                          self.user_ids[1])

    def start(self):
        db.session.add(self)
        print "Added ", self, "to db"
        db.session.commit()
        print "Committed ", self, "to db"
        i1 = get_user_from_user_id(self.user_ids[0]).username
        i2 = get_user_from_user_id(self.user_ids[1]).username
        message_text = ("Welcome to the conversation " +
                        "between {} and {}").format(i1, i2)
        self.add_message(message_text)

    def get_message_ids(self):
        return self.message_ids

    # Only call this one...
    # Get conversation
    def get_message_strings_list(self):
        message_strings_list = []
        message_list = Message.query.filter_by(conversation_id=self.id).all()
        for message in message_list:
            message_to_print = message.get_message_string()
            message_strings_list.append(message_to_print)
        return message_strings_list

    # And this.
    # Add to conversation
    def add_message(self, message_text, user_id="admin"):
        new_message = Message(message_text, self.id, user_id)
        new_message.start()


class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    message_text = db.Column(db.String(10000))
    user_id = db.Column(db.Integer)
    conversation_id = db.Column(db.Integer)

    def __init__(self, message_text, conversation_id, user_id="admin"):
        self.message_text = message_text
        self.user_id = user_id
        self.conversation_id = conversation_id
        if user_id is "admin":
            print "Admin message."
        else:
            print "User message."

    def __repr__(self):
        string = "<message from {}> with id: {}".format(self.user_id, self.id)
        return string

    def start(self):
        db.session.add(self)
        db.session.commit()

    def get_message_string(self):
        if self.user_id == "admin":
            message_to_print = self.message_text
            print "sending out admin message"
        else:
            # Always user_id defined in case of user message
            print "get_message_string message has user id: ", self.user_id
            user = get_user_from_user_id(self.user_id)
            username = user.get_username()
            message_to_print = username + " says: " + self.message_text
        return message_to_print


class ExtinctCombo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer)
    pair_id = db.Column(db.Integer)

    def __init__(self, user_id, pair_id):
        self.user_id = user_id
        self.pair_id = pair_id

    def __repr__(self):
        return "<Extinct combination with user: {}, pair: {}>".format(self.user_id, self.pair_id)

    def start(self):
        db.session.add(self)
        db.session.commit()

    def are_you_this_extinct_combo(self, user_id, pair_id):
        correct_user = self.user_id == user_id
        correct_pair = self.pair_id == pair_id
        correct_extinct_combo = correct_pair and correct_user
        return correct_extinct_combo
