import matplotlib.pyplot as plt
import pandas as pd
import scipy.stats as stats
from sklearn import linear_model
import time
import kernelml

def generate_MoG_data(num_data, means, covariances, weights):
    """ Creates a list of data points """
    num_clusters = len(weights)
    data = []
    for i in range(num_data):
        k = np.random.choice(len(weights), 1, p=weights)[0]
        x = np.random.multivariate_normal(means[k], covariances[k])
        data.append(x)
    return data
    
init_means = [
    [5, 0], # mean of cluster 1
    [1, 1], # mean of cluster 2
    [0, 5]  # mean of cluster 3
]
init_covariances = [
    [[.5, 0.], [0, .5]], # covariance of cluster 1
    [[.92, .38], [.38, .91]], # covariance of cluster 2
    [[.5, 0.], [0, .5]]  # covariance of cluster 3
]
init_weights = [1/4., 1/2., 1/4.]  # weights of each cluster

# Generate data
np.random.seed(4)
data = generate_MoG_data(1000, init_means, init_covariances, init_weights)

vals, indxs = np.histogramdd(d, normed=False,bins=20)
i=0
for indx in reversed(indxs):

    x = np.linspace(np.min(d[:,i]),np.max(d[:,i]),len(vals)) + np.diff(indx)
    if i==0:
        X = pd.DataFrame(x)
        X['i'] = 1
    else:
        newX = pd.DataFrame(x)
        newX['i'] = 1
        X = X.merge(newX,on='i',how='outer')
    i+=1

X.drop('i',inplace=True,axis=1)
vals = vals.flatten()
X = X.values
X = X[np.where(vals>0)]
vals = vals[np.where(vals>0)]
print(vals,X)


#multivariate normal sampler
def sampler_custom(self,best_param,
                                param_by_iter,
                                error_by_iter,
                                weight_history,
                                random_sample_num=100):
    
    best = param_by_iter[np.where(error_by_iter==np.min(error_by_iter))[0]]
    mean = best.flatten()
    r = []
    try:
        #w1 w3 (means)
        r[0] = np.random.normal(mean[0], 1, (random_sample_num)).T
        r[2] = np.random.normal(mean[2], 1, (random_sample_num)).T
        r[4] = np.random.normal(mean[4], 1, (random_sample_num)).T
        
        #w2 w4 (stds)
        r[1] = np.random.uniform(0.1,mean[1]+1, (random_sample_num)).T
        r[3] = np.random.uniform(0.1,mean[3]+1, (random_sample_num)).T
        r[5] = np.random.uniform(0.1,mean[5]+1, (random_sample_num)).T
        return np.array(r)
    except:
        print(best,np.where(error_by_iter==np.min(error_by_iter)))



def dist_loss(x,y,w):

        u11,u21 = w[0],w[2]
        s11,s21 = w[1],w[3]
        
        u12,u22 = w[4],w[6]
        s12,s22 = w[5],w[7]
        
        u13,u23 = w[8],w[10]
        s13,s23 = w[9],w[11]

        dist1 = stats.norm(u11,s11).pdf(x[:,0:1])
        dist2 = stats.norm(u21,s21).pdf(x[:,1:2])
        dist3 = stats.norm(u12,s12).pdf(x[:,0:1])
        dist4 = stats.norm(u22,s22).pdf(x[:,1:2])
        dist5 = stats.norm(u13,s13).pdf(x[:,0:1])
        dist6 = stats.norm(u23,s23).pdf(x[:,1:2])
         
        rv = (dist1+dist2+dist3+dist4+dist5+dist6)/6

        loss = np.sum(np.abs(y-rv))
        return loss/len(y)


start_time = time.time()
y = vals/np.max(vals)
model = kernelml.kernel_optimizer(X,y,dist_loss,num_param=12)
#change the random sampler
model.change_random_sampler(sampler_custom)
model.adjust_uniform_random_low_high(0.1,2.5)
model.kernel_optimize_(plot=True)    
end_time = time.time()
print("time:",end_time-start_time)

def generate_pdfs(x,y,w):
        u11,u21 = w[0],w[2]
        s11,s21 = w[1],w[3]
        
        u12,u22 = w[4],w[6]
        s12,s22 = w[5],w[7]
        
        u13,u23 = w[8],w[10]
        s13,s23 = w[9],w[11]
        rv = [  stats.norm(u11,s11).pdf(x[:,0:1]),stats.norm(u21,s21).pdf(x[:,1:2]),
                stats.norm(u12,s12).pdf(x[:,0:1]),stats.norm(u22,s22).pdf(x[:,1:2]),
                stats.norm(u13,s13).pdf(x[:,0:1]),stats.norm(u23,s23).pdf(x[:,1:2])
             ]
        return rv

params = model.best_parameters
error = model.best_losses
params = np.array(params)
w = params[np.where(error==np.min(error))].flatten()

df = pd.DataFrame(X)
df[['dist1','dist2','dist3','dist4','dist5','dist6']]=pd.DataFrame(np.squeeze(np.array(generate_pdf1(X,y,w)))).T
df['y'] = vals/np.max(vals)

#normalize the values
tmp = df[['dist1','dist2','dist3','dist4','dist5','dist6']].values
df[['dist1','dist2','dist3','dist4','dist5','dist6']] = tmp/np.linalg.norm(tmp,axis=0)

#combinations of distributions across each dimension
df[['c0','c1']] = pd.DataFrame(np.column_stack(
                        (np.argmax(df[['dist1','dist3','dist5']].values,axis=1),
                         np.argmax(df[['dist2','dist4','dist6']].values,axis=1)))
                         )
#assign category to each cluster
G = df[['c0','c1']].groupby(['c0','c1']).count().reset_index().reset_index()
df = df.merge(G,on=['c0','c1'])

#plot results
plt.figure(figsize=(10,10))
plt.scatter([x[0] for x in d], [y[1] for y in d])
for i in df['index'].unique():
    clust = T[[0,1,'index']][T['index']==i]
    plt.scatter([x[0] for x in clust[[0]].values], [y[0] for y in clust[[1]].values])
plt.show()