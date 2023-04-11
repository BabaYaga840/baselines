
import unittest
from typing import List

#import random
from tqdm import tqdm

import nmmo
from nmmo.core.realm import Realm
from nmmo.core.tile import TileState
from nmmo.entity.entity import Entity, EntityState
from nmmo.systems.item import ItemState
from scripted import baselines
from baseline_env import BaselineEnv
from team_helper import TeamHelper

# Allow private access for testing
# pylint: disable=protected-access

# 30 seems to be enough to test variety of agent actions
TEST_HORIZON = 1 # TODO: test is not implemented. make it short
RANDOM_SEED = 0 # random.randint(0, 10000)

class Config(nmmo.config.Medium, nmmo.config.AllGameSystems):
  RENDER = False
  SPECIALIZE = True
  PLAYERS = [
    baselines.Fisher, baselines.Herbalist, baselines.Prospector,
    baselines.Carver, baselines.Alchemist,
    baselines.Melee, baselines.Range, baselines.Mage]

class TestBaselineEnv(unittest.TestCase):
  @classmethod
  def setUpClass(cls):
    cls.config = Config()
    cls.env = BaselineEnv(
      nmmo.Env(cls.config, RANDOM_SEED),
      TeamHelper([list(range(team * 8 + 1, (team + 1) * 8 + 1)) for team in range(16)]))

  def test_action_space(self):
    action_space = self.env.action_space(0)
    self.assertSetEqual(
        set(action_space.keys()),
        set(nmmo.Action.edges(self.config)))

  def test_observations(self):
    obs = self.env.reset()
    team_helper = self.env._team_helper
    realm = self.env._env.realm

    # check team_id
    self.assertEqual(obs.keys(), team_helper.team_size.keys())

    for _ in tqdm(range(TEST_HORIZON)):
      # pylint: disable=unused-variable
      entity_locations = [
        [ev.row.val, ev.col.val, e] for e, ev in realm.players.entities.items()
      ] + [
        [ev.row.val, ev.col.val, e] for e, ev in realm.npcs.entities.items()
      ]

      # TODO: baseline obs is the result of feature extractor
      #   the below should be rewritten after the feature extractor is complete
      # for player_id, player_obs in obs.items():
      #   self._validate_tiles(player_obs, realm)
      #   self._validate_entitites(
      #       player_id, player_obs, realm, entity_locations)
      #   self._validate_inventory(player_id, player_obs, realm)
      #   self._validate_market(player_obs, realm)
      obs, _, _, _ = self.env.step({})

  def _validate_tiles(self, obs, realm: Realm):
    for tile_obs in obs["Tile"]:
      tile_obs = TileState.parse_array(tile_obs)
      tile = realm.map.tiles[(int(tile_obs.row), int(tile_obs.col))]
      for key, val in tile_obs.__dict__.items():
        if val != getattr(tile, key).val:
          self.assertEqual(val, getattr(tile, key).val,
            f"Mismatch for {key} in tile {tile_obs.row}, {tile_obs.col}")

  def _validate_entitites(self, player_id, obs, realm: Realm, entity_locations: List[List[int]]):
    observed_entities = set()

    for entity_obs in obs["Entity"]:
      entity_obs = EntityState.parse_array(entity_obs)

      if entity_obs.id == 0:
        continue

      entity: Entity = realm.entity(entity_obs.id)

      observed_entities.add(entity.ent_id)

      for key, val in entity_obs.__dict__.items():
        if getattr(entity, key) is None:
          raise ValueError(f"Entity {entity} has no attribute {key}")
        self.assertEqual(val, getattr(entity, key).val,
          f"Mismatch for {key} in entity {entity_obs.id}")

    # Make sure that we see entities IFF they are in our vision radius
    row = realm.players.entities[player_id].row.val
    col = realm.players.entities[player_id].col.val
    radius = realm.config.PLAYER_VISION_RADIUS
    visible_entities = {
      e for r, c, e in entity_locations
      if row - radius <= r <= row + radius
      and col - radius <= c <= col + radius
    }
    self.assertSetEqual(visible_entities, observed_entities,
      f"Mismatch between observed: {observed_entities} " \
        f"and visible {visible_entities} for player {player_id}, "\
        f" step {realm.tick}")

  def _validate_inventory(self, player_id, obs, realm: Realm):
    self._validate_items(
        {i.id.val: i for i in realm.players[player_id].inventory.items},
        obs["Inventory"]
    )

  def _validate_market(self, obs, realm: Realm):
    self._validate_items(
        {i.item.id.val: i.item for i in realm.exchange._item_listings.values()},
        obs["Market"]
    )

  def _validate_items(self, items_dict, item_obs):
    item_obs = item_obs[item_obs[:,0] != 0]
    if len(items_dict) != len(item_obs):
      assert len(items_dict) == len(item_obs)
    for item_ob in item_obs:
      item_ob = ItemState.parse_array(item_ob)
      item = items_dict[item_ob.id]
      for key, val in item_ob.__dict__.items():
        self.assertEqual(val, getattr(item, key).val,
          f"Mismatch for {key} in item {item_ob.id}: {val} != {getattr(item, key).val}")


if __name__ == '__main__':
  unittest.main()
