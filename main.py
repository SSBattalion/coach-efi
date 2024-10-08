import random
import time
import requests
from highrise import BaseBot, Highrise, Position, AnchorPosition, Reaction
from highrise import __main__
from asyncio import run as arun
import asyncio
from random import choice
import os
import json
from typing import List
from datetime import datetime, timedelta
from highrise.models import SessionMetadata
import re
from highrise.models import SessionMetadata,  GetMessagesRequest, User ,Item, Position, CurrencyItem, Reaction
from typing import Any, Dict, Union
from highrise.__main__ import *
import asyncio, random
questions = [
    {
        "question": "What should you do if you issue a warning and the person starts to argue?",
        "options": ["Kick them", "Ignore them and issue a mute if they continue", "Immediately mute them"],
        "answer": 1
    },
    {
        "question": "When you see two people arguing/fighting in the room, how should you respond?",
        "options": ["Issue a warning", "Separate them", "Ask if they need a mod"],
        "answer": 2
    },
    {
        "question": "When you see someone spam promotions in chat, what should you do?",
        "options": ["Mute them", "Issue a warning", "Ignore them"],
        "answer": 2
    },
    {
        "question": "What is considered a last resort?",
        "options": ["Kicks/Bans", "Mutes/Kicks", "All of above"],
        "answer": 2
    },
    {
        "question": "When should a warning take place?",
        "options": ["After asking if they need a mod and gaining context", "Immediately after you see the drama/argument", "You don't have to issue a warning"],
        "answer": 0
    },
    {
        "question": "Who is to receive mutes?",
        "options": ["Spammers", "Beggars", "All of above"],
        "answer": 1
    },
    {
        "question": "Who is allowed to kick people from the room?",
        "options": ["Mods", "Admins", "The owner"],
        "answer": 1
    },
    {
        "question": "What is the first thing you should do when the music bot breaks down?",
        "options": ["Use -np", "Check your radio", "Use -stop songs"],
        "answer": 1
    },
    {
        "question": "How many credits are you allowed to give away?",
        "options": ["200 for music, 50 for emojis", "100 for music, 500 for emojis", "50 for music, 200 for emojis"],
        "answer": 2
    },
    {
        "question": "When you encounter a minor 12 and under, how do you deal with the situation?",
        "options": ["Contact an admin", "Immediately ban them yourself", "Ignore but keep a watchful eye"],
        "answer": 0
    }
]


class BotDefinition:
    
      
    def __init__(self, bot, room_id, api_token):
        self.bot = bot
        self.room_id = room_id
        self.api_token = api_token
        self.following_username = None

class Counter:
    bot_id = ""
    static_ctr = 0
    usernames = ['Alionardo_']

class Bot(BaseBot):



    def __init__(self):
        super().__init__()
        self.maze_players = {}
        self.user_points = {}  # Dictionary to store user points
        self.questions = random.sample(questions, 10)
        self.score = 0
        self.current_question = 0
        self.user_answers = {}
        self.is_running = False 
        self.load_trainer()
        self.training_state = None

       

    def load_trainer(self):
        try:
            with open("trainer.json", "r") as file:
                self.trainer = json.load(file)
        except FileNotFoundError:
            self.trainer = []
    def save_trainer(self):
        with open("trainer.json", "w") as file:
            json.dump(self.trainer, file)
    async def on_message(self, user_id: str, conversation_id: str, is_new_conversation: bool) -> None:

        response = await self.highrise.get_messages(conversation_id)
        if isinstance(response, GetMessagesRequest.GetMessagesResponse):
            message = response.messages[0].content
            print (message)
            response = await self.highrise.get_messages(conversation_id)
            userinfo = await self.webapi.get_user(user_id)
            username = userinfo.user.username
            if message.lower().startswith("-login as trainer"):
                if username == "_efi" or username == "Alionardo_":
                    if conversation_id not in self.trainer:
                        self.trainer.append(conversation_id)
                        self.save_trainer()
                        await self.highrise.send_message(conversation_id, "Logged in as trainer!")
                    else:
                        await self.highrise.send_message(conversation_id, "You are already logged in as a trainer!")
                else:
                    await self.highrise.send_message(conversation_id, "You are not authorized to log in as a trainer!")
            if message.startswith("-say") and conversation_id in self.trainer :
                  text = message.replace("-say", "").strip()
                  try:
                      await self.highrise.chat(text)
                  except Exception as e:
                      print(f"An exception occured: {e}")      
    async def on_chat(self, user: User, message: str) -> None:
        if message.lower() != "next" and self.training_state is not None:
            txt = message
            try:
                for conversation_id in self.trainer:
                    await self.highrise.send_message(conversation_id, f"@{user.username} in the training said:\n{txt}")
            except Exception as e:
                print(f"An exception occurred: {e}")
        if message.lower().startswith("-start training") or (message.lower() in ["all clear", "next"] and hasattr(self, 'training_state') and self.training_state is not None):
            await self.training_handler(user, message)
        elif message.lower().startswith("-start exercise"):
            self.current_question = 0
            await self.start_exercise(user)
        elif self.current_question is not None:
            await self.check_answer(user,message)
        
    async def training_handler(self, user: User, message: str) -> None:
        if message.lower().startswith("-start training"):
            # Initialize the training state
            self.training_state = {"user_id": user.id, "current_step": 0, "waiting_for_next": False}
            self.training_state["waiting_for_next"] = True
            await self.show_step(user)
        elif message.lower() == "next" or message.lower() == "all clear":
            if self.training_state is None:
                await self.highrise.chat("You haven't started the training yet. Please type '-start training' to begin.")
                return
            if self.training_state["waiting_for_next"]:
                self.training_state["waiting_for_next"] = False
                self.training_state["current_step"] += 1
                await self.show_step(user)
            else:
                await self.highrise.chat("Invalid response. Please respond with All clear' or 'Next' after the previous step has finished.")
        else:
            # Invalid response
            if self.training_state is not None:
                await self.highrise.chat("Invalid response. Please respond with 'All clear' or 'Next'.")

    async def show_step(self, user: User):
        if self.training_state["current_step"] == 0:
            await self.highrise.chat("Welcome to the FADbot login and best practices training! Please follow the instructions carefully.")
            await asyncio.sleep(8)
            await self.highrise.chat("This training will guide you through the process of logging into FADbot and best practices. Please read each step carefully.")
            await asyncio.sleep(8)
            await self.highrise.chat("When you have finished reading each step, please ask your trainer if you have any questions and then type 'next' to move to the next part.")
            await asyncio.sleep(8)
            await self.highrise.chat("Please note that there will be a small test at the end of this training to ensure you have understood the material.")
            await asyncio.sleep(8)
            await self.highrise.chat("Let's begin! Please follow the instructions carefully.")
            await asyncio.sleep(1)
            await self.highrise.chat("Step 1: Logging into FADbot")
            await asyncio.sleep(1)
            await self.highrise.chat("To log into FADbot, please direct message FADbot with the command:\n`-login as mod username` Everyday.")
            await asyncio.sleep(8)
            await self.highrise.chat("Ensure you are in the same room as the mod and have their assistance throughout the process. Copy and paste the command into the chat to avoid errors.")
            await asyncio.sleep(8)
            await self.highrise.chat("Do you have any questions or concerns about this information?")
            await asyncio.sleep(2)
            await self.highrise.chat("If not, I will move on to the verifying Login. Type 'Next'")

            self.training_state["waiting_for_next"] = True
        elif self.training_state["current_step"] == 1:
            await self.highrise.chat("Step 2: Verifying Login Credentials")
            await asyncio.sleep(1)
            await self.highrise.chat("Before proceeding, please confirm with the mod that you have successfully logged into FADbot. Ensure that you did not whisper to the bot and instead sent a direct message.")
            await asyncio.sleep(8)
            await self.highrise.chat("Ask your trainer if you have a question then type 'Next'.")
            self.training_state["waiting_for_next"] = True
        elif self.training_state["current_step"] == 2:
            await self.highrise.chat("Step 3: Additional Best Practices")
            await asyncio.sleep(1)
            await self.highrise.chat("Here are some additional best practices to keep in mind when using FADbot:")
            await asyncio.sleep(2)
            await self.highrise.chat("Boosts are a requirement, at minimum about 2 boosts per day. If you are unable to do this for a time, or may need slight accommodations, reach out to an admin right away, we understand that life happens.")
            await asyncio.sleep(8)
            await self.highrise.chat("Log total boosts when you leave the room on Discord, and log all mutes/kicks/bans in the logs chat on Highrise.")
            await asyncio.sleep(8)
            await self.highrise.chat("Read the room description and familiarize yourself with the rules.")
            await asyncio.sleep(8)
            await self.highrise.chat("Mods are required to be friendly and engaging with everyone in the room, especially if they approach you.")
            await asyncio.sleep(5)
            await self.highrise.chat("Drama is NOT tolerated, but if you see anything, be sure to gain context of a conversation before taking ANY action.")
            await asyncio.sleep(5)
            await self.highrise.chat("Please read these best practices carefully and ask your trainer if you have any questions.")
            await asyncio.sleep(1)
            await self.highrise.chat("Do you have any questions or concerns about this information?")
            await asyncio.sleep(2)
            await self.highrise.chat("If not, I will move on to the modding practices. Type 'Next'")
            
            self.training_state["waiting_for_next"] = True
        elif self.training_state["current_step"] == 3:
              await self.highrise.chat("Step 4: Modding Best Practices:")
              await asyncio.sleep(1)
              await self.highrise.chat("Here are some best practices to keep in mind when modding:")
              await asyncio.sleep(3)
              await self.highrise.chat("When dealing with situations, remember that it is intimidating to have multiple mods dealing with a situation at once and it can become chaotic.")
              await asyncio.sleep(5)
              await self.highrise.chat("Only one mod should be talking to/warning someone at one time, if an admin steps in all other mods should leave the situation and leave it to the admin.")
              await asyncio.sleep(5)
              await self.highrise.chat("Spammers no longer receive mutes, kicks, OR bans.")
              await asyncio.sleep(2)
              await self.highrise.chat("Beggars should receive one warning, if they persist mute them. Beggars should not be kicked or banned under ANY circumstance. If they take it to DMs, tell that person to block them.")
              await asyncio.sleep(5)
              await self.highrise.chat("When dealing with drama, you may ask the parties involved if they require assistance from a moderator, if they say no, do not intervene.")
              await asyncio.sleep(5)
              await self.highrise.chat("When handling situations, we should follow these steps: mute, then kick, then ban.")
              await asyncio.sleep(2)
              await self.highrise.chat("Remember, mutes, kicks, and bans are LAST RESORTS, please try to resolve a situation before resorting to using these commands.")
              await asyncio.sleep(5)
              await self.highrise.chat("All kicks and bans must have admin approval, and be sure to include in your log which admin gave approval.")
              await asyncio.sleep(5)
              await self.highrise.chat("Please read these best practices carefully and ask your trainer if you have any questions.")
              await asyncio.sleep(2)
              await self.highrise.chat("When you are ready, type 'Next' to move to the next part.")
              self.training_state["waiting_for_next"] = True
        elif self.training_state["current_step"] == 4:
             await self.highrise.chat("Step 5: Important Admin Information:")
             await asyncio.sleep(1)
             await self.highrise.chat("Here are some important things to keep in mind about admins and room management:")
             await asyncio.sleep(5)
             await self.highrise.chat("All admins can be found by checking the room rules, or by looking at the moderator list for the room. Only admins are set as 'moderator' for the room to give them access to permanent bans; so all those listed for the room are admins.")
             await asyncio.sleep(5)
             await self.highrise.chat("IMMEDIATELY reach out to an admin if you see anyone under the age of 13 so that we can permanently ban them. Our room is 13+ so anyone 12 or under should be banned.")
             await asyncio.sleep(5)
             await self.highrise.chat("If you see any minors being weird with an adult or vice versa, contact an admin immediately to issue a ban.")
             await asyncio.sleep(5)
             await self.highrise.chat("It is now a requirement to check pinned posts 1-2 times a day, these will be updated often, so please read them carefully. Failure to do so will be YOUR responsibility if you make a mistake.")
             await asyncio.sleep(5)
             await self.highrise.chat("To avoid potentially being removed from this position, please adhere to everything covered.")
             await asyncio.sleep(1)
             await self.highrise.chat("Do you have any questions or concerns about this information?")
             await asyncio.sleep(2)
             await self.highrise.chat("If not, I will move on to the music bot. Type 'Next'")
             self.training_state["waiting_for_next"] = True
        elif self.training_state["current_step"] == 5:
             await self.highrise.chat("Step 6: Music Bot Instructions:")
             await asyncio.sleep(1)
             await self.highrise.chat("Here are some important things to keep in mind when using the music bot:")
             await asyncio.sleep(2)
             await self.highrise.chat("Type '-help' to view available commands.")
             await asyncio.sleep(1)
             await self.highrise.chat("Type '-buy visa' to purchase a visa.")
             await asyncio.sleep(1)
             await self.highrise.chat("Make sure you have an active mod visa account every time you enter the room, and ensure anyone you are helping with the music bot also has an active visa account.")
             await asyncio.sleep(5)
             await self.highrise.chat("To check if you have an active mod visa account, type '-visa' in normal chat and it should say you are a moderator at the bottom. If it does not, you will need your mod privileges reset.")
             await asyncio.sleep(5)
             await self.highrise.chat("If your commands stop working at any time for either bot, reach out to an admin for assistance.")
             await asyncio.sleep(1)
             await self.highrise.chat("Do you have any questions or concerns about the music bot?")
             await asyncio.sleep(2)
             await self.highrise.chat("If not, I will move on to the next part. Type 'Next'")
             self.training_state["waiting_for_next"] = True
        elif self.training_state["current_step"] == 6:
             await self.highrise.chat("Step 7: Additional Music Bot Guidelines:")
             await asyncio.sleep(1)
             await self.highrise.chat("Here are some additional guidelines to keep in mind when using the music bot:")
             await asyncio.sleep(2)
             await self.highrise.chat("To allow FADbot to DM you the queue, send a direct message to FADbot with the command '-access queue'.")
             await asyncio.sleep(5)
             await self.highrise.chat("As a mod, you have unlimited credits, but please only give a maximum of 50 credits at a time. Be cautious of potential scams.")
             await asyncio.sleep(5)
             await self.highrise.chat("Only skip songs under the following circumstances: heavy metal, highly inappropriate content, troll songs, room number drops, or if the requester asks for it to be skipped.")
             await asyncio.sleep(5)
             await self.highrise.chat("If the music bot is broken, reset it by typing '-stop songs'. Credits will be automatically refunded, so no need to retrieve the queue first.")
             await asyncio.sleep(5)
             await self.highrise.chat("Before resetting the bot, try refreshing/muting and unmuting to see if it resolves the issue.")
             await asyncio.sleep(5)
             await self.highrise.chat("You can gift friends enough credits to purchase an emoji to display next to their name (200 credits). Please only do this for close friends.")
             await asyncio.sleep(5)
             await self.highrise.chat("Do you have any questions or concerns about these music bot guidelines?")
             await asyncio.sleep(2)
             await self.highrise.chat("If not, I will conclude the training. Type 'Next'")
             self.training_state["waiting_for_next"] = True
        elif self.training_state["current_step"] == 7:
            await self.highrise.chat("Congratulations! You have successfully completed the FADbot login and best practices training.")
            await asyncio.sleep(3)
            await self.highrise.chat("You will now be given a small test to ensure you have understood the material. Please answer the questions to the best of your ability.")
            await asyncio.sleep(2)
            await self.highrise.chat("Good luck!")
            self.training_state = None
        
        else:
            await self.highrise.chat("Invalid step. Please try again.")
    async def start_exercise(self, user):
        if not self.is_running:  # Check if the exercise is not already running
            self.is_running = True
            self.current_question = 0
            self.score = 0
            await self.highrise.chat("Exercise started! Please answer the questions to the best of your ability.")
            await self.send_question()
        else:
            await self.highrise.chat("Exercise is already running!")


    async def send_question(self):
        if self.is_running:
            question = self.questions[self.current_question]
            await asyncio.sleep(2) 
            await self.highrise.chat(question["question"])
            await asyncio.sleep(1.5)  # add a 1.5-second delay
            for i, option in enumerate(question["options"]):
                await self.highrise.chat(f"{i+1}. {option}")
                await asyncio.sleep(1.5) 
        else:
            await self.highrise.chat("Exercise is not running!")

    async def check_answer(self,user: User, message):
     if self.is_running:
        question = self.questions[self.current_question]
        try:
            answer = int(message) - 1
            if answer == question["answer"]:
                self.score += 1
                await self.highrise.send_whisper(user.id,"Correct!")
            else:
                await self.highrise.send_whisper(user.id,f"Incorrect. The correct answer is {question['options'][question['answer']]}")
            self.current_question += 1
            if self.current_question < len(self.questions):
                await self.send_question()
            else:
                await self.end_exercise(user)
        except ValueError:
            await self.highrise.chat("Invalid answer. Please enter a number.")
     
        
    async def end_exercise(self ,user:User):
        if self.is_running:
            await self.highrise.chat(f"Exercise ended! \nYour final score is {self.score} out of {len(self.questions)}")
            for conversaion_id in self.trainer :
              try:
                await self.highrise.send_message(conversaion_id ,f"{user.username} has finished mod and music bot training with score {self.score} out of {len(self.questions)}")
              except Exception as e:
                print(f"error: {e}") 
            self.is_running = False
            self.current_question = None
            self.score = 0
        else:
            await self.highrise.chat("Exercise is not running!")

    async def on_user_join(self, user: User, position: Position  | AnchorPosition) -> None: 
     try:
        print(f"{user.username} joined the room standing at {position}")
        await self.highrise.send_whisper(user.id,f"Hey {user.username}")
     except Exception as e:
            print(f"An error on user_on_join: {e}") 

    async def on_user_leave(self, user: User) ->None:
        print(f"{user.username} has left the room")
    async def on_start(self, session_metadata: SessionMetadata) -> None:
      try:
         Counter.bot_id = session_metadata.user_id
         print("Ali is booting ...") 
         self.load_trainer()
         await asyncio.sleep(15)
         await self.highrise.chat(f"Coach on duty")
         self.highrise.tg.create_task(self.highrise.walk_to(AnchorPosition(entity_id='ed5f6ba1772586e8bb698eaf', anchor_ix=0)))
      except Exception as e:
          print(f"An exception occured: {e}")  
  
  
    async def run(self, room_id, token):
        definitions = [BotDefinition(self, room_id, token)]
        await __main__.main(definitions) 
 
   

   




    
