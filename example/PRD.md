# Project: Guess the Number CLI

## Overview
A simple command-line interface (CLI) game where the user attempts to guess a randomly generated number within a specified range. The game provides feedback on each guess to guide the player toward the correct answer.

## Features
- **Random Number Generation**: The game picks a secret number between 1 and 100 at the start of each round.
- **User Interaction**: Prompts the user to input their guess via the standard terminal input.
- **Feedback System**:
  - Displays "Too High" if the guess is greater than the secret number.
  - Displays "Too Low" if the guess is less than the secret number.
  - Congratulates the user when they guess correctly.
- **Attempt Tracking**: Counts and displays the total number of attempts taken to find the number.
- **Replayability**: Offers the user a choice to play again or exit after completing a game.
- **Input Validation**: Ensures the user enters valid integers and handles invalid inputs gracefully without crashing.

## Tech Stack
- Language: Python 3
