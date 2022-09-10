from graphio.graph import run_query_return_results

from graphlogger.model import Pipeline


class TestPipeline:

    def test_pipeline_merge(self, graph, clear_graph):
        p = Pipeline(graph, 'test_pipeline')
        p.merge()

        result = run_query_return_results(graph, "MATCH (p:Pipeline) RETURN count(p)")
        assert result[0][0] == 1

        # run again to test MERGE
        p.merge()

        result = run_query_return_results(graph, "MATCH (p:Pipeline) RETURN count(p)")
        assert result[0][0] == 1

    def test_start_pipeline(self, graph, clear_graph):
        p = Pipeline(graph, 'test_pipeline')
        p.merge()

        p.start_run()

        result = run_query_return_results(graph, "MATCH (p:Pipeline)-[:HAS_RUN]->(pr:PipelineRun) RETURN count(p), count(pr)")
        assert result[0][0] == 1
        assert result[0][1] == 1