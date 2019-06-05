from sklearn.model_selection import train_test_split, cross_validate, cross_val_predict
from sklearn import metrics
from sklearn.model_selection import KFold

from sklearn.linear_model import LogisticRegression
from sklearn.naive_bayes  import MultinomialNB, GaussianNB
from sklearn.svm          import LinearSVC
from sklearn.tree         import DecisionTreeClassifier
from sklearn.ensemble     import RandomForestClassifier
import numpy as np

class PredictionEndpoint:

    def __init__(self, server):
        self.server = server
        self.predictions = {}

    def post_prediction(self, corpus_id):
        try:
            code, names, x = self.server.corpora.get_x_numpy(corpus_id)
            print("Got x shape {}".format(x.shape))
            code, y = self.server.corpora.get_y(corpus_id)
            code, vector_ids = self.server.corpora.get_vector_ids(corpus_id)
            instance_ids = [self.server.vectors.get_instance_id(v)[1] for v in vector_ids]
            mask = [self.server.vectors.get_is_full_discussion(v)[1] for v in vector_ids]
            print("Got y len {}".format(len(y)))
            task = Prediction(corpus_id, x, y, mask)
            task_id = task.id
            self.predictions[task_id] = task
            return 201, task_id

            # TODO For tomorrow - figure out how to pass in discussion IDs to the cross-validation
            # so that we can get predictions on a vote-by-vote basis even if we're just training on
            # final outcomes.
        except Exception as e:
            print(e)
            return 500, None

    """
    Params: ID (int) of a prediction set
    Returns: 200, A list of vote IDs that have been modified with a newly generated influence metric,
                  ranging from 0 to 1 (and in rare cases, small values < 1).
        or   500, None if something went wrong.
    """
    def put_influences(self, prediction_id):
        try:
            code, corpus_id = self.get_corpus_id(prediction_id)
            code, vector_ids = self.server.corpora.get_vector_ids(corpus_id)
            instance_ids = [self.server.vectors.get_instance_id(v)[1] for v in vector_ids]
            contrib_ids = [self.server.vectors.get_target_id(v)[1] for v in vector_ids]
            contribs = []
            for c in contrib_ids:
                if self.server.util.is_vote(c):
                    contribs.append(self.server.votes.get_label(c, normalized=self.server.config["normalized"])[1])
                elif self.server.util.is_comment(c):
                    contribs.append("Comment")
                else:
                    contribs.append(None)

            previous_probabilities = []
            return_ids = []
            prev_instance_id = None
            for i in range(len(vector_ids)):
                code, probabilities_just_before = self.get_probabilities(prediction_id, i)
                current_instance_id = instance_ids[i]
                if i > 0 and current_instance_id == prev_instance_id:
#                    print("Found {}".format(i))
                    influence = probabilities_just_before - previous_probabilities
#                    print("{} : {} {} {}".format(contribs[i-1], influence, probabilities_just_before, previous_probabilities))
                    influence_of_vote = 0
                    for inf in influence:
                        influence_of_vote += abs(inf)
#                        print("    {}".format(inf))
                    if contribs[i-1] == "Comment":
                        code, return_id = self.server.comments.put_influence(contrib_ids[i-1], influence_of_vote)
                    elif contribs[i-1] is not None:
                        code, return_id = self.server.votes.put_influence(contrib_ids[i-1], influence_of_vote)
                    if code == 200:
                        return_ids.append(return_id)
                    previous_probabilities = probabilities_just_before
                else:
#                    print("Lost {}".format(i))
                    code, probabilities = self.get_probabilities(prediction_id, i)
                    if code == 200:
                        previous_probabilities = probabilities
#                    print("----PRIORS RESET----")
                prev_instance_id = current_instance_id

            return 200, return_ids
        except Exception as e:
            print(e)
            return 500, None
        
    """
    Params: none
    Returns: 200, All known prediction sets on the server
        or   500, None if something went wrong.
    """
    def get_all(self):
        try:
            return 200, self.predictions.keys()
        except:
            return 500, None

    """
    Params: ID (int) of a particular prediction set to look up
    Returns: 200, One single Prediction object if found
        or   404, None if ID does not exist.
        or   500, None if something else went wrong.
    """
    def get_by_id(self, pred_id):
        try:
            if pred_id in self.predictions.keys():
                return 200, self.predictions[pred_id]
            else:
                return 404, None
        except:
            return 500, None


    """
    Params: ID (int) of a particular prediction set to look up
    Returns: 200, Corpus ID that this prediction set aligns to.
        or   404, None if ID does not exist.
        or   500, None if something else went wrong.
    """
    def get_corpus_id(self, pred_id):
        try:
            if pred_id in self.predictions.keys():
                return 200, self.predictions[pred_id].corpus_id
            else:
                return 404, None
        except:
            return 500, None

    """
    Params: ID (int) of a particular prediction set to look up
            i (int) index into the prediction set.
    Returns: 200, predicted label of the ith instance in the prediction corpus.
        or   404, None if that prediction ID does not exist.
        or   500, None if something else went wrong.
    """
    def get_prediction(self, prediction_id, i):
        try:
            if prediction_id in self.predictions.keys():
                pred = self.predictions[prediction_id]
                if i < len(pred.preds_y):
                    return 200, self.predictions[prediction_id].preds_y[i]
                else:
                    return 404, None
            else:
                return 404, None
        except:
            return 500, None
    
    """
    Params: ID (int) of a particular prediction set to look up
            i (int) index into the prediction set.
    Returns: 200, probability distribution of labels for the ith instance in the prediction corpus.
        or   404, None if that prediction ID does not exist.
        or   500, None if something else went wrong.
    Distribution labels are fixed: ["Delete", "Keep", "Merge", "Other", "Redirect"]
    """
    def get_probabilities(self, prediction_id, i):
        try:
            if prediction_id in self.predictions.keys():
                pred = self.predictions[prediction_id]
                if i < len(pred.preds_y):
                    return 200, self.predictions[prediction_id].probs_y[i]
                else:
                    return 404, None
            else:
                return 404, None
        except:
            return 500, None


class Prediction:
    global_id = 1
    
    def __init__(self, corpus_id, x, y, mask):
        self.corpus_id = corpus_id
        print("Initializing task")
#        learner = RandomForestClassifier()
#        learner = LinearSVC()
#        learner = MultinomialNB()
        num_folds = 2 if len(y) < 50 else 10

        print("Starting learner")
        labels = ["Delete", "Keep", "Merge", "Other", "Redirect"]


        kf = KFold(n_splits=num_folds)
        p_y = np.empty(len(y),dtype=object)
        fold = 1
        for train_index, test_index in kf.split(x):
            print("Training fold {}".format(fold))
            masked_train_index = list(filter(lambda x: mask[x], train_index))
            print("{} --> {}".format(len(train_index), len(masked_train_index)))
            X_tr, X_te = x[masked_train_index], x[test_index]
            Y_tr, Y_te = np.array(y)[masked_train_index], np.array(y)[test_index]
            print(X_tr.shape)
            print(Y_tr.shape)
            learner = LogisticRegression(multi_class='auto', solver='liblinear')
            learner.fit(X_tr, Y_tr)
            pys = learner.predict_proba(X_te)
            for i, index in enumerate(test_index):
                    p_y[index] = pys[i]
            fold += 1
        self.preds_y = [labels[np.argmax(p)] for p in p_y]
        self.probs_y = list(p_y)
        self.winner_probs = [p_y[i][labels.index(y[i])] for i, p in enumerate(p_y)]
        self.accuracy = 100*metrics.accuracy_score(y, self.preds_y)
        self.kappa = metrics.cohen_kappa_score(y, self.preds_y)
        self.confusion_matrix = metrics.confusion_matrix(y, self.preds_y)
        self.unique_labels = sorted(list(np.unique(y)))
        print("Accuracy of trained model: {}, {} K".format(self.accuracy, self.kappa))
        print(self.confusion_matrix)
        self.id = -(400000000 + Prediction.global_id)
        Prediction.global_id += 1