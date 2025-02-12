import unittest
import numpy as np

import nmmo
from nmmo.entity.entity import EntityState
from nmmo.core.tile import TileState
from nmmo.datastore.numpy_datastore import NumpyDatastore

# pylint: disable=import-error
from feature_extractor.entity_helper import EntityHelper, ATK_TYPE
from feature_extractor.map_helper import MapHelper
from lib.team.team_helper import TeamHelper

from model.realikun.model import ModelArchitecture

EntityAttr = EntityState.State.attr_name_to_col


class MockMapHelper(MapHelper):
  # pylint: disable=unused-argument
  def nearby_features(self, row: int, col: int):
    # TODO: gather all model-related consts in one place
    return np.zeros(ModelArchitecture.NEARBY_NUM_FEATURES)

class TestEntityHelper(unittest.TestCase):
  def setUp(self):
    self.datastore = NumpyDatastore()
    self.datastore.register_object_type("Entity", EntityState.State.num_attributes)
    self.datastore.register_object_type("Tile", TileState.State.num_attributes)
    self.config = nmmo.config.Medium()

    self.num_npcs = 4
    self.num_team = 2
    self.team_size = 4
    teams = { tid: list(range(1+tid*self.team_size, 1+(tid+1)*self.team_size))
              for tid in range(self.num_team) }

    self.team_id = 0
    self.team_helper = TeamHelper(teams)
    self.entity_helper = EntityHelper(self.config, self.team_helper, self.team_id)
    self.map_helper = MockMapHelper(self.config, self.entity_helper)

  def _make_entity(self, ent_id, row=0, col=0):
    # pylint: disable=no-member
    e = EntityState(self.datastore, EntityState.Limits(self.config))
    e.id.update(ent_id)
    e.row.update(row)
    e.col.update(col)
    return e

  def create_sample_obs(self, team_id, num_npcs):
    entities = []
    for i in self.team_helper.team_and_position_for_agent:
      entities.append(self._make_entity(i, row=2*i, col=3*i))

    for i in range(1, num_npcs+1):
      entities.append(self._make_entity(-i, row=2*i, col=3))

    # create team obs
    obs = {}
    for eid in self.team_helper.teams[team_id]:
      obs[eid] = {
        "Entity": EntityState.Query.by_ids(
          self.datastore, [e.id.val for e in entities])}

    return obs

  def test_reset(self):
    obs = self.create_sample_obs(self.team_id, self.num_npcs)
    self.entity_helper.reset(obs)

    self.assertIsNotNone(self.entity_helper.member_professions)
    self.assertTrue(set(self.entity_helper.member_professions).issubset(set(ATK_TYPE)))
    self.assertEqual(len(self.entity_helper.member_professions), self.team_size)

  def test_update(self):
    obs = self.create_sample_obs(self.team_id, self.num_npcs)
    self.entity_helper.reset(obs)

    num_ent = self.num_team * self.team_size + self.num_npcs

    # pylint: disable=protected-access
    self.assertEqual(len(self.entity_helper._entities), num_ent)
    self.assertEqual(len(self.entity_helper.member_location), self.team_size)
    self.assertEqual(len(self.entity_helper._entity_features), num_ent)
    self.assertEqual(len(self.entity_helper._entity_features[1]),
                     ModelArchitecture.ENTITY_NUM_FEATURES)

  def test_team_features_and_mask(self):
    obs = self.create_sample_obs(self.team_id, self.num_npcs)
    self.entity_helper.reset(obs)

    team_features, team_mask = \
      self.entity_helper.team_features_and_mask(self.map_helper)

    n_feat = ModelArchitecture.ENTITY_NUM_FEATURES + \
             self.num_team + self.team_size + \
             ModelArchitecture.NUM_PROFESSIONS + \
             ModelArchitecture.NEARBY_NUM_FEATURES

    self.assertEqual(team_features.shape, (self.team_size, n_feat))
    self.assertEqual(team_mask.shape, (self.team_size,))

  def test_npcs_features_and_mask(self):
    obs = self.create_sample_obs(self.team_id, self.num_npcs)
    self.entity_helper.reset(obs)
    npc_features, npc_mask, npc_target = self.entity_helper.npcs_features_and_mask()

    self.assertEqual(npc_features.shape, (self.team_size,
                                          ModelArchitecture.ENTITY_NUM_NPCS_CONSIDERED,
                                          ModelArchitecture.ENTITY_NUM_FEATURES))
    self.assertEqual(npc_mask.shape, (self.team_size,
                                      ModelArchitecture.ENTITY_NUM_NPCS_CONSIDERED))
    self.assertEqual(npc_target.shape, (self.team_size,
                                        ModelArchitecture.ENTITY_NUM_NPCS_CONSIDERED))


  def test_enemies_features_and_mask(self):
    obs = self.create_sample_obs(self.team_id, self.num_npcs)
    self.entity_helper.reset(obs)
    enemy_features, enemy_mask, enemy_target = self.entity_helper.enemies_features_and_mask()

    self.assertEqual(enemy_features.shape, (self.team_size,
                                            ModelArchitecture.ENTITY_NUM_ENEMIES_CONSIDERED,
                                            ModelArchitecture.ENTITY_NUM_FEATURES))
    self.assertEqual(enemy_mask.shape, (self.team_size,
                                        ModelArchitecture.ENTITY_NUM_ENEMIES_CONSIDERED))
    self.assertEqual(enemy_target.shape, (self.team_size,
                                          ModelArchitecture.ENTITY_NUM_ENEMIES_CONSIDERED))

  def test_choose_professions(self):
    # pylint: disable=protected-access
    self.entity_helper._choose_professions()
    professions = self.entity_helper.member_professions
    self.assertEqual(len(professions), self.team_size)
    self.assertTrue(set(professions).issubset(set(ATK_TYPE)))


if __name__ == '__main__':
  unittest.main()
