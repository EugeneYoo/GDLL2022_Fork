import numpy as np
import scipy.sparse as sp
import torch
import networkx as nx

def createIndex():
    index = []
    for file in ["datasets\subgraph\hop1", "datasets\subgraph\hop2", "datasets\subgraph\hop3"]:
        with open(file) as f:
            edges = [edge.rstrip() for edge in f]
        arr = []
        for edge in edges:
            arr2 = []
            arr3 = []
            x = edge.split(',')
            y = x[1].split(' ')
            arr2.append(int(x[0]))
            for e in y:
                z = e.split('-')
                arr4 = [int(z[0]), int(z[1])]
                arr3.append(arr4)
            arr2.append(arr3)
            arr.append(arr2)

        index.append(arr)
    return index

# def get(hop, node):
#     for x in index[hop]:
#         if x[0] == node:
#             return x[1]
#
# subgraph = get(2, 114)
# print(subgraph)

class Nsubgraph:
    def __init__(self, nodeid=None, neighborlist=None, nodeFeatures=None, khop=None):
        self.nodeid = nodeid
        self.neighborlist= neighborlist
        self.nodeFeatures=nodeFeatures
        self.khop= khop

def sampling(src_nodes, sample_num, neighbor_tab):
	"""
	"""
	results = []
	for src_id in src_nodes:
		res = np.random.choice(neighbor_tab[src_id], size=(sample_num,))
		results.append(res)
	return np.asarray(results).flatten()


def multihop_sampling(src_nodes, sample_nums, neighbor_tab):
	sampling_result = [src_nodes]
	for k, hopk_num in enumerate(sample_nums):
		hopk_result = sampling(sampling_result[k], hopk_num, neighbor_tab)
		sampling_result.append(hopk_result)

	return sampling_result

def encode_onehot(labels):
    classes = set(labels)
    classes_dict = {c: np.identity(len(classes))[i, :] for i, c in enumerate(classes)}
    labels_onehot = np.array(list(map(classes_dict.get, labels)),
                             dtype=np.int32)
    return labels_onehot

def getsubgraph(hop, node, index):
    for x in index[hop]:
        if x[0] == node:
            return x[1]


def draw_kkl(nx_G, label_map, node_color, pos=None, **kwargs):
    fig, ax = plt.subplots(figsize=(10,10))
    if pos is None:
        pos = nx.spring_layout(nx_G, k=5/np.sqrt(nx_G.number_of_nodes()))

    nx.draw(
        nx_G, pos, with_labels=label_map is not None,
        labels=label_map,
        node_color=node_color,
        ax=ax, **kwargs)

def load_khop(path="./datasets/cora/", dataset="cora", khops =1):

    print('Loading {} dataset...'.format(dataset))
    index = createIndex()

    idx_features_labels = np.genfromtxt("{}{}.content".format(path, dataset),
                                        dtype=np.dtype(str))
    numOfNodes = idx_features_labels.shape[0]
    hops = []
    for x in range(numOfNodes):
        subgraph = []
        nodeID = idx_features_labels[x,0]
        if(khops==1):
            for ind in index[0]:
                if ind[0] == int(nodeID):
                    subgraph = Nsubgraph(nodeid=(int(nodeID)),neighborlist=ind[1],khop=khops)
        elif(khops==2):
            for ind in index[1]:
                if ind[0] == int(nodeID):
                    subgraph = ind[1]
        elif(khops==3):
            for ind in index[2]:
                if ind[0] == int(nodeID):
                    subgraph = ind[1]
        else:
            print("add more than 3 hops here")
        hops.append(subgraph)

    features = sp.csr_matrix(idx_features_labels[:, 1:-1], dtype=np.float32)
    labels = encode_onehot(idx_features_labels[:, -1])

    # create graph
    idx = np.array(idx_features_labels[:, 0], dtype=np.int32)
    idx_map = {j: i for i, j in enumerate(idx)}
    edges_unordered = np.genfromtxt("{}{}.1hop".format(path, dataset), dtype=np.int32)
    # edges_unordered = np.genfromtxt("{}{}.cites".format(path, dataset), dtype=np.int32)
    edges = np.array(list(map(idx_map.get, edges_unordered.flatten())),
                     dtype=np.int32).reshape(edges_unordered.shape)
    adj = sp.coo_matrix((np.ones(edges.shape[0]), (edges[:, 0], edges[:, 1])),
                        shape=(labels.shape[0], labels.shape[0]),
                        dtype=np.float32)

    # build symmetric adjacency matrix
    adj = adj + adj.T.multiply(adj.T > adj) - adj.multiply(adj.T > adj)

    features = normalize(features)
    adj = normalize(adj + sp.eye(adj.shape[0]))

    idx_train = range(140)
    idx_val = range(200, 500)
    # idx_test = range(500, 1500)

    features = torch.FloatTensor(np.array(features.todense()))
    labels = torch.LongTensor(np.where(labels)[1])
    adj = sparse_mx_to_torch_sparse_tensor(adj)

    idx_train = torch.LongTensor(idx_train)
    idx_val = torch.LongTensor(idx_val)
    # idx_test = torch.LongTensor(idx_test)

    return adj, features, labels, idx_train, idx_val  #, idx_test

def load_data(path="./datasets/cora/", dataset="cora"):

    print('Loading {} dataset...'.format(dataset))


    idx_features_labels = np.genfromtxt("{}{}.content".format(path, dataset),
                                        dtype=np.dtype(str))
    features = sp.csr_matrix(idx_features_labels[:, 1:-1], dtype=np.float32)
    labels = encode_onehot(idx_features_labels[:, -1])

    # create graph
    idx = np.array(idx_features_labels[:, 0], dtype=np.int32)
    idx_map = {j: i for i, j in enumerate(idx)}
    edges_unordered = np.genfromtxt("{}{}.cites".format(path, dataset),
                                    dtype=np.int32)
    edges = np.array(list(map(idx_map.get, edges_unordered.flatten())),
                     dtype=np.int32).reshape(edges_unordered.shape)
    adj = sp.coo_matrix((np.ones(edges.shape[0]), (edges[:, 0], edges[:, 1])),
                        shape=(labels.shape[0], labels.shape[0]),
                        dtype=np.float32)

    # build symmetric adjacency matrix
    adj = adj + adj.T.multiply(adj.T > adj) - adj.multiply(adj.T > adj)

    features = normalize(features)
    adj = normalize(adj + sp.eye(adj.shape[0]))

    idx_train = range(140)
    idx_val = range(200, 500)
    idx_test = range(500, 1500)

    features = torch.FloatTensor(np.array(features.todense()))
    labels = torch.LongTensor(np.where(labels)[1])
    adj = sparse_mx_to_torch_sparse_tensor(adj)

    idx_train = torch.LongTensor(idx_train)
    idx_val = torch.LongTensor(idx_val)
    idx_test = torch.LongTensor(idx_test)

    return adj, features, labels, idx_train, idx_val, idx_test

def load_dataT(path="./datasets/cora/", dataset="cora"):
    """Load citation network dataset (cora only for now)"""
    print('Loading {} dataset...'.format(dataset))

    # genfromtxt会从
    idx_features_labels = np.genfromtxt("{}{}.content".format(path, dataset),
                                        dtype=np.dtype(str))
    features = sp.csr_matrix(idx_features_labels[:, 1:-1], dtype=np.float32)
    labels = encode_onehot(idx_features_labels[:, -1])

    # build graph
    idx = np.array(idx_features_labels[:, 0], dtype=np.int32)
    idx_map = {j: i for i, j in enumerate(idx)} # 每篇论文的索引是多少
    edges_unordered = np.genfromtxt("{}{}.cites".format(path, dataset),
                                    dtype=np.int32)
    edges = np.array(list(map(idx_map.get, edges_unordered.flatten())), # flatten展开成一维向量
                     dtype=np.int32).reshape(edges_unordered.shape) # 将id相对应的边，改成索引相对应的边。将edges_unordered.flatten()中的值，输入get函数中，返回value
    adj = sp.coo_matrix((np.ones(edges.shape[0]), (edges[:, 0], edges[:, 1])), # (edges[:, 0], edges[:, 1])这些位置的值为1
                        shape=(labels.shape[0], labels.shape[0]),
                        dtype=np.float32)
    # 利用edges生成邻接表
    adj_table = dict()
    for i in range(len(idx)):
        adj_table[i] = []

    for edge in edges:
        if edge[1] not in adj_table[edge[0]]:
            adj_table[edge[0]].append(edge[1])


    # build symmetric adjacency matrix
    adj = adj + adj.T.multiply(adj.T > adj) - adj.multiply(adj.T > adj)

    features = normalize(features) # 对邻接矩阵采用均值归一化
    adj = normalize(adj + sp.eye(adj.shape[0]))

    idx_train = range(140)
    idx_val = range(200, 500)
    idx_test = range(500, 1500)

    features = torch.FloatTensor(np.array(features.todense()))
    labels = torch.LongTensor(np.where(labels)[1])
    adj = sparse_mx_to_torch_sparse_tensor(adj)

    idx_train = torch.LongTensor(idx_train)
    idx_val = torch.LongTensor(idx_val)
    idx_test = torch.LongTensor(idx_test)



    return adj, features, labels, idx_train, idx_val, idx_test, adj_table


def normalize(mx):
    """Row-normalize sparse matrix"""
    rowsum = np.array(mx.sum(1))
    r_inv = np.power(rowsum, -1).flatten()
    r_inv[np.isinf(r_inv)] = 0.
    r_mat_inv = sp.diags(r_inv)
    mx = r_mat_inv.dot(mx)
    return mx


def sparse_mx_to_torch_sparse_tensor(sparse_mx):
    """Convert a scipy sparse matrix to a torch sparse tensor."""
    sparse_mx = sparse_mx.tocoo().astype(np.float32)
    indices = torch.from_numpy(
        np.vstack((sparse_mx.row, sparse_mx.col)).astype(np.int64))
    values = torch.from_numpy(sparse_mx.data)
    shape = torch.Size(sparse_mx.shape)
    return torch.sparse.FloatTensor(indices, values, shape)


def accuracy(output, labels):
    preds = output.max(1)[1].type_as(labels)
    correct = preds.eq(labels).double()
    correct = correct.sum()
    return correct / len(labels)