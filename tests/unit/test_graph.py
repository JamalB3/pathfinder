"""Test Graph methods."""
from unittest import TestCase
from unittest.mock import MagicMock, call, patch

from napps.kytos.pathfinder.graph import KytosGraph
from tests.helpers import get_topology_mock


class TestGraph(TestCase):
    """Tests for the Main class."""

    def setUp(self):
        """Execute steps before each tests."""
        self.kytos_graph = KytosGraph()

    @patch('networkx.Graph.clear')
    def test_clear(self, mock_nx_clear):
        """Test clear."""
        self.kytos_graph.clear()
        mock_nx_clear.assert_called()

    @patch('napps.kytos.pathfinder.graph.KytosGraph.update_links')
    @patch('napps.kytos.pathfinder.graph.KytosGraph.update_nodes')
    @patch('networkx.Graph.clear')
    def test_update_topology(self, *args):
        """Test update topology."""
        (mock_nx_clear, mock_update_nodes, mock_update_links) = args

        topology = get_topology_mock()
        self.kytos_graph.update_topology(topology)

        mock_nx_clear.assert_called()
        mock_update_nodes.assert_called_with(topology.switches)
        mock_update_links.assert_called_with(topology.links)

    @patch('networkx.Graph.add_edge')
    @patch('networkx.Graph.add_node')
    def test_update_nodes(self, *args):
        """Test update nodes."""
        (mock_nx_add_node, mock_nx_add_edge) = args

        topology = get_topology_mock()
        self.kytos_graph.update_nodes(topology.switches)
        switch = topology.switches["00:00:00:00:00:00:00:01"]

        calls = [call(switch.id)]
        calls += [call(interface.id)
                  for interface in switch.interfaces.values()]
        mock_nx_add_node.assert_has_calls(calls)

        calls = [call(switch.id, interface.id)
                 for interface in switch.interfaces.values()]
        mock_nx_add_edge.assert_has_calls(calls)

    @patch('napps.kytos.pathfinder.graph.KytosGraph._set_default_metadata')
    def test_update_links(self, mock_set_default_metadata):
        """Test update nodes."""
        topology = get_topology_mock()
        self.kytos_graph.graph = MagicMock()
        self.kytos_graph.update_links(topology.links)

        keys = []
        all_metadata = [link.metadata for link in topology.links.values()]
        for metadata in all_metadata:
            keys.extend(key for key in metadata.keys())
        mock_set_default_metadata.assert_called_with(keys)

    def test_remove_switch_hops(self):
        """Test remove switch hops."""
        circuit = {"hops": ["00:00:00:00:00:00:00:01:1",
                            "00:00:00:00:00:00:00:01",
                            "00:00:00:00:00:00:00:01:2"]}
        expected_circuit = {"hops": ["00:00:00:00:00:00:00:01:1",
                                     "00:00:00:00:00:00:00:01:2"]}
        self.kytos_graph._remove_switch_hops(circuit)
        self.assertEqual(circuit, expected_circuit)

    @patch('networkx.shortest_simple_paths')
    def test_shortest_paths(self, mock_shortest_simple_paths):
        """Test shortest paths."""
        path = ["00:00:00:00:00:00:00:01:1", "00:00:00:00:00:00:00:01",
                "00:00:00:00:00:00:00:01:2"]
        mock_shortest_simple_paths.return_value = path
        source, dest = "00:00:00:00:00:00:00:01:1", "00:00:00:00:00:00:00:02:2"
        shortest_paths = self.kytos_graph.shortest_paths(source, dest)
        mock_shortest_simple_paths.assert_called_with(self.kytos_graph.graph,
                                                      source, dest, None)
        self.assertEqual(path, shortest_paths)
