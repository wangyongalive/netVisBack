# coding=utf-8
import json
import calNetwork
from flask import Flask, request
from flask import render_template, jsonify
from igraph import *
import networkx as nx
import itertools
import mongo
from networkx.readwrite import json_graph
import myutil
from functools import partial
from multiprocessing import Pool
import copy
import datetime

edge_id_container = []
app = Flask(__name__)

G = nx.Graph()


def testObj(result):
    try:
        if (result['nodes']):
            pass
        if (result['links']):
            pass
    except:
        return 'fail'


def parallel(choose_subgraph, sub_g, G):
    edge_id_list = []
    subgraph = G.subgraph(choose_subgraph)
    if nx.algorithms.isomorphism.is_isomorphic(subgraph, sub_g):
        for item in list(subgraph.edges):
            edge_id_list.append(G[item[0]][item[1]]['id'])
    return edge_id_list


def buildGraph():
    global G
    result = mongo.get_all_data()
    for source in result['links']:
        G.add_edge(source['target'], source['source'], id=source['id'])
    global degee_contain
    degee_contain = dict(G.degree())
    return result


# 计算布局数据
def cal_back_layout_data(result, layout_type):
    if layout_type == 'force' or layout_type == 'bundle':
        return False
    nodes = []
    links = []
    for node in result['nodes']:
        nodes.append(node['id'])
    for link in result['links']:
        source = nodes.index(link['source'])
        target = nodes.index(link['target'])
        links.append((source, target))

    graph = Graph()
    graph.add_vertices(len(nodes))
    graph.add_edges(links)
    lay = graph.layout(layout_type)

    for node in result['nodes']:
        for i, row in enumerate(lay):
            if nodes[i] == node['id']:
                node['x'] = row[0]
                node['y'] = row[1]
                break

    for link in result['links']:
        for node in result['nodes']:
            if link['source'] == node['id']:
                link['x1'] = node['x']
                link['y1'] = node['y']
            if link['target'] == node['id']:
                link['x2'] = node['x']
                link['y2'] = node['y']


# GN改进算法的分组
def get_community(ind, sub_g, contain):
    comp = nx.algorithms.community.greedy_modularity_communities(sub_g)
    for index, x in enumerate(comp):
        for item in x:
            contain[item] = {'com': ind, 'group': index}


def partition(G, subgraphs, node_id_container):
    for index, c in enumerate(subgraphs):
        sub_g = G.subgraph(c)
        get_community(index, sub_g, node_id_container)


# 社区划分 使用GN的改进算法
def cal_community(result):
    node_id_container = {}  # 打印的时候会有错　但实际应该没有错
    global G
    partition(G, nx.algorithms.components.connected_component_subgraphs(G), node_id_container)
    for node in result['nodes']:
        node_id = node['id']
        node['com'] = node_id_container[node_id]['com']
        node['group'] = node_id_container[node_id]['group']
        G.nodes[node['id']]['com'] = node['com']
        G.nodes[node['id']]['group'] = node['group']
    return result


@app.route('/')
def index():
    return render_template('index.html')


# 刷取数据  返回前端可以使用的数据格式
@app.route('/get/formresult', methods=['POST'])
def form_result():
    result = request.form['data']
    json_result = json.loads(result)  # 从前端传递过来的数据
    result_link = {'links': [], 'nodes': []}  # 保存处理的结果
    nodes = []  # 取出节点
    for val in json_result:  # val是一个对象
        result_link['nodes'].append({'id': val['id'], 'group': val['group']})
        nodes.append(val['id'])
        for item in val[val['id']]:
            result_link['links'].append({'source': item['id'], 'target': val['id']})
    form_links = []  # 变为v3可以使用的格式
    for val in result_link['links']:
        link = {'source': '', 'target': '', 'value': 1}
        for key, vaule in val.items():
            if (key == 'source'):
                for i, val2 in enumerate(nodes):  # 遍历数组里面的每一项 当相等的时候就赋值
                    if (val2 == vaule):
                        link['source'] = i
            else:
                for i, val2 in enumerate(nodes):  # 遍历数组里面的每一项 当相等的时候就赋值
                    if (val2 == vaule):
                        link['target'] = i
        form_links.append(link)
    result_link['links'] = form_links
    return jsonify(result_link)


# 把数据处理为v3可以使用的格式
# 变化target和source为序列号
@app.route('/get/handledata', methods=['GET'])
def handledata():
    global result
    global G
    # 先计算静态特征
    calNetwork.cal_characters_arguments(result)
    cal_community(result)
    # 深度拷贝
    # hand_result result
    # 在计算特征参数的时候 cal_characters_arguments的源节点和目标节点是id
    # 但是在前端显示的时候 源节点和目标节点是序列号
    hand_result = copy.deepcopy(result)
    myutil.handleData(hand_result)
    # 图的属性
    hand_result['info'] = myutil.get_graph_info(G)
    return jsonify(hand_result)


@app.route('/get/shortpath', methods=['GET'])
def position():
    path_node = request.args.get('path')  # 默认接收的是一个字符串
    path_node_json = json.loads(path_node)  # json.loads变为对象
    shortPath = {'node': [], 'link': []}  # 返回最短路径的节点和边
    global G
    path = dict(nx.all_pairs_shortest_path(G))
    try:
        short_path_name = path[path_node_json[0]][path_node_json[1]]
        shortPath['node'] = short_path_name
        pairs = myutil.getListLink(G, short_path_name)
        shortPath['link'] = pairs
        return jsonify(shortPath)
    except:
        return jsonify({})


degee_contain = {}


def degree_compare(x, y):
    global degee_contain
    return degee_contain[y] - degee_contain[x]


@app.route('/get/findsubgraph', methods=['POST'])
def finding():
    skeleton = request.form['skeleton']  # 默认接收的是一个字符串
    skeleton_json = json.loads(skeleton)  # json.loads变为对象
    skeleton_sub = nx.Graph()
    for link in skeleton_json['link']:
        skeleton_sub.add_edge(link['target']['id'], link['source']['id'])
    global G
    # 对连通子图的大小进行排序
    for c in sorted(nx.algorithms.components.connected_components(G), key=len, reverse=True):
        component_len_nodes = myutil.find_number_of_nodes(nx.subgraph(G, c))  # 数据图节点数
        if component_len_nodes == 40:
            # 计算查询图 数据图的节点和边的数量
            component_graph = nx.Graph(nx.subgraph(G, c))  # 深度拷贝
            component_len_edges = myutil.find_number_of_edges(nx.subgraph(G, c))  # 数据图边数
            sub_len_nodes = myutil.find_number_of_nodes(skeleton_sub)  # 查询图的节点数
            sub_len_edges = myutil.find_number_of_edges(skeleton_sub)  # 查询图的边数

            print
            nx.algorithms.distance_measures.center(nx.subgraph(G, c))
            # actual_degrees = myutil.sort_degree(nx.subgraph(G, c))  # 对度范围进行排序
            # actual_sub_degrees = myutil.sort_degree(skeleton_sub)  # 对度范围进行排序

            # 环的数量

            # 数据图的节点数 要大于等于查询图
            # 数据图的边数 要大于等于查询图
            if (component_len_nodes < sub_len_nodes or component_len_edges < sub_len_edges):
                return

            # 如果查询图的最大的度大于 数据图的最大的度 直接返回
            max_degree = myutil.find_max_degree(nx.subgraph(G, c))
            max_degree_sub = myutil.find_max_degree(skeleton_sub)
            if max_degree_sub > max_degree:
                return

            # 如果查询图的度的最大值和最小值的范围 大于数据图的最大值和最小值的范围 直接返回
            # if (myutil.find_arrange_degree(actual_degrees) > myutil.find_arrange_degree(actual_sub_degrees)):
            #     return
            # print actual_degrees
            # print actual_sub_degrees
            # print myutil.find_arrange_degree(actual_degrees)
            # print myutil.find_arrange_degree(actual_sub_degrees)

            # 查找图中最小的度  过滤不可能的节点
            min_degree = myutil.find_min_degree(skeleton_sub)
            choose_list = []  # choose_list保存的是剔除不可能情况后的节点id
            unchoose_list = []  # choose_list保存的是剔除的节点id
            # choose_list_id保存的是节点在sort_nodes_degree的序号
            for n, degree in nx.classes.function.degree(nx.subgraph(G, c)):
                if degree >= min_degree:
                    choose_list.append(n)
                else:
                    unchoose_list.append(n)
            # 对choose_list排序 按照度的大小排序
            choose_list = sorted(choose_list, cmp=degree_compare)

            # 过滤后的数据图的节点数 要大于等于查询图
            # 过滤后的数据图的边数 要大于等于查询图
            component_graph.remove_nodes_from(unchoose_list)
            if (myutil.find_number_of_edges(component_graph) < sub_len_edges or myutil.find_number_of_nodes(
                    component_graph) < sub_len_nodes):
                return

            dict_nodes = {}
            lenth = nx.algorithms.distance_measures.diameter(skeleton_sub)
            for index, ii in enumerate(choose_list):
                dict_nodes[ii] = set(list(nx.dfs_preorder_nodes(G, source=ii, depth_limit=lenth)))

            choose_subgraph = []
            for i in itertools.combinations(choose_list, sub_len_nodes):
                nodes = list(i)
                result_inter = set(nodes) & set(dict_nodes[nodes[0]])
                ii = 1
                while (len(result_inter) == sub_len_nodes and ii <= sub_len_nodes - 1):
                    result_inter = result_inter & set(dict_nodes[nodes[ii]])
                    ii = ii + 1

                # # if (len(result_inter) != sub_len_nodes or np.sum(com_matrix[list(i)][:, list(i)]) != sub_len_edges * 2):
                # #     continue
                # # 如果节点个数一致则匹配列表中
                if (len(result_inter) == sub_len_nodes):
                    choose_subgraph.append(nodes)
            print
            len(choose_subgraph)

            partial_work = partial(parallel, sub_g=skeleton_sub, G=G)
            pool = Pool(4)  # 创建拥有4个进程数量的进程池
            edge_id_container = pool.map(partial_work, choose_subgraph)
            pool.close()  # 关闭进程池，不再接受新的进程
            pool.join()  # 主进程阻塞等待子进程的退出
            g = lambda x: x != []
            # link_data 返回的边的信息
            global link_data
            link_data = [element for element in edge_id_container if g(element)]
            break
    return jsonify({'link_data': link_data})


@app.route('/get/division', methods=['POST'])
def division():
    res = request.form['data']
    show_nodes = json.loads(res)  # 要显示的节点
    result = mongo.get_all_data()
    G = nx.Graph()
    for source in result['links']:
        G.add_edge(source['target'], source['source'], id=source['id'])
    delete_nodes = myutil.remove_list(G.nodes, show_nodes)  # 要删除的节点
    G.remove_nodes_from(delete_nodes)  # 从图中删除节点
    data1 = json_graph.node_link_data(G)
    result_json = {'nodes': data1['nodes'], 'links': data1['links']}
    myutil.handleData(result_json)
    # contain = cal_community()  # 社区划分的结果[[],[],[]]
    # myutil.get_group(contain, result_json['nodes'])  # 分group
    return jsonify(result_json)


@app.route('/get/neibor', methods=['GET'])
def neibor():
    id = request.args.get('ID')
    edgeId = []
    global G
    idList = G.edges(id)
    nodeId = list(G.adj[id])
    attrList = nx.get_edge_attributes(G, 'id')
    for item in idList:
        try:
            edgeId.append('link_' + attrList[(item[0], item[1])])
        except:
            edgeId.append('link_' + attrList[(item[1], item[0])])
    return jsonify({'edgeId': edgeId, 'nodeId': nodeId})


# 通过传入进来的id 获取到对应G的点和边
@app.route('/get/nodeLink', methods=['POST'])
def getnodeLink():
    nodeId = json.loads(request.form['nodeId'])
    global G
    edge_id_list = []
    for item in G.subgraph(nodeId).edges():
        edge_id_list.append(G[item[0]][item[1]]['id'])
    return jsonify({'edgeId': edge_id_list, 'nodeId': nodeId})


@app.route('/get/nodes', methods=['GET'])
def getnodes():
    global link_data
    global G

    counter = myutil.all_np(link_data)
    attrList = nx.get_edge_attributes(G, 'id')
    new_dict = {v: k for k, v in attrList.items()}
    for key, value in counter.items():
        print
        new_dict[key]
    return jsonify({})


@app.route('/get/test', methods=['GET', 'POST'])
def test():
    try:
        basepath = os.path.dirname(__file__)  # 当前文件所在路径
        filename = request.files['file'].filename  # 文件名
        filename = filename[:-5] + datetime.datetime.now().strftime("%H%M%S") + '.json'
        upload_path = os.path.join(basepath, 'static\uploads', filename)  # 合并路径
        request.files['file'].save(upload_path)
        with open(upload_path) as fi:
            result = json.load(fi)  # 返回dict
            # 简单对数据进行判断
            if (result.has_key('nodes') and result.has_key('links')):
                mongo.importJson(result, filename[:-5])  # 将json数据导入到数据库中
                return jsonify({'status': 'success'})
            else:
                return jsonify({'status': '数据格式不符合规范'})
    except:
        return jsonify({'status': 'fail'})


if __name__ == '__main__':
    global link_data
    global result
    result = buildGraph()
    app.debug = True
    app.run(threaded=True)
