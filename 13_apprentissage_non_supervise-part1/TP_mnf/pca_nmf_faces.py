# -*- coding: utf-8 -*-

# Authors: Vlad Niculae, Alexandre Gramfort, Slim Essid
# License: BSD

from time import time
from numpy.random import RandomState
import pylab as pl
import numpy as np

from sklearn.datasets import fetch_olivetti_faces
from sklearn import decomposition

from sklearn.discriminant_analysis import LinearDiscriminantAnalysis
from sklearn.cross_validation import ShuffleSplit
# -- Prepare data and define utility functions ---------------------------------

image_shape = (64, 64)
rng = RandomState(0)

# Load faces data
dataset = fetch_olivetti_faces(data_home='/tmp/',shuffle=True, random_state=rng)
faces = dataset.data


n_samples, n_features = faces.shape

# global centering
faces_centered = faces - faces.mean(axis=0, dtype=np.float64)

print "Dataset consists of %d faces" % n_samples
print "********************************"

def plot_gallery(title, images,n_col,n_row):
    pl.figure(figsize=(2. * n_col, 2.26 * n_row))
    pl.suptitle(title, size=16)
    for i, comp in enumerate(images):
        pl.subplot(n_row, n_col, i + 1)
        
        comp = comp.reshape(image_shape)
        vmax = comp.max()
        vmin = comp.min()
        dmy = np.nonzero(comp<0)
        if len(dmy[0])>0:
            yz, xz = dmy            
        comp[comp<0] = 0

        pl.imshow(comp, cmap=pl.cm.gray, vmax=vmax, vmin=vmin)
        #print "vmax: %f, vmin: %f" % (vmax, vmin)
        #print comp
        
        if len(dmy[0])>0:
            pl.plot( xz, yz, 'r,', hold=True)
            print len(dmy[0]), "negative-valued pixels"
                  
        pl.xticks(())
        pl.yticks(())
        
    pl.subplots_adjust(0.01, 0.05, 0.99, 0.93, 0.04, 0.)
    
# Plot a sample of the input data
plot_gallery("First centered Olivetti faces", faces_centered[:25],5,5)

# -- Decomposition methods -----------------------------------------------------
labels = dataset.target
X = faces
X_ = faces_centered

# cross-validaton shuffle
cv = 5
rs = ShuffleSplit(n_samples,n_iter=cv,test_size=0.2)

# list of number of components
n_components_list = [5,10,15,20,25,30,35] # shoud be multiple of 5
scores_pca = np.zeros(len(n_components_list))
scores_nmf = np.zeros(len(n_components_list))

for i,n_components in enumerate(n_components_list):

    # List of the different estimators and whether to center the data
    estimators = [
        ('pca', 'Eigenfaces - PCA',
	     decomposition.PCA(n_components=n_components, whiten=True),
	     True),

	('nmf', 'Non-negative components - NMF',
	     decomposition.NMF(n_components=n_components, init='random', tol=1e-6, 
			       sparseness=None, max_iter=1000), 
	     False)
	]

    # -- Transform and classify ----------------------------------------------------
    for shortname, name, estimator, center in estimators:
        #if shortname != 'nmf': continue
        print "Extracting the top %d %s..." % (n_components, name)
        print "*****************************************************"
        t0 = time()
     
        data = X
        if center:
    	    data = X_
        print "--- Cross validation using LDA %d-cross-validation..." % (cv) 
	scores = []
        for train_index,test_index in rs:
		X_train = data[train_index,:]
		y_train = labels[train_index]
		X_test = data[test_index,:]
		y_test = labels[test_index]
		X_train_reduced = estimator.fit_transform(X_train) 
		X_test_reduced = estimator.transform(X_test) 
		clf_lda = LinearDiscriminantAnalysis()
		clf_lda.fit(X_train_reduced,y_train)
		scores.append(clf_lda.score(X_test_reduced,y_test))
        mean_score = np.mean(np.asarray(scores))
	print "--- Cross validation scores : ",scores
	print "--- Cross validation mean score : %f" % mean_score
        if shortname == 'pca':
            scores_pca[i] = mean_score
        else:
            scores_nmf[i] = mean_score
	train_time = (time() - t0)
	print "--- done in %0.3fs" % train_time
	 
	components_ = estimator.components_
	plot_gallery('%s - Train time %.1fs' % (name, train_time),
	components_[:n_components],n_components/5,5)
	# pl.show()

pl.clf()
pl.title('Scores depending on number of components')
pl.ylabel('score (%)')
pl.xlabel('number of components')
pl.plot(n_components_list,100*scores_pca,'g',label='PCA')
pl.plot(n_components_list,100*scores_nmf,'b',label='NMF')
pl.legend()
pl.savefig('pca_nmf_faces_scores.png')
#pl.show()
