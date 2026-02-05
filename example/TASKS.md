# Project Tasks

1.  **Project Initialization**
    - [ ] Create the project directory structure (if not already present).
    - [ ] Create a main script file named \`game.py\`.
    - [ ] Implement a basic "Hello World" print statement to ensure the environment is working.

2.  **Core Logic - Random Number Generation**
    - [ ] Import the \`random\` module.
    - [ ] Write a function or logic to generate a random integer between 1 and 100.
    - [ ] Store this number in a variable (e.g., \`target_number\`) for the current game session.

3.  **Game Loop & User Input**
    - [ ] Implement a \`while\` loop that continues until the game is won.
    - [ ] Inside the loop, prompt the user to enter a guess using the \`input()\` function.
    - [ ] Convert the user's input string into an integer.

4.  **Feedback Mechanics**
    - [ ] Add conditional logic (\`if/elif/else\`) to compare the user's guess with the \`target_number\`.
    - [ ] Print "Too High" if the guess is larger than the target.
    - [ ] Print "Too Low" if the guess is smaller than the target.
    - [ ] Print a success message and break the loop if the guess is correct.

5.  **Refinement: Validation & Replay**
    - [ ] Wrap the input conversion in a \`try-except\` block to handle non-numeric inputs without crashing.
    - [ ] Track and display the number of attempts it took to win.
    - [ ] Wrap the entire game logic in an outer loop to allow the user to play again (prompt for "Play again? y/n").