# Shapeland Simulator
- Source code to accompany Defunctland's video "FASTPASS: A Complicated Legacy"
- Download the video at https://www.youtube.com/watch?v=9yjZpBq1XBE

## License

- This source code is licensed under the Creative Commons 4.0 International License
- See the file named LICENSE for details

## Tools You Will Need to Run The Simulation

The simulation is written in Python and has been tested with python 3.6.9.  Download the latest version
of python here: https://www.python.org/downloads/

The code also uses Jupyter Notebooks, available here: https://jupyter.org/install

## Installation and Setup

Clone this repository to your local machine:

```
$ git clone https://github.com/TouringPlans/shapeland.git
```

Inside the repository is a directory called "Code".  Start Jupyter Notebook like this and you'll see the
entire notebook that runs the simulator and prints results:

```
$ jupyter notebook amusement_park_sim.ipynb
```

## Code Organization

There are 5 main classes in this simulation:

- activity.py: An activity is something an agent can do inside the park.  Activities include going on rides, eating, and so on.

- agent.py: Simulates one guest making decisions in the park.
- attraction.py: Encapsulates all of the calculations to simulate an attraction, including whether it has FASTPASS, its hourly capacity, how that capacity is split among different lines, and so on.
- behavior_reference.py: Each Agent has a behavioral archetype.
-- Ride Enthusiast: wants to stay for a long time, go on as many attractions as possible, doesn't want to visit activites, doesn't mind waiting
-- Ride Favorer: wants to go on a lot of attractions, but will vists activites occasionally, will wait for a while in a queue
-- Park Tourer: wants to stay for a long time and wants to see attractions and activities equally, reasonable about wait times
-- Park Visitor: doesn't want to stay long and wants to see attractions and activities equally, inpatient about wait times
-- Activity Favorer: doesn't want to stay long and prefers activities, reasonable about wait times
-- Activity Enthusiast: wants to visit a lot of activities, reasonable about wait times
-- Archetypes can be tweaked and new archetypes can be added in behavior_reference.py.
- park.py: The park contains Agents, Attractions and Activities.
-- Total Daily Agents: dictates how many agents visit the park within a day
-- Hourly Percent: dictates what percentage of Total Daily Agents visits the park at each hour
-- Perfect Arrivals: enforces that the exact amount of Total Daily Agents arrives during the day
-- Expedited Pass Ability Percent: percent of agents aware of expeditied passes
-- Expedited Threshold: acceptable queue wait time length before searching for an expedited pass
-- Expedited Limit: total number of expedited pass an agent can hold at any given time

