
import time
from re import A, M
import pandas as pd
from sklearn.neighbors import KNeighborsClassifier
from sklearn.neural_network import MLPClassifier
from extract_features import *
from classifiers.MOClassifier import MOClassifier
import random
import sys

MFCC_SET = [f'mfcc_{type}{i}' for i in range(1, 21) for type in {'mean', 'var'}]
FEATURE_SET = ['sc', 'zcr', 'rolloff']
 
class SelectFeatures:
    def __init__(self, model, length_range=(8, 36)):
        self.model = model
        self.features = [ f'{pref}_{suf}' for suf in {'mean', 'var'} for pref in FEATURE_SET] + ['tempo'] + MFCC_SET
        self.length_range = length_range
        self.data = pd.read_csv('data/data.csv')

    def rand_feature(self):
        num_features = len(self.features)
        return self.features[random.randint(0, num_features-1)]

    def rand_individual(self):
        a,b = self.length_range
        rand_size = random.randint(a, b)
        features = random.sample(self.features, k=rand_size)

        return features

    def evaluate(self, individual):
        full_data = self.data
        # data = full_data[feature_names]
        labels = full_data.iloc[:,-1]
        data = full_data[individual]
        self.model.fit(data,labels)
        preds = self.model.predict()
        classification_report = self.model.metrics(preds,dict=True)[1]

        return classification_report['accuracy']
        

    def optimize(self, population_size=100, generations=50):
        t0 = time.time()
        population = []

        for i in range(population_size):
            individual = self.rand_individual()
            cost = self.evaluate(individual)
            population.append((individual, cost))

        # note: this sorts by cost in ascending order (by accuracy)
        population.sort(key = lambda g : g[1], reverse=True)

        #POTENTIALLY ONLY MATE THE FITEST INDIVIDUALS AND FILL REST OF POPULATION WITH PARENTS
        for g in range(generations):
            print("Begin Generation: " + str(g))
            t1 = time.time()
            new_population = []            
            for i in range(0, len(population)//2, 2):
                a, b  = population[i], population[i+1]
                parent1, parent2 = a[0], b[0]
                child1 = self.reproduce_features(parent1,parent2, length=len(parent1))
                child2 = self.reproduce_features(parent1,parent2, length=len(parent2))

                t0_eval = time.time()
                new_population.append( (child1, self.evaluate(child1)) )
                print(f"Evaluate time: {time.time()-t0_eval}")

                t0_eval = time.time()
                new_population.append( (child2, self.evaluate(child2)) )
                print(f"Evaluate time: {time.time()-t0_eval}")

            half = len(population)//2
            population = population[:half] + new_population
            population.sort(key = lambda g : g[1], reverse=True)
            print('End Generation: ' + str(g) + ', Time: ' + str(time.time()-t1))
        print(time.time()-t0)
        print(population[0])
        return population[0][0] # return subset of features with highest score

    def interleave_uniq(self, parent1, parent2):
        i = 0; j = 0;
        n = len(parent1); m = len(parent2);
        is_i = True
        interleaved = []
        while i < n and j < m:
            if is_i:
                if parent1[i] not in interleaved:
                    interleaved.append(parent1[i])
                i+=1
            else:
                if parent2[j] not in interleaved:
                    interleaved.append(parent2[j])
                j+=1
            is_i = not is_i

        return interleaved

    # takes in as input two parent lists of features (no costs are provided)
    # called on both parents' lengths
    def reproduce_features(self, parent1, parent2, length=6):
        t0 = time.time()

        # crossover
        child = self.interleave_uniq(parent1, parent2)

        # if child is too small, add random features until it matches the individual size
        if len(child) < length: 
            unique_features = list(set(self.features).difference(set(child)))
            random.shuffle(unique_features)
            child_len = len(child)
            for i in range(0, length-child_len):
                rand_feature = unique_features[i]
                child.append(rand_feature)

        # if child is too long, clip the end
        child = child[:length] 

        if len(child) != 47:
        # mutate: randomly choose a gene to randomly change
            rand_gene_pos = random.randint(0, length-1)

            # keep trying until that feature is unique in the feature vector
            unique_features = list(set(self.features).difference(set(child)))
            rand_feature = random.choice(unique_features)
            # while rand_feature in child:
            #     # print(rand_feature)
            #     rand_feature = self.rand_feature()
            child[rand_gene_pos] = rand_feature

        # print(f"Reproduce time: {time.time()-t0}")
        return child
    


class GANets(SelectFeatures):

    def __init__(self):
        super().__init__(MOClassifier(MLPClassifier()))
    
    def rand_individual(self):
        a,b = self.length_range
        rand_size = random.randint(a, b)
        features = random.sample(self.features, k=rand_size)
        layers = random.randint(1,5)
        neurons = random.randint(1,47)
        return [features,layers,neurons]

    def evaluate(self, individual):
        full_data = pd.read_csv('data/data.csv')
        labels = full_data.iloc[:,-1]
        data = full_data[individual[0]]

        hidden_layers = np.full((individual[1]),individual[2])
        print(hidden_layers)
        self.model.setClassifier(MLPClassifier(hidden_layer_sizes=hidden_layers))
        self.model.fit(data,labels) 
        preds = self.model.predict()
        
        classification_report = self.model.metrics(preds,dict=True)[1]
        return classification_report['accuracy']

    def optimize(self, population_size=10, generations=10):
        t0 = time.time()
        population = []

        for i in range(population_size):
            individual = self.rand_individual()
            cost = self.evaluate(individual)
            population.append((individual, cost))

        # note: this sorts by cost in ascending order (by accuracy)
        population.sort(key = lambda g : g[1], reverse=True)

        #POTENTIALLY ONLY MATE THE FITEST INDIVIDUALS AND FILL REST OF POPULATION WITH PARENTS
        for g in range(generations):
            print("Begin Generation: " + str(g))
            t1 = time.time()
            new_population = []            
            for i in range(0, len(population)//2, 2):
                a, b  = population[i], population[i+1]
                parent1, parent2 = a[0], b[0]
                child1[0] = self.reproduce_features(parent1[0],parent2[0], length=len(parent1))
                child2[0] = self.reproduce_features(parent1[0],parent2[0], length=len(parent2))
                c1_net,c2_net = self.reproduce_nets(parent1,parent2)
                child1 = [child1,c1_net[1],c1_net[2]]
                child2 = [child2, c2_net[1], c2_net[2]]
                new_population.append( (child1, self.evaluate(child1)) )
                new_population.append( (child2, self.evaluate(child2)) )

            half = len(population)//2
            population = population[:half] + new_population
            population.sort(key = lambda g : g[1], reverse=True)
            print('End Generation: ' + str(g) + ', Time: ' + str(time.time()-t1))
        print(time.time()-t0)
        print(population[0])
        return population[0][0] # return subset of features with highest score
    
    def reproduce_nets(self, parent1, parent2):
        child1 = parent1
        child2 = parent2
        child1[1], child2[1] = (parent1[1] + parent2[1])//2
        
        mutate = random.randint(0,1)
        if mutate <= 0.07:
            child1[1] -= 1
        elif mutate <= 0.14:
            child2[1] -= 1
        elif mutate <= 0.21:
            child1[1] += 1
        elif mutate <= 0.28:
            child2[1] += 1
        elif mutate <= 0.32:
            child1[1] += 1
            child2[1] += 1
        elif mutate <= 0.36:
            child1[1] += 1
            child2[1] -= 1
        elif mutate <= 0.40:
            child1[1] -= 1
            child2[1] += 1
        elif mutate <= 0.44:
            child1[1] -= 1
            child2[1] -= 1
        
        child1[2], child2[2] = (parent1[2] + parent2[2])//2
        mutate = random.randint(0,1)
        if mutate <= 0.07:
            child1[2] -= 1
        elif mutate <= 0.14:
            child2[2] -= 1
        elif mutate <= 0.21:
            child1[2] += 1
        elif mutate <= 0.28:
            child2[2] += 1
        elif mutate <= 0.32:
            child1[2] += 1
            child2[2] += 1
        elif mutate <= 0.36:
            child1[2] += 1
            child2[2] -= 1
        elif mutate <= 0.40:
            child1[2] -= 1
            child2[2] += 1
        elif mutate <= 0.44:
            child1[2] -= 1
            child2[2] -= 1

        return child1,child2




""" neural net -- change different number of layers """

if __name__ == '__main__':
    #sf = GANets()
    knn = KNeighborsClassifier(5)
    sf = SelectFeatures(MOClassifier(knn))
    # ind = sf.rand_individual()
    # print(ind, len(ind))
    if len(sys.argv) > 1:
        print(sf.optimize(population_size=int(sys.argv[1])))
    else:
        print(sf.optimize())
    