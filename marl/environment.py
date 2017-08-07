__author__ = 'alestainer'
"""This is a gym-like environment for the game Wolfpack that allows multiple agents and message exchange between them"""

import numpy as np
import sys

ACTION_MAP = {
    0: (0, 0),
    1: (-1, 0),
    2: (1, 0),
    3: (0, -1),
    4: (0, 1)
}


class Field(object):
    def __init__(self, size, wall_density):
        """
        
        :param size: Size of the field
        :param wall_density: Probability for ea h cell that it will be wall there.
        """
        self.size = size
        field = np.zeros(shape=(size, size))  # Initialize field
        for i in range(size):
            for j in range(size):
                if (field[i][j] != 2 and field[i][j] != 3):
                    field[i][j] = np.random.binomial(1, wall_density)  # Create walls in the labyrinth
        field.flags.writeable = False
        self.field = field


class Hunter():
    def __init__(self, field, coordinates, algorithm):
        """
        
        :param field: Instance of class Field where the hunter is acting.
        :param coordinates: Coordinates in the field.
        :param algorithm: Algorithm that chooses moves and messages.
        """
        self.algorithm = algorithm
        self.coordinates = coordinates
        #self.action = self.algorithm

    # def perceive(self, game):
    #     """
    #     :param game: Instance of Game class.
    #     """
    #     self.information = game.reveal_state(self)

    def action(self):
        self.action = self.algorithm


# class Prey(Actor):
#     def __init__(self, coordinates, algorithm):
#         super(self).__init__()
#         self.algorithm = algorithm
#         self.coordinates = coordinates
#
#     def perceive(self, game):
#         self.information = game.reveal_state(self)
#
#     def action(self):
#         return self.algorithm(self.information)


class Game(object):
    def __init__(self, num_of_hunters=1, algorithms=None, duration=1000, reward_distance=4, message_len=0,
                 field=Field(10, 0.2)):
        """
        
        :param num_of_hunters: Number of hunters playing
        :param algorithms: algorithms that are passed to hunters
        :param duration: Number of steps before interruption
        :param reward_distance: distance from which hunter is getting reward
        :param field: Field where the game is played
        """
        self.duration = duration
        self.number_of_steps = 0
        self.field = field
        self.done = False
        self.reward_distance = reward_distance
        self.message_len = message_len

        prey_coordinates = tuple(np.random.randint(0, field.size, 2))
        while (self.field.field[prey_coordinates] == 1):
            prey_coordinates = tuple(np.random.randint(0, field.size, 2))
        # self.prey = Prey(prey_coordinates, prey_algorithm)

        hunters = []
        for i in range(num_of_hunters):
            coordinates = tuple(np.random.randint(0, field.size, 2))
            while (self.field.field[tuple(coordinates)] == 1 or (coordinates[0] == prey_coordinates[0] and coordinates[1] == prey_coordinates[1])):
                coordinates = tuple(np.random.randint(0, field.size, 2))
            hunters.append(Hunter(self.field, coordinates=coordinates, algorithm=algorithms[i]))
        self.hunters = hunters

        state = self.field.field.copy()
        state[prey_coordinates] = 3
        self.prey_coordinates = prey_coordinates
        for hunter in self.hunters:
            state[hunter.coordinates] = 2

        self.state = state

    def render(self):
        """
        Gives representation of the current game state
        :return: 
        """
        return sys.stdout.write(repr(self.state))

    def reset(self):
        """
        Resets the game with the same walls but with different prey and hunter coordinates
        :return:
        """
        self.number_of_steps = 0
        self.done = False

        prey_coordinates = tuple(np.random.randint(0, self.field.size, 2))
        while (self.field.field[tuple(prey_coordinates)] == 1):
            prey_coordinates = tuple(np.random.randint(0, self.field.size, 2))

        for hunter in self.hunters:
            hunter.coordinates = tuple(np.random.randint(0, self.field.size, 2))
            while (self.field.field[tuple(hunter.coordinates)] == 1 or (hunter.coordinates[0] == prey_coordinates[0]
                                                                        and hunter.coordinates[1] == prey_coordinates[1])):
                hunter.coordinates = tuple(np.random.randint(0, self.field.size, 2))

        state = self.field.field.copy()
        state[tuple(prey_coordinates)] = 3
        for hunter in self.hunters:
            state[tuple(hunter.coordinates)] = 2

        self.state = state

    def validate_position(self, coordinates):
        """
        Check if coordinates do not violate physics restrictions
        :param coordinates: 
        :return: 
        """
        return not (coordinates[0] not in range(0, self.field.size)
                    or coordinates[1] not in range(0, self.field.size)
                    or self.field.field[tuple(coordinates)] == 1)

    def action(self):
        """
        Aggregate hunter's actions and represent them onto the field
        :return: 
        """
        for hunter in self.hunters:
            move = ACTION_MAP[hunter.action()]
            if self.validate_position(np.add(hunter.coordinates, move)):
                hunter.coordinates = np.add(hunter.coordinates, move)

    def calculate_reward(self):
        """
        
        :return: Vector of rewards
        """
        rewards = np.zeros(len(self.hunters))
        for i, hunter in enumerate(self.hunters):
            if np.sqrt((hunter.coordinates[0] - self.prey_coordinates[0]) ** 2
                               + (hunter.coordinates[1] - self.prey_coordinates[1]) ** 2) < self.reward_distance:
                rewards[i] = 1

        multiplier = sum(rewards)
        return rewards * multiplier

    def step(self, actions):
        """
        One basic step in the environment
        :param actions: Set of hunter's actions
        :return: 
        """
        rewards = 0 * len(self.hunters)

        self.number_of_steps += 1

        if self.number_of_steps == self.duration:
            self.done = True

        if any((x.coordinates[0] == self.prey_coordinates[0] and x.coordinates[1] == self.prey_coordinates[1]) for x in self.hunters):
            rewards = self.calculate_reward()
            self.done = True


        self.action()
        observations = []
        for i in range(len(self.hunters)):
            field_observation = self.field.field.copy()
            field_observation[tuple(self.prey_coordinates)] = 3
            field_observation[tuple(self.hunters[i].coordinates)] = 2
            #message_observation = [self.hunters[j].action[1] for j in range(len(self.hunters))]
            #del message_observation[i]
            observations.append(field_observation) # , message_observation

        state = self.field.field.copy()
        state[tuple(self.prey_coordinates)] = 3
        for hunter in self.hunters:
            state[tuple(hunter.coordinates)] = 2

        self.state = state
        return observations, rewards, self.done


def keyboard_read():
    return int(input())


if __name__ == '__main__':
    test_field = Field(10, 0.1)
    test_game = Game(num_of_hunters=2, field=test_field, algorithms= [keyboard_read, keyboard_read])
    for i in range(10):
        test_game.render()
        actions = [test_game.hunters[j].action() for j in range(2)]
        test_game.step(actions=actions)
