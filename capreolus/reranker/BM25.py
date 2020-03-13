from capreolus.registry import Dependency
from capreolus.reranker import Reranker
from capreolus.utils.loginit import get_logger

logger = get_logger(__name__)  # pylint: disable=invalid-name


class BM25Reranker(Reranker):
    """ BM25 implemented in Python as a reranker. Tested only with PES20 benchmark.
        This mainly serves as a demonstration of how non-neural methods can be prototyped as rerankers.
    """

    name = "BM25"
    dependencies = {
        "extractor": Dependency(module="extractor", name="docstats"),
        "trainer": Dependency(module="trainer", name="unsupervised"),
    }

    @staticmethod
    def config():
        b = 0.4
        k1 = 0.9

    def build(self):
        return self

    def test(self, d):
        if not hasattr(self["extractor"], "doc_len"):
            raise RuntimeError("reranker's extractor has not been created yet. try running the task's train() method first.")

        query = self["extractor"].qid2toks[d["qid"]]
        avg_doc_len = self["extractor"].query_avg_doc_len[d["qid"]]
        return [self.score_document(query, docid, avg_doc_len) for docid in [d["posdocid"]]]

    def score_document(self, query, docid, avg_doc_len):
        # TODO is it correct to skip over terms that don't appear to be in the idf vocab?
        return sum(
            self.score_document_term(term, docid, avg_doc_len) for term in query if term in self["extractor"].background_idf
        )
        # return sum(self.score_document_term(term, docid, avg_doc_len) for term in query)

    def score_document_term(self, term, docid, avg_doc_len):
        tf = self["extractor"].doc_tf[docid].get(term, 0)
        numerator = tf * (self.cfg["k1"] + 1)
        denominator = tf + self.cfg["k1"] * (1 - self.cfg["b"] + self.cfg["b"] * (self["extractor"].doc_len[docid] / avg_doc_len))

        idf = self["extractor"].background_idf[term]

        return idf * (numerator / denominator)