from models import db, User, get_pair_list, get_user_list, \
    clear_all_users, clear_all_pairs, get_user_from_user_id, get_conversation_from_conversation_id, get_message_from_message_id, get_match_from_match_id, get_user_conversations_in_match

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

dom_next_pair = dom.get_next_pair()
print "Dom's 1st pair is: ", dom_next_pair

match = dom.make_pair_match(dom_next_pair)
print "Made match with id: ", match.id

dom_next_pair = dom.get_next_pair()
print "Dom's 2nd pair is: ", dom_next_pair

match = dom.make_pair_match(dom_next_pair)
print "Made match with id: ", match.id

dom_next_pair = dom.get_next_pair()
print "Dom's 3rd pair is: ", dom_next_pair

match = dom.make_pair_match(dom_next_pair)
print "Made match with id: ", match.id

user = get_user_from_user_id(2)
print user

conversation_id = match.conversation_id
print "Conversation id is: ", conversation_id

conversation = get_conversation_from_conversation_id(conversation_id)
print "Conversation is: ", conversation

message_list = conversation.get_message_strings_list()
print message_list

new_message_text = "OMGEE YOU ARE SO FIT #DoMe"

conversation.add_message(new_message_text, dom.id)
print "Message: ", new_message_text, " added to conversation: ", conversation

new_message_text = "LOL IKR ;) #tits"

conversation.add_message(new_message_text, joe.id)
print "Message: ", new_message_text, " added to conversation: ", conversation

new_message_text = "BACK OFF BITCH #myman"

conversation.add_message(new_message_text, isobel.id)
print "Message: ", new_message_text, " added to conversation: ", conversation

message_list = conversation.get_message_strings_list()
for line in message_list:
    print line

convo = get_user_conversations_in_match(match.id, dom.id, isobel.id)
print convo
