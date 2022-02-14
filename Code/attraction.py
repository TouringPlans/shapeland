
class Attraction:
    """ Class which defines Attractions within the park simulation. Stores attraction characteristics, current state and log. """

    def __init__(self, attraction_characteristics):
        """  
        Required Inputs:
            attraction_characteristics: dictionary of characteristics for the attraction        
        """

        self.attraction_characteristics = attraction_characteristics
        self.state = {} # characterizes attractions current state
        self.history = {} 

        if (
            type(self.attraction_characteristics["popularity"]) != int 
            or self.attraction_characteristics["popularity"] < 1
            or self.attraction_characteristics["popularity"] > 10
        ):
            raise AssertionError(
                f"Attraction {self.attraction_characteristics['name']} 'popularity' value must be an integer between"
                "1 and 10"
            )
        self.initialize_attraction()

    
    def initialize_attraction(self):
        """ Sets up the attraction """ 

        #characteristics
        self.name = self.attraction_characteristics["name"]
        self.run_time = self.attraction_characteristics["run_time"]
        self.capacity = self.attraction_characteristics["hourly_throughput"] * (self.attraction_characteristics["run_time"]/60) 
        self.popularity = self.attraction_characteristics["popularity"]
        self.child_eligible = self.attraction_characteristics["child_eligible"]
        self.adult_eligible = self.attraction_characteristics["adult_eligible"]
        self.run_time_remaining = 0
        self.expedited_queue = self.attraction_characteristics["expedited_queue"]
        self.exp_queue_ratio = self.attraction_characteristics["expedited_queue_ratio"]
        self.exp_queue_passes = 0

        #state
        self.state["agents_in_attraction"] = []
        self.state["queue"] = []
        self.state["exp_queue"] = []
        self.state["exp_queue_passes_distributed"] = 0

        # history
        self.history["queue_length"] = {}
        self.history["queue_wait_time"] = {}
        self.history["exp_queue_length"] = {}
        self.history["exp_queue_wait_time"] = {}
           

    def get_wait_time(self):
        """ Returns the expected queue wait time according the the equation
        """

        if self.expedited_queue:
            queue_len = len(self.state["queue"])
            exp_queue_len = len(self.state["exp_queue"])
            exp_seats = int(self.capacity * self.exp_queue_ratio)
            standby_seats = self.capacity - exp_seats

            runs = 0
            while queue_len >= self.capacity:    
                if exp_queue_len > exp_seats:
                    exp_queue_len -= exp_seats
                    if queue_len > standby_seats:
                        queue_len -= standby_seats
                    else:
                        queue_len = 0
                else:
                    queue_len -= self.capacity - exp_queue_len
                    exp_queue_len = 0
                
                runs += 1

            return runs * self.run_time + self.run_time_remaining
        else:
            return (len(self.state["queue"]) // self.capacity) * self.run_time + self.run_time_remaining
    
    def get_exp_wait_time(self):
        """ Returns the expected queue wait time according the the equation
        """

        if self.expedited_queue:
            queue_len = len(self.state["queue"])
            exp_queue_len = len(self.state["exp_queue"])
            exp_seats = int(self.capacity * self.exp_queue_ratio)
            standby_seats = self.capacity - exp_seats

            runs = 0
            while exp_queue_len >= self.capacity:    
                if exp_queue_len > exp_seats:
                    exp_queue_len -= exp_seats
                    if queue_len > standby_seats:
                        queue_len -= standby_seats
                    else:
                        queue_len = 0
                else:
                    queue_len -= self.capacity - exp_queue_len
                    exp_queue_len = 0
                
                runs += 1

            return runs * self.run_time + self.run_time_remaining
        else:
            return 0
    
    def add_to_queue(self, agent_id):
        """ Adds an agent to the queue """

        self.state["queue"].append(agent_id)
    
    def add_to_exp_queue(self, agent_id):
        """ Adds an agent to the expeditied queue """

        self.state["exp_queue"].append(agent_id)
        expedited_wait_time = self.get_exp_wait_time()
        return expedited_wait_time

    def remove_pass(self):
        """ Removes a expedited pass """

        self.exp_queue_passes -= 1
        self.state["exp_queue_passes_distributed"] += 1
        
    def return_pass(self, agent_id):
        """ Removes an expedited pass without redeeming it """

        self.exp_queue_passes += 1
        self.state["exp_queue_passes_distributed"] -= 1
        self.state["exp_queue"].remove(agent_id)

    def step(self, time, park_close):
        """ Handles the following actions:
            - Allows agents to exit attraction if the run is complete
            - Loads expedited queue agents
            - Loads queue agents
            - Begins Ride
        """
        
        exiting_agents = []
        loaded_agents = []

        # calculate total exp queue passes available
        if self.expedited_queue:
            if time < park_close:
                remaining_operating_hours = (park_close - time) // 60
                passed_operating_hours = time // 60
                self.exp_queue_passes = (
                    (self.capacity * (60/self.run_time) * self.exp_queue_ratio * remaining_operating_hours) 
                    - max(
                            (
                                self.state["exp_queue_passes_distributed"] - 
                                (self.capacity * (60/self.run_time) * self.exp_queue_ratio * passed_operating_hours)
                            )
                        , 0
                    )
                )
            else:
                self.exp_queue_passes = 0 

        if self.run_time_remaining == 0:
            # left agents off attraction
            exiting_agents = self.state["agents_in_attraction"]
            self.state["agents_in_attraction"] = []
            self.run_time_remaining = self.run_time

            # devote seats to queue and expedited queue
            max_exp_queue_agents = int(self.capacity * self.exp_queue_ratio)
            # Handle case where expedited queue has fewer agents than the maximum number of expedited queue spots
            if len(self.state["exp_queue"]) < max_exp_queue_agents:
                max_queue_agents = int(self.capacity - len(self.state["exp_queue"]))
            else:
                max_queue_agents = int(self.capacity - max_exp_queue_agents)
            
            # load expeditied queue agents
            expedited_agents_to_load = [agent_id for agent_id in self.state["exp_queue"][:max_exp_queue_agents]]
            self.state["agents_in_attraction"] = expedited_agents_to_load
            self.state["exp_queue"] = self.state["exp_queue"][max_exp_queue_agents:]

            # load queue agents
            agents_to_load = [agent_id for agent_id in self.state["queue"][:max_queue_agents]]
            self.state["agents_in_attraction"].extend(agents_to_load)
            self.state["queue"] = self.state["queue"][max_queue_agents:]

            loaded_agents = self.state["agents_in_attraction"]
        
        return exiting_agents, loaded_agents

    def pass_time(self):
        """ Pass 1 minute of time """

        self.run_time_remaining -= 1

    def store_history(self, time):
        """ Stores metrics """

        self.history["queue_length"].update(
            {
                time: len(self.state["queue"])
            }
        ) 
        self.history["queue_wait_time"].update(
            {
                time: self.get_wait_time()
            }
        )
        self.history["exp_queue_length"].update(
            {
                time: len(self.state["exp_queue"])
            }
        ) 
        self.history["exp_queue_wait_time"].update(
            {
                time: self.get_exp_wait_time()
            }
        ) 



        

        
