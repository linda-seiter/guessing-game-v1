from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import MetaData
from random import randint
from enum import  StrEnum, auto
import uuid

metadata=MetaData(naming_convention={
    'pk': 'pk_%(table_name)s',
    'fk': 'fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s',
    'ix': 'ix_%(table_name)s_%(column_0_name)s',
    'uq': 'uq_%(table_name)s_%(column_0_name)s',
    'ck': 'ck_%(table_name)s_%(constraint_name)s',
})

db = SQLAlchemy(metadata=metadata)


class GuessStatus(StrEnum):
    CORRECT = auto() 
    HIGH = auto()    
    LOW= auto()      
    INVALID = auto() 

class DifficultyLevel(StrEnum):
    EASY = auto()   
    HARD= auto()   
  
class Round(db.Model):
    """Round model"""
    id = db.Column(db.Integer, primary_key=True)
    min_value = db.Column(db.Integer, nullable=False)
    max_value = db.Column(db.Integer, nullable=False)
    guess = db.Column(db.Integer)
    status = db.Column(db.String)

    game_id = db.Column(db.Integer, db.ForeignKey("game.id"), nullable=False)
    game = db.relationship("Game", back_populates="rounds")

    __table_args__ = (
        db.CheckConstraint("min_value <= max_value", name="min_max_range"),
    )
    
def create_secret_number(context):
    return randint(context.get_current_parameters()["min_value"], context.get_current_parameters()["max_value"]);


class Game(db.Model):
    """Game model"""
    id = db.Column(db.Integer, primary_key=True)
    difficulty = db.Column(db.String, nullable=False)
    min_value = db.Column(db.Integer, nullable=False)
    max_value = db.Column(db.Integer, nullable=False)
    secret_number = db.Column(db.Integer, default=create_secret_number)
    is_over = db.Column(db.Boolean, default=False)
    rounds = db.relationship(
        "Round", back_populates="game", cascade="all, delete-orphan")

    __table_args__ = (
        db.CheckConstraint("min_value <= max_value", name="min_max_range"),
    )
            
    def play_round(self, guess):
        """Update the current round based on the guess"""
        if self.is_over: 
            raise Exception("Game is over.")
        current_round = max(self.rounds, key=lambda round: round.id)
        current_round.guess = guess
        if guess == self.secret_number:
            current_round.status = GuessStatus.CORRECT
            self.is_over = True
        else:
            #assign status to current round and create the next round of play
            next_min = current_round.min_value
            next_max = current_round.max_value
            if guess < current_round.min_value or guess > current_round.max_value:
                current_round.status = GuessStatus.INVALID
            elif guess > self.secret_number:
                current_round.status = GuessStatus.HIGH
                if self.difficulty == DifficultyLevel.EASY:
                    next_max = guess - 1  #adjust max_value for next round   
            else:
                current_round.status = GuessStatus.LOW
                if self.difficulty == DifficultyLevel.EASY:
                    next_min= guess + 1  #adjust min_value for next round      

            return Round(game = self, min_value = next_min, max_value = next_max) #create next round