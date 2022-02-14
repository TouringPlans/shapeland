# Parameters describing behavior of Agent Archetypes
# Parameters
    # stay_time_preference: mean total park stay time, actual value will be draw from a 
    #   normal distribution. 
    # allow_repeats: dictates whether agent will repeat an attraction or only visit an
    #   an attraction once
    # attraction_preference: value between 0 and 1, larger values influence agents decision to
    #   vists attractions, smaller values influence agents decision to vist attractions
    # wait_threshold: how many minutes agent is willing to wait in a queue, if a wait time is
    #   longer than this the agent will seek and expedited pass
    # percent_children: percent of agents with this archetype that will be children
    # percent_adults: percent of agents with this archetype that will be adults


BEHAVIOR_ARCHETYPE_PARAMETERS = {
    # Agent wants to stay for a long time, go on as many attractions as possible, doesn't want to visit activites,
    # doesn't mind waiting
    "ride_enthusiast": {
        "stay_time_preference": 540,
        "allow_repeats": True,
        "attraction_preference": 0.6,
        "wait_threshold":480,
        "percent_no_child_rides": 0.0,
        "percent_no_adult_rides": 1.0,
        "percent_no_preference": 0.0
    },
    # Agent wants to go on a lot of attractions, but will vists activites occasionally, will wait for a while in a queue
    "ride_favorer": {
        "stay_time_preference": 480,
        "allow_repeats": True,
        "attraction_preference": 0.5,
        "wait_threshold": 420,
        "percent_no_child_rides": 0.0,
        "percent_no_adult_rides": 1.0,
        "percent_no_preference": 0.0
    },
    # Agent wants to stay for a long time and wants to see attractions and activities equally, reasonable about wait times
    "park_tourer": {
        "stay_time_preference": 420,
        "allow_repeats": False,
        "attraction_preference": 0.4, 
        "wait_threshold": 360,
        "percent_no_child_rides": 0.0,
        "percent_no_adult_rides": 1.0,
        "percent_no_preference": 0.0
    },
    # Agent doesn't want to stay long and wants to see attractions and activities equally, inpatient about wait times
    "park_visitor": {
        "stay_time_preference": 360,
        "allow_repeats": False,
        "attraction_preference": 0.3,
        "wait_threshold": 240,
        "percent_no_child_rides": 0.0,
        "percent_no_adult_rides": 1.0,
        "percent_no_preference": 0.0
    },
    # Agent doesn't want to stay long and prefers activities, reasonable about wait times
    "activity_favorer": {
        "stay_time_preference": 300,
        "allow_repeats": False,
        "attraction_preference": 0.2,
        "wait_threshold": 180,
        "percent_no_child_rides": 0.0,
        "percent_no_adult_rides": 1.0,
        "percent_no_preference": 0.0
    },
    # Agent wants to visit a lot of activities, reasonable about wait times
    "activity_enthusiast": {
        "stay_time_preference": 240,
        "allow_repeats": False,
        "attraction_preference": 0.2,
        "wait_threshold": 90,
        "percent_no_child_rides": 0.0,
        "percent_no_adult_rides": 1.0,
        "percent_no_preference": 0.0
    },

}
