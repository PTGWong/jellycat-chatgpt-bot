import random
import logging
import mysql.connector
from mysql.connector import errorcode
import requests
import json
import os
import datetime
from telegram import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardButton, InlineKeyboardMarkup, InputMediaPhoto, Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackQueryHandler, CallbackContext
import openai
from datetime import datetime, timedelta

import threading

# local vars for GPT
user_conversations = {}
good_key = []

# config vars
TOKEN = (os.environ['ACCESS_TOKEN'])

def ask(update: Update, msg: CallbackContext) -> None:
    if len(msg.args) < 1:
        update.message.reply_text("你好像没有输入问题内容捏, 示例: /ask 能不能给我喵一个？")
        return
    query = ''
    for ele in msg.args:
        query += ele

    user_id = update.effective_chat.id
    user_message = query
    logging.info("user Id: " + str(user_id) + " User Ask: " + user_message)

    initial_prompt = """
        Now you are a assistant.
    """
    global user_conversations

    if user_id not in user_conversations:
        user_conversations[user_id] = {
            'history': [{"role": "system", "content": initial_prompt},
                        ],
            'expiration': datetime.now() + timedelta(minutes=10)
        }

    if user_id in user_conversations and datetime.now() > user_conversations[user_id]['expiration']:
        del user_conversations[user_id]
        user_conversations[user_id] = {
            'history': [{"role": "system", "content": initial_prompt},
                        ],
            'expiration': datetime.now() + timedelta(minutes=10)
        }

    # If the conversation history is still valid, send the user's message to the API
    user_conversations[user_id]['history'].append({'role': 'user', 'content': user_message})

    # url = "https://chatgpt-api.shn.hk/v1/"
    # headers = {"Content-Type": "application/json", "User-Agent": "PostmanRuntime/7.31.3"}
    # data = {"model": "gpt-3.5-turbo", "messages": user_conversations[user_id]['history']}
    if len(good_key) < 1:
        update.message.reply_text('Oops! we encountered a problem with GPT key, maybe try me later.')
    openai.api_key = good_key[0]
    # openAi python sdk
    result = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=user_conversations[user_id]['history']
    )

    reply = result['choices'][0]['message']['content']
    user_conversations[user_id]['history'].append({'role': 'assistant', 'content': reply})
    logging.info("GPT: " + reply)
    update.message.reply_text(reply)

def find_a_working_key():
    global good_key
    url = "https://freeopenai.xyz/api.txt"
    response = requests.get(url)
    lines = response.text.split("\n")

    for key in lines:
        openai.api_key = key[:-1]
        try:
            # Use the key to make a test request to the API
            response = openai.Completion.create(
                engine="text-davinci-002",
                prompt="Hello, World!",
                max_tokens=5,
                n=1,
                stop=None,
                temperature=0.5,
                timeout=5,
                frequency_penalty=0,
                presence_penalty=0
            )
            good_key.append(key[:-1])
            logging.info('find a good key! ' + key[:-1])
        except Exception as e:
            continue

# 重置历史对话
def reset(update: Update, msg: CallbackContext):
    global user_conversations
    user_id = update.effective_chat.id
    reply = ""
    if user_id in user_conversations:
        del user_conversations[user_id]
        reply = "已经重置了历史对话, 开启新一轮对话吧!"
    else:
        reply = "似乎没有历史对话捏, 无需重置"

    update.message.reply_text(reply)


def main():
    logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
    updater = Updater(token=TOKEN, use_context=True)
    dispatcher = updater.dispatcher

    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("help", help))
    dispatcher.add_handler(CommandHandler("recommend", recommend))
    dispatcher.add_handler(CommandHandler("get", get))

    # add up functions
    dispatcher.add_handler(CommandHandler('ask', ask))
    dispatcher.add_handler(CommandHandler('reset', reset))

    # initialize key
    # start new thread to filter key list every hour
    find_a_working_key()
    t = threading.Timer(3600.0, find_a_working_key)
    t.start()

    dispatcher.add_handler(CallbackQueryHandler(button_callback))

    # Start the bot
    updater.start_polling()

<<<<<<< HEAD
    updater.idle()
=======
# Define a few command handlers. These usually take the two arguments update and
# context. Error handlers also receive the raised TelegramError object in error.
def help_command(update: Update, context: CallbackContext) -> None:
    """Send a message when the command /help is issued."""
    update.message.reply_text('/ask + 问题进行提问\n'
                              '/reset 重置')


def add(update: Update, context: CallbackContext) -> None:
    """Send a message when the command /add is issued."""
    try:
        global redis1
        logging.info(context.args[0])
        msg = context.args[0]  # /add keyword <-- this should store the keyword
        redis1.incr(msg)
        update.message.reply_text('You have said ' + msg + ' for ' + redis1.get(msg).decode('UTF-8') + ' times.')
    except (IndexError, ValueError):
        update.message.reply_text('Usage: /add <keyword>')

>>>>>>> b53642ddd70a824614ec47d234cc5d83d1190611

if __name__ == '__main__':
    main()
