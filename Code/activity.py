import numpy as np

class Activity:
    """ Class which defines Activitys within the park simulation. Stores activity characteristics, current state and log. """

    def __init__(self, activity_characteristics, random_seed=None):
        """  
        Required Inputs:
            activity_characteristics: dictionary of characteristics for the activity        
        """

        self.activity_characteristics = activity_characteristics
        self.state = {} # characterizes activity current state
        self.history = {} 
        self.random_seed = random_seed

        if (
            type(self.activity_characteristics["popularity"]) != int 
            or self.activity_characteristics["popularity"] < 0
            or self.activity_characteristics["popularity"] > 10
        ):
            raise AssertionError(
                f"activity {self.activity_characteristics['name']} 'popularity' value must be an integer between"
                "1 and 10"
            )
        self.initialize_activity()

    
    def initialize_activity(self):
        """ Sets up the activity """ 

        #characteristics
        self.name = self.activity_characteristics["name"]
        self.popularity = self.activity_characteristics["popularity"]
        self.mean_time = self.activity_characteristics["mean_time"]
       
        #state
        self.state["visitors"] = []
        self.state["visitor_time_remaining"] = []

        # history
        self.history["total_vistors"] = {}
           

    def add_to_activity(self, agent_id, expedited_return_time):
        """ Adds an agent to the activity and generates the time they will spend there. """

        self.state["visitors"].append(agent_id)

        if self.random_seed:
            rng = np.random.default_rng(self.random_seed+agent_id)
            stay_time = int(
                max((rng.normal(self.mean_time, self.mean_time/2, 1))[0], 1)
            )
        else:
            stay_time = int(
                max((np.random.normal(self.mean_time, self.mean_time/2, 1))[0], 1)
            )
        
        # if agent has is waiting in exp queue, make them leave before they need to board ride
        if expedited_return_time:
            stay_time = min(max(1, min(expedited_return_time)), stay_time)
        
        self.state["visitor_time_remaining"].append(stay_time)

    def force_exit(self, agent_id):
        """ Handles case where agent is forced to leave an activity to get on their
        expedited queue attraction """

        ind = self.state["visitors"].index(agent_id)
        del self.state["visitors"][ind]
        del self.state["visitor_time_remaining"][ind]

    def step(self, time):
        """ Handles the following actions:
            - Allows agents to exit activity if they've spent all their time there
        """

        exiting_agents = [
            (ind, agent_id) for ind, agent_id in enumerate(self.state["visitors"])
            if self.state["visitor_time_remaining"][ind] == 0
        ]

        # remove from visitor list, going in reverse maintins indices
        exiting_agents.reverse()
        for ind, agent_id in exiting_agents:
            del self.state["visitors"][ind]
            del self.state["visitor_time_remaining"][ind]

        exiting_agents = [agent_id for ind, agent_id in exiting_agents]

        return exiting_agents

    def pass_time(self):
        """ Pass 1 minute of time """

        self.state["visitor_time_remaining"] = [visitor_time-1 for visitor_time in self.state["visitor_time_remaining"]]

    def store_history(self, time):
        """ Stores metrics """

        self.history["total_vistors"].update(
            {
                time: len(self.state["visitors"])
            }
        ) 