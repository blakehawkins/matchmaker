from models import db, User, get_pair_list, get_user_list, \
    clear_all_users, clear_all_pairs, get_user_from_user_id

db.drop_all()
db.create_all()

clear_all_users()
clear_all_pairs()
dom = User("Dom", "dom@dom")
arthur = User("Arthur", "arthur@arthur")
isobel = User("Isobel", "isobel@isobel")
joe = User("Joe", "joe@joe")
dom.start()
arthur.start()
isobel.start()
joe.start()

user_list = get_user_list()
print "user list is: ", user_list
pair_list = get_pair_list()
print pair_list

# new match - success

dom_next_pair = dom.get_next_pair()
print "Dom's next pair is: ", dom_next_pair

match1 = dom.make_pair_match(dom_next_pair)
print "Made match 1 with id: ", match1.id

# new match - success

dom_next_pair = dom.get_next_pair()
print "Dom's next pair is: ", dom_next_pair

match2 = dom.make_pair_match(dom_next_pair)
print "Made match 2 with id: ", match2.id

# test wingman matches

dom_wingman_matches = dom.matches_as_wingman()
print "Dom has wingmanned for: {}".format(dom_wingman_matches)

# new match - fail on too many

dom_next_pair = dom.get_next_pair()
print "Dom's next pair is: ", dom_next_pair

match3 = dom.make_pair_match(dom_next_pair)
print "Made match 3 with id: ", match3.id



user = get_user_from_user_id(2)
print user

