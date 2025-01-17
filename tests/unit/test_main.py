"""Test Main methods."""

from unittest import TestCase
from unittest.mock import MagicMock, patch
from datetime import timedelta

from kytos.core.events import KytosEvent
from kytos.lib.helpers import get_controller_mock, get_test_client

# pylint: disable=import-error
from napps.kytos.pathfinder.main import Main
from tests.helpers import get_topology_mock, get_topology_with_metadata


# pylint: disable=protected-access
class TestMain(TestCase):
    """Tests for the Main class."""

    def setUp(self):
        """Execute steps before each tests."""
        self.napp = Main(get_controller_mock())

    def test_update_topology_success_case(self):
        """Test update topology method to success case."""
        topology = get_topology_mock()
        event = KytosEvent(
            name="kytos.topology.updated", content={"topology": topology}
        )
        self.napp.update_topology(event)

        self.assertEqual(self.napp._topology, topology)

    def test_update_topology_events_out_of_order(self):
        """Test update topology events out of order.

        If a subsequent older event is sent, then the topology
        shouldn't get updated.
        """
        topology = get_topology_mock()
        assert self.napp._topology_updated_at is None
        first_event = KytosEvent(
            name="kytos.topology.updated", content={"topology": topology}
        )
        self.napp.update_topology(first_event)
        assert self.napp._topology_updated_at == first_event.timestamp
        assert self.napp._topology == topology

        second_topology = get_topology_mock()
        second_event = KytosEvent(
            name="kytos.topology.updated", content={"topology": second_topology}
        )
        second_event.timestamp = first_event.timestamp - timedelta(seconds=10)
        self.napp.update_topology(second_event)
        assert self.napp._topology == topology

    def test_update_topology_failure_case(self):
        """Test update topology method to failure case."""
        event = KytosEvent(name="kytos.topology.updated")
        self.napp.update_topology(event)

        self.assertIsNone(self.napp._topology)

    def setting_shortest_path_mocked(self, mock_shortest_paths):
        """Set the primary elements needed to test the retrieving
        process of the shortest path under a mocked approach."""
        self.napp._topology = get_topology_mock()
        path = ["00:00:00:00:00:00:00:01:1", "00:00:00:00:00:00:00:02:1"]
        mock_shortest_paths.return_value = [path]

        api = get_test_client(self.napp.controller, self.napp)

        return api, path

    @patch("napps.kytos.pathfinder.graph.KytosGraph._path_cost")
    @patch("napps.kytos.pathfinder.graph.KytosGraph.k_shortest_paths")
    def test_shortest_path_response(self, mock_shortest_paths, path_cost):
        """Test shortest path."""
        cost_mocked_value = 1
        path_cost.return_value = cost_mocked_value
        api, path = self.setting_shortest_path_mocked(mock_shortest_paths)
        url = "http://127.0.0.1:8181/api/kytos/pathfinder/v2"
        data = {
            "source": "00:00:00:00:00:00:00:01:1",
            "destination": "00:00:00:00:00:00:00:02:1",
            "desired_links": ["1"],
            "undesired_links": None,
        }
        response = api.open(url, method="POST", json=data)

        expected_response = {
            "paths": [{"hops": path, "cost": cost_mocked_value}]
        }
        self.assertEqual(response.json, expected_response)

    @patch("napps.kytos.pathfinder.graph.KytosGraph._path_cost")
    @patch("napps.kytos.pathfinder.graph.KytosGraph.k_shortest_paths")
    def test_shortest_path_response_status_code(
        self, mock_shortest_paths, path_cost
    ):
        """Test shortest path."""
        path_cost.return_value = 1
        api, _ = self.setting_shortest_path_mocked(mock_shortest_paths)
        url = "http://127.0.0.1:8181/api/kytos/pathfinder/v2"
        data = {
            "source": "00:00:00:00:00:00:00:01:1",
            "destination": "00:00:00:00:00:00:00:02:1",
            "desired_links": ["1"],
            "undesired_links": None,
        }
        response = api.open(url, method="POST", json=data)

        self.assertEqual(response.status_code, 200)

    def setting_shortest_constrained_path_mocked(
        self, mock_constrained_k_shortest_paths
    ):
        """Set the primary elements needed to test the retrieving process
        of the shortest constrained path under a mocked approach."""
        source = "00:00:00:00:00:00:00:01:1"
        destination = "00:00:00:00:00:00:00:02:1"
        path = [source, destination]
        base_metrics = {"ownership": "bob"}
        fle_metrics = {"delay": 30}
        metrics = {**base_metrics, **fle_metrics}
        mock_constrained_k_shortest_paths.return_value = [
            {"hops": [path], "metrics": metrics}
        ]

        api = get_test_client(self.napp.controller, self.napp)
        url = "http://127.0.0.1:8181/api/kytos/pathfinder/v2/"
        data = {
            "source": "00:00:00:00:00:00:00:01:1",
            "destination": "00:00:00:00:00:00:00:02:1",
            "base_metrics": {"ownership": "bob"},
            "flexible_metrics": {"delay": 30},
            "minimum_flexible_hits": 1,
        }
        response = api.open(url, method="POST", json=data)

        return response, metrics, path

    @patch("napps.kytos.pathfinder.graph.KytosGraph._path_cost")
    @patch(
        "napps.kytos.pathfinder.graph.KytosGraph.constrained_k_shortest_paths",
        autospec=True,
    )
    def test_shortest_constrained_path_response(
        self, mock_constrained_k_shortest_paths, path_cost
    ):
        """Test constrained flexible paths."""
        cost_mocked_value = 1
        path_cost.return_value = cost_mocked_value
        (
            response,
            metrics,
            path,
        ) = self.setting_shortest_constrained_path_mocked(
            mock_constrained_k_shortest_paths
        )
        expected_response = [
            {"metrics": metrics, "hops": [path], "cost": cost_mocked_value}
        ]

        self.assertDictEqual(response.json["paths"][0], expected_response[0])

    @patch("napps.kytos.pathfinder.graph.KytosGraph._path_cost")
    @patch(
        "napps.kytos.pathfinder.graph.KytosGraph.constrained_k_shortest_paths",
        autospec=True,
    )
    def test_shortest_constrained_path_response_status_code(
        self, mock_constrained_k_shortest_paths, path_cost
    ):
        """Test constrained flexible paths."""
        path_cost.return_value = 1
        response, _, _ = self.setting_shortest_constrained_path_mocked(
            mock_constrained_k_shortest_paths
        )

        self.assertEqual(response.status_code, 200)

    def test_filter_paths_response_on_desired(self):
        """Test filter paths."""
        self.napp._topology = get_topology_mock()
        paths = [
            {
                "hops": [
                    "00:00:00:00:00:00:00:01:1",
                    "00:00:00:00:00:00:00:02:1",
                    "00:00:00:00:00:00:00:02:2",
                    "00:00:00:00:00:00:00:03:2",
                ]
            },
            {
                "hops": [
                    "00:00:00:00:00:00:00:01:1",
                    "00:00:00:00:00:00:00:01",
                    "00:00:00:00:00:00:00:04",
                    "00:00:00:00:00:00:00:04:1",
                ],
                "cost": 3,
            },
        ]
        desired = ["1", "3"]

        for link in desired:
            assert self.napp._topology.links[link]
        filtered_paths = self.napp._filter_paths_desired_links(paths, desired)
        assert filtered_paths == [paths[0]]

        filtered_paths = self.napp._filter_paths_desired_links(paths, ["1", "2"])
        assert not filtered_paths

        filtered_paths = self.napp._filter_paths_desired_links(paths, ["inexistent_id"])
        assert not filtered_paths

    def test_filter_paths_le_cost_response(self):
        """Test filter paths."""
        self.napp._topology = get_topology_mock()
        paths = [
            {
                "hops": [
                    "00:00:00:00:00:00:00:01:1",
                    "00:00:00:00:00:00:00:01",
                    "00:00:00:00:00:00:00:02:1",
                    "00:00:00:00:00:00:00:02",
                    "00:00:00:00:00:00:00:02:2",
                    "00:00:00:00:00:00:00:04",
                    "00:00:00:00:00:00:00:04:1",
                ],
                "cost": 6,
            },
            {
                "hops": [
                    "00:00:00:00:00:00:00:01:1",
                    "00:00:00:00:00:00:00:01",
                    "00:00:00:00:00:00:00:04",
                    "00:00:00:00:00:00:00:04:1",
                ],
                "cost": 3,
            },
        ]
        filtered_paths = self.napp._filter_paths_le_cost(paths, 3)
        assert len(filtered_paths) == 1
        assert filtered_paths[0]["cost"] == 3

    def test_filter_paths_response_on_undesired(self):
        """Test filter paths."""
        self.napp._topology = get_topology_mock()
        paths = [
            {
                "hops": [
                    "00:00:00:00:00:00:00:01:1",
                    "00:00:00:00:00:00:00:02:1",
                    "00:00:00:00:00:00:00:02:2",
                    "00:00:00:00:00:00:00:03:2",
                ]
            }
        ]

        undesired = ["1"]
        filtered_paths = self.napp._filter_paths_undesired_links(paths, undesired)
        assert not filtered_paths

        undesired = ["3"]
        filtered_paths = self.napp._filter_paths_undesired_links(paths, undesired)
        assert not filtered_paths

        undesired = ["1", "3"]
        filtered_paths = self.napp._filter_paths_undesired_links(paths, undesired)
        assert not filtered_paths

        filtered_paths = self.napp._filter_paths_undesired_links(paths, ["none"])
        assert filtered_paths == paths

    def setting_path(self):
        """Set the primary elements needed to test the topology
        update process under a "real-simulated" scenario."""
        topology = get_topology_with_metadata()
        event = KytosEvent(
            name="kytos.topology.updated", content={"topology": topology}
        )
        self.napp.update_topology(event)

    def test_update_links_changed(self):
        """Test update_links_metadata_changed."""
        self.napp.graph.update_link_metadata = MagicMock()
        self.napp.controller.buffers.app.put = MagicMock()
        event = KytosEvent(
            name="kytos.topology.links.metadata.added",
            content={"link": MagicMock(), "metadata": {}}
        )
        self.napp.update_links_metadata_changed(event)
        assert self.napp.graph.update_link_metadata.call_count == 1
        assert self.napp.controller.buffers.app.put.call_count == 0

    def test_update_links_changed_out_of_order(self):
        """Test update_links_metadata_changed out of order."""
        self.napp.graph.update_link_metadata = MagicMock()
        self.napp.controller.buffers.app.put = MagicMock()
        link = MagicMock(id="1")
        assert link.id not in self.napp._links_updated_at
        event = KytosEvent(
            name="kytos.topology.links.metadata.added",
            content={"link": link, "metadata": {}}
        )
        self.napp.update_links_metadata_changed(event)
        assert self.napp.graph.update_link_metadata.call_count == 1
        assert self.napp.controller.buffers.app.put.call_count == 0
        assert self.napp._links_updated_at[link.id] == event.timestamp

        second_event = KytosEvent(
            name="kytos.topology.links.metadata.added",
            content={"link": link, "metadata": {}}
        )
        second_event.timestamp = event.timestamp - timedelta(seconds=10)
        self.napp.update_links_metadata_changed(second_event)
        assert self.napp.graph.update_link_metadata.call_count == 1
        assert self.napp.controller.buffers.app.put.call_count == 0
        assert self.napp._links_updated_at[link.id] == event.timestamp

    def test_update_links_changed_key_error(self):
        """Test update_links_metadata_changed key_error."""
        self.napp.graph.update_link_metadata = MagicMock()
        self.napp.controller.buffers.app.put = MagicMock()
        event = KytosEvent(
            name="kytos.topology.links.metadata.added",
            content={"link": MagicMock()}
        )
        self.napp.update_links_metadata_changed(event)
        assert self.napp.graph.update_link_metadata.call_count == 1
        assert self.napp.controller.buffers.app.put.call_count == 1

    def test_shortest_path(self):
        """Test shortest path."""
        self.setting_path()

        api = get_test_client(self.napp.controller, self.napp)
        url = "http://127.0.0.1:8181/api/kytos/pathfinder/v2/"

        source, destination = "User1", "User4"
        data = {"source": source, "destination": destination}

        response = api.open(url, method="POST", json=data)

        for path in response.json["paths"]:
            assert source == path["hops"][0]
            assert destination == path["hops"][-1]

    def setting_shortest_constrained_path_exception(self, side_effect):
        """Set the primary elements needed to test the shortest
        constrained path behavior under exception actions."""
        self.setting_path()
        api = get_test_client(self.napp.controller, self.napp)

        with patch(
            "napps.kytos.pathfinder.graph.KytosGraph."
            "constrained_k_shortest_paths",
            side_effect=side_effect,
        ):
            url = "http://127.0.0.1:8181/api/kytos/pathfinder/v2/"

            data = {
                "source": "00:00:00:00:00:00:00:01:1",
                "destination": "00:00:00:00:00:00:00:02:1",
                "base_metrics": {"ownership": "bob"},
                "flexible_metrics": {"delay": 30},
                "minimum_flexible_hits": 1,
            }

            response = api.open(url, method="POST", json=data)

        return response

    def test_shortest_constrained_path_400_exception(self):
        """Test shortest path."""
        response = self.setting_shortest_constrained_path_exception(TypeError)

        self.assertEqual(response.status_code, 400)
