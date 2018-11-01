# @Author      : 'Savvy'
# @Created_date: 2018/10/25 9:13 PM

from sklearn import svm
from database import Database
from sklearn.externals import joblib
from sklearn.cross_validation import train_test_split

def train():
    print("Initialize database...")
    Database.initialize()
    gesture = []
    label = []

    trainData = Database.find(collection='Accelerometer1', query={})
    for data in trainData:
        print(type(data['label']))
        label.append(data['label'])
        # l = [int(i) for i in data['data']]
        # print(type(data['data'][0]))
        gesture.append(data['data'])
    
    print("label:\n", label)
    print("data:\n", gesture)
    a_train, a_test, b_train, b_test = train_test_split(gesture, label, test_size=0.33, random_state=42)
    clf = svm.SVC(kernel='poly')
    clf.fit(a_train, b_train)
    print(clf.predict(a_test))
    print(b_test)
    joblib.dump(clf, 'COLUMBIA_SVM_3.joblib')


train()
