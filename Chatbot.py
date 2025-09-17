import json
from datetime import date
from datetime import datetime
from difflib import get_close_matches


def load_knowledge_base(file_path):
    with open(file_path, 'r') as file:
        data: dict = json.load(file)
        return data


def save_knowledge_base(file_path, data):
    with open(file_path, 'w') as file:
        json.dump(data, file, indent=2)


def find_best_match(user_question, questions):
    matches = get_close_matches(user_question, questions, n=1, cutoff=0.6)
    return matches[0]


def get_answer_for_question(question, knowledge_base):
    for q in knowledge_base["questions"]:

        if q["question"] == question:
            return q["answer"]


def chat_bot():
    knowledge_base = load_knowledge_base('General_Information.json')

    while True:

        user_input = input('You: ')

        if user_input.lower() == 'quit':
            break

        if user_input.lower() == 'exit':
            break

        # print(q)

        best_match = find_best_match(user_input, [q["question"] for q in knowledge_base["questions"]])

        if best_match:

            answer = get_answer_for_question(best_match, knowledge_base)

            print(f'Bot: {answer}')

        else:

            print('Bot: I don\'t know the answer, can you teach me pls?')

            new_answer: str = input('Type the answer or "skip" to skip: ')

            if new_answer.lower() != 'skip':
                knowledge_base["questions"].append({"question": user_input, "answer": new_answer})

                save_knowledge_base('General_Information.json', knowledge_base)

                print('Bot: Thank you! I learned a new response!')


chat_bot()

