import random
import numpy as np

from behavior_reference import BEHAVIOR_ARCHETYPE_PARAMETERS

class Agent:
    """ Class which defines agents within the park simulation. Stores agent characteristics, current state and log. """

    def __init__(self, random_seed):
        """  """

        self.agent_id = None # unique identification number for agent
        self.state = {} # characterizes agents current state
        self.log = "" # logs agent history as text
        self.random_seed = random_seed

        for behavior_type, behavior_dict in BEHAVIOR_ARCHETYPE_PARAMETERS.items():
            age_class_sum = behavior_dict["percent_no_child_rides"] + behavior_dict["percent_no_adult_rides"] + behavior_dict["percent_no_preference"]
            # deal with fuzzy float addition
            if not 0.98 <= age_class_sum <= 1.0:
                raise AssertionError(
                    f"Behavior Archtype {behavior_type} characteristics percent_no_child_rides, percent_no_adult_rides,"
                    "and percent_no_preference, must add up to 1"
                )

    def initialize_agent(
        self, 
        behavior_archetype_distribution, 
        exp_ability, 
        exp_wait_threshold,
        exp_limit,
        agent_id, 
        attraction_names, 
        activity_names
    ):
        """ Takes a dictionary of the agent behavior distributions, the agents unique id, a list of all attractions, and
        a list of all activities (non-attraction things to do at park). Initializes the agents characteristics, current state
        and their log. """

        self.agent_id = agent_id

        # initialize agent state
        self.state.update(
            {
                "arrival_time": None, 
                "exit_time": None, 
                "within_park": False, 
                "current_location": None,
                "current_action": None,
                "time_spent_at_current_location": 0,
                "expedited_return_time": [],
                "expedited_pass": [],
                "expedited_pass_ability": exp_ability,
                "exp_wait_threshold": exp_wait_threshold,
                "exp_limit": exp_limit
            }
        )
        # initialize attraction history
        self.state.update(
            {
                "attractions": {
                    attraction: {
                        "times_completed": 0,
                    } for attraction in attraction_names
                }
            }
        )
        # initialize activity history
        self.state.update(
            {
                "activities": {
                    activity: {
                        "times_visited": 0,
                        "time_spent": 0,
                    } for activity in activity_names
                }
            }
        )

        # initialize agent behavior
        behavior_archetype = self.select_behavior_archetype(
            behavior_archetype_distribution=behavior_archetype_distribution,
            agent_id=agent_id,
        )

        self.state.update(
            {
                "age_class": self.select_age_class(
                    agent_id=agent_id,
                    behavior_archetype_dict=BEHAVIOR_ARCHETYPE_PARAMETERS[behavior_archetype]
                )
            }
        )
        if not self.state["age_class"]:
            assert True is False

        parameters = BEHAVIOR_ARCHETYPE_PARAMETERS[behavior_archetype]
        rng = np.random.default_rng(self.random_seed+self.agent_id)
        stay_time_preference = int(
            max((rng.normal(parameters["stay_time_preference"], parameters["stay_time_preference"]/4, 1))[0], 0)
        )

        self.behavior = {
            "archetype": behavior_archetype,
            "stay_time_preference": stay_time_preference,
            "allow_repeats": parameters["allow_repeats"],
            "attraction_preference": parameters["attraction_preference"],
            "wait_threshold": parameters["wait_threshold"],
        }

    def select_behavior_archetype(self, agent_id, behavior_archetype_distribution):
        """ Selects a behavior_archetype based off of the behavior_archetype_distribution. """

        rng = random.uniform(0, sum(behavior_archetype_distribution.values()))
        floor = 0.0
        for behavior_archetype, behavior_archetype_weight in behavior_archetype_distribution.items():
            floor += behavior_archetype_weight
            if rng < floor: 
                return behavior_archetype
    
    def select_age_class(self, agent_id, behavior_archetype_dict):
        """ Selects a behavior_archetype based off of the behavior_archetype_distribution. """

        age_class_distribution = {
            "no_child_rides": behavior_archetype_dict["percent_no_child_rides"],
            "no_adult_rides": behavior_archetype_dict["percent_no_adult_rides"],
            "no_preference": behavior_archetype_dict["percent_no_preference"]
        }
        rng = random.uniform(0, sum(age_class_distribution.values()))
        floor = 0.0
        for age_class, age_class_weight in age_class_distribution.items():
            floor += age_class_weight
            if rng < floor: 
                return age_class

    def arrive_at_park(self, time):
        """ Takes a time (mins). Updates the Agent state and log to reflect arrival at the park """

        self.state["within_park"] = True
        self.state["arrival_time"] = time
        self.state["current_location"] = "gate"
        self.state["current_action"] = "idling"
        self.state["time_spent_at_current_location"] = 0
        self.log += f"Agent arrived at park at time {time}. "

    def make_state_change_decision(self, attractions_dict, activities_dict, time, park_closed):
        """  When an agent is idle allow them to make a decison about what to do next. """

        # always leave park if the park is closed
        if park_closed:
            action = "leaving"
            location = "gate"

        # decide if they want to leave
        action, location = self.decide_to_leave_park(time=time)

        if not action:
            # make decisions while holding an expedited pass
            action, location = self.make_attraction_activity_decision(
                activities_dict=activities_dict,
                attractions_dict=attractions_dict,
            )

        return action, location

    def make_attraction_activity_decision(self, activities_dict, attractions_dict):
        """ Decide what to do """

        desired_decision_type, valid_attractions = self.decide_attraction_or_activity(
            attractions_dict=attractions_dict,
        )
        # select activity
        if desired_decision_type == "activity":
            selected_activity = self.select_activity_decision(activities_dict=activities_dict)
            action, location = "traveling", selected_activity
        # try to select attraction
        else:
            action, location = self.select_attraction_decision(
                valid_attractions=valid_attractions,
                attractions_dict=attractions_dict,
            )
            # only default to activity if all wait times are too long for agent and
            # no exp passes are available
            if not action:
                selected_activity = self.select_activity_decision(activities_dict=activities_dict)
                action, location = "traveling", selected_activity
        
        return action, location

    def decide_attraction_or_activity(self, attractions_dict):
        """ Agent decides if the want to visit an attraction or activity. The agent will decide between
        an attraction or activity. If they select an activity that's it. If the select an attraction they
        see if an valid attractions exist for them to visit, while considering there attraction visit
        history and their expedited_pass status. If no valid attractions exist then they will default to 
        an activity. """

        coinflip = random.uniform(0, 1)
        if coinflip <= self.behavior["attraction_preference"]:
            # determine which attractions agent is eligible for
            if self.behavior["allow_repeats"]:
                valid_attractions = [
                    attraction for attraction in attractions_dict.keys() 
                    if attraction not in self.state["expedited_pass"]
                ]
                if self.state["age_class"] == "no_child_rides":
                    valid_attractions = [
                        attraction for attraction in valid_attractions
                        if (
                            (attractions_dict[attraction].child_eligible and attractions_dict[attraction].adult_eligible)
                            or (attractions_dict[attraction].adult_eligible and not attractions_dict[attraction].child_eligible)
                        )
                    ]
                    
                elif self.state["age_class"] == "no_adult_rides":
                    valid_attractions = [
                        attraction for attraction in valid_attractions
                        if (
                            (attractions_dict[attraction].child_eligible and attractions_dict[attraction].adult_eligible)
                            or (attractions_dict[attraction].child_eligible and not attractions_dict[attraction].adult_eligible)
                        )
                    ]
                    
            else:
                valid_attractions = [
                    attraction for attraction, attractions_history in self.state["attractions"].items()
                    if attractions_history["times_completed"] == 0 and attraction not in self.state["expedited_pass"]
                ]
                if self.state["age_class"] == "no_child_rides":
                    valid_attractions = [
                        attraction for attraction in valid_attractions
                        if (
                            (attractions_dict[attraction].child_eligible and attractions_dict[attraction].adult_eligible)
                            or (attractions_dict[attraction].adult_eligible and not attractions_dict[attraction].child_eligible)
                        )
                    ]
                    
                elif self.state["age_class"] == "no_adult_rides":
                    valid_attractions = [
                        attraction for attraction in valid_attractions
                        if (
                            (attractions_dict[attraction].child_eligible and attractions_dict[attraction].adult_eligible)
                            or (attractions_dict[attraction].child_eligible and not attractions_dict[attraction].adult_eligible)
                        )
                    ]
            if len(valid_attractions) == 0:
                desired_decision_type = "activity"
                valid_attractions = []
            else:
                desired_decision_type = "attraction"

        else:
            desired_decision_type = "activity"
            valid_attractions = []

        return desired_decision_type, valid_attractions

    def select_attraction_decision(self, valid_attractions, attractions_dict):
        """ Selects an attraction to visit based off of the attraction popularity """

        # get valid attraction wait times
        attraction_wait_times = {
            attraction_name: attraction.get_wait_time() 
            for attraction_name, attraction in attractions_dict.items()
            if attraction_name in attractions_dict
        }

        action, location = None, None
        step_rng = 0 
        while len(valid_attractions) > 0 and not action:
            step_rng += 1
            # generate popularity distribution for valid attractions
            attraction_popularity_distribution = {
                attraction_name: parameters.popularity for attraction_name, parameters in attractions_dict.items()
                if attraction_name in valid_attractions 
            }
            rng = random.uniform(0, sum(attraction_popularity_distribution.values()))
            floor, ceiling = 0.0, 0.0
            for attraction, attraction_weight in attraction_popularity_distribution.items():
                ceiling += attraction_weight
                if floor < rng <= ceiling: 
                    desired_attraction = attraction
                floor += attraction_weight

            if (
                attraction_wait_times[desired_attraction] > self.state["exp_wait_threshold"]
                and self.state["expedited_pass_ability"]
                and len(self.state["expedited_pass"]) < self.state["exp_limit"]
                and attractions_dict[desired_attraction].expedited_queue 
                and attractions_dict[desired_attraction].exp_queue_passes > 0
            ): 
                action, location = "get pass", desired_attraction
            elif (
                attraction_wait_times[desired_attraction] 
                > (self.behavior["wait_threshold"] + (attractions_dict[desired_attraction].popularity * 6))
            ):
                valid_attractions.remove(desired_attraction)
            elif any(
                rt < attraction_wait_times[desired_attraction] + attractions_dict[desired_attraction].run_time
                for rt in self.state["expedited_return_time"]
            ):
                valid_attractions.remove(desired_attraction)
            else:
                action, location = "traveling", desired_attraction
        
        return action, location
                             
    def decide_to_leave_park(self, time):
        """ Agent determines if they should leave the park. Agents who just arrived will always decide to stay,
        otherwise agents will look at how long they have been at the park and how long they prefer to stay to make
        this decision """

        action, location = None, None

        # determine if they should leave park, the larger this number is the more likely they are to leave
        if time != self.state["arrival_time"]:
            actual_preference_value = (time - self.state["arrival_time"]) - self.behavior["stay_time_preference"]           
            rng = np.random.default_rng(self.random_seed+self.agent_id+time)
            normal_coinflip = (rng.normal(0, 1, 1) * 60)[0]
            if actual_preference_value > normal_coinflip:
                action = "leaving"
                location = "gate"

        return action, location
    
    def select_activity_decision(self, activities_dict):
        """ Selects an activity to visit based off of the activity popularity. """

        activity_popularity_distribution = {
            activity: parameters.popularity for activity, parameters in activities_dict.items()
        }
        rng = random.uniform(0, sum(activity_popularity_distribution.values()))
        floor = 0.0
        for activity, activity_weight in activity_popularity_distribution.items():
            floor += activity_weight
            if rng < floor: 
                return activity
    
    def pass_time(self):
        """ Pass 1 minute of time """
        if self.state["within_park"]:
            self.state["time_spent_at_current_location"] += 1
            if self.state["expedited_pass"]:
                self.state["expedited_return_time"] = [val-1 for val in self.state["expedited_return_time"]]

    # ACTIONS
    def leave_park(self, time):
        """ Updates agent state when they leave park """

        self.state["within_park"] = False
        self.state["current_location"] = "outside park"
        self.state["current_action"] = None
        self.state["exit_time"] = time
        self.state["time_spent_at_current_location"] = 0
        self.log += f"Agent left park at {time}. "

    def enter_queue(self, attraction, time):
        """ Updates agent state when they enter an attraction queue """

        self.state["current_location"] = attraction
        self.state["current_action"] = "queueing"
        self.state["time_spent_at_current_location"] = 0
        self.log += f"Agent entered queue for {attraction} at time {time}. "

    def begin_activity(self, activity, time):
        """ Updates agent state when they visit an activity """

        self.state["current_location"] = activity
        self.state["current_action"] = "browsing"
        self.state["time_spent_at_current_location"] = 0
        self.log += f"Agent visited the activity {activity} at time {time}. "

    def get_pass(self, attraction, time):
        """ Updates agent state when the get a pass """

        self.state["current_location"] = "gate"
        self.state["current_action"] = "getting pass"
        self.state["expedited_pass"].append(attraction)
        self.state["time_spent_at_current_location"] = 0
        self.log += (
            f"Agent picked up an expedited pass for {attraction} at time {time}. "
        )
    
    def assign_expedited_return_time(self, expedited_wait_time):
        """ Updates agent state when are assigned a return time to their expedited attraction """

        self.state["expedited_return_time"].append(expedited_wait_time)
        self.state["current_action"] = "idling"
        self.log += (
            f"The estimated expedited queue wait time is {expedited_wait_time} minutes. "
        )
        
    def return_exp_pass(self, attraction):
        """ Updates agent state when they leave park before using the pass """

        ind_to_remove = None
        for ind, attraction_pass in enumerate(self.state["expedited_pass"]):
            if attraction_pass == attraction:
                ind_to_remove = ind

        del self.state["expedited_pass"][ind_to_remove]
        del self.state["expedited_return_time"][ind_to_remove]

        self.log += (
            f"Agent decided to leave park and returned the expedited pass. "
        )

    def agent_exited_attraction(self, name, time):
        """ Update agents state after they leave an attraction """

        self.state["current_location"] = "gate"
        self.state["current_action"] = "idling"
        self.state["attractions"][name]["times_completed"] += 1
        self.state["time_spent_at_current_location"] = 0

        self.log += f"Agent exited {name} at time {time}. "

    def agent_boarded_attraction(self, name, time):
        """ Update agents state after they board an attraction """
        if name in self.state["expedited_pass"]:
            ind_to_remove = None
            for ind, attraction_pass in enumerate(self.state["expedited_pass"]):
                if attraction_pass == name:
                    ind_to_remove = ind

            if ind_to_remove != None:
                del self.state["expedited_pass"][ind_to_remove]
                del self.state["expedited_return_time"][ind_to_remove]

            self.state["current_location"] = name
            self.state["current_action"] = "riding"
            self.state["time_spent_at_current_location"] = 0
            self.log += (
                f"Agent boarded {name} and redeemed their expedited queue pass at time {time}. "
            )
            return True
        else:
            self.state["current_location"] = name
            self.state["current_action"] = "riding"
            self.state["time_spent_at_current_location"] = 0
            self.log += f"Agent boarded {name} at time {time}. "
            return False

    def agent_exited_activity(self, name, time):
        """ Update agents state after they leave an activity """

        self.state["current_location"] = "gate"
        self.state["current_action"] = "idling"
        self.state["activities"][name]["times_visited"] += 1
        self.state["time_spent_at_current_location"] = 0
        self.log += f"Agent exited the activity {name} at time {time}. "