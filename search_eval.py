import math
import sys
import time

import metapy
import pytoml
#import numpy as np
#from scipy import stats
class InL2Ranker(metapy.index.RankingFunction):
    """
    Create a new ranking function in Python that can be used in MeTA.
    """
    def __init__(self, some_param=1.0):
        self.param = some_param
        # You *must* call the base class constructor here!
        super(InL2Ranker, self).__init__()

    def score_one(self, sd):
        """
        You need to override this function to return a score for a single term.
        For fields available in the score_data sd object,
        @see https://meta-toolkit.org/doxygen/structmeta_1_1index_1_1score__data.html
        """
        tfn = sd.doc_term_count * math.log(1+(sd.avg_dl/sd.doc_size),2)
        return sd.query_term_weight * (tfn / (tfn + self.param)) * math.log((sd.num_docs + 1) / (sd.corpus_term_count + .5), 2)
       #return (self.param + sd.doc_term_count) / (self.param * sd.doc_unique_terms + sd.doc_size)


def load_ranker(cfg_file):
    """
    Use this function to return the Ranker object to evaluate, e.g. return InL2Ranker(some_param=1.0) 
    The parameter to this function, cfg_file, is the path to a
    configuration file used to load the index. You can ignore this for MP2.
    """
    return InL2Ranker()

if __name__ == '__main__':
    print("test")
    #if len(sys.argv) != 2:
     #   print("Usage: {} config.toml".format(sys.argv[0]))
      #  sys.exit(1)

    cfg = "config.toml"
    print('Building or loading index...')
    idx = metapy.index.make_inverted_index(cfg)
    ranker = load_ranker(cfg)
    ev = metapy.index.IREval(cfg)

    with open(cfg, 'r') as fin:
        cfg_d = pytoml.load(fin)

    query_cfg = cfg_d['query-runner']
    if query_cfg is None:
        print("query-runner table needed in {}".format(cfg))
        sys.exit(1)

    start_time = time.time()
    top_k = 10
    query_path = query_cfg.get('query-path', 'queries.txt')
    query_start = query_cfg.get('query-id-start', 0)

    result_inl2, result_bm25 = [],[]

    query = metapy.index.Document()
    print('Running queries')
    with open(query_path) as query_file:
        for query_num, line in enumerate(query_file):
            query.content(line.strip())
            results = ranker.score(idx, query, top_k)
            avg_p = ev.avg_p(results, query_start + query_num, top_k)
            result_inl2.append(format(avg_p))
            print("Query {} average precision: {}".format(query_num + 1, avg_p))

    print("Mean average precision: {}".format(ev.map()))
    print("Elapsed: {} seconds".format(round(time.time() - start_time, 4)))

    queryBM25 = metapy.index.Document()
    rankerBM25 = metapy.index.OkapiBM25(k1=1.2,b=0.75,k3=500)
    eval_BM25 = metapy.index.IREval('config.toml')

    query_cfg = cfg_d['query-runner']
    query_start = query_cfg.get('query-id-start', 0)

    if query_cfg is None:
        print("query-runner table needed in {}".format(cfg))
        sys.exit(1)
    with open(query_path) as query_file:
        for query_num, line in enumerate(query_file):
            queryBM25.content(line.strip())
            results = rankerBM25.score(idx, queryBM25, top_k)
            avg_p = eval_BM25.avg_p(results, query_start + query_num, top_k)
            result_bm25.append(format(avg_p))
            print("Query {} average precision: {}".format(query_num + 1, avg_p))

    eval_BM25.map()

    with open ('inl2.avg_p.txt','w') as outFile:
        for res in result_inl2:
            print(res)
            outFile.write("%s\n" % res)

    with open ('bm25.avg_p.txt','w') as outFile:
        for res in result_bm25:
            outFile.write("%s\n" % res)

    #result_inl2 = np.array(map(float,result_inl2))
    #result_bm25 = np.array(map(float,result_bm25))
    #print(stats.ttest_ind(result_inl2,result_bm25).pvalue)
    #with open ('significance.txt','w') as finalFile:
        #finalFile.write(str(stats.ttest_ind(result_inl2,result_bm25).pvalue))

