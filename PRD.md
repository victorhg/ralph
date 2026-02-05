# Project MyRalph agentic system
We are building a agentic loop following the strategy called Ralph Loop, following the post https://ghuntley.com/ralph.

This is a loop using bash script that connects to a local ollama server running an agentic model in the local machine that will read the instructions as prompt in the project folder and run a few loops until the project is finished. 

## Restrictions

The whole instance should be runed in a container to reduce the security risks 

It should access the local ollama installation

It should allow for configuration of the model used and the number of interactions 

Use markdown as tasks configuration  



## Reference

Ralph code by Snarktank: https://github.com/snarktank/ralph/blob/main/ralph.sh
