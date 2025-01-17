"""Module to test the KytosGraph in graph.py"""
from unittest import TestCase

from kytos.core.interface import Interface
from kytos.core.link import Link
from kytos.core.switch import Switch

from napps.kytos.pathfinder.graph import KytosGraph


class TestPaths(TestCase):
    """Tests for the graph class."""

    def initializer(self, val=0):
        """Test setup for a specific topology"""

        method_name = (
            "generate_topology" if not val else "generate_topology_" + str(val)
        )
        method = getattr(self, method_name)
        method()
        switches, links = method()

        self.graph = KytosGraph()
        self.graph.clear()
        self.graph.update_nodes(switches)
        self.graph.update_links(links)

    @staticmethod
    def generate_topology():
        """Generates a predetermined topology"""
        switches = {}
        links = {}
        return switches, links

    @staticmethod
    def create_switch(name, switches):
        """Add a new switch to the list of switches"""
        switch = Switch(name)
        switch.is_active = lambda: True
        switches[name] = switch

    @staticmethod
    def add_interfaces(count, switch, interfaces):
        """Add a new interface to the list of interfaces"""
        for i in range(1, count + 1):
            str1 = f"{switch.dpid}:{i}"
            interface = Interface(str1, i, switch)
            interface.enable()
            interface.activate()
            interfaces[str1] = interface
            switch.update_interface(interface)

    @staticmethod
    def create_link(interface_a, interface_b, interfaces, links):
        """Add a new link between two interfaces into the list of links"""
        compounded = f"{interface_a}|{interface_b}"
        final_name = compounded
        link = Link(
            interfaces[interface_a], interfaces[interface_b]
        )
        link.enable()
        link.activate()
        links[final_name] = link

    @staticmethod
    def add_metadata_to_link(interface_a, interface_b, metrics, links):
        """Add metadata to an existing link in the list of links"""
        compounded = f"{interface_a}|{interface_b}"
        links[compounded].extend_metadata(metrics)
