# coding=utf-8
import networkx as nx
import json
import time
from multiprocessing import Pool
import itertools


def GN():
    nx.algorithms.community.girvan_newman()
    nx.algorithms.community.modularity(G, [{0, 1, 2}, {3, 4, 5}])


with open('small-443nodes-476edges2.json') as fi:
    result = json.load(fi)
    node_id_container = {}
    G = nx.Graph()
    for source in result['links']:
        G.add_edge(source['target'], source['source'], id=source['id'])
    for c in nx.algorithms.components.connected_component_subgraphs(G):
        sub_g = c
        comp = nx.algorithms.community.girvan_newman(c)
        break


def run(fn):
    return nx.algorithms.community.modularity(sub_g, fn)


# 减少迭代的次数
def division(Gi, testFL):
    #   当划分的个数大于ｋ时候，停止划分
    #   k为4 则划分的结果为3
    k = int(nx.classes.function.number_of_nodes(Gi) / 2)
    comp = nx.algorithms.community.girvan_newman(Gi)
    limited = itertools.takewhile(lambda c: len(c) <= k, comp)
    for communities in limited:
        # print(tuple(sorted(c) for c in communities))
        testFL.append(tuple(sorted(c) for c in communities))
    return testFL


def main():
    s = time.time()
    with open('small-443nodes-476edges2.json') as fi:
        result = json.load(fi)
        G = nx.Graph()
        for source in result['links']:
            G.add_edge(source['target'], source['source'], id=source['id'])
        for c in nx.algorithms.components.connected_component_subgraphs(G):
            sub = c
            break
    e1 = time.time()
    print e1 - s
    testFL = []
    division(sub, testFL)
    e2 = time.time()
    print e2 - e1
    print 'concurrent:'  # 创建多个进程，并行执行
    pool = Pool(4)  # 创建拥有5个进程数量的进程池
    # testFL:要处理的数据列表，run：处理testFL列表中数据的函数
    rl = pool.map(run, testFL)
    pool.close()  # 关闭进程池，不再接受新的进程
    pool.join()  # 主进程阻塞等待子进程的退出
    e3 = time.time()
    print "bx", e3 - e2
    # print max(rl, key=lambda x: x[0])
    print max(rl)


if __name__ == "__main__":
    main()
