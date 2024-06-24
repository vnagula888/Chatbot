import json
from difflib import get_close_matches


def load_knowledge_base(file_path):
    with open(file_path, 'r') as file1:
        filecontents = json.load(file1)
        return filecontents


def chat_bot():
    # replace 'file path' with the file path to where the JSON file is stored
    file_contents = load_knowledge_base(
        'file path')

    while True:
        user_input = input('You: ')
        if user_input.lower() == 'quit':
            break
        elif user_input.lower() == 'exit':
            break
        else:
            possibilities = (x["question"] for x in file_contents["chatbot_questions"])
            best_matched_question = get_close_matches(user_input, possibilities, n=1, cutoff=0.6)
            if len(best_matched_question) == 0:
                print("Sorry, I do not know the answer to that, pls ask relevant question to the school")
                continue

            for x in file_contents["chatbot_questions"]:
                if x["question"] == best_matched_question[0]:
                    print(x["answer"])


chat_bot()
