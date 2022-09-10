from uuid import uuid4
from typing import List
import logging
from datetime import datetime

from graphio.queries import merge_clause, CypherQuery
from graphio.graph import run_query_return_results

log = logging.getLogger(__name__)


class BaseNode:
    """
    Base node class with functions to write/update data.
    """

    LABELS = []
    MERGE_KEYS = []

    def __init__(self, graph, properties: dict = None):
        self.graph = graph
        if properties:
            self.properties = properties
        else:
            self.properties = {}

    @property
    def label_string(self):
        """
        Return `:Label1:Label2`
        """
        return ':'.join(self.LABELS)

    def merge(self):
        q = "WITH $properties AS properties "
        q += merge_clause(self.LABELS, self.MERGE_KEYS)

        run_query_return_results(self.graph, q, properties=self.properties)

    def neighbors(self, reltype: str, target_labels: List[str]):
        q = CypherQuery()
        q.append("WITH $properties AS properties")
        q.append(f"MATCH (n:{self.label_string})-[:{reltype}]-(target_node:{':'.join(target_labels)})")

        where_filter = []
        for mk in self.MERGE_KEYS:
            filter_string = f"n.{mk} = properties.{mk}"
            where_filter.append(filter_string)
        q.append(f"WHERE {' AND '.join(where_filter)}")

        q.append("RETURN target_node")
        log.debug(q)

        run_query_return_results(self.graph, q.query(), properties=self.properties)

    def connect(self, reltype: str, target_node: 'BaseNode'):
        q = CypherQuery()
        q.append("WITH $start_node_properties AS start_node_properties, $end_node_properties AS end_node_properties")
        q.append(f"MATCH (start_node:{self.label_string}), (end_node:{target_node.label_string})")

        where_filter = []
        for mk in self.MERGE_KEYS:
            filter_string = f"start_node.{mk} = start_node_properties.{mk}"
            where_filter.append(filter_string)

        for mk in target_node.MERGE_KEYS:
            filter_string = f"end_node.{mk} = end_node_properties.{mk}"
            where_filter.append(filter_string)

        q.append(f"WHERE {' AND '.join(where_filter)}")

        q.append(f"MERGE (start_node)-[:{reltype}]->(end_node)")

        log.debug(q)

        run_query_return_results(self.graph, q.query(), start_node_properties=self.properties, end_node_properties=target_node.properties)


class Pipeline(BaseNode):

    LABELS = ['Pipeline']
    MERGE_KEYS = ['name']

    def __init__(self, graph, name: str):
        self.name = name

        super(Pipeline, self).__init__(graph, {'name': self.name})

    def start_run(self):
        pr = PipelineRun(self.graph)
        now = datetime.now()
        pr.properties['start_datetime'] = now
        pr.properties['start_timestamp'] = datetime.timestamp(now)

        pr.merge()

        self.connect('HAS_RUN', pr)

        return pr

    def pipeline_runs(self, graph):
        return self.neighbors(graph, 'HAS_RUN', 'PipelineRun')


class PipelineRun(BaseNode):

    LABELS = ['PipelineRun']
    MERGE_KEYS = ['uuid']

    def __init__(self, graph, uuid=None):

        if not uuid:
            uuid = str(uuid4())
        self.uuid = uuid

        super(PipelineRun, self).__init__(graph, {'uuid': self.uuid})


class PipelineStep(BaseNode):
    pass


class PipelineEvent(BaseNode):
    pass